"""Archived payload -> structured records. Stdlib-only, offline, deterministic.

This is the *rebuildable derived layer* (SPEC-01 §3 doctrine: raw is immutable and authoritative,
everything downstream is recomputable from it). Nothing here fetches: every input is bytes already
pulled from the archive, so a page can never be built from a live endpoint.

Formats the WARN fleet actually archives (verified against real R2 vintages 2026-07-29):
  csv / socrata-csv  TX
  xlsx               CA (multi-sheet: Index + Summary + Detailed report), IL, NJ (sheet per year)
  html / html-table  MD, FL, NY (retired table), WA, PA, WI

Honesty rule: a state whose payload does NOT yield a header we recognize returns [] and the site
labels it "archived, not yet machine-readable" — it never guesses at a company or a headcount.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import xml.etree.ElementTree as ET
import zipfile
from datetime import date, timedelta
from html.parser import HTMLParser

import zstandard as zstd

# Bump on ANY change to the extraction rules below: a consumer must be able to tell a real shift in
# the underlying notices from a change in how we read them (the SPEC-01 §3 schema-version rule).
EXTRACT_VERSION = "warn-extract-v1"

# Canonical WARN notice fields -> header substrings seen in the live sources, MOST SPECIFIC FIRST.
# Matching is on the *source's own header text*, never on column position: states reorder columns
# between vintages and positional parsing fails silently. Earlier hints outrank later ones, so
# IL's "COUNTY:" wins over its "COMPANY ADDRESS:" and its "TYPE OF LAYOFF:" over "TYPE OF COMPANY:".
FIELD_HINTS = {
    "company": ("company name", "job_site_name", "employer", "business name", "company"),
    "notice_date": ("state notification date", "notice date", "notice_date", "date posted",
                    "date received", "received date", "wfdd_received_date", "month posted"),
    "effective_date": ("effective date", "effective_ date", "layoff start date", "layoff date",
                       "layoff_date", "date of layoff", "effective"),
    "employees": ("total employees", "employees affected", "workers affected", "no. of employees",
                  "no. of workers", "# of workers", "workforce affected", "total_layoff_number",
                  "number of employees", "employees", "workers", "affected"),
    "location": ("county/parish", "county_name", "county", "local area", "city_name", "city",
                 "location", "region", "address"),
    "kind": ("layoff/ closure", "layoff/closure", "type of layoff", "type of event", "closure layoff",
             "notice type", "type"),
}

# A row that is really a pagination control / footer, not a notice (FL renders "1 2 >" as a row).
_JUNK_ROW = re.compile(r"^[\s\d>«»<|·,\-–—]*$")


def notice_id(state: str, rec: dict, occurrence: int = 0) -> str:
    """Stable id for one notice: the receipts key and the feed's dedupe key. Derived from the
    notice's own content, so re-extracting the same archived bytes yields the same id forever.

    `occurrence` disambiguates rows a source cannot tell apart itself — NY publishes only
    (company, region, two dates), so two real notices from one employer collide. Collapsing them
    would silently undercount layoffs, so the Nth repeat within a table gets its own id."""
    basis = "|".join([state, rec.get("company", ""), rec.get("notice_date", ""),
                      rec.get("effective_date", ""), str(rec.get("employees", "")),
                      rec.get("location", "")])
    if occurrence:
        basis += f"|#{occurrence}"
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()[:16]


def compare_key(rec: dict) -> tuple:
    """The key used to decide whether a notice is NEW since the previous archived vintage.

    Deliberately narrower than `notice_id`, which pins every field so a receipt addresses one exact
    row. If a state adds or drops a column between vintages, every full-field id changes at once
    and an unchanged list would read as entirely new filings. Identity here is the employer, the
    date the source gives, and the headcount — the fields a WARN notice is actually about."""
    return (rec.get("state", ""), rec.get("company", "").lower(),
            rec.get("notice_date") or rec.get("effective_date") or "", rec.get("employees"))


# --------------------------------------------------------------------------- value normalizers
def _clean(x) -> str:
    return re.sub(r"\s+", " ", (x or "")).strip()


def _clean_multiline(x) -> str:
    """Collapse whitespace WITHIN each line but keep the line breaks, because a `<br>` inside a
    cell is structure: FL packs company + street + city into one <td> separated by them, and
    flattening first would publish 'COLSA Corporation 591 Eglin BoulevardEGLIN AFB, FL' as a
    company name. Callers split on "\\n" to recover the source's own fields."""
    lines = [_clean(ln) for ln in (x or "").split("\n")]
    return "\n".join(ln for ln in lines if ln)


def excel_serial_to_iso(v: str) -> str:
    """Excel stores dates as day counts (CA/NJ archive them raw: 46203 == 2026-07-14). Excel's
    1900 epoch carries the deliberate leap-year bug, so day 1 == 1900-01-01 == base 1899-12-30.
    Only plausible serials convert; anything else is left alone rather than mangled."""
    try:
        n = int(str(v).strip())
    except (TypeError, ValueError):
        return ""
    if not 20000 <= n <= 80000:          # ~1954..2119 — outside this it is a headcount, not a date
        return ""
    return (date(1899, 12, 30) + timedelta(days=n)).isoformat()


def parse_date(v) -> str:
    """-> ISO date, or "" if this value is not confidently a date. Never invents a date."""
    s = _clean(str(v).split("\n")[0])            # a range cell ("9/30/26<br>thru<br>10/4/26") starts
    if not s:                                    # at its first date; the range end is not the date
        return ""
    iso = excel_serial_to_iso(s)
    if iso:
        return iso
    s = s.split(" thru ")[0].split(" - ")[0].split("(")[0].strip()   # "7/1 thru 7/9", "x (Amended)"
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", s)                     # ISO / Socrata timestamps
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    m = re.match(r"^(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})$", s)        # US m/d/y and m-d-y
    if m:
        mm, dd, yy = int(m.group(1)), int(m.group(2)), int(m.group(3))
        yy += 2000 if yy < 100 else 0
        try:
            return date(yy, mm, dd).isoformat()
        except ValueError:
            return ""
    return ""


def parse_int(v):
    """-> int, or None. '4(Remote workers in MD)' -> 4; '' -> None. Never guesses a headcount."""
    m = re.search(r"\d[\d,]*", _clean(str(v)))
    return int(m.group(0).replace(",", "")) if m else None


def map_header(header) -> dict:
    """Header row -> {canonical_field: column_index}. The most specific hint (earliest in the
    field's list) wins; each column is claimed by at most one field, so a single 'Date' column
    cannot become both the notice date and the effective date."""
    cols = [_clean(h).lower().replace("\n", " ") for h in header]
    out, taken = {}, set()
    for field, hints in FIELD_HINTS.items():
        best = None
        for i, c in enumerate(cols):
            if i in taken or not c:
                continue
            for rank, hint in enumerate(hints):
                if hint in c:
                    score = (-rank, len(hint))
                    if best is None or score > best[0]:
                        best = (score, i)
                    break
        if best is not None:
            out[field] = best[1]
            taken.add(best[1])
    return out


def rows_to_notices(rows, state: str, source_label: str = "", stats: dict | None = None) -> list:
    """[[header...], [row...]] -> canonical notice records. Needs a company column AND at least one
    date or headcount column, or it declines to interpret the table at all (returns []).

    `stats` (optional dict) accumulates what was NOT published, so the gap between a source's row
    count and our notice count is disclosed rather than buried: TX ships one row with an empty
    employer field, and a notice with no employer cannot be published as a named fact."""
    rows = [r for r in rows if any(_clean(c) for c in r)]
    for hi, header in enumerate(rows[:8]):            # the header is rarely row 0 (CA: title row)
        m = map_header(header)
        if "company" in m and ({"notice_date", "effective_date", "employees"} & set(m)):
            break
    else:
        return []
    out, occurrences = [], {}
    for r in rows[hi + 1:]:
        if len(r) < 2 or _JUNK_ROW.match(" ".join(_clean(c) for c in r)):
            continue                                   # pagination/footer control, not a notice

        def cell(f, flatten=True):
            i = m.get(f)
            if i is None or i >= len(r):
                return ""
            v = _clean_multiline(r[i])
            return _clean(v.replace("\n", " ")) if flatten else v

        packed = cell("company", flatten=False).split("\n")
        company = packed[0]
        if company.lower() == _clean(header[m["company"]]).lower():
            continue                                   # a repeated header row mid-table (IL)
        if not company:
            # Only a row that otherwise LOOKS like a notice counts as an unnamed one. IL's sheet
            # carries section headers ("SUPPLEMENTAL NOTICES"), a totals line and a disclaimer —
            # all company-less, none a notice — and reporting those as suppressed employers would
            # itself be a false statement.
            if stats is not None and sum(1 for c in r if _clean(str(c))) >= 3:
                stats["unnamed_rows"] = stats.get("unnamed_rows", 0) + 1
            continue                                   # no employer named -> not publishable
        # A source that packs address lines under the company (FL) supplies the location itself;
        # only fall back to them when the table has no location column of its own.
        location = cell("location") or _clean(" ".join(packed[1:]))
        rec = {"state": state, "company": company,
               "notice_date": parse_date(cell("notice_date", flatten=False)),
               "effective_date": parse_date(cell("effective_date", flatten=False)),
               "employees": parse_int(cell("employees")),
               "location": location, "kind": cell("kind"),
               "source_label": source_label}
        base = notice_id(state, rec)
        n = occurrences.get(base, 0)
        occurrences[base] = n + 1
        rec["id"] = notice_id(state, rec, n)           # n==0 keeps the plain content-derived id
        out.append(rec)
    return out


# --------------------------------------------------------------------------- format readers
def read_csv(raw: bytes, delimiter=",") -> list:
    text = raw.decode("utf-8-sig", errors="replace")
    return [list(r) for r in csv.reader(io.StringIO(text), delimiter=delimiter)]


_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"


def _xlsx_shared_strings(zf) -> list:
    if "xl/sharedStrings.xml" not in zf.namelist():
        return []
    root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
    return ["".join(t.text or "" for t in si.iter(f"{_NS}t")) for si in root.findall(f"{_NS}si")]


def _xlsx_sheet_rows(zf, name: str, sst: list) -> list:
    """One worksheet -> list of rows. Honors the cell's column letter so a sparse row keeps its
    alignment with the header (a skipped empty cell would otherwise shift every later column)."""
    rows = []
    for row in ET.fromstring(zf.read(name)).iter(f"{_NS}row"):
        cells = {}
        for c in row.findall(f"{_NS}c"):
            ref = c.get("r") or ""
            letters = "".join(ch for ch in ref if ch.isalpha())
            idx = 0
            for ch in letters:
                idx = idx * 26 + (ord(ch.upper()) - 64)
            idx = max(idx - 1, 0)
            t, v = c.get("t"), c.find(f"{_NS}v")
            if t == "s" and v is not None and v.text is not None:
                try:
                    val = sst[int(v.text)]
                except (ValueError, IndexError):
                    val = ""
            elif t == "inlineStr":
                val = "".join(x.text or "" for x in c.iter(f"{_NS}t"))
            else:
                val = v.text if v is not None else ""
            cells[idx] = _clean(val)
        if cells:
            rows.append([cells.get(i, "") for i in range(max(cells) + 1)])
        else:
            rows.append([])
    return rows


def read_xlsx_sheets(raw: bytes) -> list:
    """-> [(sheet_name, rows)] for every worksheet, densest first. CA ships an Index sheet, a
    summary, the detailed report, and a call-center report in one workbook — the caller picks the
    first sheet whose header we recognize rather than assuming sheet 1 is the data."""
    zf = zipfile.ZipFile(io.BytesIO(raw))
    names = {}
    try:
        for i, s in enumerate(ET.fromstring(zf.read("xl/workbook.xml")).iter(f"{_NS}sheet"), 1):
            names[f"xl/worksheets/sheet{i}.xml"] = s.get("name") or f"sheet{i}"
    except Exception:
        pass
    sst = _xlsx_shared_strings(zf)
    out = []
    for n in sorted(x for x in zf.namelist()
                    if x.startswith("xl/worksheets/") and x.endswith(".xml") and "_rels" not in x):
        try:
            out.append((names.get(n, n), _xlsx_sheet_rows(zf, n, sst)))
        except Exception:
            continue                                  # one unreadable sheet must not lose the rest
    out.sort(key=lambda t: -len(t[1]))
    return out


class _TableParser(HTMLParser):
    """Every <table> on the page -> list of rows. Keeps a STACK so a table nested inside a layout
    table (WA does exactly this) neither truncates its parent nor vanishes. A <br> becomes a real
    line break in the cell text: FL separates company/street/city that way, and the source's own
    structure is the only honest way to tell them apart."""

    _BREAKS = ("br", "p", "div", "li")

    def __init__(self):
        super().__init__()
        self.tables, self._stack, self._cell = [], [], None

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self._stack.append([])
        elif tag == "tr" and self._stack:
            self._stack[-1].append([])
        elif tag in ("td", "th") and self._stack and self._stack[-1]:
            self._cell = []
        elif tag in self._BREAKS and self._cell is not None:
            self._cell.append("\n")

    def handle_startendtag(self, tag, attrs):        # <br/>
        self.handle_starttag(tag, attrs)

    def handle_data(self, d):
        if self._cell is not None:
            # Collapse the source's own line wrapping FIRST. Only a tag may create a line break:
            # MD's markup wraps "Taft Broadcasting,\n LLC" mid-name, and treating that newline as
            # structure would publish the company as "Taft Broadcasting," — a wrong legal name.
            self._cell.append(re.sub(r"\s+", " ", d))

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self._cell is not None:
            self._stack[-1][-1].append(_clean_multiline("".join(self._cell)))
            self._cell = None
        elif tag in self._BREAKS and self._cell is not None:
            self._cell.append("\n")                   # FL emits the invalid-but-common `</br>`
        elif tag == "table" and self._stack:
            t = self._stack.pop()
            self.tables.append([r for r in t if r])


def read_html_tables(raw: bytes) -> list:
    p = _TableParser()
    p.feed(raw.decode("utf-8", errors="replace"))
    for t in p._stack:                               # unclosed <table> — keep what we parsed
        p.tables.append([r for r in t if r])
    p.tables.sort(key=lambda t: -len(t))
    return p.tables


# --------------------------------------------------------------------------- the dispatcher
def decompress(key: str, blob: bytes) -> bytes:
    """Archive objects are stored .zst unless the source format was already compressed."""
    if key.endswith(".zst"):
        return zstd.ZstdDecompressor().decompress(blob, max_output_size=512 * 1024 * 1024)
    return blob


def _dedupe(recs: list) -> list:
    """Same notice id twice = the same notice rendered twice (NJ repeats a company across its
    per-year sheets; a page can print its table in a mobile and a desktop copy). Keep the first."""
    seen, out = set(), []
    for r in recs:
        if r["id"] not in seen:
            seen.add(r["id"])
            out.append(r)
    return out


def extract_notices(fmt: str, raw: bytes, state: str, stats: dict | None = None) -> list:
    """Archived WARN payload -> canonical notices. Never raises: an unreadable payload is a page
    that says 'archived, not yet machine-readable', never a page with a made-up number."""
    fmt = (fmt or "").lower()
    try:
        if fmt in ("csv", "socrata-csv", "tsv"):
            return rows_to_notices(read_csv(raw, "\t" if fmt == "tsv" else ","), state, "csv", stats)
        if fmt == "xlsx":
            # EVERY readable sheet, not just the densest: NJ files one sheet per year, so taking
            # the biggest would publish 2020's notices and silently drop this year's.
            out = []
            for sheet_name, rows in read_xlsx_sheets(raw):
                out += rows_to_notices(rows, state, f"xlsx:{sheet_name}", stats)
            return _dedupe(out)
        if fmt in ("html", "html-table"):
            out = []
            for i, t in enumerate(read_html_tables(raw)):
                out += rows_to_notices(t, state, f"html:table[{i}]", stats)
            return _dedupe(out)
        if fmt in ("json", "socrata-json"):
            j = json.loads(raw)
            recs = j if isinstance(j, list) else next(
                (j[k] for k in ("data", "results", "records", "value") if isinstance(j.get(k), list)), [])
            if not recs or not isinstance(recs[0], dict):
                return []
            header = list(recs[0].keys())
            return rows_to_notices([header] + [[r.get(k, "") for k in header] for r in recs],
                                   state, "json", stats)
    except Exception:
        return []
    return []
