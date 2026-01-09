from __future__ import annotations
import os
import re
from typing import Dict, List, Tuple, Optional

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
    embedder: Optional[OllamaEmbeddings] = None,
    threshold: Optional[float] = None,
    cache: Optional[Dict[str, List[float]]] = None,
) -> Dict[str, object]:
    """Compute semantic similarity via embeddings.

    - Respects threshold argument, else falls back to SEMANTIC_THRESHOLD env (default 0.80)
    - Uses an optional cache dict[text] = embedding to avoid repeat calls within a run
    - Gracefully returns skipped=true if embeddings are unavailable
    """
    thr = threshold if threshold is not None else float(os.getenv("SEMANTIC_THRESHOLD", "0.80"))
    texts: List[str] = [output] + list(variants or [])
    if not variants:
        return {"metric": "semantic", "pass": False, "skipped": True, "reason": "no variants"}

    emb = embedder or OllamaEmbeddings()
    cache = cache if cache is not None else {}

    # Prepare to embed missing texts using cache
    to_embed: List[str] = []
    for t in texts:
        if t not in cache:
            to_embed.append(t)
    try:
        if to_embed:
            vecs_new = await emb.embed(to_embed)
            if not isinstance(vecs_new, list) or len(vecs_new) != len(to_embed):
                return {"metric": "semantic", "pass": False, "skipped": True, "reason": "unexpected embedding shape"}
            for t, v in zip(to_embed, vecs_new):
                cache[t] = v
        # Gather vectors
        out_vec = cache.get(output)
        var_vecs = [cache.get(v) for v in variants]
        if out_vec is None or any(vv is None for vv in var_vecs):
            return {"metric": "semantic", "pass": False, "skipped": True, "reason": "embedding cache miss"}
        scores: List[float] = []
        best_idx = -1
        best_score = -1.0
        for i, v in enumerate(var_vecs):
            sc = OllamaEmbeddings.cosine(out_vec, v)  # type: ignore[arg-type]
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
    except Exception as e:
        # Graceful skip on embed failure
        return {"metric": "semantic", "pass": False, "skipped": True, "reason": f"embeddings unavailable: {str(e)}"}
