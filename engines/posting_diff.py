"""E1 Posting-Diff — the observational artifact core.

Given two normalized snapshots of one board (earlier, later), compute what was pulled, added, and
kept. This is publishable day one as REPORTING (naming-gate carve-out): "Company X removed 78% of
its postings in 3 weeks — here are the diffs." No signature inference, no prediction — just the
company's own public postings, differenced. The receipts are the removed/added postings themselves.
"""
from __future__ import annotations


def diff(prev, cur):
    """prev/cur: lists of normalized Posting dicts (need 'id' + 'title'). Returns the diff with
    receipts (the actual pulled/added postings) and the pulled/added rates vs the earlier snapshot."""
    pby = {p["id"]: p for p in prev}
    cby = {c["id"]: c for c in cur}
    prev_ids, cur_ids = set(pby), set(cby)
    removed = sorted(prev_ids - cur_ids)
    added = sorted(cur_ids - prev_ids)
    kept = prev_ids & cur_ids
    n_prev = len(prev_ids)
    return {
        "prev_count": n_prev,
        "cur_count": len(cur_ids),
        "kept_count": len(kept),
        "removed_count": len(removed),
        "added_count": len(added),
        "pulled_pct": round(len(removed) / n_prev, 4) if n_prev else 0.0,
        "added_pct": round(len(added) / n_prev, 4) if n_prev else 0.0,
        "net_pct": round((len(cur_ids) - n_prev) / n_prev, 4) if n_prev else 0.0,
        # receipts: the actual postings that moved
        "removed": [{"id": i, "title": pby[i]["title"], "url": pby[i]["url"]} for i in removed],
        "added": [{"id": i, "title": cby[i]["title"], "url": cby[i]["url"]} for i in added],
    }


def headline(company, d, window_desc):
    """One declarative sentence (no adjectives) for the artifact — the born-shareable unit."""
    return (f"{company} removed {d['removed_count']} of {d['prev_count']} public job postings "
            f"({d['pulled_pct']:.0%}) {window_desc}; added {d['added_count']}.")
