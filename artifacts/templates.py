"""The approved artifact templates (SPEC-04 §1).

Posting an artifact is autonomous ONLY when it is a cadence or anomaly artifact of an already
launched aggregate index rendered "from approved templates". This module IS that approved set:
the compiler may not emit a sentence that is not built here, so a new claim shape is a code change
under review, never something a job improvises at 04:00.

Every template is a flat statement of something we counted in an archived file. No adjectives, no
inference, no forecast — "never predict, only measure". Named companies appear only where the
naming-gate carve-out allows it: an observational fact with receipts (the employer filed a public
WARN notice; the board removed a posting), never a signature or a prediction.
"""
from __future__ import annotations

CADENCE = "cadence"
ANOMALY = "anomaly"


def _plural(n, one, many=None):
    return one if n == 1 else (many or one + "s")


def warn_new_notices(*, state, n, workers, since, as_of):
    """New WARN filings a state published between two archived vintages."""
    w = f" covering {workers:,} {_plural(workers, 'worker')}" if workers else ""
    return (f"{state} published {n:,} new WARN {_plural(n, 'notice')}{w} "
            f"between {since} and {as_of}.")


def warn_state_level(*, state, n, as_of):
    """The level a state's own published list stood at in one archived vintage."""
    return f"{state}'s published WARN list held {n:,} {_plural(n, 'notice')} in the {as_of} vintage."


def warn_volume_anomaly(*, state, n, median, as_of):
    """A state's list moving far outside its own trailing band — reported, never interpreted."""
    return (f"{state}'s published WARN list moved to {n:,} {_plural(n, 'notice')} on {as_of}, "
            f"against a trailing median of {median:,}.")


def postings_removed(*, company, removed, prev_count, added, window):
    """E1 Posting-Diff, the day-one observational artifact (naming-gate carve-out: the diffs are
    the receipts). Delegates the sentence to the engine so page and artifact cannot disagree."""
    from engines.posting_diff import headline
    return headline(company, {"removed_count": removed, "prev_count": prev_count,
                              "added_count": added,
                              "pulled_pct": (removed / prev_count) if prev_count else 0.0}, window)


def postings_level(*, company, n, as_of):
    return f"{company} listed {n:,} public job {_plural(n, 'posting')} in the {as_of} snapshot."


# name -> (callable, kind). The compiler looks templates up HERE; an unknown name raises.
APPROVED = {
    "warn_new_notices": (warn_new_notices, CADENCE),
    "warn_state_level": (warn_state_level, CADENCE),
    "warn_volume_anomaly": (warn_volume_anomaly, ANOMALY),
    "postings_removed": (postings_removed, CADENCE),
    "postings_level": (postings_level, CADENCE),
}


class UnapprovedTemplate(Exception):
    """Raised when something tries to publish a sentence shape nobody approved."""


def render(name: str, **kw):
    """-> (text, kind). Refuses any template not in APPROVED (SPEC-04 §1 is a hard boundary)."""
    if name not in APPROVED:
        raise UnapprovedTemplate(
            f"'{name}' is not an approved artifact template; approved: {sorted(APPROVED)}")
    fn, kind = APPROVED[name]
    return fn(**kw), kind
