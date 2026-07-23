import os
from functools import lru_cache
from typing import List

import numpy as np
from sentence_transformers import SentenceTransformer


EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
)


@lru_cache(maxsize=1)
def get_model() -> SentenceTransformer:
    """
    Loads the embedding model once and caches it.
    This model converts text into semantic vectors.
    """
    return SentenceTransformer(EMBEDDING_MODEL)


def embed_text(text: str) -> List[float]:
    """
    Converts text into a normalized vector.
    Normalized vectors make cosine similarity easier.
    """
    if not text or not text.strip():
        text = "empty document"

    model = get_model()
    vector = model.encode(text, normalize_embeddings=True)
    return vector.tolist()


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    a = np.array(vec1)
    b = np.array(vec2)

    denominator = np.linalg.norm(a) * np.linalg.norm(b)

    if denominator == 0:
        return 0.0

    return float(np.dot(a, b) / denominator)