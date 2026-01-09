from __future__ import annotations
import re
from typing import Dict, List, Any, Set, Optional

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


_REFUSAL_PAT = re.compile(
    r"(" 
    r"\b(can't|cannot|unable|not able|won't|refuse|refusal|decline|denied)\b"
    r"|\b(we\s+cannot|we\s+can't)\b"
    r"|\b(not\s+allowed|against\s+policy|policy\s+prohibits)\b"
    r"|\b(no\s+refund)\b"
    r"|unfortunately[^\n]{0,40}\b(cannot|can't|won't)\b"
    r")",
    re.IGNORECASE,
)


def adherence(output: str, constraints: Dict[str, Any] | None, expected_decision: Optional[str] = None) -> Dict[str, Any]:
    reasons: List[str] = []
    flags: List[str] = []
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
            flags.append("exceeds_max_refund")

    # Incorrect refusal for expected ALLOW outcome
    if (expected_decision or "").upper() == "ALLOW":
        if _REFUSAL_PAT.search(output or ""):
            reasons.append("incorrect refusal for allowed outcome")
            flags.append("incorrect_refusal")

    return {"metric": "adherence", "pass": len(reasons) == 0, "reasons": reasons, "flags": flags}


DATE_PAT = re.compile(r"\b(?:\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{2,4}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\s+\d{1,2}(?:,\s*\d{4})?)\b", re.I)
PCT_PAT = re.compile(r"\b(\d{1,3}(?:\.\d+)?)\s*%|\b(\d{1,3}(?:\.\d+)?)\s*percent\b", re.I)


def _extract_dates(text: str) -> List[str]:
    return [m.group(0) for m in DATE_PAT.finditer(text or "")]


def _extract_percents(text: str) -> List[float]:
    vals: List[float] = []
    for m in PCT_PAT.finditer(text or ""):
        grp = m.group(1) or m.group(2)
        try:
            vals.append(float(grp))
        except Exception:
            pass
    return vals


def hallucination(
    output: str,
    state: Dict[str, Any],
    history_texts: List[str],
    *,
    threshold: Optional[float] = None,
    support_texts: Optional[List[str]] = None,
) -> Dict[str, Any]:
    reasons: List[str] = []
    supports = list(history_texts or []) + list(support_texts or [])

    # Known entities from supports and state
    known_ids: Set[str] = set()
    for h in supports:
        known_ids.update(_extract_order_ids(h))
    if state.get("order_id"):
        known_ids.add(state["order_id"])

    known_amounts: Set[float] = set()
    for h in supports:
        for a in _extract_amounts(h):
            known_amounts.add(a)
    for k in ("refund_amount", "totals", "amount"):
        if isinstance(state.get(k), (int, float)):
            known_amounts.add(float(state[k]))

    known_dates: Set[str] = set()
    for h in supports:
        for d in _extract_dates(h):
            known_dates.add(d)

    known_pcts: Set[float] = set()
    for h in supports:
        for p in _extract_percents(h):
            known_pcts.add(p)

    # Entities in output
    out_ids = _extract_order_ids(output)
    out_amounts = _extract_amounts(output)
    out_dates = _extract_dates(output)
    out_pcts = _extract_percents(output)

    new_ids = [x for x in out_ids if x not in known_ids]
    new_amounts = [x for x in out_amounts if x not in known_amounts]
    new_dates = [x for x in out_dates if x not in known_dates]
    new_pcts = [x for x in out_pcts if x not in known_pcts]

    if new_ids:
        reasons.append(f"unseen order ids: {new_ids}")
    if new_amounts:
        reasons.append(f"unseen amounts: {new_amounts}")
    if new_dates:
        reasons.append(f"unseen dates: {new_dates}")
    if new_pcts:
        reasons.append(f"unseen percentages: {new_pcts}")

    # Normalized support score
    total = len(out_ids) + len(out_amounts) + len(out_dates) + len(out_pcts)
    supported = (
        (len(out_ids) - len(new_ids))
        + (len(out_amounts) - len(new_amounts))
        + (len(out_dates) - len(new_dates))
        + (len(out_pcts) - len(new_pcts))
    )
    score = 1.0 if total == 0 else supported / float(total)

    passed = False
    if threshold is None:
        passed = len(reasons) == 0
    else:
        passed = score >= float(threshold)

    return {
        "metric": "hallucination",
        "pass": passed,
        "reasons": reasons,
        "score": round(score, 4),
        "threshold": threshold,
    }
