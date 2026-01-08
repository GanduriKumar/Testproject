from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict


DEFAULT_PARAMS = {
    "temperature": 0.2,
    "max_tokens": 512,
    "top_p": 1.0,
    "presence_penalty": 0,
    "frequency_penalty": 0,
}


@dataclass
class SystemPrompt:
    content: str
    params: Dict[str, Any]


def build_system_prompt(
    *,
    domain: str,
    behavior: str,
    axes: Dict[str, str],
    policy_text: str,
    facts_text: str,
    params_override: Dict[str, Any] | None = None,
    max_len: int = 6000,
) -> SystemPrompt:
    """Compose a single system message including policy and scenario facts.

    Sections: Role, Safety/Policy, Scenario Facts, Output Requirements.
    Truncates conservatively if length exceeds max_len.
    """
    role = (
        "You are a commerce assistant for a merchant app. "
        "Follow company policy strictly while being helpful and concise."
    )
    policy = policy_text.strip()
    facts = facts_text.strip()

    req = (
        "Output Requirements:\n"
        "- Ask clarifying questions when needed; do not resolve prematurely.\n"
        "- For the final answer (A2), provide a policy-compliant, actionable resolution.\n"
        "- Do not invent facts; rely only on Scenario Facts and the Safety/Policy excerpt.\n"
    )

    axes_line = ", ".join(f"{k}={v}" for k, v in axes.items())
    header = f"Domain: {domain} | Behavior: {behavior} | Axes: {axes_line}"

    content = (
        f"{header}\n\n"
        f"Role:\n{role}\n\n"
        f"Safety/Policy:\n{policy}\n\n"
        f"Scenario Facts:\n{facts}\n\n"
        f"{req}"
    )

    if len(content) > max_len:
        content = content[: max_len - 1] + "…"

    params = dict(DEFAULT_PARAMS)
    if params_override:
        params.update(params_override)

    return SystemPrompt(content=content, params=params)
