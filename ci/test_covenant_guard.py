"""Covenant-guard tests. Run: python ci/test_covenant_guard.py"""
import os
import pathlib
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import covenant_guard as cg  # noqa: E402


def main():
    banned = cg.load_banned()
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)
        (root / "collectors").mkdir()
        (root / ".github" / "workflows").mkdir(parents=True)

        # clean baseline
        (root / "collectors" / "ok.py").write_text("URL = 'https://data.cms.gov/x'\n", encoding="utf-8")
        (root / ".github" / "workflows" / "ci.yml").write_text("steps:\n  - run: echo hi\n", encoding="utf-8")
        assert cg.check_collectors(banned, root) == []
        assert cg.check_r1_no_llm_key(root) == []

        # broadened LLM-credential detection (not just the literal ANTHROPIC_API_KEY)
        (root / ".github" / "workflows" / "bad.yml").write_text(
            "env:\n  ANTHROPIC_AUTH_TOKEN: ${{ secrets.X }}\n", encoding="utf-8")
        assert cg.check_r1_no_llm_key(root), "should catch ANTHROPIC_AUTH_TOKEN"

        # do-not-collect: direct ALEC fails, Wayback-wrapped ALEC passes (SPEC-01)
        (root / "collectors" / "bad_alec.py").write_text("U = 'https://alecexposed.org/wiki'\n", encoding="utf-8")
        (root / "collectors" / "ok_wayback.py").write_text(
            "U = 'https://web.archive.org/web/2020/https://alecexposed.org/wiki'\n", encoding="utf-8")
        (root / "collectors" / "bad_legacy.py").write_text("U = 'https://legacy.com/x'\n", encoding="utf-8")
        v = cg.check_collectors(banned, root)
        assert any("bad_alec.py" in x for x in v), "direct alecexposed.org must fail"
        assert not any("ok_wayback.py" in x for x in v), "wayback-wrapped ALEC must pass"
        assert any("bad_legacy.py" in x for x in v), "legacy.com must always fail"

        # W-005c/F04: the register must be enforced in the SEED FILES too — that is where every
        # source URL has lived since W-004. A banned data_url in a seed used to pass CI green.
        (root / "collectors" / "seed_ok.json").write_text(
            '{"states": [{"state": "TX", "data_url": "https://data.texas.gov/resource/x.csv"}]}',
            encoding="utf-8")
        assert not any("seed_ok.json" in x for x in cg.check_collectors(banned, root))
        (root / "collectors" / "seed_bad.json").write_text(
            '{"states": [{"state": "XX", "data_url": "https://www.indeed.com/cmp/acme/reviews"}]}',
            encoding="utf-8")
        v2 = cg.check_collectors(banned, root)
        assert any("seed_bad.json" in x for x in v2), "banned source in a seed .json must fail"

    print("COVENANT GUARD TESTS PASS")


if __name__ == "__main__":
    main()
