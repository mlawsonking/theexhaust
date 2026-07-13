"""Tiered entity resolution (SPEC-09 §1). A query resolves at the cheapest tier that can decide;
ambiguous pairs escalate. T0 hard keys and T1 exact crosswalk are $0 and certain; T2 is a
conservative normalized-name token-similarity with an auto-accept band and an ambiguity band that
QUEUES rather than guesses; T3 (LLM adjudication of T2-ambiguous pairs) is gated and lives
elsewhere (never auto-invoked here). Local embeddings are a later T2 enhancement (4080)."""
from __future__ import annotations

import re

# Legal-form and filler tokens stripped before matching.
_LEGAL = {"inc", "incorporated", "corp", "corporation", "co", "company", "companies", "llc", "llp",
          "lp", "ltd", "limited", "plc", "holdings", "holding", "group", "the", "sa", "ag", "nv",
          "and", "of", "class", "common", "stock", "cos"}

# Auto-accept only when clearly the best AND clearly ahead of the runner-up (avoids false merges).
T2_ACCEPT = 0.85
T2_MARGIN = 0.15
T2_AMBIG = 0.60


def norm_tokens(name):
    s = re.sub(r"[^a-z0-9 ]", " ", (name or "").lower())
    return [t for t in s.split() if t and t not in _LEGAL]


def norm_key(name):
    return " ".join(norm_tokens(name))


def jaccard(a, b):
    sa, sb = set(a), set(b)
    return len(sa & sb) / len(sa | sb) if (sa | sb) else 0.0


def _hit(row, tier, conf, evidence):
    return {"match": {"cik": row["cik"], "ticker": row["ticker"], "title": row["title"]},
            "tier": tier, "confidence": round(conf, 4), "evidence": evidence}


def _cands(rows):
    return [{"cik": r["cik"], "ticker": r["ticker"], "title": r["title"]} for r in rows]


def resolve_company(cx, query):
    """Return a hit {match,tier,confidence,evidence}, an {ambiguous:[...]} queue item, or None."""
    q = (query or "").strip()
    if not q:
        return None
    # T0: exact CIK or ticker
    if q.isdigit() and q in cx.by_cik:
        return _hit(cx.by_cik[q], "T0", 1.0, "CIK exact")
    if q.upper() in cx.by_ticker and (q.isupper() or (q.isalpha() and len(q) <= 5)):
        return _hit(cx.by_ticker[q.upper()], "T0", 1.0, f"ticker exact ({q.upper()})")
    # T1: exact normalized legal name
    nk = norm_key(q)
    if nk and nk in cx.by_norm:
        rows = cx.by_norm[nk]
        ciks = {r["cik"] for r in rows}
        if len(ciks) == 1:  # one entity, possibly several share-class tickers -> unambiguous
            note = f" ({len(rows)} share classes)" if len(rows) > 1 else ""
            return _hit(rows[0], "T1", 0.98, f"exact normalized name '{nk}'{note}")
        return {"query": query, "ambiguous": _cands(rows), "tier": "T1",
                "reason": f"{len(ciks)} distinct issuers share the normalized name '{nk}'"}
    # T2: normalized-name token similarity
    qt = norm_tokens(q)
    if not qt:
        return None
    scored = sorted(((jaccard(qt, norm_tokens(r["title"])), r) for r in cx.rows),
                    key=lambda x: x[0], reverse=True)
    best_s, best_r = scored[0]
    second = scored[1][0] if len(scored) > 1 else 0.0
    if best_s >= T2_ACCEPT and (best_s - second) >= T2_MARGIN:
        return _hit(best_r, "T2", best_s, f"token similarity {best_s:.2f} (runner-up {second:.2f})")
    if best_s >= T2_AMBIG:
        return {"query": query, "ambiguous": _cands([r for _s, r in scored[:5]]), "tier": "T2",
                "reason": f"top similarity {best_s:.2f} within the ambiguity band — queue for T3"}
    return None
