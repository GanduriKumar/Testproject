from __future__ import annotations
import time
from typing import List
import httpx
import os

EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")

class OllamaEmbeddings:
    def __init__(self, host: str | None = None) -> None:
        self.base_url = (host or os.getenv("OLLAMA_HOST", "http://localhost:11434")).rstrip("/")

    async def embed(self, texts: List[str]) -> List[List[float]]:
        # Ollama embeddings endpoint with simple retry
        url = f"{self.base_url}/api/embeddings"
        payload = {"model": EMBED_MODEL, "input": texts}
        last_err: Exception | None = None
        for attempt in range(3):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    r = await client.post(url, json=payload)
                    r.raise_for_status()
                    data = r.json()
                    # Support both single and batch formats
                    if isinstance(data, dict) and "embeddings" in data:
                        return data["embeddings"]
                    if isinstance(data, dict) and "embedding" in data:
                        return [data["embedding"]]
                    # fallback attempt
                    if isinstance(data, list) and data and isinstance(data[0], list):
                        return data
                    raise RuntimeError("unexpected embeddings response")
            except Exception as e:
                last_err = e
                # small backoff
                try:
                    import asyncio
                    await asyncio.sleep(0.2 * (attempt + 1))
                except Exception:
                    pass
        # After retries, raise the last error
        raise RuntimeError(f"embedding failed after retries: {last_err}")

    @staticmethod
    def cosine(a: List[float], b: List[float]) -> float:
        import math
        if not a or not b or len(a) != len(b):
            return 0.0
        dot = sum(x*y for x, y in zip(a, b))
        na = math.sqrt(sum(x*x for x in a))
        nb = math.sqrt(sum(y*y for y in b))
        if na == 0 or nb == 0:
            return 0.0
        return dot / (na * nb)
