from typing import Optional, TypedDict
import json
import os

from pydantic import ValidationError
from robyn import ALLOW_CORS, Request, Response, Robyn
from robyn.argument_parser import Config
from robyn.types import JSONResponse

from requestModel import RequestModel

try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

import vector_db
import processor
import db


config = Config()
config.disable_openapi = True
app = Robyn(__file__, config=config)

ALLOW_CORS(
    app,
    origins=[
        "http://localhost:5173",
        "http://localhost:8080",
        "https://hakonw.github.io"
    ],
)


def _error(detail: str, status: int = 400) -> Response:
    print("Error", detail)
    return Response(
        status_code=status,
        headers={"Content-Type": "application/json"},
        description=json.dumps({"detail": detail}),
    )


class SearchResult(TypedDict):
    preview_url: str
    download_url: str
    page_url: str
    image_width: int
    image_height: int
    score: float
    bbox: Optional[list[int]]
    motive: Optional[str]
    date: Optional[str]


class SearchResponse(JSONResponse):
    results: list[SearchResult]


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/search")
async def search(request: Request) -> SearchResponse | Response:
    print("Handling search request!")

    try:
        params = RequestModel.of(request)
    except ValidationError as e:
        err = e.errors()[0]
        return _error(f"Invalid {err['loc'][0]}: {err['msg']}")

    try:
        img = processor.image_from_request(request)
        face = processor.process_image(img)
    except processor.ProcessorError as e:
        return _error(str(e))

    query_vector = face.normed_embedding.astype(float).tolist()
    hits = await vector_db.retry_query(query_vector, params)
    hit_map = vector_db.best_result_per_image(hits)

    image_ids = list(hit_map.keys())
    if not image_ids:
        return {"results": []}

    images = db.images_by_id(image_ids)

    results = []
    for row in images:
        score = hit_map[row.id].score
        bbox = hit_map[row.id].bbox
        results.append(
            {
                "preview_url": row.preview_url or row.download_url or "",
                "download_url": row.download_url or "",
                "page_url": row.page_url or row.preview_url or "",
                "image_width": int(row.image_width or 0),
                "image_height": int(row.image_height or 0),
                "score": float(score),
                "bbox": bbox,
                "motive": row.motive,
                "date": row.date,
            }
        )

    results.sort(key=lambda item: item["score"], reverse=True)
    return {"results": results}


if __name__ == "__main__":
    app.start(host="0.0.0.0", port=int(os.getenv("PORT", "8080")))
