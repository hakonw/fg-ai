import os
from dataclasses import dataclass
from typing import List

from supabase import create_client


def require_env(key: str) -> str:
    value = os.getenv(key)
    if value is None:
        raise RuntimeError(f"Environment variable {key} is not set")
    return value


supabase = create_client(require_env("SUPABASE_URL"), require_env("SUPABASE_KEY"))


@dataclass(frozen=True)
class ImageRow:
    id: str
    download_url: str
    preview_url: str | None = None
    page_url: str | None = None
    image_width: int | None = None
    image_height: int | None = None
    motive: str | None = None
    date: str | None = None


def images_by_id(image_ids: List[str]) -> List[ImageRow]:
    rows = (
        supabase.table("images")
        .select("id, preview_url, download_url, image_width, image_height, page_url, motive, date")
        .in_("id", image_ids)
        .execute()
    ).data or []
    return [ImageRow(**row) for row in rows]
