import os
from typing import Any, Dict, List, Optional
from uuid import uuid4

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from app.services.embedding_service import embed_text


QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant:6333")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "skillmatch_documents")
VECTOR_SIZE = 384


def create_client() -> QdrantClient:
    return QdrantClient(url=QDRANT_URL, timeout=180)


def ensure_collection(client: QdrantClient) -> None:
    collections = client.get_collections().collections
    collection_names = [collection.name for collection in collections]

    if QDRANT_COLLECTION not in collection_names:
        client.create_collection(
            collection_name=QDRANT_COLLECTION,
            vectors_config=VectorParams(
                size=VECTOR_SIZE,
                distance=Distance.COSINE,
            ),
        )


def index_document(
    text: str,
    doc_type: str,
    metadata: Optional[Dict[str, Any]] = None,
    point_id: Optional[str] = None,
) -> Dict[str, Any]:
    metadata = metadata or {}

    client = create_client()
    ensure_collection(client)

    vector = embed_text(text)

    if point_id is None:
        source_id = metadata.get("source_id")
        if source_id:
            point_id = f"{doc_type}_{source_id}"
        else:
            point_id = str(uuid4())

    payload = {
        "type": doc_type,
        "text": text,
        **metadata,
    }

    client.upsert(
        collection_name=QDRANT_COLLECTION,
        points=[
            PointStruct(
                id=point_id,
                vector=vector,
                payload=payload,
            )
        ],
    )

    return {
        "id": point_id,
        "type": doc_type,
        "metadata": metadata,
    }
def search_documents(
    query: str,
    limit: int = 5,
    doc_type: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Searches Qdrant by semantic meaning.
    """
    client = create_client()
    ensure_collection(client)

    query_vector = embed_text(query)

    response = client.query_points(
        collection_name=QDRANT_COLLECTION,
        query=query_vector,
        limit=max(limit * 10, 50),
        with_payload=True,
    )

    results = response.points

    formatted = []

    for item in results:
        payload = item.payload or {}

        if doc_type and payload.get("type") != doc_type:
            continue

        formatted.append(
            {
                "id": item.id,
                "score": item.score,
                "payload": payload,
            }
        )

        if len(formatted) >= limit:
            break

    return formatted