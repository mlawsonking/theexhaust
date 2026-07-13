"""Deterministic crosswalk tables (T0/T1) — free, official, $0.

Currently: SEC company_tickers.json (CIK <-> ticker <-> legal name; 9,304 issuers, ~710 KB,
verified 2026-07-13). GLEIF LEI and the free bi-weekly OpenCorporates-ID->LEI file, Census
Gazetteer/FIPS, and HUD ZIP crosswalks slot in behind the same Crosswalk interface as they land.
SEC requires a descriptive User-Agent (org + contact) or it 403s.
"""
from __future__ import annotations

import json
import os
import urllib.request

from .resolve import norm_key

UA = "TheExhaust/0.1 (+https://theexhaust.org; contact ops@theexhaust.org)"
SEC_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"


def fetch_sec_tickers(dest=None):
    req = urllib.request.Request(SEC_TICKERS_URL, headers={"User-Agent": UA})
    raw = urllib.request.urlopen(req, timeout=60).read()
    if dest:
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "wb") as f:
            f.write(raw)
    return raw


def rows_from_sec(raw) -> list[dict]:
    j = json.loads(raw) if isinstance(raw, (bytes, str, bytearray)) else raw
    out = []
    for v in j.values():
        out.append({"cik": str(v.get("cik_str")), "ticker": str(v.get("ticker", "")).upper(),
                    "title": v.get("title", ""), "source": "sec"})
    return out


class Crosswalk:
    """Indexed view over resolved entity rows {cik, ticker, title, source}."""

    def __init__(self, rows):
        self.rows = rows
        self.by_ticker = {r["ticker"]: r for r in rows if r.get("ticker")}
        self.by_cik = {r["cik"]: r for r in rows if r.get("cik")}
        self.by_norm = {}
        for r in rows:
            self.by_norm.setdefault(norm_key(r["title"]), []).append(r)

    @classmethod
    def from_sec(cls, raw):
        return cls(rows_from_sec(raw))

    @classmethod
    def load_or_fetch(cls, cache="local-archive/resolver/company_tickers.json"):
        raw = open(cache, "rb").read() if os.path.exists(cache) else fetch_sec_tickers(cache)
        return cls.from_sec(raw)
