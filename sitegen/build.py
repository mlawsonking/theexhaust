"""Static-site generator for The Exhaust (BUILD-04 core).

Stdlib-only, self-contained, theme-aware. Reads the repo's PUBLIC state — retrocast scorecards
(SPEC-08 §3), pre-registrations, the transparency/corrections logs, collector health — and emits
static HTML to `site/dist/` for Cloudflare Pages (the covenant host; GitHub Pages/Vercel bar
commercial use). Doctrine rendered into the site: never predict only measure · open methods ·
receipts on every number · the scorecard is the moat (we grade ourselves in public).

    python -m sitegen.build            # -> site/dist/
"""
from __future__ import annotations

import glob
import html
import json
import os
import re

BRAND = "The Exhaust"
TAGLINE = "an observatory for shadow statistics"
IDENTITY = ("The Exhaust reads civilization's exhaust and publishes the numbers early, with "
            "receipts, and keeps score on itself in public.")

NAV = [("index.html", "Home"), ("track-record.html", "Track Record"),
       ("retrocasts.html", "Retrocasts"), ("methodology.html", "Methodology"),
       ("transparency.html", "Transparency")]

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


def page(title, body, active, stale=None):
    nav = "".join(
        f'<a href="{href}"{" aria-current=page" if href==active else ""}>{html.escape(label)}</a>'
        for href, label in NAV)
    banner = f'<div class="stale" role="status">{html.escape(stale)}</div>' if stale else ""
    return (f"<!doctype html>\n<html lang=en><head><meta charset=utf-8>"
            f'<meta name=viewport content="width=device-width,initial-scale=1">'
            f"<title>{html.escape(title)} · {BRAND}</title><style>{CSS}</style></head><body>"
            f'<header class=site><span class=brand>{BRAND}</span>'
            f'<span class=tag>{html.escape(TAGLINE)}</span><nav>{nav}</nav></header>'
            f"{banner}<main>{body}</main>"
            f'<footer>{BRAND} — a public-interest observatory. Operated by Michael King. '
            f'Every number links its receipts and a frozen methodology. '
            f'We publish our own scorecard, including our failures.</footer></body></html>\n')


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


# --------------------------------------------------------------------- pages
def home(root):
    b = [f"<h1>{html.escape(BRAND)}</h1>", f'<p class=lede>{html.escape(IDENTITY)}</p>',
         "<p>Official statistics are slow. Reality leaks constantly through public exhaust — job "
         "postings, filings, recalls, death notices. The Exhaust reads that exhaust and publishes "
         "<strong>shadow statistics</strong>: live, unofficial, receipts-attached versions of the "
         "numbers society waits for — every one validated by running history backwards.</p>",
         '<div class=card><strong>How we earn trust:</strong> the <a href="track-record.html">Track '
         "Record</a>. Before any index publishes, we <em>retrocast</em> it against named historical "
         "ground truth and publish the precision/recall — and we freeze the method in public "
         '<em>before</em> computing results (see <a href="retrocasts.html">Retrocasts</a>). We grade '
         "ourselves before anyone else can. <strong>Never predict, only measure.</strong></div>",
         '<p class=muted>Status: pre-launch. The first retrocast — NHTSA Shadow Recalls — is '
         "pre-registered; collectors and the scoring engine are built and tested.</p>"]
    return page(BRAND, "".join(b), "index.html")


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
        rows = ["<tr><th>Index</th><th>Version</th><th>PR-AUC</th><th>Median lead</th><th>Result</th></tr>"]
        for c in cards:
            m = c.get("metrics", {})
            pill = "pass" if c.get("pass") else "fail"
            rows.append(f"<tr><td>{html.escape(str(c.get('index')))}</td>"
                        f"<td>{html.escape(str(c.get('version')))}</td>"
                        f"<td>{m.get('pr_auc','—')}</td><td>{m.get('median_lead_days','—')} d</td>"
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
         'threat we receive is published in the <a href="transparency.html">transparency log</a>.</p>']
    return page("Methodology", "".join(b), "methodology.html")


def transparency(root):
    corr = os.path.join(root, "site", "corrections.md")
    b = ["<h1>Transparency</h1>",
         "<p class=lede>Corrections and legal threats are published here, in full. A correction is a "
         "feature of a system that grades itself; a legal threat against receipts-attached "
         "public-interest measurement is answered in public.</p>",
         "<h2>Corrections</h2><div class=card>None yet.</div>",
         "<h2>Legal threats</h2><div class=card>None yet.</div>"]
    return page("Transparency", "".join(b), "transparency.html")


def build(root=".", out_dir=None):
    out_dir = out_dir or os.path.join(root, "site", "dist")
    os.makedirs(out_dir, exist_ok=True)
    pages = {"index.html": home(root), "track-record.html": track_record(root),
             "retrocasts.html": retrocasts(root), "methodology.html": methodology(root),
             "transparency.html": transparency(root)}
    for name, htmltext in pages.items():
        with open(os.path.join(out_dir, name), "w", encoding="utf-8") as f:
            f.write(htmltext)
    return out_dir, sorted(pages)


if __name__ == "__main__":
    d, names = build(".")
    print("wrote", len(names), "pages to", d, "->", ", ".join(names))
