from __future__ import annotations

from dataclasses import dataclass, asdict
from time import perf_counter
from typing import Any, Dict, Generator, Iterable, List, Optional, Sequence, Tuple

from .coverage_engine import CoverageEngine, Scenario


def iter_chunks(seq: Sequence[Any], chunk_size: int) -> Generator[Sequence[Any], None, None]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be > 0")
    for i in range(0, len(seq), chunk_size):
        yield seq[i : i + chunk_size]


@dataclass
class PerfMetrics:
    total: int
    chunk_size: int
    chunks: int
    max_chunk: int
    elapsed_sec: float


def global_combined_scenarios(
    eng: Optional[CoverageEngine] = None,
    *,
    domains: Optional[Iterable[str]] = None,
    behaviors: Optional[Iterable[str]] = None,
    seed: int = 42,
) -> List[Scenario]:
    eng = eng or CoverageEngine()
    tax = eng.taxonomy
    all_domains = list(domains) if domains is not None else list(tax.get("domains", []))
    all_behaviors = list(behaviors) if behaviors is not None else list(tax.get("behaviors", []))
    out: List[Scenario] = []
    for d in all_domains:
        for b in all_behaviors:
            out.extend(eng.scenarios_for(d, b, seed=seed))
    return out


def chunk_global_combined(
    *,
    eng: Optional[CoverageEngine] = None,
    domains: Optional[Iterable[str]] = None,
    behaviors: Optional[Iterable[str]] = None,
    seed: int = 42,
    chunk_size: int = 200,
    max_total: Optional[int] = None,
) -> Tuple[List[List[Scenario]], PerfMetrics]:
    t0 = perf_counter()
    scenarios = global_combined_scenarios(eng, domains=domains, behaviors=behaviors, seed=seed)
    total = len(scenarios)
    if max_total is not None and total > max_total:
        raise RuntimeError(f"total {total} exceeds max_total {max_total}")
    chunks: List[List[Scenario]] = [list(c) for c in iter_chunks(scenarios, chunk_size)]
    max_chunk = max((len(c) for c in chunks), default=0)
    dt = perf_counter() - t0
    return chunks, PerfMetrics(total=total, chunk_size=chunk_size, chunks=len(chunks), max_chunk=max_chunk, elapsed_sec=dt)
