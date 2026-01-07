from __future__ import annotations
import re
from typing import Dict, List, Any, Set

try:
    from .state_extractor import ORDER_PAT, AMOUNT_GENERAL_PAT, AMOUNT_REFUND_PAT
except ImportError:
    from state_extractor import ORDER_PAT, AMOUNT_GENERAL_PAT, AMOUNT_REFUND_PAT

# Local decision detection to avoid circular deps
_DECISION_ALLOW = re.compile(r"\b(approve(d)?|allow(ed)?|grant(ed)?)\b", re.I)
_DECISION_DENY = re.compile(r"\b(deny|denied|cannot|can't|not able|refuse|refusal)\b", re.I)
_DECISION_PARTIAL = re.compile(r"\b(partial|partly)\b", re.I)


def _detect_decision(text: str) -> str | None:
    if _DECISION_ALLOW.search(text):
        return "ALLOW"
    if _DECISION_DENY.search(text):
        return "DENY"
    if _DECISION_PARTIAL.search(text):
        return "PARTIAL"
    return None


def _extract_order_ids(text: str) -> List[str]:
    ids: List[str] = []
    for m in ORDER_PAT.finditer(text or ""):
        gid = m.group(1) or m.group(2)
        if gid:
            ids.append(gid)
    return ids


def _extract_amounts(text: str) -> List[float]:
    vals: List[float] = []
    for m in AMOUNT_GENERAL_PAT.finditer(text or ""):
        try:
            vals.append(float(m.group(1)))
        except Exception:
            pass
    return vals


def _extract_refund_amounts(text: str) -> List[float]:
    vals: List[float] = []
    for m in AMOUNT_REFUND_PAT.finditer(text or ""):
        try:
            vals.append(float(m.group(1)))
        except Exception:
            pass
    return vals


def consistency(output: str, state: Dict[str, Any]) -> Dict[str, Any]:
    reasons: List[str] = []
    out_dec = _detect_decision(output)
    st_dec = state.get("decision")
    if st_dec and out_dec and st_dec != out_dec:
        reasons.append(f"decision mismatch: state={st_dec}, output={out_dec}")

    # Order ID mismatch: if output mentions an order id different from state.order_id
    st_oid = state.get("order_id")
    if st_oid:
        out_ids = _extract_order_ids(output)
        if out_ids and any(oid != st_oid for oid in out_ids):
            reasons.append(f"order_id contradiction: state={st_oid}, output_ids={out_ids}")

    # Refund amount mismatch: only consider explicit refund mentions
    st_ref = state.get("refund_amount")
    if st_ref is not None:
        out_refs = _extract_refund_amounts(output)
        if out_refs and any(abs(x - float(st_ref)) > 1e-6 for x in out_refs):
            reasons.append(f"refund_amount contradiction: state={st_ref}, output_refs={out_refs}")

    return {"metric": "consistency", "pass": len(reasons) == 0, "reasons": reasons}


def adherence(output: str, constraints: Dict[str, Any] | None) -> Dict[str, Any]:
    reasons: List[str] = []
    cs = constraints or {}

    # refund_after_ship = False -> if output mentions refund after shipped
    raf = cs.get("refund_after_ship")
    if raf is False:
        # detect phrasing like "refund after it's shipped"
        if re.search(r"refund[\w\s]{0,80}after (it'?s )?shipp(?:ed|ing)", output, re.I):
            reasons.append("violates refund_after_ship=false")

    # max_refund numeric
    mr = cs.get("max_refund")
    if isinstance(mr, (int, float)):
        out_refs = _extract_refund_amounts(output)
        # Fallback: if no explicit refund-amount pattern found, but sentence mentions refund,
        # consider any dollar amounts as potential refund amounts.
        if not out_refs and re.search(r"refund", output, re.I):
            out_refs = _extract_amounts(output)
        if any(x > float(mr) for x in out_refs):
            reasons.append(f"refund exceeds max_refund={mr}")

    return {"metric": "adherence", "pass": len(reasons) == 0, "reasons": reasons}


def hallucination(output: str, state: Dict[str, Any], history_texts: List[str]) -> Dict[str, Any]:
    reasons: List[str] = []
    # Known IDs and amounts from history and state
    known_ids: Set[str] = set()
    for h in history_texts:
        known_ids.update(_extract_order_ids(h))
    if state.get("order_id"):
        known_ids.add(state["order_id"])

    known_amounts: Set[float] = set()
    for h in history_texts:
        for a in _extract_amounts(h):
            known_amounts.add(a)
    for k in ("refund_amount", "totals", "amount"):
        if isinstance(state.get(k), (int, float)):
            known_amounts.add(float(state[k]))

    # Entities in output
    out_ids = _extract_order_ids(output)
    out_amounts = _extract_amounts(output)

    new_ids = [x for x in out_ids if x not in known_ids]
    new_amounts = [x for x in out_amounts if x not in known_amounts]

    if new_ids:
        reasons.append(f"unseen order ids: {new_ids}")
    if new_amounts:
        reasons.append(f"unseen amounts: {new_amounts}")

    return {"metric": "hallucination", "pass": len(reasons) == 0, "reasons": reasons}
