"""The artifact compiler (BUILD-04) — archived snapshots -> receipted public artifacts.

    python -m artifacts.compile [--days 14] [--local-root DIR] [--out site/data]

Reads ONLY the archive (SPEC-01 raw objects + their per-day manifests) and writes two things:

  site/data/*.json      the derived layer the site renders (rebuildable, never authoritative)
  site/receipts/...     one immutable evidence bundle per published number (SPEC-09 §2)

Three invariants this file exists to hold:

1. **No live fetch, ever.** Every input is an archived object addressed by its manifest key, so a
   page can only ever say what a stored, hashed vintage said. Government sources can freeze mid
   publication (the appropriations lapse is live); the archive is the retrocast-of-record.
2. **Fail-closed on receipts.** Every number is emitted through `_publish`, which builds a bundle
   and refuses (raises) if the evidence is incomplete. `resolver.receipts.write_bundle` is the
   second lock, and `sitegen` refuses to render a number whose bundle does not validate.
3. **Approved templates only.** Sentences come from `artifacts.templates.APPROVED`; the compiler
   cannot invent a claim shape (SPEC-04 §1).

Discovery walks DATES, not a bucket listing: manifest keys are deterministic
(`raw/warn/<ST>/<Y>/<m>/<d>/manifest.json`), so the compiler needs nothing from the storage
backend but `get` — which keeps it working against LocalFS in tests and R2 in production.
"""
from __future__ import annotations

import argparse
import json
import os
from datetime import date, timedelta

from engines import ats, posting_diff
from resolver import receipts

from . import extract, templates

INDEX_WARN = "warn-watch"
INDEX_POSTINGS = "posting-diff"

# Both indexes are OBSERVATIONAL (aggregate counts + the naming-gate carve-out for facts with
# receipts). Neither carries a retrocast, so neither may ever make a signature claim; the version
# string is what a receipt pins, so bump it whenever the derivation changes.
WARN_VERSION = f"warn-watch-v1+{extract.EXTRACT_VERSION}"
POSTINGS_VERSION = f"posting-diff-v1+{ats.SCHEMA_VERSION}"
METHODOLOGY_REF = "methodology.html#warn-watch"
POSTINGS_METHODOLOGY_REF = "methodology.html#posting-diff"

DEFAULT_DAYS = 21

# Notices carried into the rendered layer per state. The ARCHIVE is the full record — TX's list
# runs to 2,367 notices back to 2021 — and every page states the full count and links the hashed
# snapshot it came from. Capping keeps the built site small and fast without hiding anything:
# the number we publish is the total, not the length of the table we drew.
MAX_NOTICES_PER_STATE = 100


class UnreceiptedNumber(Exception):
    """A number reached publication without evidence that validates. Always a bug, never a warning."""


# --------------------------------------------------------------------------- archive discovery
def _manifest(storage, key):
    blob = storage.get(key)
    if not blob:
        return None
    try:
        return json.loads(blob)
    except Exception:
        return None                      # a corrupt manifest loses that day, never the whole run


def vintages(storage, prefix: str, days: int, today: date) -> list:
    """Every archived vintage under `prefix` in the last `days`, oldest first.

    -> [{date, key, sha256, manifest_key, meta}] where `key` is the raw object and `meta` is that
    file's manifest entry (row counts, source_url, parser version, volume band)."""
    out = []
    for back in range(days, -1, -1):
        d = today - timedelta(days=back)
        datepath = f"{prefix}/{d:%Y}/{d:%m}/{d:%d}"
        mkey = f"raw/{datepath}/manifest.json"
        man = _manifest(storage, mkey)
        if not man:
            continue
        for f in man.get("files", []):
            if not f.get("file") or not f.get("sha256"):
                continue                 # an entry without a hash cannot be receipted -> not usable
            out.append({"date": d.isoformat(), "key": f"raw/{datepath}/{f['file']}",
                        "sha256": f["sha256"], "manifest_key": mkey, "manifest": man, "meta": f})
    out.sort(key=lambda v: (v["date"], v["meta"].get("stored_at", ""), v["key"]))
    return out


def _payload(storage, v):
    blob = storage.get(v["key"])
    return extract.decompress(v["key"], blob) if blob else None


# --------------------------------------------------------------------------- receipted publish
def _publish(out, *, receipts_root, index, number_id, number, unit, as_of, version, methodology_ref,
             inputs, code_ref, template, kind, text, extra=None):
    """Write the evidence bundle, then the artifact. THE fail-closed gate: if the bundle does not
    validate, nothing is written and the run fails loudly — a number without receipts must not be
    publishable by any path, including a future caller that forgets to check."""
    bundle = receipts.build_bundle(number=number, unit=unit, as_of=as_of, index_version=version,
                                   methodology_ref=methodology_ref, inputs=inputs, code_ref=code_ref)
    if not receipts.valid_bundle(bundle):
        raise UnreceiptedNumber(f"{index}/{number_id}: refusing to publish '{text}' without receipts")
    receipts.write_bundle(receipts_root, index, number_id, bundle)
    art = {"id": number_id, "index": index, "kind": kind, "template": template, "text": text,
           "number": number, "unit": unit, "as_of": as_of, "index_version": version,
           "receipt": f"receipts/{index}/{number_id}.html"}
    art.update(extra or {})
    out.append(art)
    return art


def _inputs(vs):
    """Archived objects -> receipt input rows. r2_path + sha256 are what make a bundle valid."""
    return [{"r2_path": v["key"], "sha256": v["sha256"], "manifest_ref": v["manifest_key"]} for v in vs]


# --------------------------------------------------------------------------- WARN Watch
def compile_warn(storage, seed_path, *, receipts_root, days=DEFAULT_DAYS, today=None, code_ref="",
                 health_medians=None):
    today = today or date.today()
    seed = json.load(open(seed_path, encoding="utf-8")).get("states", [])
    states, arts = [], []
    for entry in seed:
        st = entry["state"]
        vs = vintages(storage, f"warn/{st}", days, today)
        rec = {"state": st, "agency": entry.get("agency", ""), "format": entry.get("format", ""),
               "source_url": entry.get("data_url") or entry.get("landing_url", ""),
               "vintages": [{"date": v["date"], "key": v["key"], "sha256": v["sha256"],
                             "stored_at": v["meta"].get("stored_at", "")} for v in vs],
               "notes": entry.get("notes", ""), "notices": [], "parse_status": "no-vintage"}
        if not vs:
            states.append(rec)
            continue

        latest = vs[-1]
        stats = {}
        raw = _payload(storage, latest)
        notices = extract.extract_notices(entry.get("format", ""), raw, st, stats) if raw else []
        rec.update(as_of=latest["date"], latest_key=latest["key"], latest_sha256=latest["sha256"],
                   source_url=latest["meta"].get("source_url") or rec["source_url"],
                   unnamed_rows=stats.get("unnamed_rows", 0),
                   parse_status="notices" if notices else ("unreadable" if raw else "unfetched"))
        if not notices:
            # Archived and hashed, but this state's format yields no notice table we can read
            # (PA/WI publish link lists, not tables). The page says exactly that and shows the
            # snapshot — it must never fill the gap with a guess.
            states.append(rec)
            continue

        ordered = sorted(notices, key=_notice_sort, reverse=True)
        rec["notices"] = ordered[:MAX_NOTICES_PER_STATE]
        rec["notices_total"] = len(ordered)
        rec["notices_shown"] = len(rec["notices"])
        _publish(arts, receipts_root=receipts_root, index=INDEX_WARN,
                 number_id=f"{st}-level-{latest['date']}", number=len(notices),
                 unit="WARN notices on the state's published list", as_of=latest["date"],
                 version=WARN_VERSION, methodology_ref=METHODOLOGY_REF, inputs=_inputs([latest]),
                 code_ref=code_ref, template="warn_state_level", kind=templates.CADENCE,
                 text=templates.render("warn_state_level", state=st, n=len(notices),
                                       as_of=latest["date"])[0],
                 extra={"state": st, "page": f"warn/{st}.html"})

        # The cadence artifact: what this state published that it had not published before. Needs
        # two distinct archived vintages, which is exactly the "within one collector cycle" flow.
        prior = next((v for v in reversed(vs[:-1]) if v["sha256"] != latest["sha256"]), None)
        if prior:
            praw = _payload(storage, prior)
            before = {extract.compare_key(n)
                      for n in extract.extract_notices(entry.get("format", ""), praw, st)} \
                if praw else set()
            fresh = [n for n in ordered if extract.compare_key(n) not in before]
            rec["new_notices"] = fresh[:MAX_NOTICES_PER_STATE]
            rec["compared_to"] = {"date": prior["date"], "key": prior["key"], "sha256": prior["sha256"]}
            # Circuit breaker: a state's published list does not turn over wholesale between two
            # snapshots. When it appears to, the likely cause is the source reshaping its table,
            # not a mass layoff event — so we say the list changed shape rather than publish a
            # number we would have to retract. Same instinct as the collector's volume band.
            churn = (len(fresh) / len(ordered)) if ordered else 0.0
            if len(before) >= 10 and churn > 0.5:
                rec["delta_suppressed"] = (
                    f"{len(fresh)} of {len(ordered)} notices differ from the {prior['date']} "
                    f"vintage ({churn:.0%}). A published list does not turn over that far between "
                    f"snapshots, so this is treated as the source changing shape, not as new "
                    f"filings, and no change figure is published for this vintage.")
                fresh = []
            if fresh and before:                 # an empty `before` means the prior vintage was
                workers = sum(n["employees"] or 0 for n in fresh)   # unreadable — not a real delta
                _publish(arts, receipts_root=receipts_root, index=INDEX_WARN,
                         number_id=f"{st}-new-{prior['date']}-{latest['date']}", number=len(fresh),
                         unit="new WARN notices", as_of=latest["date"], version=WARN_VERSION,
                         methodology_ref=METHODOLOGY_REF, inputs=_inputs([prior, latest]),
                         code_ref=code_ref, template="warn_new_notices", kind=templates.CADENCE,
                         text=templates.render("warn_new_notices", state=st, n=len(fresh),
                                               workers=workers, since=prior["date"],
                                               as_of=latest["date"])[0],
                         extra={"state": st, "page": f"warn/{st}.html", "workers": workers,
                                "notices": [n["id"] for n in fresh]})

        # The anomaly artifact reports the collector's OWN detector firing (SPEC-03 §2). The band
        # and the trailing median are the collector's, taken from committed state — the compiler
        # does not run a second, differently-tuned detector that could disagree with the alarm.
        band = latest["meta"].get("volume_band")
        if band in ("anomaly", "extreme"):
            median = (health_medians or {}).get(st) or len(ordered)
            _publish(arts, receipts_root=receipts_root, index=INDEX_WARN,
                     number_id=f"{st}-anomaly-{latest['date']}", number=len(ordered),
                     unit="WARN notices (outside trailing band)", as_of=latest["date"],
                     version=WARN_VERSION, methodology_ref=METHODOLOGY_REF, inputs=_inputs([latest]),
                     code_ref=code_ref, template="warn_volume_anomaly", kind=templates.ANOMALY,
                     text=templates.render("warn_volume_anomaly", state=st, n=len(ordered),
                                           median=median, as_of=latest["date"])[0],
                     extra={"state": st, "page": f"warn/{st}.html", "band": band})
        states.append(rec)
    return {"index": INDEX_WARN, "version": WARN_VERSION, "states": states}, arts


def warn_medians(repo_root: str) -> dict:
    """{state: rows_median} from the collector's committed health state, or {} if unavailable."""
    p = os.path.join(repo_root, "ops", "state", "health", "warn.json")
    try:
        node = json.load(open(p, encoding="utf-8"))["collectors"]["warn"]["states"]
    except Exception:
        return {}
    return {st: rec.get("rows_median") for st, rec in node.items() if rec.get("rows_median")}


def _notice_sort(n):
    """Newest first, by whatever date the source actually gives (NJ publishes only an effective
    date; NY only a notice date). Undated notices sort last rather than being dropped."""
    return (n.get("notice_date") or n.get("effective_date") or "", n.get("company", ""))


# --------------------------------------------------------------------------- Posting-Diff
def compile_postings(storage, seed_path, *, receipts_root, days=DEFAULT_DAYS, today=None, code_ref=""):
    today = today or date.today()
    seed = json.load(open(seed_path, encoding="utf-8")).get("boards", [])
    boards, arts = [], []
    for b in seed:
        a, token = b["ats"], b["token"]
        company = b.get("company") or token
        slug = f"{a}-{token}".replace("/", "-")
        vs = vintages(storage, f"ats-boards/{a}/{token}", days, today)
        rec = {"ats": a, "token": token, "company": company, "slug": slug,
               "vintages": [{"date": v["date"], "key": v["key"], "sha256": v["sha256"],
                             "postings": v["meta"].get("postings")} for v in vs],
               "diff": None, "postings": None}
        if not vs:
            boards.append(rec)
            continue
        latest = vs[-1]
        cur_raw = _payload(storage, latest)
        try:
            cur = ats.normalize(a, cur_raw) if cur_raw else []
        except Exception:
            cur = []                     # an unparseable archived board shows as "no snapshot read"
        rec.update(as_of=latest["date"], latest_key=latest["key"], latest_sha256=latest["sha256"],
                   postings=len(cur) if cur_raw else None,
                   source_url=latest["meta"].get("source_url", ""))
        if cur_raw and cur:
            _publish(arts, receipts_root=receipts_root, index=INDEX_POSTINGS,
                     number_id=f"{slug}-level-{latest['date']}", number=len(cur),
                     unit="public job postings", as_of=latest["date"], version=POSTINGS_VERSION,
                     methodology_ref=POSTINGS_METHODOLOGY_REF, inputs=_inputs([latest]),
                     code_ref=code_ref, template="postings_level", kind=templates.CADENCE,
                     text=templates.render("postings_level", company=company, n=len(cur),
                                           as_of=latest["date"])[0],
                     extra={"slug": slug, "page": f"postings/{slug}.html"})

        prior = next((v for v in reversed(vs[:-1]) if v["sha256"] != latest["sha256"]), None)
        if prior and cur:
            praw = _payload(storage, prior)
            try:
                prev = ats.normalize(a, praw) if praw else []
            except Exception:
                prev = []
            if prev:
                d = posting_diff.diff(prev, cur)
                rec["diff"] = d
                rec["compared_to"] = {"date": prior["date"], "key": prior["key"],
                                      "sha256": prior["sha256"]}
                # Boards are snapshotted several times a day, so the two compared vintages are
                # often from the same date; "between 2026-07-29 and 2026-07-29" reads as an error.
                window = (f"between consecutive snapshots archived on {latest['date']}"
                          if prior["date"] == latest["date"]
                          else f"between {prior['date']} and {latest['date']}")
                if not (d["removed_count"] or d["added_count"]):
                    boards.append(rec)          # nothing moved: the level artifact already says so
                    continue
                _publish(arts, receipts_root=receipts_root, index=INDEX_POSTINGS,
                         number_id=f"{slug}-removed-{prior['date']}-{latest['date']}",
                         number=d["removed_count"], unit="postings removed", as_of=latest["date"],
                         version=POSTINGS_VERSION, methodology_ref=POSTINGS_METHODOLOGY_REF,
                         inputs=_inputs([prior, latest]), code_ref=code_ref,
                         template="postings_removed", kind=templates.CADENCE,
                         text=templates.render("postings_removed", company=company,
                                               removed=d["removed_count"], prev_count=d["prev_count"],
                                               added=d["added_count"], window=window)[0],
                         extra={"slug": slug, "page": f"postings/{slug}.html",
                                "pulled_pct": d["pulled_pct"]})
        boards.append(rec)
    return {"index": INDEX_POSTINGS, "version": POSTINGS_VERSION, "boards": boards}, arts


# --------------------------------------------------------------------------- driver
def compile_all(storage, repo_root=".", *, out_dir=None, receipts_root=None, days=DEFAULT_DAYS,
                today=None, code_ref=None):
    from collectors.framework import git_ref, utcnow_iso
    out_dir = out_dir or os.path.join(repo_root, "site", "data")
    receipts_root = receipts_root or os.path.join(repo_root, "site", "receipts")
    code_ref = git_ref(repo_root) if code_ref is None else code_ref
    warn, warn_arts = compile_warn(storage, os.path.join(repo_root, "collectors", "seed_warn.json"),
                                   receipts_root=receipts_root, days=days, today=today,
                                   code_ref=code_ref, health_medians=warn_medians(repo_root))
    posts, post_arts = compile_postings(storage,
                                        os.path.join(repo_root, "collectors", "seed_boards.json"),
                                        receipts_root=receipts_root, days=days, today=today,
                                        code_ref=code_ref)
    arts = sorted(warn_arts + post_arts, key=lambda a: (a["as_of"], a["index"], a["id"]), reverse=True)
    generated = utcnow_iso()
    for name, payload in (("warn.json", warn), ("postings.json", posts),
                          ("artifacts.json", {"generated": generated, "code_ref": code_ref,
                                              "artifacts": arts})):
        payload.setdefault("generated", generated)
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, name), "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, sort_keys=False)
    return {"out_dir": out_dir, "receipts_root": receipts_root, "artifacts": len(arts),
            "warn_states": len(warn["states"]), "boards": len(posts["boards"]),
            "code_ref": code_ref, "generated": generated}


if __name__ == "__main__":
    from collectors.framework import select_storage
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=DEFAULT_DAYS)
    ap.add_argument("--local-root", default="local-archive")
    ap.add_argument("--out", default=None)
    ap.add_argument("--repo-root", default=".")
    args = ap.parse_args()
    res = compile_all(select_storage(args.local_root), args.repo_root, out_dir=args.out,
                      days=args.days)
    print(json.dumps(res, indent=2))
