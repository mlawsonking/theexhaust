"""Static-site generator tests (offline). Run:
    python -m sitegen.tests.test_site
    python -m pytest sitegen/tests/test_site.py
Builds against the real repo root so the NHTSA pre-registration is discovered and rendered."""
from __future__ import annotations

import os

from sitegen import build

PAGES = {"index.html", "track-record.html", "retrocasts.html", "methodology.html", "transparency.html"}


def test_site_builds(tmp_path):
    out, names = build.build(".", out_dir=str(tmp_path / "dist"))
    assert set(names) == PAGES

    def read(n):
        return open(os.path.join(out, n), encoding="utf-8").read()

    idx = read("index.html")
    assert "The Exhaust" in idx and "shadow statistics" in idx
    assert "Never predict, only measure" in idx

    tr = read("track-record.html")
    assert "Track Record" in tr and "pre-registered" in tr.lower()

    rc = read("retrocasts.html")
    assert "NHTSA" in rc and "frozen" in rc.lower()          # the real pre-registration is rendered

    meth = read("methodology.html")
    assert "Never predict" in meth and "Michael King" in meth

    # well-formed, theme-aware, self-contained (no external asset refs)
    for n in PAGES:
        h = read(n)
        assert h.startswith("<!doctype html>") and h.rstrip().endswith("</html>")
        assert "prefers-color-scheme" in h                  # theme-aware
        assert "http://" not in h and "https://" not in h.replace("width=device-width", "")  # self-contained


def test_placeholder_mode_emits_one_page_with_required_lines(tmp_path):
    """W-005b: the operator-approved pre-launch surface. Exactly one page, carrying the identity,
    the pre-launch status, the factual archive line, and the method-before-results links."""
    out, names = build.build(".", out_dir=str(tmp_path / "dist"), placeholder_mode=True)
    assert names == ["index.html"], names
    h = open(os.path.join(out, "index.html"), encoding="utf-8").read()

    assert "The Exhaust" in h and "an observatory for shadow statistics" in h
    assert "receipts" in h                                    # the identity sentence
    assert "pre-launch" in h.lower()                          # status line
    assert "collecting since July 2026" in h                  # the factual operational line
    assert build.REPO_URL in h                                # public repo
    assert "PRE-REGISTRATION-v1.md" in h                      # the frozen pre-registration itself
    assert "before" in h and "git history" in h               # the ordering claim readers can check
    assert "Michael King" in h                                # operator identity (covenant 5)

    # well-formed, theme-aware, and it carries the full site's CSS spine
    assert h.startswith("<!doctype html>") and h.rstrip().endswith("</html>")
    assert "prefers-color-scheme" in h and "--accent" in h
    # no nav to pages that do not exist in this mode
    for dead in ("track-record.html", "retrocasts.html", "methodology.html", "transparency.html"):
        assert dead not in h


def test_placeholder_publishes_nothing_measured(tmp_path):
    """The whole point of the placeholder: near-zero surface. No numbers, no index content, no
    third-party assets, no trackers. If this test ever has to be relaxed, that is a gate, not a fix."""
    out, _ = build.build(".", out_dir=str(tmp_path / "dist"), placeholder_mode=True)
    h = open(os.path.join(out, "index.html"), encoding="utf-8").read()
    body = h.split("</style>", 1)[1]                          # judge the CONTENT, not the CSS

    # no measured content of any kind
    for banned in ("%", "PR-AUC", "precision", "median lead", "scorecard.json", "<table",
                   "PASS", "FAIL", "GB", "complaints", "WARN notice"):
        assert banned not in body, f"placeholder leaked measured content: {banned}"
    # No BARE number may appear in the visible prose. Dates and a version tag are legitimate (a
    # frozen-on date is provenance, not a measurement); anything else is a statistic and must not
    # be here pre-launch. Entities are unescaped first so "civilization&#x27;s" isn't read as "27".
    import html as _html
    import re as _re
    text = _html.unescape(_re.sub(r"<[^>]+>", " ", body))
    text = _re.sub(r"\d{4}-\d{2}-\d{2}", " ", text)           # ISO dates (pre-registration frozen)
    text = _re.sub(r"\b(19|20)\d{2}\b", " ", text)            # bare years ("since July 2026")
    text = _re.sub(r"\bv\d+\b", " ", text)                    # version tags
    assert not _re.search(r"\d", text), \
        f"bare number in placeholder prose: {_re.findall(r'[^.]*\d[^.]*', text)}"

    # no trackers, no scripts, no third-party assets — ever
    # (the page's own prose says "no analytics", so match tracker INVOCATIONS, not the word)
    for banned in ("<script", "<img", "<iframe", "@import", "google-analytics", "gtag(",
                   "googletagmanager", "plausible.io", "fbq(", "<link "):
        assert banned not in h, f"placeholder pulled in {banned}"
    # every external reference is an anchor href to our own public repo (no asset fetches)
    for url in _re.findall(r'https?://[^"\s<]+', h):
        assert url.startswith(build.REPO_URL), f"unexpected external URL: {url}"


def test_placeholder_clears_a_stale_full_build(tmp_path):
    """A full build left in the output dir must not survive into a placeholder deploy — otherwise
    an unlaunched page ships by accident (site/dist/ is gitignored and really does hold one locally)."""
    dist = str(tmp_path / "dist")
    build.build(".", out_dir=dist)                            # full site first
    assert os.path.exists(os.path.join(dist, "methodology.html"))
    build.build(".", out_dir=dist, placeholder_mode=True)
    assert os.listdir(dist) == ["index.html"]
    assert "pre-launch" in open(os.path.join(dist, "index.html"), encoding="utf-8").read().lower()


def test_stale_banner():
    p = build.page("T", "<p>x</p>", "index.html", stale="Official source last updated 2026-06; index chains to that vintage.")
    assert "chains to that vintage" in p and "stale" in p


def _run_plain():
    import tempfile
    import pathlib
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            if "tmp_path" in fn.__code__.co_varnames[:fn.__code__.co_argcount]:
                with tempfile.TemporaryDirectory() as d:
                    fn(pathlib.Path(d))
            else:
                fn()
            print("ok:", name)
    print("ALL SITE TESTS PASS")


if __name__ == "__main__":
    _run_plain()
