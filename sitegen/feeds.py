"""RSS 2.0 + JSON Feed 1.1 over the compiled artifacts. Stdlib-only.

One artifact = one feed item, and every item carries the link to its receipt bundle. That is the
whole distribution contract: nothing reaches a reader without the evidence attached, so a feed
item can be checked against the archived, hashed vintage it came from without asking us.

`format-not-information` (covenant 8): the feeds carry exactly what the pages carry, at the same
moment. No early access, no subscriber-only number, ever.
"""
from __future__ import annotations

import html
import json
from email.utils import format_datetime
from datetime import datetime, timezone

SITE = "https://theexhaust.org"
TITLE = "The Exhaust — shadow statistics"
DESC = ("Receipts-attached measurements compiled from archived public records. "
        "Never predict, only measure.")


def _abs(path: str) -> str:
    return f"{SITE}/{path.lstrip('/')}"


def _rfc822(day: str) -> str:
    """An artifact's as_of date -> RFC-822. Dates, not times: the vintage is a day, and inventing
    a publication time we did not measure would be a small lie in a system that sells honesty."""
    try:
        dt = datetime.strptime(day, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except Exception:
        dt = datetime.now(timezone.utc)
    return format_datetime(dt)


def _item_link(a) -> str:
    return _abs(a.get("page") or "index.html")


def rss(artifacts, generated="") -> str:
    items = []
    for a in artifacts:
        items.append(
            "<item>"
            f"<title>{html.escape(a['text'])}</title>"
            f"<link>{html.escape(_item_link(a))}</link>"
            f"<guid isPermaLink=\"false\">{html.escape(a['index'])}/{html.escape(a['id'])}</guid>"
            f"<pubDate>{_rfc822(a.get('as_of',''))}</pubDate>"
            f"<category>{html.escape(a.get('kind',''))}</category>"
            "<description>"
            f"{html.escape(a['text'])} "
            f"Receipts: {html.escape(_abs(a['receipt']))} "
            f"(index {html.escape(a.get('index_version',''))})"
            "</description>"
            "</item>")
    return ('<?xml version="1.0" encoding="utf-8"?>\n'
            '<rss version="2.0"><channel>'
            f"<title>{html.escape(TITLE)}</title>"
            f"<link>{SITE}</link>"
            f"<description>{html.escape(DESC)}</description>"
            "<language>en-us</language>"
            f"<lastBuildDate>{_rfc822((artifacts[0].get('as_of') if artifacts else ''))}</lastBuildDate>"
            f"{''.join(items)}"
            "</channel></rss>\n")


def json_feed(artifacts, generated="") -> str:
    items = [{
        "id": f"{a['index']}/{a['id']}",
        "url": _item_link(a),
        "title": a["text"],
        "content_text": (f"{a['text']}\n\nReceipts: {_abs(a['receipt'])}\n"
                         f"Index version: {a.get('index_version','')}\n"
                         f"Archived vintage: {a.get('as_of','')}"),
        "date_published": f"{a.get('as_of','')}T00:00:00Z",
        "tags": [a.get("index", ""), a.get("kind", "")],
        "_exhaust": {"number": a.get("number"), "unit": a.get("unit"),
                     "receipt": _abs(a["receipt"]), "index_version": a.get("index_version")},
    } for a in artifacts]
    return json.dumps({"version": "https://jsonfeed.org/version/1.1", "title": TITLE,
                       "home_page_url": SITE, "feed_url": _abs("feed.json"),
                       "description": DESC, "_generated": generated, "items": items},
                      indent=2) + "\n"
