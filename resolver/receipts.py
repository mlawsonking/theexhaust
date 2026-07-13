"""The receipts store (SPEC-09 §2) — every published number's immutable evidence bundle.

Fail-closed is the point: an un-receipted number cannot physically publish (the artifact compiler
refuses to render one lacking a valid bundle). Corrections create a SUCCESSOR bundle + a
corrections-log entry — never a mutation.
"""
from __future__ import annotations

import json
import os

REQUIRED = ("number", "unit", "as_of", "index_version", "methodology_ref", "inputs", "code_ref")


def build_bundle(*, number, unit, as_of, index_version, methodology_ref, inputs, code_ref,
                 resolver_entries=None, official_chain=None):
    """inputs: [{r2_path, sha256, manifest_ref}] — the exact raw vintages used."""
    return {"number": number, "unit": unit, "as_of": as_of, "index_version": index_version,
            "methodology_ref": methodology_ref, "inputs": list(inputs), "code_ref": code_ref,
            "resolver_entries": list(resolver_entries or []), "official_chain": official_chain or {}}


def bundle_path(receipts_root, index, number_id):
    return os.path.join(receipts_root, index, str(number_id), "bundle.json")


def write_bundle(receipts_root, index, number_id, bundle):
    if not valid_bundle(bundle):
        raise ValueError("refusing to write an incomplete receipts bundle (fail-closed)")
    p = bundle_path(receipts_root, index, number_id)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(bundle, f, indent=2)
    return p


def valid_bundle(bundle) -> bool:
    if not isinstance(bundle, dict) or any(k not in bundle for k in REQUIRED):
        return False
    inputs = bundle.get("inputs")
    if not isinstance(inputs, list) or not inputs:
        return False
    return all(isinstance(i, dict) and i.get("r2_path") and i.get("sha256") for i in inputs)


def has_valid_bundle(receipts_root, index, number_id) -> bool:
    """The artifact compiler's fail-closed gate: no valid bundle -> the number cannot render."""
    p = bundle_path(receipts_root, index, number_id)
    if not os.path.exists(p):
        return False
    try:
        return valid_bundle(json.load(open(p, encoding="utf-8")))
    except Exception:
        return False


def render_bundle(bundle) -> str:
    """Human-readable rendering behind the public 'receipts' link."""
    lines = [f"# Receipt — {bundle.get('index_version','')}",
             f"Number: {bundle.get('number')} {bundle.get('unit','')} (as of {bundle.get('as_of')})",
             f"Methodology: {bundle.get('methodology_ref')}",
             f"Code: {bundle.get('code_ref')}", "", "## Raw inputs (immutable vintages)"]
    for i in bundle.get("inputs", []):
        lines.append(f"- {i.get('r2_path')}  sha256={i.get('sha256')}")
    oc = bundle.get("official_chain") or {}
    if oc:
        lines.append("")
        lines.append(f"## Official chain: {oc.get('series','')} = {oc.get('last_value','')} "
                     f"({oc.get('divergence_state','')})")
    return "\n".join(lines) + "\n"
