from __future__ import annotations
import os
import re
from typing import Dict, List, Tuple

try:
    from .embeddings.ollama_embed import OllamaEmbeddings
except ImportError:
    from embeddings.ollama_embed import OllamaEmbeddings


def _normalize_text(s: str) -> str:
    # Lowercase, collapse whitespace, strip
    s2 = re.sub(r"\s+", " ", s or "").strip().casefold()
    return s2


def exact_match(output: str, variants: List[str]) -> Dict[str, object]:
    out_n = _normalize_text(output)
    norm_variants = [_normalize_text(v) for v in variants]
    match = out_n in norm_variants
    return {
        "metric": "exact",
        "pass": match,
        "output_norm": out_n,
        "variants_norm": norm_variants,
    }


async def semantic_similarity(
    output: str,
    variants: List[str],
    embedder: OllamaEmbeddings | None = None,
    threshold: float | None = None,
) -> Dict[str, object]:
    thr = threshold if threshold is not None else float(os.getenv("SEMANTIC_THRESHOLD", "0.80"))
    emb = embedder or OllamaEmbeddings()
    # Batch embed: [output] + variants
    vecs = await emb.embed([output] + variants)
    out_vec = vecs[0]
    scores: List[float] = []
    best_idx = -1
    best_score = -1.0
    for i, v in enumerate(vecs[1:]):
        sc = OllamaEmbeddings.cosine(out_vec, v)
        scores.append(sc)
        if sc > best_score:
            best_score = sc
            best_idx = i
    passed = best_score >= thr
    return {
        "metric": "semantic",
        "pass": passed,
        "score_max": best_score,
        "threshold": thr,
        "scores": scores,
        "best_variant_index": best_idx,
    }
