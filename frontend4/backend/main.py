from typing import Any, Optional, TypedDict
import os

import cv2
import numpy as np
from insightface.app import FaceAnalysis
from qdrant_client import QdrantClient
from supabase import create_client
from robyn import ALLOW_CORS, Request, Robyn
from robyn.types import JSONResponse

try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

MODEL = os.getenv("FACE_MODEL", "buffalo_l")
COLLECTION = os.getenv("QDRANT_COLLECTION", "samfundet_faces")

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
qdrant = QdrantClient(url=os.getenv("QDRANT_URL"), api_key=os.getenv("QDRANT_KEY"))

face_app = FaceAnalysis(name=MODEL, root="./models", providers=["CPUExecutionProvider"])
face_app.prepare(ctx_id=-1)

app = Robyn(__file__, openapi_file_path="openapi.json")

ALLOW_CORS(
    app,
    origins=[
        "http://localhost:5173",
        "http://localhost:8080",
        "https://hakonw.github.io/fg-ai/",
        "*"
    ],
)


def _form_value(request: Request, key: str, default: str) -> str:
    value = None
    if hasattr(request, "form_data") and request.form_data:
        value = request.form_data.get(key)
    if value is None and request.query_params:
        value = request.query_params.get(key)
    if isinstance(value, list):
        value = value[0] if value else None
    return value if value is not None else default


def _build_page_url(row: dict[str, Any]) -> str:
    page_url = row.get("page_url")
    if page_url:
        return page_url

    return row.get("preview_url") or ""


class SearchResult(TypedDict):
    preview_url: str
    download_url: str
    page_url: str
    image_width: int
    image_height: int
    score: float
    bbox: Optional[list[int]]
    motive: Optional[str]


class SearchResponse(JSONResponse):
    results: list[SearchResult]

class FaultResponse(JSONResponse):
    detail: str


@app.post("/search")
async def search(request: Request) -> SearchResponse | FaultResponse | tuple[dict, dict, int]:
    images = list(request.files.items())
    # ("name", b"image")
    image_entry = images[0][1] if images else None
    if image_entry is None:
        return {"detail": "Missing image upload."}, {}, 400

    if isinstance(image_entry, (bytes, bytearray, memoryview)):
      contents = bytes(image_entry)
    else:
        contents = getattr(image_entry, "data", None)
    if not contents:
        return {"detail": "Unable to read uploaded image."}, {}, 400


    max_images_raw = _form_value(request, "max_images", "20")
    try:
        max_images = max(1, min(int(max_images_raw), 200))
    except ValueError:
        return {"detail": "Invalid max_images."}, {}, 400

    score_threshold_raw = _form_value(request, "score_threshold", "0.3")
    try:
        score_threshold = float(score_threshold_raw)
    except ValueError:
        return {"detail": "Invalid score_threshold."}, {}, 400

    arr = np.asarray(bytearray(contents), dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        return {"detail": "Unsupported image format."}, {}, 400

    faces = face_app.get(img)

    if not faces:
        return {"results": []}

    faces_sorted = sorted(faces, key=lambda f: float(f.det_score), reverse=True)
    query_vector = faces_sorted[0].normed_embedding.astype(float).tolist()

    hits = qdrant.query_points(
        collection_name=COLLECTION,
        query=query_vector,
        limit=max_images,
        with_payload=True,
        score_threshold=score_threshold,
    )

    hit_map: dict[str, tuple[float, list[int] | None]] = {}
    for hit in hits.points:
        img_id = hit.payload.get("image_id")
        if not img_id:
            continue
        bbox = hit.payload.get("bbox")
        if img_id not in hit_map or hit.score > hit_map[img_id][0]:
            hit_map[img_id] = (hit.score, bbox)

    image_ids = list(hit_map.keys())
    if not image_ids:
        return {"results": []}

    response = (
        supabase.table("images")
        .select("id, preview_url, download_url, image_width, image_height, page_url, motive")
        .in_("id", image_ids)
        .execute()
    )

    results = []
    for row in response.data or []:
        score, bbox = hit_map[row["id"]]
        results.append(
            {
                "preview_url": row.get("preview_url") or row.get("download_url") or "",
                "download_url": row.get("download_url") or "",
                "page_url": _build_page_url(row),
                "image_width": int(row.get("image_width") or 0),
                "image_height": int(row.get("image_height") or 0),
                "score": float(score),
                "bbox": bbox,
                "motive": row.get("motive"),
            }
        )

    results.sort(key=lambda item: item["score"], reverse=True)
    return {"results": results}


if __name__ == "__main__":
    app.start(host="0.0.0.0", port=int(os.getenv("PORT", "8080")))
