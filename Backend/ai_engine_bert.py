from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Load once (important)
model = SentenceTransformer("all-MiniLM-L6-v2")

def compute_bert_similarity(text1: str, text2: str) -> float:
    """
    Compute semantic similarity between two texts using BERT embeddings.
    Returns a value between 0 and 1.
    """
    if not text1 or not text2:
        return 0.0

    embeddings = model.encode([text1, text2])
    similarity = cosine_similarity(
        [embeddings[0]],
        [embeddings[1]]
    )[0][0]

    return float(similarity)
