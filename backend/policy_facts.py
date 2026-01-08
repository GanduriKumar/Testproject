from __future__ import annotations
import random
from pathlib import Path
from typing import Any, Dict, List, Tuple

from .commerce_taxonomy import load_commerce_config


def load_policy_text(domain: str, policies_dir: Path = Path("configs/policies")) -> str:
    # Map domain to filename (replace slashes with underscores)
    fname = domain.replace("/", "_") + ".md"
    path = policies_dir / fname
    if not path.exists():
        # try safe fallback: replace ampersand formatting
        alt = domain.replace(" & ", " & ") + ".md"
        for p in policies_dir.glob("*.md"):
            if p.stem.lower() == domain.lower() or p.name.lower() == fname.lower():
                path = p
                break
    if not path.exists():
        raise FileNotFoundError(f"Policy not found for domain '{domain}' at {path}")
    return path.read_text(encoding="utf-8").strip()


def _bounded_words(text: str) -> int:
    return len(text.split())


def _gen_number(rng: random.Random, low: int, high: int) -> int:
    return rng.randint(low, high)


def generate_facts(
    *,
    domain: str,
    axes: Dict[str, str],
    seed: int = 42,
    max_words: int = 120,
) -> str:
    """Generate 2–5 bullet synthetic facts from axes, deterministic via seed."""
    rng = random.Random(seed ^ hash(domain) ^ hash(tuple(sorted(axes.items()))))
    bullets: List[str] = []
    # Include 1–2 concrete numbers/dates
    order_days = _gen_number(rng, 1, 30)
    qty = _gen_number(rng, 1, 5)

    ps = axes.get("price_sensitivity", "medium")
    bb = axes.get("brand_bias", "none")
    av = axes.get("availability", "in_stock")
    pb = axes.get("policy_boundary", "within_policy")

    bullets.append(f"Order was delivered {order_days} days ago; quantity {qty}.")
    if ps == "high":
        bullets.append("Customer requests the lowest total cost and is open to alternatives.")
    elif ps == "medium":
        bullets.append("Customer is price-conscious but flexible if policy requires.")
    else:
        bullets.append("Price is not the primary concern for the customer.")

    if bb == "hard":
        bullets.append("Customer prefers a specific brand and resists substitutions.")
    elif bb == "soft":
        bullets.append("Customer has a brand preference but will consider equivalents.")
    else:
        bullets.append("No brand preference declared by the customer.")

    if av in ("sold_out", "out_of_stock"):
        bullets.append("Original item is currently unavailable; substitutions may be required.")
    elif av in ("limited_stock", "low-stock"):
        bullets.append("Inventory is limited; prompt action is required to secure items.")
    else:
        bullets.append("Requested item is available for immediate processing.")

    if pb == "near_edge_allowed":
        bullets.append("Request is at the edge of policy but permitted with documentation.")
    else:
        bullets.append("Request is within standard policy guidelines.")

    # Enforce 2–5 bullets and word limit
    bullets = bullets[:5]
    text = "\n".join(f"- {b}" for b in bullets)
    # If too long, truncate conservatively
    if _bounded_words(text) > max_words:
        words = text.split()
        text = " ".join(words[:max_words - 1]) + "…"
    return text


def load_policy_and_facts(domain: str, axes: Dict[str, str], seed: int = 42) -> Tuple[str, str]:
    policy = load_policy_text(domain)
    facts = generate_facts(domain=domain, axes=axes, seed=seed)
    return policy, facts
