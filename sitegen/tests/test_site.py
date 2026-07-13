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
