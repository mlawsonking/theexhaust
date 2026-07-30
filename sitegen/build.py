"""Static-site generator for The Exhaust (BUILD-04 core).

Stdlib-only, self-contained, theme-aware. Reads the repo's PUBLIC state — retrocast scorecards
(SPEC-08 §3), pre-registrations, the transparency/corrections logs, collector health — and emits
static HTML to `site/dist/` for Cloudflare Pages (the covenant host; GitHub Pages/Vercel bar
commercial use). Doctrine rendered into the site: never predict only measure · open methods ·
receipts on every number · the scorecard is the moat (we grade ourselves in public).

    python -m sitegen.build              # full site  -> site/dist/
    python -m sitegen.build --placeholder  # ONE no-numbers pre-launch page -> site/dist/
"""
from __future__ import annotations

import glob
import html
import json
import os
import re
from datetime import datetime, timezone

from resolver import receipts as receipts_mod
from sitegen import feeds

BRAND = "The Exhaust"
TAGLINE = "an observatory for shadow statistics"
IDENTITY = ("The Exhaust reads civilization's exhaust and publishes the numbers early, with "
            "receipts, and keeps score on itself in public.")
REPO_URL = "https://github.com/mlawsonking/theexhaust"
ARCHIVE_HOST = "https://archive.theexhaust.org"

NAV = [("index.html", "Home"), ("warn.html", "WARN Watch"), ("postings.html", "Postings"),
       ("track-record.html", "Track Record"), ("retrocasts.html", "Retrocasts"),
       ("methodology.html", "Methodology"), ("transparency.html", "Transparency")]

# How stale a collector's last success may be before its pages say so out loud. WARN runs 2x/day
# and the ATS fleet 3x/day, so a day and a half of silence is already an anomaly worth a banner.
STALE_AFTER_HOURS = {"warn": 36, "ats-boards": 36}
DEFAULT_STALE_AFTER_HOURS = 72


class UnreceiptedNumber(Exception):
    """A page tried to render a number whose receipt bundle is missing or invalid.

    This RAISES rather than skipping, and the raise aborts the whole build. That is deliberate:
    silently dropping one number leaves a page that looks complete and is not, and the deploy
    step only replaces the live site on success — so a failed build leaves the last good site up
    rather than publishing an unevidenced figure. Accuracy is a legal control (covenant 4), not a
    presentation preference.
    """

CSS = """
:root{--bg:#fbfbfa;--fg:#1a1a1a;--muted:#5c5c5c;--line:#e4e4e0;--card:#fff;--accent:#0b6b62;--warn:#8a5a00;--warnbg:#fff7e6}
:root[data-theme=dark]{--bg:#141416;--fg:#ececec;--muted:#a0a0a0;--line:#2c2c30;--card:#1c1c1f;--accent:#4fd1c5;--warn:#e0b050;--warnbg:#2a2410}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#141416;--fg:#ececec;--muted:#a0a0a0;--line:#2c2c30;--card:#1c1c1f;--accent:#4fd1c5;--warn:#e0b050;--warnbg:#2a2410}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline}
header.site{border-bottom:1px solid var(--line);padding:14px 20px;display:flex;flex-wrap:wrap;gap:6px 18px;align-items:baseline}
header.site .brand{font-weight:700;font-size:18px;letter-spacing:-.01em}
header.site .tag{color:var(--muted);font-size:13px}
header.site nav{margin-left:auto;display:flex;gap:16px;flex-wrap:wrap}
main{max-width:760px;margin:0 auto;padding:32px 20px 64px}
h1{font-size:30px;line-height:1.2;letter-spacing:-.02em;margin:.2em 0 .3em}
h2{font-size:20px;margin:2em 0 .5em;padding-bottom:.2em;border-bottom:1px solid var(--line)}
.lede{font-size:19px;color:var(--fg)}
.muted{color:var(--muted)}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px 18px;margin:14px 0}
.pill{display:inline-block;font-size:12px;font-weight:600;padding:2px 9px;border-radius:999px;border:1px solid var(--line);color:var(--muted)}
.pill.pass{color:#0a7d33;border-color:#0a7d3355}.pill.fail{color:#b00;border-color:#b0000055}
.stale{background:var(--warnbg);color:var(--warn);border:1px solid var(--warn);border-radius:8px;padding:8px 12px;margin:0 auto;max-width:760px}
table{border-collapse:collapse;width:100%;font-size:14px}th,td{text-align:left;padding:7px 10px;border-bottom:1px solid var(--line)}
code{background:var(--card);border:1px solid var(--line);border-radius:4px;padding:.1em .35em;font-size:.9em}
footer{border-top:1px solid var(--line);color:var(--muted);font-size:13px;padding:22px 20px;max-width:760px;margin:0 auto}
ul.tight li{margin:.25em 0}
"""


def page(title, body, active, stale=None, depth=0):
    """depth = how many directories deep this page sits (warn/TX.html -> 1), so nav and asset
    links resolve from a sub-page without hardcoding the deploy origin."""
    up = "../" * depth
    nav = "".join(
        f'<a href="{up}{href}"{" aria-current=page" if href==active else ""}>{html.escape(label)}</a>'
        for href, label in NAV)
    banners = [stale] if isinstance(stale, str) else list(stale or [])
    banner = "".join(f'<div class="stale" role="status">{b}</div>' for b in banners)
    return (f"<!doctype html>\n<html lang=en><head><meta charset=utf-8>"
            f'<meta name=viewport content="width=device-width,initial-scale=1">'
            f'<link rel="alternate" type="application/rss+xml" title="{html.escape(BRAND)}" '
            f'href="{up}feed.xml">'
            f"<title>{html.escape(title)} · {BRAND}</title><style>{CSS}</style></head><body>"
            f'<header class=site><span class=brand>{BRAND}</span>'
            f'<span class=tag>{html.escape(TAGLINE)}</span><nav>{nav}</nav></header>'
            f"{banner}<main>{body}</main>"
            f'<footer>{BRAND} — a public-interest observatory. Operated by Michael King. '
            f'Every number links its receipts and a frozen methodology. '
            f'We publish our own scorecard, including our failures. '
            f'<a href="{up}feed.xml">RSS</a> · <a href="{up}feed.json">JSON feed</a>'
            f"</footer></body></html>\n")


# --------------------------------------------------------------------- data
def _scorecards(root):
    cards = []
    for p in sorted(glob.glob(os.path.join(root, "retrocast", "*", "results", "*", "scorecard.json"))):
        try:
            cards.append(json.load(open(p, encoding="utf-8")))
        except Exception:
            pass
    return cards


def _preregs(root):
    out = []
    for p in sorted(glob.glob(os.path.join(root, "retrocast", "*", "PRE-REGISTRATION-*.md"))):
        txt = open(p, encoding="utf-8").read()
        m = re.search(r"^#\s+(.+)$", txt, re.M)
        frozen = re.search(r"Frozen\s+(\d{4}-\d{2}-\d{2})", txt)
        idx = os.path.basename(os.path.dirname(p))
        out.append({"index": idx, "title": (m.group(1).strip() if m else idx),
                    "frozen": (frozen.group(1) if frozen else "—"),
                    "path": os.path.relpath(p, root).replace(os.sep, "/")})
    return out


def _load(root, name, default):
    p = os.path.join(root, "site", "data", name)
    try:
        return json.load(open(p, encoding="utf-8"))
    except Exception:
        return default


def receipts_root(root):
    return os.path.join(root, "site", "receipts")


def require_receipt(root, art):
    """THE fail-closed gate (SPEC-09 §2). Returns the artifact if its evidence bundle exists and
    validates; otherwise refuses — the number does not render, and the build stops. There is no
    flag, override, or 'draft' path around this: an unreceipted number must be unpublishable."""
    if not receipts_mod.has_valid_bundle(receipts_root(root), art.get("index", ""), art.get("id", "")):
        raise UnreceiptedNumber(
            f"refusing to render {art.get('index')}/{art.get('id')} "
            f"({art.get('text','')!r}): no valid receipts bundle")
    return art


def _fmt(n):
    return f"{n:,}" if isinstance(n, int) else html.escape(str(n))


def _hours_since(iso):
    try:
        t = datetime.strptime(iso, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except Exception:
        return None
    return (datetime.now(timezone.utc) - t).total_seconds() / 3600.0


def health_banner(root, collector):
    """Stale-data banner wired to HEALTH (SPEC-03 §1). The government-continuity posture is a
    page-level obligation, not a footnote: official publishers freeze (the federal appropriations
    lapse has been live since Oct 2025), so every index page states the vintage it is standing on
    and says so loudly when the archive behind it has stopped moving."""
    try:
        from opscore.report import merged_health
        rec = (merged_health(root).get("collectors") or {}).get(collector) or {}
    except Exception:
        rec = {}
    if not rec:
        return None
    last = rec.get("last_success") or rec.get("last_run") or ""
    age = _hours_since(last)
    limit = STALE_AFTER_HOURS.get(collector, DEFAULT_STALE_AFTER_HOURS)
    paused = rec.get("paused_states") or rec.get("paused_boards") or []
    if age is not None and age > limit:
        return (f"<strong>Stale data.</strong> The <code>{html.escape(collector)}</code> archive "
                f"last stored successfully on {html.escape(last)} — {int(age)} hours ago. "
                f"Everything below is the last archived vintage, not a live reading.")
    if paused:
        return (f"<strong>Partial coverage.</strong> Paused after repeated fetch failures and "
                f"awaiting an operator decision: {html.escape(', '.join(map(str, paused)))}. "
                f"Their pages show the last vintage archived before the pause.")
    return None


def _continuity_note(as_of):
    return ('<p class=muted>Every figure on this page is computed from an archived, hashed '
            'snapshot — never a live call to the source. Official publishers can freeze or '
            'restate without notice; the archive is the record of what they actually published, '
            f'and this page stands on the {html.escape(str(as_of))} vintage.</p>')


def artifact_card(root, art, depth=0):
    """One receipted number. The receipt link is not decoration — it is the claim's warrant."""
    require_receipt(root, art)
    up = "../" * depth
    return (f'<div class=card><strong>{html.escape(art["text"])}</strong><br>'
            f'<span class=muted>{html.escape(art["kind"])} artifact · vintage '
            f'{html.escape(art.get("as_of",""))} · <code>{html.escape(art.get("index_version",""))}</code> · '
            f'<a href="{up}{html.escape(art["receipt"])}">receipts</a></span></div>')


# --------------------------------------------------------------------- pages
def home(root):
    b = [f"<h1>{html.escape(BRAND)}</h1>", f'<p class=lede>{html.escape(IDENTITY)}</p>',
         "<p>Official statistics are slow. Reality leaks constantly through public exhaust — job "
         "postings, filings, recalls, death notices. The Exhaust reads that exhaust and publishes "
         "<strong>shadow statistics</strong>: live, unofficial, receipts-attached versions of the "
         "numbers society waits for.</p>",
         "<p>Two kinds of number live here, and we never blur them. <strong>Observational</strong> "
         "figures count and difference records a publisher put out itself — those need no "
         "prediction to be true, and they carry a link to the archived file they came from. "
         "<strong>Signature</strong> indexes, which say a pattern resembles past cases, publish "
         "only after a retrocast against named historical ground truth clears bars we fixed in "
         "public beforehand. Nothing of the second kind is published yet.</p>",
         '<div class=card><strong>How we earn trust:</strong> the <a href="track-record.html">Track '
         "Record</a>. Before any index publishes, we <em>retrocast</em> it against named historical "
         "ground truth and publish the precision/recall — and we freeze the method in public "
         '<em>before</em> computing results (see <a href="retrocasts.html">Retrocasts</a>). We grade '
         "ourselves before anyone else can. <strong>Never predict, only measure.</strong></div>",

         "<h2>What is published now</h2>",
         '<div class=card><strong><a href="warn.html">WARN Watch</a></strong> — what each state\'s '
         "own layoff-notice list said on a given day, archived and hashed, with the new filings "
         "between consecutive snapshots.</div>",
         '<div class=card><strong><a href="postings.html">Postings</a></strong> — public job boards '
         "snapshotted and differenced: what a company listed, and what it quietly removed.</div>",
         "<p class=muted>Both are <strong>observational</strong>: counts and diffs of records the "
         "publishers put out themselves, every figure linking the archived file it was computed "
         "from. No index here forecasts anything, and no company is scored or flagged.</p>",

         '<div class=card><strong>Neither retrocast we have run cleared its bars.</strong> We '
         "pre-registered a complaints&rarr;recall signature for NHTSA and a nurse-staffing"
         "&rarr;care-harm signature for nursing homes, ran both, and both failed — so both are "
         'published as failures, with their autopsies, on the '
         '<a href="track-record.html">Track Record</a>. A scorecard that only ever shows wins is '
         "not a scorecard.</div>",
         '<p class=muted>Everything is machine-readable: <a href="feed.xml">RSS</a> · '
         '<a href="feed.json">JSON feed</a>. Same numbers, same moment, no paid tier.</p>']
    return page(BRAND, "".join(b), "index.html")


def _num(v, places=4):
    """Render a scorecard metric for humans. A float straight out of JSON prints ~17 significant
    figures, which publishes a precision the measurement does not have — the raw value stays in
    `scorecard.json`, which is what a critic reruns against."""
    if v is None:
        return "—"
    if isinstance(v, float):
        return f"{v:.{places}f}".rstrip("0").rstrip(".") if v == v else "—"
    return html.escape(str(v))


def track_record(root):
    cards = _scorecards(root)
    b = ["<h1>Track Record</h1>",
         "<p class=lede>Every published number is a call, and every call is scored here — "
         "automatically, against the official figure as it arrives.</p>"]
    if not cards:
        b.append('<div class=card>No published scorecards yet. Publishing a number here requires a '
                 "completed retrocast that clears its <em>pre-registered</em> bars and a hostile "
                 'review. Our first is pre-registered now — see <a href="retrocasts.html">Retrocasts</a>. '
                 "<br><br>No live public entity in our lanes publishes a falsifiable precision/recall "
                 "scorecard. That is the point.</div>")
    else:
        b.append('<div class=card>Every bar in this table was <strong>pre-registered</strong> and '
                 'frozen in public <em>before</em> the data was scored — see '
                 '<a href="retrocasts.html">Retrocasts</a> for the registrations and the commit '
                 "dates that prove the ordering. Failures stay on this page permanently; a "
                 "retrocast that misses its bars is published with an autopsy, not deleted.</div>")
        rows = ["<tr><th>Index</th><th>Version</th><th>PR-AUC</th><th>Median lead</th><th>Result</th></tr>"]
        for c in cards:
            m = c.get("metrics", {})
            pill = "pass" if c.get("pass") else "fail"
            rows.append(f"<tr><td>{html.escape(str(c.get('index')))}</td>"
                        f"<td>{html.escape(str(c.get('version')))}</td>"
                        f"<td>{_num(m.get('pr_auc'))}</td><td>{_num(m.get('median_lead_days'))} d</td>"
                        f'<td><span class="pill {pill}">{"PASS" if c.get("pass") else "FAIL"}</span></td></tr>')
        b.append("<table>" + "".join(rows) + "</table>")
    return page("Track Record", "".join(b), "track-record.html")


def retrocasts(root):
    pr = _preregs(root)
    b = ["<h1>Retrocasts</h1>",
         "<p class=lede>A retrocast runs an index backwards against named ground truth. We commit the "
         "full method — signal, labels, controls, splits, pass/fail bars — to this public repository "
         "<strong>before</strong> a single result is computed. Git history makes that ordering "
         "unforgeable: our numbers cannot be a product of hindsight.</p>"]
    if not pr:
        b.append("<div class=card>No pre-registrations yet.</div>")
    else:
        for p in pr:
            b.append(f'<div class=card><strong>{html.escape(p["title"])}</strong><br>'
                     f'<span class=muted>Pre-registration frozen {html.escape(p["frozen"])} · '
                     f'<code>{html.escape(p["path"])}</code></span></div>')
    b.append('<p class=muted>Failed retrocasts are published too, with an autopsy — a killed index '
             "builds exactly the trust the scorecard exists to build.</p>")
    return page("Retrocasts", "".join(b), "retrocasts.html")


def methodology(root):
    b = ["<h1>Methodology</h1>",
         "<p class=lede>Open methods, open receipts, open scorecard. Anything a critic cannot rerun, "
         "we do not publish.</p>",
         "<h2>The retrocast gate</h2><p>No index publishes without: (1) a historical backtest against "
         "named ground truth, (2) published precision/recall and calibration, (3) a frozen, versioned "
         "methodology, (4) a receipts link on every number. Change the method, and the full backtest "
         "republishes under a new version.</p>",
         "<h2>Never predict, only measure</h2><p>Every claim is a computed comparison to history, in "
         "the past or present tense, with receipts — never an assertion about what will happen.</p>",
         "<h2>Not ShadowStats</h2><p>The name sits one step from crankery. We are its opposite: every "
         "method is versioned and rerunnable, every number carries its raw receipts, every index "
         "carries its own public scorecard. We grade ourselves in public before anyone else can.</p>",
         "<h2>Who</h2><p>Operated by Michael King. Press and corrections: via the site. Every legal "
         'threat we receive is published in the <a href="transparency.html">transparency log</a>.</p>',

         '<h2 id=warn-watch>WARN Watch <code>' + html.escape(_version(root, "warn.json")) + '</code></h2>'
         "<p>Each state labor department publishes its own layoff-notice list, in its own format, "
         "and amends it without notice. Twice a day we fetch each state's primary source, hash the "
         "bytes, and store them immutably; a byte-identical payload is not stored twice. Pages are "
         "then built <em>only</em> from those stored objects — never from a live request — so every "
         "figure is reproducible from a file whose hash we publish.</p>"
         "<p>From each stored payload we read the notice table using the source's own column "
         "headers (never column positions, which states reorder). A notice is an employer, the "
         "date(s) the source gives, a headcount, and a location. Dates stored as Excel day counts "
         "are converted; a value we cannot confidently read as a date is left empty rather than "
         "guessed. Rows naming no employer are counted and disclosed but not published as notices. "
         "Where a state publishes a link list or a document instead of a table, we say so on its "
         "page and publish no count — the snapshot is archived either way.</p>"
         "<p><strong>What is new</strong> is computed by differencing consecutive stored vintages, "
         "matching notices on employer, source date and headcount. If more than half a state's "
         "list appears to change between two snapshots, we treat that as the source changing shape "
         "rather than as new filings, and publish no change figure for that vintage.</p>"
         "<p>These are <strong>observational facts with receipts</strong> — an employer's own "
         "public filing, as its state published it. We attach no signature, score, or forecast to "
         "any company named here, and the counts are of each state's own list: they are not a "
         "national total, and we do not publish one.</p>",

         '<h2 id=posting-diff>Posting-Diff <code>' + html.escape(_version(root, "postings.json")) + '</code></h2>'
         "<p>We snapshot public, unauthenticated job-board endpoints for a small seed universe of "
         "companies, hash and store each payload, and difference consecutive stored snapshots to "
         "get the postings removed, added, and kept. The removed postings themselves are the "
         "receipts. Expanding the board universe is an operator decision, not something the system "
         "does on its own.</p>"
         "<p>We report what moved and make no claim about why. A posting can vanish because a role "
         "was filled, reposted, or cancelled, and the diff cannot tell those apart.</p>",

         "<h2>Corrections</h2><p>A number is never edited in place. A correction publishes a "
         "successor receipt bundle and an entry in the "
         '<a href="transparency.html">corrections log</a>, so the record shows what we said, when, '
         "and what changed. Data and methodology bugs are treated as accuracy failures, not "
         "cosmetic ones.</p>"]
    return page("Methodology", "".join(b), "methodology.html")


def _version(root, data_file):
    """The compiled index version, so the methodology page names the exact derivation that produced
    the numbers in this build rather than a version hardcoded in prose."""
    return _load(root, data_file, {}).get("version", "") or \
        {"warn.json": "warn-watch-v1", "postings.json": "posting-diff-v1"}[data_file]


def transparency(root):
    corr = os.path.join(root, "site", "corrections.md")
    b = ["<h1>Transparency</h1>",
         "<p class=lede>Corrections and legal threats are published here, in full. A correction is a "
         "feature of a system that grades itself; a legal threat against receipts-attached "
         "public-interest measurement is answered in public.</p>",
         "<h2>Corrections</h2><div class=card>None yet.</div>",
         "<h2>Legal threats</h2><div class=card>None yet.</div>"]
    return page("Transparency", "".join(b), "transparency.html")


# --------------------------------------------------------------------- WARN Watch (C2)
WARN_LEDE = ("State labor departments publish WARN layoff notices on their own pages, in their own "
             "formats, and amend or remove them without notice. We snapshot each state's published "
             "list, hash it, and keep it forever — so this page can show what a state actually "
             "published on a given day, and prove it.")


def _notice_rows(notices, limit=None):
    rows = ["<tr><th>Employer</th><th>Notice date</th><th>Effective</th><th>Workers</th>"
            "<th>Location</th></tr>"]
    for n in (notices[:limit] if limit else notices):
        rows.append(f'<tr><td>{html.escape(n.get("company",""))}</td>'
                    f'<td>{html.escape(n.get("notice_date") or "—")}</td>'
                    f'<td>{html.escape(n.get("effective_date") or "—")}</td>'
                    f'<td>{_fmt(n["employees"]) if n.get("employees") is not None else "—"}</td>'
                    f'<td>{html.escape(n.get("location",""))}</td></tr>')
    return "<table>" + "".join(rows) + "</table>"


def _notice_rows_with_state(pairs):
    rows = ["<tr><th>Employer</th><th>State</th><th>Notice date</th><th>Effective</th>"
            "<th>Workers</th><th>Location</th></tr>"]
    for n, st in pairs:
        rows.append(f'<tr><td>{html.escape(n.get("company",""))}</td>'
                    f'<td><a href="warn/{html.escape(st)}.html">{html.escape(st)}</a></td>'
                    f'<td>{html.escape(n.get("notice_date") or "—")}</td>'
                    f'<td>{html.escape(n.get("effective_date") or "—")}</td>'
                    f'<td>{_fmt(n["employees"]) if n.get("employees") is not None else "—"}</td>'
                    f'<td>{html.escape(n.get("location",""))}</td></tr>')
    return "<table>" + "".join(rows) + "</table>"


def warn_watch(root):
    data = _load(root, "warn.json", {"states": []})
    arts = [a for a in _load(root, "artifacts.json", {}).get("artifacts", [])
            if a.get("index") == "warn-watch"]
    states = data.get("states", [])
    b = ["<h1>WARN Watch</h1>", f"<p class=lede>{WARN_LEDE}</p>"]
    if not states:
        b.append("<div class=card>No archived WARN vintages in this build.</div>")
        return page("WARN Watch", "".join(b), "warn.html")

    readable = [s for s in states if s.get("parse_status") == "notices"]
    b.append(f'<p class=muted>{len(states)} states archived · {len(readable)} currently machine-'
             f'readable into individual notices. Counts below are of each state\'s own published '
             f'list, which spans different histories by state — they are not a national total, '
             f'and we do not publish one.</p>')

    recent = [a for a in arts if a.get("template") == "warn_new_notices"]
    if recent:
        b.append("<h2>What changed</h2>")
        b += [artifact_card(root, a) for a in recent]

    b.append("<h2>States</h2>")
    rows = ["<tr><th>State</th><th>Agency</th><th>Notices on list</th><th>Vintage</th>"
            "<th>Status</th></tr>"]
    for s in states:
        st = s["state"]
        status = {"notices": "machine-readable", "unreadable": "archived, not yet machine-readable",
                  "no-vintage": "no snapshot in window",
                  "unfetched": "snapshot unreadable"}.get(s.get("parse_status"), s.get("parse_status", ""))
        count = _fmt(s["notices_total"]) if s.get("notices_total") is not None else "—"
        rows.append(f'<tr><td><a href="warn/{html.escape(st)}.html">{html.escape(st)}</a></td>'
                    f'<td>{html.escape(s.get("agency",""))}</td><td>{count}</td>'
                    f'<td>{html.escape(s.get("as_of") or "—")}</td>'
                    f'<td class=muted>{html.escape(status)}</td></tr>')
    b.append("<table>" + "".join(rows) + "</table>")

    # Ranked on the NOTICE date only. Some states (NJ) publish just an effective date, which for a
    # WARN filing is deliberately in the future — ranking on it would put notices that have not
    # happened yet at the top of a list headed "most recently filed". A notice with no filing date
    # has no knowable position in a recency ranking, so it stays on its state page instead.
    dated = [(n, s["state"]) for s in readable for n in s.get("notices", []) if n.get("notice_date")]
    newest = sorted(dated, key=lambda t: t[0]["notice_date"], reverse=True)[:25]
    undated = sum(1 for s in readable for n in s.get("notices", []) if not n.get("notice_date"))
    if newest:
        b.append("<h2>Most recently filed notices across archived states</h2>")
        b.append('<p class=muted>Each row is an employer\'s own filing as its state published it. '
                 'These are observational facts with receipts, not signals or predictions.'
                 + (f' {undated} archived notices carry no filing date in their source and are '
                    f'listed on their state pages rather than ranked here.' if undated else "")
                 + '</p>')
        b.append(_notice_rows_with_state(newest))
    b.append(_continuity_note(max((s.get("as_of") or "") for s in states) or "latest"))
    return page("WARN Watch", "".join(b), "warn.html", stale=_banners(root, "warn"))


def _banners(root, collector):
    bn = health_banner(root, collector)
    return [bn] if bn else []


def warn_state_page(root, s, arts):
    st = s["state"]
    mine = [a for a in arts if a.get("state") == st]
    b = [f'<h1>WARN Watch — {html.escape(st)}</h1>',
         f'<p class=lede>{html.escape(s.get("agency",""))} publishes this list; we archive it '
         f'{"twice a day" if True else ""} and diff consecutive vintages.</p>']
    if s.get("notes"):
        b.append(f'<div class=card><strong>Source note.</strong> {html.escape(s["notes"])}</div>')
    b += [artifact_card(root, a, depth=1) for a in mine]

    if s.get("delta_suppressed"):
        b.append(f'<div class=card><strong>No change figure for this vintage.</strong> '
                 f'{html.escape(s["delta_suppressed"])}</div>')
    if s.get("parse_status") == "notices":
        total, shown = s.get("notices_total", 0), s.get("notices_shown", 0)
        if s.get("new_notices") and not s.get("delta_suppressed"):
            b.append("<h2>New since the previous archived vintage</h2>")
            b.append(_notice_rows(s["new_notices"]))
        b.append("<h2>Notices on the published list</h2>")
        if shown < total:
            b.append(f'<p class=muted>Showing the {shown} most recent of {_fmt(total)}. The full '
                     f'list is in the archived snapshot below — that file, not this table, is the '
                     f'record.</p>')
        if s.get("unnamed_rows"):
            b.append(f'<p class=muted>{s["unnamed_rows"]} row(s) in this vintage name no employer '
                     f'and are therefore not shown; they are still counted in the source file.</p>')
        b.append(_notice_rows(s["notices"]))
    else:
        b.append('<div class=card><strong>Archived, not yet machine-readable.</strong> This state '
                 'publishes its notices in a shape our stdlib extractor does not yet read (a link '
                 'list or a document, rather than a table). The snapshot below is archived and '
                 'hashed exactly the same way — we simply do not publish a count we cannot '
                 'derive.</div>')

    b.append("<h2>The archived snapshot</h2>")
    if s.get("latest_key"):
        b.append(f'<div class=card><code>{html.escape(s["latest_key"])}</code><br>'
                 f'<span class=muted>sha256 <code>{html.escape(s.get("latest_sha256",""))}</code><br>'
                 f'archived {html.escape(s.get("as_of",""))} from '
                 f'<a href="{html.escape(s.get("source_url",""))}">the state source</a> · '
                 f'served from <code>{ARCHIVE_HOST}</code></span></div>')
    b.append(f'<p class=muted>{len(s.get("vintages", []))} vintage(s) of this source are archived '
             f'in the window this page was built from.</p>')
    b.append(_continuity_note(s.get("as_of", "latest")))
    return page(f"WARN Watch — {st}", "".join(b), "warn.html", stale=_banners(root, "warn"), depth=1)


# --------------------------------------------------------------------- Posting-Diff (E1)
POSTINGS_LEDE = ("Companies publish their open roles and quietly remove them. We snapshot public "
                 "job boards and difference consecutive snapshots, so a hiring reversal is visible "
                 "as it happens rather than a quarter later. The removed postings are the receipts.")


def postings_page(root):
    data = _load(root, "postings.json", {"boards": []})
    arts = [a for a in _load(root, "artifacts.json", {}).get("artifacts", [])
            if a.get("index") == "posting-diff"]
    boards = data.get("boards", [])
    b = ["<h1>Postings</h1>", f"<p class=lede>{POSTINGS_LEDE}</p>",
         '<p class=muted>This is reporting, not inference: a company\'s own public board, '
         'differenced. We make no claim about why a posting moved.</p>']
    if not boards:
        b.append("<div class=card>No archived board snapshots in this build.</div>")
        return page("Postings", "".join(b), "postings.html")
    moved = [a for a in arts if a.get("template") == "postings_removed"]
    if moved:
        b.append("<h2>What changed</h2>")
        b += [artifact_card(root, a) for a in moved]
    b.append("<h2>Boards</h2>")
    rows = ["<tr><th>Company</th><th>Board</th><th>Postings</th><th>Vintage</th><th>Snapshots</th></tr>"]
    for x in boards:
        rows.append(f'<tr><td><a href="postings/{html.escape(x["slug"])}.html">'
                    f'{html.escape(x["company"])}</a></td>'
                    f'<td class=muted>{html.escape(x["ats"])}</td>'
                    f'<td>{_fmt(x["postings"]) if x.get("postings") is not None else "—"}</td>'
                    f'<td>{html.escape(x.get("as_of") or "—")}</td>'
                    f'<td>{len(x.get("vintages", []))}</td></tr>')
    b.append("<table>" + "".join(rows) + "</table>")
    b.append('<p class=muted>The board universe is deliberately small; expanding it is an operator '
             'gate (new-source onboarding), not something this system does on its own.</p>')
    b.append(_continuity_note(max((x.get("as_of") or "") for x in boards) or "latest"))
    return page("Postings", "".join(b), "postings.html", stale=_banners(root, "ats-boards"))


def postings_board_page(root, x, arts):
    mine = [a for a in arts if a.get("slug") == x["slug"]]
    b = [f'<h1>{html.escape(x["company"])} — public job postings</h1>',
         f'<p class=lede>Snapshots of this company\'s own public board on '
         f'<code>{html.escape(x["ats"])}</code>, differenced between consecutive archived '
         f'vintages.</p>']
    b += [artifact_card(root, a, depth=1) for a in mine]
    d = x.get("diff")
    if d:
        cmp_to = x.get("compared_to", {})
        b.append(f'<h2>Diff vs the previous archived snapshot</h2>'
                 f'<p class=muted>{_fmt(d["prev_count"])} postings then · {_fmt(d["cur_count"])} now '
                 f'· {_fmt(d["removed_count"])} removed · {_fmt(d["added_count"])} added · compared '
                 f'against the vintage archived {html.escape(cmp_to.get("date",""))} '
                 f'(<code>{html.escape(cmp_to.get("sha256","")[:16])}</code>).</p>')
        for label, key in (("Removed", "removed"), ("Added", "added")):
            items = d.get(key, [])
            if items:
                b.append(f"<h3>{label} ({len(items)})</h3><ul class=tight>")
                for p in items[:50]:
                    b.append(f'<li><a href="{html.escape(p.get("url",""))}">'
                             f'{html.escape(p.get("title",""))}</a></li>')
                b.append("</ul>")
                if len(items) > 50:
                    b.append(f'<p class=muted>{len(items) - 50} more in the archived snapshot.</p>')
    else:
        b.append('<div class=card>Only one archived vintage of this board so far — a diff needs '
                 'two. The snapshot is archived regardless; that is the whole point of collecting '
                 'before computing.</div>')
    if x.get("latest_key"):
        b.append("<h2>The archived snapshot</h2>")
        b.append(f'<div class=card><code>{html.escape(x["latest_key"])}</code><br>'
                 f'<span class=muted>sha256 <code>{html.escape(x.get("latest_sha256",""))}</code> · '
                 f'from <a href="{html.escape(x.get("source_url",""))}">the public board API</a>'
                 f'</span></div>')
    b.append(_continuity_note(x.get("as_of", "latest")))
    return page(x["company"], "".join(b), "postings.html", stale=_banners(root, "ats-boards"),
                depth=1)


# --------------------------------------------------------------------- receipts
def receipt_page(root, art):
    """The public rendering of one evidence bundle: what was counted, from exactly which archived
    objects, under which code and methodology version. This is the page a critic reruns."""
    require_receipt(root, art)
    p = receipts_mod.bundle_path(receipts_root(root), art["index"], art["id"])
    bundle = json.load(open(p, encoding="utf-8"))
    b = ["<h1>Receipt</h1>",
         f'<p class=lede>{html.escape(art["text"])}</p>',
         "<div class=card><table>"
         f'<tr><th>Number</th><td>{_fmt(bundle["number"])} {html.escape(bundle.get("unit",""))}</td></tr>'
         f'<tr><th>Vintage</th><td>{html.escape(bundle.get("as_of",""))}</td></tr>'
         f'<tr><th>Index version</th><td><code>{html.escape(bundle.get("index_version",""))}</code></td></tr>'
         f'<tr><th>Methodology</th><td><a href="../../{html.escape(bundle.get("methodology_ref",""))}">'
         f'<code>{html.escape(bundle.get("methodology_ref",""))}</code></a></td></tr>'
         f'<tr><th>Code</th><td><a href="{REPO_URL}/commit/{html.escape(bundle.get("code_ref",""))}">'
         f'<code>{html.escape(bundle.get("code_ref",""))}</code></a></td></tr>'
         "</table></div>",
         "<h2>Raw inputs (immutable archived vintages)</h2>",
         "<p class=muted>Each row is an object in our archive, addressed by key and content hash. "
         "The hash is of the bytes we stored; re-fetching the source later may give something "
         "different, and that difference is exactly what an archive exists to preserve.</p>"]
    rows = ["<tr><th>Archive key</th><th>sha256</th></tr>"]
    for i in bundle.get("inputs", []):
        rows.append(f'<tr><td><code>{html.escape(i.get("r2_path",""))}</code></td>'
                    f'<td><code>{html.escape(i.get("sha256",""))}</code></td></tr>')
    b.append("<table>" + "".join(rows) + "</table>")
    b.append(f'<p class=muted>Served from <code>{ARCHIVE_HOST}</code>. Template: '
             f'<code>{html.escape(art.get("template",""))}</code> — one of a fixed set of approved '
             f'artifact shapes; the compiler cannot emit a sentence that is not in that set.</p>')
    return page("Receipt", "".join(b), "", depth=2)


# --------------------------------------------------------------- pre-launch placeholder
# W-005b: the operator-approved (2026-07-28) pre-launch surface for theexhaust.org. Deliberately
# near-zero legal surface: it states WHAT the project is and WHERE the method lives, and publishes
# NOTHING measured — no numbers, no index content, no named entities, no trackers. The full site
# stays held for the retrocast launch story (W-007). It reuses the site's CSS spine but NOT the
# nav (the other pages don't exist in this mode).
def placeholder(root="."):
    pr = next((p for p in _preregs(root) if "nhtsa" in p["index"].lower()), None)
    method_link = (f'<a href="{REPO_URL}/blob/main/{pr["path"]}">the frozen pre-registration for our '
                   f'first retrocast</a> (frozen {html.escape(pr["frozen"])})') if pr else \
                  f'<a href="{REPO_URL}">the public repository</a>'
    body = (
        f"<h1>{html.escape(BRAND)}</h1>"
        f'<p class=lede>{html.escape(IDENTITY)}</p>'          # the header already carries the tagline
        f'<p class=muted>Status: pre-launch. Nothing is published here yet — no numbers, no '
        f"estimates, no claims. When the first index publishes, it will arrive with its receipts "
        f"and its own scorecard, or it will not arrive at all.</p>"
        f"<div class=card>The archive has been collecting since July 2026. Perishable public "
        f"records disappear quietly, so collection starts before analysis does — every uncollected "
        f"week is gone for good.</div>"
        f"<div class=card><strong>The method is committed in public <em>before</em> the results "
        f"exist.</strong> Read {method_link}, and check the git history yourself: the commit that "
        f"freezes a method is timestamped ahead of the commit that reports how it scored. That "
        f"ordering is the point — our numbers cannot be a product of hindsight."
        f'<br><br>Everything is open: <a href="{REPO_URL}">{html.escape(REPO_URL)}</a></div>'
        f"<p class=muted>No trackers, no analytics, no cookies — on this page or any other.</p>")
    nav_free_footer = (
        f'<footer>{BRAND} — a public-interest observatory. Operated by Michael King. '
        f'Contact: ops@theexhaust.org. Every number we publish will link its receipts and a frozen '
        f'methodology, and we publish our own scorecard, including our failures.</footer>')
    return (f"<!doctype html>\n<html lang=en><head><meta charset=utf-8>"
            f'<meta name=viewport content="width=device-width,initial-scale=1">'
            f'<meta name=description content="{html.escape(BRAND)} — {html.escape(TAGLINE)}. '
            f'Pre-launch.">'
            f"<title>{html.escape(BRAND)} · {html.escape(TAGLINE)}</title><style>{CSS}</style>"
            f"</head><body>"
            f'<header class=site><span class=brand>{BRAND}</span>'
            f'<span class=tag>{html.escape(TAGLINE)}</span></header>'
            f"<main>{body}</main>{nav_free_footer}</body></html>\n")


# Top-level full-site pages, so placeholder mode can REMOVE any left over in the output dir.
# Without this a local full build followed by a placeholder deploy would quietly publish
# unlaunched pages. Sub-directories (warn/, postings/, receipts/) are removed wholesale.
FULL_PAGES = ("index.html", "warn.html", "postings.html", "track-record.html", "retrocasts.html",
              "methodology.html", "transparency.html", "feed.xml", "feed.json")
FULL_DIRS = ("warn", "postings", "receipts")


def build(root=".", out_dir=None, placeholder_mode=False):
    out_dir = out_dir or os.path.join(root, "site", "dist")
    os.makedirs(out_dir, exist_ok=True)
    if placeholder_mode:
        import shutil
        for name in FULL_PAGES:                      # clear a stale full build before publishing
            p = os.path.join(out_dir, name)
            if os.path.exists(p):
                os.remove(p)
        for d in FULL_DIRS:
            shutil.rmtree(os.path.join(out_dir, d), ignore_errors=True)
        pages = {"index.html": placeholder(root)}
        _write(out_dir, pages)
        return out_dir, sorted(pages)

    warn_data = _load(root, "warn.json", {"states": []})
    post_data = _load(root, "postings.json", {"boards": []})
    arts = _load(root, "artifacts.json", {}).get("artifacts", [])
    # Every artifact is receipt-checked BEFORE anything is written, so a build cannot leave a
    # half-published site behind when one number turns out to be unevidenced.
    for a in arts:
        require_receipt(root, a)

    pages = {"index.html": home(root), "warn.html": warn_watch(root),
             "postings.html": postings_page(root), "track-record.html": track_record(root),
             "retrocasts.html": retrocasts(root), "methodology.html": methodology(root),
             "transparency.html": transparency(root)}
    for s in warn_data.get("states", []):
        pages[f"warn/{s['state']}.html"] = warn_state_page(root, s, arts)
    for x in post_data.get("boards", []):
        pages[f"postings/{x['slug']}.html"] = postings_board_page(root, x, arts)
    for a in arts:
        pages[a["receipt"]] = receipt_page(root, a)
    pages["feed.xml"] = feeds.rss(arts)
    pages["feed.json"] = feeds.json_feed(arts)
    _write(out_dir, pages)
    return out_dir, sorted(pages)


def _write(out_dir, pages):
    for name, text in pages.items():
        p = os.path.join(out_dir, name.replace("/", os.sep))
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(text)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--placeholder", action="store_true",
                    help="emit ONLY the no-numbers pre-launch page (the live theexhaust.org build)")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    d, names = build(".", out_dir=args.out, placeholder_mode=args.placeholder)
    print(("wrote placeholder: " if args.placeholder else "wrote ") + f"{len(names)} page(s) to {d}"
          f" -> {', '.join(names)}")
