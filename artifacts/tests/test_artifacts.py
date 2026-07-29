"""Artifact compiler tests (offline, deterministic). Run:
    python -m artifacts.tests.test_artifacts
    python -m pytest artifacts/tests/test_artifacts.py

Fixtures reproduce the SHAPES the live sources actually ship (verified against archived R2
vintages 2026-07-29): a Socrata CSV with ISO timestamps, a multi-sheet workbook with Excel serial
dates, and an HTML table that packs company + address into one cell with <br>.
"""
from __future__ import annotations

import io
import json
import os
import zipfile
from datetime import date

from artifacts import compile as ac
from artifacts import extract, templates
from collectors.framework import LocalFSBackend, sha256_hex
from resolver import receipts

TODAY = date(2026, 7, 29)


# --------------------------------------------------------------------------- fixtures
def _xlsx(sheets):
    """Minimal real .xlsx: {sheet_name: [[cell,...],...]} -> bytes. Inline strings only, so the
    reader's sharedStrings path and its inlineStr path are both exercised across the suite."""
    from xml.sax.saxutils import escape

    def cell(ci, r, v):
        col = chr(ord("A") + ci)
        if isinstance(v, (int, float)):
            return f'<c r="{col}{r}"><v>{v}</v></c>'
        return f'<c r="{col}{r}" t="inlineStr"><is><t>{escape(str(v))}</t></is></c>'

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("[Content_Types].xml",
                   '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/'
                   'package/2006/content-types"/>')
        names = "".join(f'<sheet name="{n}" sheetId="{i}" r:id="rId{i}"/>'
                        for i, n in enumerate(sheets, 1))
        z.writestr("xl/workbook.xml",
                   '<?xml version="1.0"?><workbook xmlns="http://schemas.openxmlformats.org/'
                   f'spreadsheetml/2006/main" xmlns:r="r"><sheets>{names}</sheets></workbook>')
        for i, (name, rows) in enumerate(sheets.items(), 1):
            xml = []
            for r, row in enumerate(rows, 1):
                cells = "".join(cell(ci, r, v) for ci, v in enumerate(row))
                xml.append(f'<row r="{r}">{cells}</row>')
            z.writestr(f"xl/worksheets/sheet{i}.xml",
                       '<?xml version="1.0"?><worksheet xmlns="http://schemas.openxmlformats.org/'
                       f'spreadsheetml/2006/main"><sheetData>{"".join(xml)}</sheetData></worksheet>')
    return buf.getvalue()


CSV_TX = (b'"notice_date","job_site_name","county_name","total_layoff_number","layoff_date"\n'
          b'"2026-07-20T00:00:00.000","Acme Freight","Bexar","120","2026-09-01T00:00:00.000"\n'
          b'"2026-07-18T00:00:00.000","Borden Mills","Harris","45","2026-08-15T00:00:00.000"\n'
          b'"2026-07-17T00:00:00.000","","Travis","9","2026-08-10T00:00:00.000"\n')

HTML_FL = (b"<html><body><table>"
           b"<thead><tr><th>Company Name</th><th>State Notification Date</th>"
           b"<th>Layoff Date</th><th>Employees Affected</th></tr></thead>"
           b"<tfoot><tr><td colspan=4>1 2 &gt;</td></tr></tfoot><tbody>"
           b"<tr><td><b>COLSA Corporation</b> </br>591 Eglin Boulevard</br>EGLIN AFB, FL</td>"
           b"<td>07-27-26</td><td>09-30-26</br><i> thru </i></br>10-04-26</td><td>97</td></tr>"
           b"<tr><td>Gulf Diner,\n LLC</td><td>07-21-26</td><td>08-01-26</td><td>12</td></tr>"
           b"</tbody></table></body></html>")

# Two rows a source cannot tell apart: same employer, region and dates, no headcount column.
HTML_NY = (b"<html><table><tr><th>Company Name</th><th>Region</th><th>Notice Dated</th></tr>"
           b"<tr><td>Plug Power, Inc.</td><td>Capital</td><td>3/25/2026</td></tr>"
           b"<tr><td>Plug Power, Inc.</td><td>Capital</td><td>3/25/2026</td></tr></table></html>")

XLSX_CA = _xlsx({
    "Index": [["This worksheet contains 5 sheets."], ["WARN Report Index"]],
    "WARN Report Summary": [["Summary table"], ["Report Summary", "Total"],
                            ["Employees Affected", 3297]],
    "Detailed WARN Report": [
        ["WARN REPORT - 07/01/26 to 07/27/2026"],
        ["County/Parish", "Notice Date", "Company", "No. Of Employees", "Address"],
        ["Monterey County", 46230, "PD Systems", 81, "1 Main St"],
        ["Los Angeles County", 46227, "Chick-fil-A & Fig", 77, "2 Fig St"],
    ],
})


def _seed(tmp, states=None, boards=None):
    root = str(tmp)
    os.makedirs(os.path.join(root, "collectors"), exist_ok=True)
    json.dump({"states": states if states is not None else []},
              open(os.path.join(root, "collectors", "seed_warn.json"), "w", encoding="utf-8"))
    json.dump({"boards": boards if boards is not None else []},
              open(os.path.join(root, "collectors", "seed_boards.json"), "w", encoding="utf-8"))
    return root


def _archive(storage, prefix, d, fname, raw, meta=None):
    """Store a payload the way a collector does, plus its per-day manifest entry."""
    datepath = f"{prefix}/{d:%Y}/{d:%m}/{d:%d}"
    storage.put(f"raw/{datepath}/{fname}", raw)
    mkey = f"raw/{datepath}/manifest.json"
    man = json.loads(storage.get(mkey) or b'{"files": []}')
    man.setdefault("files", []).append(
        {"file": fname, "sha256": sha256_hex(raw), "stored_at": f"{d:%Y-%m-%d}T12:00:00Z",
         **(meta or {})})
    storage.put(mkey, json.dumps(man).encode())


# --------------------------------------------------------------------------- extraction
def test_csv_extraction_and_unnamed_row_is_counted_not_published():
    stats = {}
    got = extract.extract_notices("socrata-csv", CSV_TX, "TX", stats)
    assert [n["company"] for n in got] == ["Acme Freight", "Borden Mills"]
    assert got[0]["notice_date"] == "2026-07-20" and got[0]["effective_date"] == "2026-09-01"
    assert got[0]["employees"] == 120 and got[0]["location"] == "Bexar"
    # the third row names no employer: not publishable as a named fact, but disclosed
    assert stats["unnamed_rows"] == 1


def test_html_cell_breaks_split_company_from_address():
    got = extract.extract_notices("html", HTML_FL, "FL")
    assert [n["company"] for n in got] == ["COLSA Corporation", "Gulf Diner, LLC"]
    assert got[0]["location"] == "591 Eglin Boulevard EGLIN AFB, FL"
    assert got[0]["effective_date"] == "2026-09-30"        # start of the range, not the end
    # a company name wrapped across source lines keeps its suffix
    assert got[1]["company"].endswith("LLC")
    # the pagination row in <tfoot> is not a notice
    assert all("1 2" not in n["company"] for n in got)


def test_identical_source_rows_are_two_notices_not_one():
    got = extract.extract_notices("html", HTML_NY, "NY")
    assert len(got) == 2, "collapsing indistinguishable rows would undercount layoffs"
    assert len({n["id"] for n in got}) == 2


def test_excel_serial_dates_decode_against_known_anchors():
    """CA and NJ archive dates as raw Excel day counts. Anchored on serials whose calendar dates
    are independently known, so the 1900-leap-year-bug offset cannot drift unnoticed."""
    assert extract.excel_serial_to_iso("44197") == "2021-01-01"
    assert extract.excel_serial_to_iso("45292") == "2024-01-01"
    assert extract.excel_serial_to_iso("46023") == "2026-01-01"


def test_xlsx_picks_the_data_sheet_and_decodes_serial_dates():
    """The data is not sheet 1: CA ships an index page and a summary ahead of the detail table,
    and a reader that assumed the first sheet would publish a disclaimer as a layoff list."""
    got = extract.extract_notices("xlsx", XLSX_CA, "CA")
    assert [n["company"] for n in got] == ["PD Systems", "Chick-fil-A & Fig"]
    assert got[0]["notice_date"] == "2026-07-27" == extract.excel_serial_to_iso("46230")
    assert got[0]["employees"] == 81 and got[0]["location"] == "Monterey County"


def test_header_mapping_prefers_the_specific_column():
    m = extract.map_header(["COMPANY NAME:", "COMPANY ADDRESS:", "COUNTY:", "TYPE OF COMPANY:",
                            "TYPE OF LAYOFF:", "WARN RECEIVED DATE:", "WORKERS AFFECTED:"])
    assert m["company"] == 0                       # not the ADDRESS column, which also says COMPANY
    assert m["location"] == 2                      # COUNTY beats ADDRESS
    assert m["kind"] == 4                          # TYPE OF LAYOFF beats TYPE OF COMPANY
    assert m["notice_date"] == 5 and m["employees"] == 6
    assert len(set(m.values())) == len(m)          # no column claimed twice


def test_unreadable_payload_yields_nothing_rather_than_a_guess():
    assert extract.extract_notices("html", b"<html><p>See the PDF links below.</p></html>", "PA") == []
    assert extract.extract_notices("xlsx", b"not a zip", "CA") == []
    assert extract.parse_date("sometime next year") == ""
    assert extract.excel_serial_to_iso("120") == ""            # a headcount is not a date


# --------------------------------------------------------------------------- templates
def test_only_approved_templates_render():
    text, kind = templates.render("warn_state_level", state="TX", n=1, as_of="2026-07-28")
    assert "1 notice" in text and kind == templates.CADENCE
    try:
        templates.render("layoffs_are_accelerating", state="TX")
    except templates.UnapprovedTemplate as e:
        assert "not an approved artifact template" in str(e)
    else:
        raise AssertionError("an unapproved claim shape must not render")


# --------------------------------------------------------------------------- compiler
def _compile_fixture(tmp, *, two_vintages=True):
    root = _seed(tmp, states=[{"state": "TX", "agency": "TWC", "format": "socrata-csv",
                               "data_url": "https://example.invalid/warn.csv"},
                              {"state": "PA", "agency": "PA DLI", "format": "html"}],
                 boards=[{"ats": "greenhouse", "token": "acme", "company": "Acme"}])
    storage = LocalFSBackend(os.path.join(root, "archive"))
    if two_vintages:
        _archive(storage, "warn/TX", date(2026, 7, 28), "1200-a.csv",
                 b'"notice_date","job_site_name","county_name","total_layoff_number","layoff_date"\n'
                 b'"2026-07-20T00:00:00.000","Acme Freight","Bexar","120","2026-09-01T00:00:00.000"\n')
    _archive(storage, "warn/TX", date(2026, 7, 29), "1200-b.csv", CSV_TX)
    _archive(storage, "warn/PA", date(2026, 7, 29), "1200-c.html", b"<html><p>links only</p></html>")
    board = json.dumps({"jobs": [{"id": 1, "title": "Engineer", "absolute_url": "u1"},
                                 {"id": 2, "title": "Designer", "absolute_url": "u2"}]}).encode()
    board2 = json.dumps({"jobs": [{"id": 2, "title": "Designer", "absolute_url": "u2"}]}).encode()
    _archive(storage, "ats-boards/greenhouse/acme", date(2026, 7, 28), "1200-a.json", board,
             {"postings": 2})
    _archive(storage, "ats-boards/greenhouse/acme", date(2026, 7, 29), "1200-b.json", board2,
             {"postings": 1})
    res = ac.compile_all(storage, root, days=7, today=TODAY, code_ref="deadbeef")
    return root, res


def test_compiler_emits_receipted_artifacts_from_the_archive(tmp_path):
    root, res = _compile_fixture(tmp_path)
    arts = json.load(open(os.path.join(root, "site", "data", "artifacts.json"),
                          encoding="utf-8"))["artifacts"]
    texts = [a["text"] for a in arts]
    assert any("TX published 1 new WARN notice covering 45 workers" in t for t in texts), texts
    assert any("Acme removed 1 of 2 public job postings" in t for t in texts), texts

    # EVERY published number has a bundle that validates, pinning the exact archived inputs
    for a in arts:
        assert receipts.has_valid_bundle(res["receipts_root"], a["index"], a["id"]), a["id"]
        b = json.load(open(receipts.bundle_path(res["receipts_root"], a["index"], a["id"]),
                           encoding="utf-8"))
        assert b["code_ref"] == "deadbeef" and b["inputs"]
        assert all(i["r2_path"].startswith("raw/") and i["sha256"] for i in b["inputs"])

    warn = json.load(open(os.path.join(root, "site", "data", "warn.json"), encoding="utf-8"))
    pa = next(s for s in warn["states"] if s["state"] == "PA")
    assert pa["parse_status"] == "unreadable" and pa["latest_sha256"], \
        "an unreadable state stays archived and hashed; it just publishes no count"


def test_no_delta_artifact_without_a_second_vintage(tmp_path):
    """The cadence claim is 'new since the last archived vintage'. With only one vintage there is
    no 'since', so the compiler must publish the level and stay silent about change."""
    root, res = _compile_fixture(tmp_path, two_vintages=False)
    arts = json.load(open(os.path.join(root, "site", "data", "artifacts.json"),
                          encoding="utf-8"))["artifacts"]
    assert not [a for a in arts if a["template"] == "warn_new_notices"]
    assert [a for a in arts if a["template"] == "warn_state_level"]


def test_a_reshaped_source_does_not_publish_as_mass_new_filings(tmp_path):
    """If a state renames or reorders its columns, every row can look new at once. That is a
    source changing shape, not a wave of layoffs, and publishing it as one would be a retraction
    waiting to happen — so the change figure is withheld and the page says why."""
    root = _seed(tmp_path, states=[{"state": "TX", "agency": "TWC", "format": "socrata-csv"}])
    storage = LocalFSBackend(os.path.join(root, "archive"))
    old = ['"notice_date","job_site_name","total_layoff_number"']
    new = ['"Notice Date","Company Name","Total Employees"']          # same data, new headers...
    for i in range(12):
        old.append(f'"2026-07-0{i%9+1}T00:00:00.000","Employer {i}","{10+i}"')
        new.append(f'"2026-07-0{i%9+1}","Employer {i} Inc","{10+i}"')  # ...and renamed employers
    _archive(storage, "warn/TX", date(2026, 7, 28), "a.csv", ("\n".join(old) + "\n").encode())
    _archive(storage, "warn/TX", date(2026, 7, 29), "b.csv", ("\n".join(new) + "\n").encode())
    ac.compile_all(storage, root, days=7, today=TODAY, code_ref="c")

    warn = json.load(open(os.path.join(root, "site", "data", "warn.json"), encoding="utf-8"))
    tx = next(s for s in warn["states"] if s["state"] == "TX")
    assert tx["delta_suppressed"] and "changing shape" in tx["delta_suppressed"]
    arts = json.load(open(os.path.join(root, "site", "data", "artifacts.json"),
                          encoding="utf-8"))["artifacts"]
    assert not [a for a in arts if a["template"] == "warn_new_notices"], \
        "a reshaped source must not publish a change figure"
    assert [a for a in arts if a["template"] == "warn_state_level"], "the level is still publishable"


def test_publish_refuses_a_number_whose_evidence_is_incomplete(tmp_path):
    """The compiler-side half of fail-closed: no valid bundle, no artifact, loudly."""
    out = []
    try:
        ac._publish(out, receipts_root=str(tmp_path), index="warn-watch", number_id="x", number=5,
                    unit="notices", as_of="2026-07-29", version="v1", methodology_ref="m",
                    inputs=[{"r2_path": "raw/x", "sha256": ""}],      # hash missing -> unusable
                    code_ref="c", template="warn_state_level", kind="cadence", text="5 notices")
    except ac.UnreceiptedNumber:
        assert out == []
    else:
        raise AssertionError("published a number without valid receipts")


def test_manifest_entry_without_a_hash_is_not_usable_evidence(tmp_path):
    root = _seed(tmp_path, states=[{"state": "TX", "format": "socrata-csv"}])
    storage = LocalFSBackend(os.path.join(root, "archive"))
    storage.put("raw/warn/TX/2026/07/29/1200-a.csv", CSV_TX)
    storage.put("raw/warn/TX/2026/07/29/manifest.json",
                json.dumps({"files": [{"file": "1200-a.csv"}]}).encode())   # no sha256
    assert ac.vintages(storage, "warn/TX", 7, TODAY) == []


def _run_plain():
    import pathlib
    import tempfile
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            if "tmp_path" in fn.__code__.co_varnames[:fn.__code__.co_argcount]:
                with tempfile.TemporaryDirectory() as d:
                    fn(pathlib.Path(d))
            else:
                fn()
            print("ok:", name)
    print("ALL ARTIFACT TESTS PASS")


if __name__ == "__main__":
    _run_plain()
