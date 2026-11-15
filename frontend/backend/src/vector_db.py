import asyncio
import os
from dataclasses import dataclass

from qdrant_client import AsyncQdrantClient, models
from qdrant_client.conversions.common_types import QueryResponse
from qdrant_client.http.exceptions import ResponseHandlingException

from requestModel import RequestModel

timeout = 60
COLLECTION = os.getenv("QDRANT_COLLECTION", "samfundet_faces")
qdrant = AsyncQdrantClient(url=os.getenv("QDRANT_URL"), api_key=os.getenv("QDRANT_KEY"), timeout=timeout)

BBox = list[int] # [x1, y1, x2, y2]

@dataclass(frozen=True)
class ImageHit:
    score: float
    bbox: BBox | None

async def query(vector, params: 'RequestModel') -> 'QueryResponse':
    hits = await qdrant.query_points(
        collection_name=COLLECTION,
        query=vector,
        limit=params.max_images,
        with_payload=True,
        score_threshold=params.score_threshold,
        search_params=models.SearchParams(quantization=models.QuantizationSearchParams(rescore=True, oversampling=2.0)),
        timeout=timeout,
    )
    return hits

async def retry_query(vector, params: 'RequestModel') -> 'QueryResponse':
    attempts = 0
    while True:
        try:
            hits = await query(vector, params)
            return hits
        except ResponseHandlingException:
            if attempts == 1:
                raise
            attempts += 1
            await asyncio.sleep(1)

def best_result_per_image(hits: 'QueryResponse') -> dict[str, ImageHit]:
    hit_map: dict[str, ImageHit] = {}
    for hit in hits.points:
        img_id = hit.payload.get("image_id")
        if not img_id:
            continue
        if img_id not in hit_map or hit.score > hit_map[img_id].score:
            bbox = hit.payload.get("bbox")
            hit_map[img_id] = ImageHit(hit.score, bbox)
    return hit_map
