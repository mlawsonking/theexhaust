"""Static-site generator tests (offline). Run:
    python -m sitegen.tests.test_site
    python -m pytest sitegen/tests/test_site.py
Builds against the real repo root so the NHTSA pre-registration is discovered and rendered."""
from __future__ import annotations

import json
import os

from sitegen import build

PAGES = {"index.html", "warn.html", "postings.html", "track-record.html", "retrocasts.html",
         "methodology.html", "transparency.html", "feed.xml", "feed.json"}


def test_site_builds(tmp_path):
    out, names = build.build(".", out_dir=str(tmp_path / "dist"))
    # site/data/ is a rebuildable derived layer and is gitignored, so a clean checkout builds the
    # narrative pages plus empty-state index pages. Sub-pages appear only when data is compiled.
    assert PAGES <= set(names), PAGES - set(names)

    def read(n):
        return open(os.path.join(out, n), encoding="utf-8").read()

    idx = read("index.html")
    assert "The Exhaust" in idx and "shadow statistics" in idx
    assert "Never predict, only measure" in idx

    tr = read("track-record.html")
    assert "Track Record" in tr and "pre-registered" in tr.lower()

    # A metric straight out of scorecard.json prints ~17 significant figures, which publishes a
    # precision the measurement does not have. The raw value stays in the JSON a critic reruns.
    import re as _re
    for cell in _re.findall(r"<td>([0-9.]+)</td>", tr):
        frac = cell.split(".")[1] if "." in cell else ""
        assert len(frac) <= 4, f"track record published an over-precise number: {cell}"

    rc = read("retrocasts.html")
    assert "NHTSA" in rc and "frozen" in rc.lower()          # the real pre-registration is rendered

    meth = read("methodology.html")
    assert "Never predict" in meth and "Michael King" in meth

    # well-formed, theme-aware, and loading NO third-party asset. Anchors to outside pages are
    # legitimate and load-bearing here — a receipt that cannot link its source is not a receipt —
    # so the rule is about what the browser FETCHES, not what it links.
    for n in PAGES - {"feed.xml", "feed.json"}:
        h = read(n)
        assert h.startswith("<!doctype html>") and h.rstrip().endswith("</html>")
        assert "prefers-color-scheme" in h                  # theme-aware
        for banned in ("<script", "<img", "<iframe", "@import", "googletagmanager",
                       "google-analytics", "gtag(", "plausible.io", "fbq("):
            assert banned not in h, f"{n} pulled in {banned}"
        for link in __import__("re").findall(r'<link [^>]*href="([^"]+)"', h):
            assert not link.startswith(("http://", "https://", "//")), \
                f"{n} loads an external stylesheet/asset: {link}"


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


# --------------------------------------------------------------------- BUILD-04 launch surfaces
def _fixture_site(tmp_path, removed_posting_url="u1"):
    """A self-contained repo root: fixture archive -> compiled artifacts -> built site. Exercises
    the real path (archive bytes in, HTML out) without touching the network or live R2."""
    from datetime import date

    from artifacts import compile as ac
    from artifacts.tests import test_artifacts as fx
    from collectors.framework import LocalFSBackend

    root = str(tmp_path / "repo")
    os.makedirs(os.path.join(root, "collectors"), exist_ok=True)
    json.dump({"states": [{"state": "TX", "agency": "Texas Workforce Commission",
                           "format": "socrata-csv", "notes": "Socrata endpoint."},
                          {"state": "PA", "agency": "PA DLI", "format": "html"}]},
              open(os.path.join(root, "collectors", "seed_warn.json"), "w", encoding="utf-8"))
    json.dump({"boards": [{"ats": "greenhouse", "token": "acme", "company": "Acme Corp"}]},
              open(os.path.join(root, "collectors", "seed_boards.json"), "w", encoding="utf-8"))

    storage = LocalFSBackend(os.path.join(root, "archive"))
    fx._archive(storage, "warn/TX", date(2026, 7, 28), "1200-a.csv",
                b'"notice_date","job_site_name","county_name","total_layoff_number","layoff_date"\n'
                b'"2026-07-20T00:00:00.000","Acme Freight","Bexar","120","2026-09-01T00:00:00.000"\n')
    fx._archive(storage, "warn/TX", date(2026, 7, 29), "1200-b.csv", fx.CSV_TX)
    fx._archive(storage, "warn/PA", date(2026, 7, 29), "1200-c.html", b"<html><p>links</p></html>")
    fx._archive(storage, "ats-boards/greenhouse/acme", date(2026, 7, 28), "a.json",
                json.dumps({"jobs": [{"id": 1, "title": "Engineer",
                                      "absolute_url": removed_posting_url},
                                     {"id": 2, "title": "Designer", "absolute_url": "u2"}]}).encode())
    fx._archive(storage, "ats-boards/greenhouse/acme", date(2026, 7, 29), "b.json",
                json.dumps({"jobs": [{"id": 2, "title": "Designer", "absolute_url": "u2"}]}).encode())
    ac.compile_all(storage, root, days=7, today=date(2026, 7, 29), code_ref="cafe1234")
    out, names = build.build(root, out_dir=os.path.join(root, "dist"))
    return root, out, names


def _data(root, name):
    return json.load(open(os.path.join(root, "site", "data", name), encoding="utf-8"))


def _write_data(root, name, doc):
    json.dump(doc, open(os.path.join(root, "site", "data", name), "w", encoding="utf-8"))


def _rebuild(root, sub="dist_x"):
    return build.build(root, out_dir=os.path.join(root, sub))


def _refuses(root, exc, sub):
    """Rebuild `root` expecting a refusal of type `exc`; returns the exception message."""
    try:
        _rebuild(root, sub)
    except exc as e:
        assert not os.path.exists(os.path.join(root, sub, "warn.html")), \
            "a refused build must not leave half a site behind"
        return str(e)
    raise AssertionError(f"build did not raise {exc.__name__}")


def test_warn_and_postings_surfaces_render_from_the_archive(tmp_path):
    root, out, names = _fixture_site(tmp_path)

    def read(n):
        return open(os.path.join(out, n.replace("/", os.sep)), encoding="utf-8").read()

    assert "warn/TX.html" in names and "warn/PA.html" in names
    assert "postings/greenhouse-acme.html" in names

    watch = read("warn.html")
    assert "WARN Watch" in watch and "Texas Workforce Commission" in watch
    assert "Acme Freight" in watch                          # a real notice reached the index page
    assert "archived, not yet machine-readable" in watch    # PA is disclosed, not hidden

    tx = read("warn/TX.html")
    assert "Borden Mills" in tx                             # the notice new in the later vintage
    assert "raw/warn/TX/2026/07/29/1200-b.csv" in tx        # the archive key it came from
    assert "name no employer" in tx                         # the blank-employer row is disclosed
    assert 'href="../feed.xml"' in tx                       # sub-page links resolve upward

    pa = read("warn/PA.html")
    assert "not yet machine-readable" in pa and "sha256" in pa
    assert "notices on the published list" not in pa.lower()  # no count it cannot derive

    board = read("postings/greenhouse-acme.html")
    assert "Acme Corp" in board and "Engineer" in board     # the removed posting IS the receipt


def test_every_number_on_a_page_carries_a_receipt_link(tmp_path):
    root, out, names = _fixture_site(tmp_path)
    arts = json.load(open(os.path.join(root, "site", "data", "artifacts.json"),
                          encoding="utf-8"))["artifacts"]
    assert arts, "fixture produced no artifacts"
    for a in arts:
        rp = os.path.join(out, a["receipt"].replace("/", os.sep))
        assert os.path.exists(rp), f"no receipt page for {a['id']}"
        h = __import__("html").unescape(open(rp, encoding="utf-8").read())
        assert a["text"] in h and "cafe1234" in h
        b = json.load(open(os.path.join(root, "site", "receipts", a["index"], a["id"],
                                        "bundle.json"), encoding="utf-8"))
        for i in b["inputs"]:                               # every input hash is on the page
            assert i["sha256"] in h and i["r2_path"] in h


def test_published_surfaces_do_not_claim_retrocast_validation(tmp_path):
    """WARN Watch and Posting-Diff are observational and carry NO retrocast. Saying or implying
    every published number is backtest-validated would be the overclaim the SPEC-08 §5 hostile
    checklist exists to catch — and the naming gate turns on exactly that distinction."""
    root, out, names = _fixture_site(tmp_path)
    import html as _h
    import re as _re
    for n in ("index.html", "warn.html", "postings.html"):
        body = open(os.path.join(out, n), encoding="utf-8").read().split("</style>", 1)[1]
        text = _re.sub(r"\s+", " ", _h.unescape(_re.sub(r"<[^>]+>", " ", body)))
        assert "every one validated by running history backwards" not in text
        # PHRASES that can only be forward-looking claims. Deliberately not bare words like
        # "forecast" or "predict": the pages disclaim those out loud ("no index here forecasts
        # anything"), and a keyword test would fail on its own disclaimer and invite weakening.
        for banned in ("will be laid off", "at risk of", "likely to", "we predict",
                       "we expect", "expected to lay off", "is going to", "signals that"):
            assert banned not in text.lower(), f"{n} drifted into prediction: {banned}"
    idx = open(os.path.join(out, "index.html"), encoding="utf-8").read()
    assert "Observational" in idx and "Signature" in idx, \
        "the home page must keep the two kinds of number visibly distinct"
    watch = open(os.path.join(out, "warn.html"), encoding="utf-8").read()
    assert "not signals or predictions" in watch


def test_every_receipt_points_at_a_methodology_section_that_exists(tmp_path):
    """Full disclosure is mechanical (covenant 4): a receipt cites the methodology its number came
    from, so a dangling anchor silently breaks the opinion-on-disclosed-facts chain."""
    root, out, names = _fixture_site(tmp_path)
    meth = open(os.path.join(out, "methodology.html"), encoding="utf-8").read()
    arts = json.load(open(os.path.join(root, "site", "data", "artifacts.json"),
                          encoding="utf-8"))["artifacts"]
    seen = set()
    for a in arts:
        b = json.load(open(os.path.join(root, "site", "receipts", a["index"], a["id"],
                                        "bundle.json"), encoding="utf-8"))
        ref = b["methodology_ref"]
        page_name, _, anchor = ref.partition("#")
        assert page_name in names, f"receipt cites a page that is not built: {ref}"
        assert f'id={anchor}' in meth or f'id="{anchor}"' in meth, \
            f"receipt cites a methodology anchor that does not exist: {ref}"
        seen.add(ref)
    assert len(seen) >= 2, "both indexes should cite their own methodology section"


def test_an_unreceipted_number_refuses_to_render(tmp_path):
    """THE fail-closed covenant (SPEC-09 §2). Strip a number's evidence and the page must refuse
    — and the build must fail rather than quietly publish a page that looks complete."""
    root, out, names = _fixture_site(tmp_path)
    arts = json.load(open(os.path.join(root, "site", "data", "artifacts.json"),
                          encoding="utf-8"))["artifacts"]
    victim = arts[0]
    bp = os.path.join(root, "site", "receipts", victim["index"], victim["id"], "bundle.json")

    # (a) evidence emptied out: the bundle exists but proves nothing
    b = json.load(open(bp, encoding="utf-8"))
    b["inputs"] = []
    json.dump(b, open(bp, "w", encoding="utf-8"))
    try:
        build.build(root, out_dir=os.path.join(root, "dist2"))
    except build.UnreceiptedNumber as e:
        assert victim["id"] in str(e)
    else:
        raise AssertionError("build published a number whose receipts do not validate")
    assert not os.path.exists(os.path.join(root, "dist2", "warn.html")), \
        "a refused build must not leave half a site behind"

    # (b) bundle deleted outright
    os.remove(bp)
    try:
        build.artifact_card(root, victim)
    except build.UnreceiptedNumber:
        pass
    else:
        raise AssertionError("rendered a number with no receipts bundle at all")


def test_feeds_carry_the_same_numbers_and_their_receipts(tmp_path):
    """Covenant 8, format-not-information: the feed says exactly what the page says, at the same
    moment, with the same evidence — no subscriber-only figure, ever."""
    root, out, names = _fixture_site(tmp_path)
    arts = json.load(open(os.path.join(root, "site", "data", "artifacts.json"),
                          encoding="utf-8"))["artifacts"]
    rss = open(os.path.join(out, "feed.xml"), encoding="utf-8").read()
    jf = json.load(open(os.path.join(out, "feed.json"), encoding="utf-8"))

    assert rss.startswith("<?xml") and "<rss version=\"2.0\">" in rss
    assert jf["version"] == "https://jsonfeed.org/version/1.1"
    assert len(jf["items"]) == len(arts)
    rss_text = __import__("html").unescape(rss)
    for a in arts:
        assert a["text"] in rss_text
        assert f"https://theexhaust.org/{a['receipt']}" in rss
        item = next(i for i in jf["items"] if i["id"] == f"{a['index']}/{a['id']}")
        assert item["_exhaust"]["receipt"].endswith(a["receipt"])
        assert item["_exhaust"]["number"] == a["number"]


def test_stale_archive_says_so_on_the_page(tmp_path):
    """A frozen collector must announce itself. Official publishers do freeze — the appropriations
    lapse is live — so a silent page standing on old data is the failure mode to prevent."""
    root, out, names = _fixture_site(tmp_path)
    hdir = os.path.join(root, "ops", "state", "health")
    os.makedirs(hdir, exist_ok=True)
    json.dump({"collectors": {"warn": {"last_success": "2026-01-01T00:00:00Z"}}},
              open(os.path.join(hdir, "warn.json"), "w", encoding="utf-8"))
    banner = build.health_banner(root, "warn")
    assert banner and "Stale data" in banner and "2026-01-01" in banner
    out2, _ = build.build(root, out_dir=os.path.join(root, "dist3"))
    assert "Stale data" in open(os.path.join(out2, "warn.html"), encoding="utf-8").read()

    json.dump({"collectors": {"warn": {"last_success": "2026-01-01T00:00:00Z",
                                       "paused_states": ["WA"]}}},
              open(os.path.join(hdir, "warn.json"), "w", encoding="utf-8"))
    assert "Stale data" in build.health_banner(root, "warn")     # staleness outranks partial


def test_placeholder_clears_the_launch_surfaces_too(tmp_path):
    """W-005b's hazard, now with sub-directories: a full build followed by a placeholder deploy
    must not leave WARN pages, receipts or feeds published under a no-numbers page."""
    root, out, names = _fixture_site(tmp_path)
    assert os.path.isdir(os.path.join(out, "warn"))
    build.build(root, out_dir=out, placeholder_mode=True)
    assert os.listdir(out) == ["index.html"], os.listdir(out)


def test_stale_banner():
    p = build.page("T", "<p>x</p>", "index.html", stale="Official source last updated 2026-06; index chains to that vintage.")
    assert "chains to that vintage" in p and "stale" in p


# ------------------------------------------------------- W-007c: the publish path is fail-closed
def test_a_torn_derived_layer_refuses_to_build(tmp_path):
    """W-007c/G01. The receipts gate is keyed off the artifacts.json enumeration, so an
    artifacts.json that is missing or unparseable while warn.json survives used to render every
    notice table and diff count with ZERO receipts on disk — and the build stayed green. Torn
    derived layers are reachable without anyone hand-editing anything: a compile crash between
    writes, a bad merge, a half-synced deploy cache."""
    root, out, _ = _fixture_site(tmp_path)
    import shutil

    # (a) the enumeration is gone but the numbers are still there
    os.remove(os.path.join(root, "site", "data", "artifacts.json"))
    shutil.rmtree(os.path.join(root, "site", "receipts"))
    assert "torn" in _refuses(root, build.DerivedLayerError, "dist_a")

    # (b) merge-conflict junk where the enumeration should be
    open(os.path.join(root, "site", "data", "artifacts.json"), "w",
         encoding="utf-8").write("<<<<<<< HEAD\n{}\n=======\n")
    assert "does not parse" in _refuses(root, build.DerivedLayerError, "dist_b")


def test_a_derived_layer_from_two_compile_runs_refuses_to_build(tmp_path):
    """The same defect one step subtler: every file parses, but they are not from the same run —
    fresh receipts under a stale artifacts.json publishes yesterday's numbers over today's
    evidence. The (generated, code_ref) stamp is what makes that DETECTABLE rather than merely
    unlikely; a state carrying a count with no artifact behind it is caught the same way."""
    root, out, _ = _fixture_site(tmp_path)
    arts = _data(root, "artifacts.json")
    arts["code_ref"] = "deadbeef99"                     # a different compile run
    _write_data(root, "artifacts.json", arts)
    assert "different" in _refuses(root, build.DerivedLayerError, "dist_c")

    arts["code_ref"] = _data(root, "warn.json")["code_ref"]
    arts["artifacts"] = [a for a in arts["artifacts"] if not a["id"].startswith("TX-level")]
    _write_data(root, "artifacts.json", arts)
    assert "no matching artifact" in _refuses(root, build.DerivedLayerError, "dist_d")


def test_a_number_that_contradicts_its_own_receipt_refuses_to_render(tmp_path):
    """W-007c/G02. Bundle-exists was never the same as bundle-agrees: an artifact whose number was
    inflated 10x rendered on its own receipt page directly above the un-inflated bundle table, and
    the fail-closed gate passed it. A receipt that does not match the number it is attached to is
    worse than no receipt, because it looks like proof."""
    root, out, _ = _fixture_site(tmp_path)
    pristine = json.dumps(_data(root, "artifacts.json"))
    victim_id = next(a["id"] for a in json.loads(pristine)["artifacts"]
                     if isinstance(a.get("number"), int))

    def corrupt(mutate, sub):
        doc = json.loads(pristine)
        mutate(next(a for a in doc["artifacts"] if a["id"] == victim_id))
        _write_data(root, "artifacts.json", doc)
        return _refuses(root, build.UnreceiptedNumber, sub)

    def inflate(a):
        a["number"] *= 10
        a["text"] = a["text"].replace(str(a["number"] // 10), str(a["number"]))
    assert "contradicts its own receipt bundle" in corrupt(inflate, "dist_e")

    # the same for the vintage the claim is dated to, and for the unit it is counted in
    assert "as_of" in corrupt(lambda a: a.update(as_of="1999-01-01"), "dist_f")
    assert "unit" in corrupt(lambda a: a.update(unit="jellybeans"), "dist_f2")

    # and a sentence that does not contain the number it is receipted for
    assert "does not appear in the sentence" in \
        corrupt(lambda a: a.update(text="A sentence with no figure in it at all."), "dist_g")


# ------------------------------------------------------------- W-007c: the scorecard is the moat
def _plant_scorecard(root, index="demo-index", **over):
    """A minimal committed retrocast: a pre-registration plus one results scorecard."""
    d = os.path.join(root, "retrocast", index)
    os.makedirs(os.path.join(d, "results", "v1"), exist_ok=True)
    open(os.path.join(d, "PRE-REGISTRATION-v1.md"), "w", encoding="utf-8").write(
        "# Demo Index — v1\n\nFrozen 2026-07-01.\n")
    card = {"index": index, "version": "v1", "registration_commit": "a" * 40,
            "metrics": {"pr_auc": 0.25, "median_lead_days": 100},
            "bars": {"precision": 0.3}, "pass": False,
            "pass_detail": {"beats_baseline": False, "precision_ok": False},
            "leakage_flags": [],
            "provenance": {"dirty": False, "registration_is_ancestor_of_code": True}}
    card.update(over)
    p = os.path.join(d, "results", "v1", "scorecard.json")
    json.dump(card, open(p, "w", encoding="utf-8"))
    return p


def test_a_corrupt_scorecard_aborts_the_build(tmp_path):
    """W-007c/G04. Absent is not broken. `except Exception: pass` meant a truncated scorecard —
    bad merge, partial write, glob regression — made the published FAIL silently vanish from the
    Track Record while the home page kept saying the failure is published there, and the build
    went green. A permanent public failure record must not be losable by accident."""
    root, out, _ = _fixture_site(tmp_path)
    p = _plant_scorecard(root)
    out2, _ = _rebuild(root, "dist_ok")
    assert "demo-index" in open(os.path.join(out2, "track-record.html"), encoding="utf-8").read()

    open(p, "w", encoding="utf-8").write('{"index": "demo-index", "met')      # truncated
    assert "does not parse" in _refuses(root, build.CorruptScorecard, "dist_h")


def test_a_scorecard_that_cannot_support_the_pre_registered_banner_refuses(tmp_path):
    """W-007c/G07. The Track Record asserts in prose that every bar was pre-registered and frozen
    in public before scoring. Nothing checked the card being rendered under that banner, so a
    dirty-tree run, a broken ancestry, an unregistered index, or a PASS pill contradicting its own
    pass_detail would have made the page's central falsifiability claim publicly false."""
    root, out, _ = _fixture_site(tmp_path)
    for i, over in enumerate([
            {"provenance": {"dirty": True, "registration_is_ancestor_of_code": True}},
            {"provenance": {"dirty": False, "registration_is_ancestor_of_code": False}},
            {"pass": "false"},                                  # a truthy string renders as PASS
            {"pass": True},                                     # contradicts its own pass_detail
    ]):
        _plant_scorecard(root, **over)
        _refuses(root, build.CorruptScorecard, f"dist_g7{i}")

    # a scorecard for an index with no public pre-registration is not a track record at all
    _plant_scorecard(root)                                  # restore the valid card first
    _plant_scorecard(root, index="unregistered")
    os.remove(os.path.join(root, "retrocast", "unregistered", "PRE-REGISTRATION-v1.md"))
    assert "no pre-registration" in _refuses(root, build.CorruptScorecard, "dist_g7x")


def test_two_scorecards_render_both_pills_in_a_stable_order(tmp_path):
    """Until W-008 the page had only ever rendered one row, and no test had ever rendered a PASS
    pill at all — so the pill branch and the multi-row ordering were both unexercised."""
    root, out, _ = _fixture_site(tmp_path)
    _plant_scorecard(root, index="aaa-index")                       # a FAIL card
    _plant_scorecard(root, index="zzz-index", **{
        "pass": True, "pass_detail": {"beats_baseline": True, "precision_ok": True,
                                      "lead_degenerate": False}})   # a PASS card
    out2, _ = _rebuild(root, "dist_pills")
    tr = open(os.path.join(out2, "track-record.html"), encoding="utf-8").read()
    assert tr.count('class="pill fail">FAIL') == 1
    assert tr.count('class="pill pass">PASS') == 1
    assert tr.index("aaa-index") < tr.index("zzz-index"), "rows must render in a stable order"
    # a clean PASS card carries no caveat row; the FAIL card names the bars it missed
    assert "bars missed: beats_baseline, precision_ok" in tr


def test_track_record_publishes_both_real_failures_with_their_evidence():
    """The committed artifact, not a fixture: both retrocasts we have run FAILED, and both must
    render — with the scorecard and autopsy a critic reruns (G12), the missed bars named, and no
    over-precise digits. This is the tripwire on the project's stated moat."""
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        out, _ = build.build(".", out_dir=os.path.join(d, "dist"))
        tr = open(os.path.join(out, "track-record.html"), encoding="utf-8").read()

    cards = build._scorecards(".")
    assert {c["index"] for c in cards} >= {"nhtsa-recalls", "hospital-care"}, cards
    assert tr.count('class="pill fail">FAIL') == len(cards)
    for c in cards:
        assert c["pass"] is False, f"{c['index']} is no longer a published failure — read this test"
        assert c["index"] in tr and build._num(c["metrics"]["pr_auc"]) in tr
        assert f'{build.REPO_URL}/tree/main/{c["_results_dir"]}' in tr      # the scorecard itself
        assert f'{build.REPO_URL}/blob/main/{c["_report"]}' in tr           # the autopsy
        for flag in c.get("leakage_flags") or []:
            assert "leakage check" in tr
        assert "bars missed" in tr


def test_committed_scorecards_agree_with_the_frozen_bars():
    """A scorecard is only a record if its bars are the ones that were frozen in public. Loading
    the committed cards against the frozen modules is what makes a hand-edit or a partial rerun
    fail CI instead of rendering quietly (W-007c/G07)."""
    from retrocast.hospital_care import spec as hc_spec
    from retrocast.nhtsa_recalls import lexicon as nhtsa_lex

    frozen = {"nhtsa-recalls": nhtsa_lex.BARS, "hospital-care": hc_spec.BARS}
    for c in build._scorecards("."):
        assert c["bars"] == frozen[c["index"]], (c["index"], c["bars"])
        assert build._detail_verdict(c["pass_detail"]) == c["pass"]
        assert c["provenance"]["dirty"] is False
        assert c["provenance"]["registration_is_ancestor_of_code"] is True
        assert c["registration_commit"] and len(c["registration_commit"]) == 40
        for v in (c["data_vintages"] or {}).values():          # every input vintage is pinned
            leaves = v.values() if "sha256" not in v else [v]
            for leaf in leaves:
                assert leaf.get("sha256") and leaf.get("r2_key")


# ------------------------------------------------------------------ W-007c: hostile render inputs
def test_a_hostile_url_in_an_archived_payload_never_becomes_a_link(tmp_path):
    """W-007c/G08. The collector archives third-party board payloads verbatim — correct, that is
    its job — and `html.escape` makes a URL safe as text but does nothing to a `javascript:` scheme
    inside an href. A spoofed unauthenticated ATS endpoint must not be able to put an executable
    link on theexhaust.org."""
    root, out, _ = _fixture_site(tmp_path, removed_posting_url="javascript:alert(document.cookie)")
    board = open(os.path.join(out, "postings", "greenhouse-acme.html"), encoding="utf-8").read()
    assert "Engineer" in board                                # the removed posting is still shown
    assert "javascript:" not in board                         # but never as a link, and not at all
    assert 'href="u2"' not in board                           # relative junk is not linked either

    assert build._safe_href("https://boards.greenhouse.io/acme/jobs/1") == \
        "https://boards.greenhouse.io/acme/jobs/1"
    for bad in ("javascript:alert(1)", "JavaScript:alert(1)", "data:text/html,<script>", "  ",
                None, "//evil.example/x"):
        assert build._safe_href(bad) == "", bad


# --------------------------------------------------------- W-007c: disclosure never fails open
def test_a_damaged_health_file_says_freshness_cannot_be_verified(tmp_path):
    """W-007c/G15. The stale-data chain used to fail open exactly when the state it reads is
    damaged: a truncated health/warn.json was skipped, no banner rendered, and the page presented
    an old vintage as if the pipeline were healthy. 'We cannot tell' is its own disclosure."""
    root, out, _ = _fixture_site(tmp_path)
    hdir = os.path.join(root, "ops", "state", "health")
    os.makedirs(hdir, exist_ok=True)
    assert build.health_banner(root, "warn") is None          # absent state -> no banner, still

    open(os.path.join(hdir, "warn.json"), "w", encoding="utf-8").write('{"collectors": {"warn"')
    banner = build.health_banner(root, "warn")
    assert banner and "Freshness cannot be verified" in banner
    out2, _ = _rebuild(root, "dist_h15")
    assert "Freshness cannot be verified" in \
        open(os.path.join(out2, "warn.html"), encoding="utf-8").read()


def test_a_paused_state_says_partial_coverage_on_its_pages(tmp_path):
    """W-007c/G21. The paused branch of health_banner had no test at all — only the assertion that
    staleness outranks it — so a regression there would silently remove the disclosure from a
    state that is genuinely not being collected, and every test would still pass."""
    root, out, _ = _fixture_site(tmp_path)
    hdir = os.path.join(root, "ops", "state", "health")
    os.makedirs(hdir, exist_ok=True)
    from collectors.framework import utcnow_iso
    json.dump({"collectors": {"warn": {"last_success": utcnow_iso(), "paused_states": ["WA"]}}},
              open(os.path.join(hdir, "warn.json"), "w", encoding="utf-8"))
    banner = build.health_banner(root, "warn")
    assert banner and "Partial coverage" in banner and "WA" in banner
    out2, _ = _rebuild(root, "dist_h21")
    for p in ("warn.html", os.path.join("warn", "TX.html")):
        h = open(os.path.join(out2, p), encoding="utf-8").read()
        assert "Partial coverage" in h and "WA" in h, p


def test_warn_page_counts_only_states_it_actually_archived(tmp_path):
    """W-007c/G17. '{len(states)} states archived' counted seeded states with no snapshot at all,
    contradicting the page's own per-row 'no snapshot in window' cells on a page whose credibility
    rests on stating exactly what is held."""
    root, out, _ = _fixture_site(tmp_path)
    warn = _data(root, "warn.json")
    warn["states"].append({"state": "WA", "agency": "WA ESD", "vintages": [],
                           "notices": [], "parse_status": "no-vintage"})
    _write_data(root, "warn.json", warn)
    out2, _ = _rebuild(root, "dist_h17")
    h = open(os.path.join(out2, "warn.html"), encoding="utf-8").read()
    assert "2 states archived" in h and "1 further state(s) are seeded" in h
    assert "3 states archived" not in h


def test_feeds_refuse_to_invent_a_publication_date(tmp_path):
    """W-007c/G16. The now() fallback stamped an undated artifact with the BUILD time, so it moved
    on every rebuild and resurfaced as unread in every reader; the JSON feed emitted a bare
    'T00:00:00Z' that strict readers can reject the whole feed over. The empty feed — what every
    clean-checkout deploy builds — is validated here for the first time."""
    from sitegen import feeds

    assert feeds.rss([]).startswith("<?xml")
    assert json.loads(feeds.json_feed([]))["items"] == []
    undated = [{"index": "warn-watch", "id": "x", "text": "t", "receipt": "receipts/x.html",
                "as_of": "", "kind": "cadence"}]
    for fn in (feeds.rss, feeds.json_feed):
        try:
            fn(undated)
        except feeds.UndatedArtifact:
            pass
        else:
            raise AssertionError(f"{fn.__name__} invented a date for an undated artifact")


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
