"""E1 Posting-Diff — ATS board clients + normalizers.

Snapshots public, unauthenticated job-board JSON (Greenhouse / Lever / Ashby / SmartRecruiters)
and normalizes each vendor's shape to a common Posting record. The raw JSON is archived immutably
(collectors/ats_boards.py); normalization is the rebuildable derived layer that feeds posting_diff.

Covenant: public no-auth endpoints, honest UA, polite rate-limited polling, no circumvention.
Lever's README explicitly permits third-party scraping of published postings; the others require
no auth and carry no README prohibition (a one-time robots/master-ToS check precedes fleet polling).
Shapes verified live 2026-07-13 (stripe / leverdemo / Ramp).
"""
from __future__ import annotations

import json

from collectors.framework import http_get

ENDPOINTS = {
    "greenhouse": "https://boards-api.greenhouse.io/v1/boards/{token}/jobs",
    "lever": "https://api.lever.co/v0/postings/{token}?mode=json",
    "ashby": "https://api.ashbyhq.com/posting-api/job-board/{token}",
    "smartrecruiters": "https://api.smartrecruiters.com/v1/companies/{token}/postings?limit=100",
}


def board_url(ats, token):
    return ENDPOINTS[ats].format(token=token)


def fetch_board(ats, token, max_bytes=None):
    """(status, headers, raw_bytes, url) — the raw JSON to archive."""
    status, headers, body = http_get(board_url(ats, token), max_bytes=max_bytes, timeout=60)
    return status, headers, body, board_url(ats, token)


def _s(x):
    return x if isinstance(x, str) else ("" if x is None else str(x))


def normalize(ats, raw):
    """Raw board JSON -> list of common Posting dicts {id,title,location,url,updated_at}.
    id is namespaced by ats+token-scope via the vendor id (unique within a board)."""
    j = json.loads(raw) if isinstance(raw, (bytes, str, bytearray)) else raw
    out = []
    if ats == "greenhouse":
        for job in j.get("jobs", []):
            loc = job.get("location") or {}
            out.append({"id": _s(job.get("id")), "title": _s(job.get("title")),
                        "location": _s(loc.get("name")), "url": _s(job.get("absolute_url")),
                        "updated_at": _s(job.get("updated_at"))})
    elif ats == "lever":
        for p in (j if isinstance(j, list) else []):
            cats = p.get("categories") or {}
            out.append({"id": _s(p.get("id")), "title": _s(p.get("text")),
                        "location": _s(cats.get("location")), "url": _s(p.get("hostedUrl")),
                        "updated_at": _s(p.get("createdAt"))})
    elif ats == "ashby":
        for job in j.get("jobs", []):
            out.append({"id": _s(job.get("id")), "title": _s(job.get("title")),
                        "location": _s(job.get("location")), "url": _s(job.get("jobUrl") or job.get("applyUrl")),
                        "updated_at": _s(job.get("publishedAt"))})
    elif ats == "smartrecruiters":
        for it in j.get("content", []):
            loc = it.get("location") or {}
            place = ", ".join(x for x in (loc.get("city"), loc.get("region"), loc.get("country")) if x)
            out.append({"id": _s(it.get("id")), "title": _s(it.get("name")),
                        "location": place, "url": _s(it.get("ref") or it.get("applyUrl")),
                        "updated_at": _s(it.get("releasedDate"))})
    else:
        raise ValueError(f"unknown ATS '{ats}'")
    return out
