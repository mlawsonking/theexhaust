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


class UndatedArtifact(Exception):
    """An artifact reached the feeds with no usable vintage date (W-007c/G16)."""


def _parse_day(day: str):
    try:
        return datetime.strptime(str(day), "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except Exception:
        return None


def _rfc822(day: str) -> str:
    """An artifact's as_of date -> RFC-822. Dates, not times: the vintage is a day, and inventing
    a publication time we did not measure would be a small lie in a system that sells honesty.

    W-007c/G16 — the old now() fallback told exactly that lie: an artifact with a blank as_of got
    the BUILD time, so it shifted on every rebuild and resurfaced as unread in every RSS reader.
    An item with no vintage is a broken artifact, and the build refuses broken artifacts rather
    than dating them for them."""
    dt = _parse_day(day)
    if dt is None:
        raise UndatedArtifact(f"artifact vintage {day!r} is not a YYYY-MM-DD date — refusing to "
                              f"stamp a feed item with a publication time we did not measure")
    return format_datetime(dt)


def _channel_date(artifacts) -> str:
    """The channel's own lastBuildDate. This one IS a build-time fact, so `now()` is honest here —
    it is the only place the fallback survives, and only when there is no artifact to date from."""
    dt = _parse_day(artifacts[0].get("as_of", "")) if artifacts else None
    return format_datetime(dt or datetime.now(timezone.utc))


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
            f"<lastBuildDate>{_channel_date(artifacts)}</lastBuildDate>"
            f"{''.join(items)}"
            "</channel></rss>\n")


def _json_date(day: str) -> str:
    """RFC-3339 for JSON Feed. A blank as_of used to emit 'T00:00:00Z', which is not a date at all
    and which strict readers can reject the whole feed over (W-007c/G16)."""
    if _parse_day(day) is None:
        raise UndatedArtifact(f"artifact vintage {day!r} is not a YYYY-MM-DD date")
    return f"{day}T00:00:00Z"


def json_feed(artifacts, generated="") -> str:
    items = [{
        "id": f"{a['index']}/{a['id']}",
        "url": _item_link(a),
        "title": a["text"],
        "content_text": (f"{a['text']}\n\nReceipts: {_abs(a['receipt'])}\n"
                         f"Index version: {a.get('index_version','')}\n"
                         f"Archived vintage: {a.get('as_of','')}"),
        "date_published": _json_date(a.get("as_of", "")),
        "tags": [a.get("index", ""), a.get("kind", "")],
        "_exhaust": {"number": a.get("number"), "unit": a.get("unit"),
                     "receipt": _abs(a["receipt"]), "index_version": a.get("index_version")},
    } for a in artifacts]
    return json.dumps({"version": "https://jsonfeed.org/version/1.1", "title": TITLE,
                       "home_page_url": SITE, "feed_url": _abs("feed.json"),
                       "description": DESC, "_generated": generated, "items": items},
                      indent=2) + "\n"
