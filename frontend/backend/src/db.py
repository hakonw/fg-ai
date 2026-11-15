import json
import os
from dataclasses import dataclass
from datetime import date
from typing import List
from urllib.parse import quote

from supabase import create_client


def require_env(key: str) -> str:
    value = os.getenv(key)
    if value is None:
        raise RuntimeError(f"Environment variable {key} is not set")
    return value


supabase = create_client(require_env("SUPABASE_URL"), require_env("SUPABASE_KEY"))

SITE_URL = "https://foto.samfundet.no"


@dataclass(frozen=True)
class Motive:
    fg_motive_id: str | None = None
    title: str | None = None
    date: str | None = None

    @property
    def display_date(self) -> str | None:
        if not self.date:
            return None
        return date.fromisoformat(self.date[:10]).strftime("%d.%m.%Y")


@dataclass(frozen=True)
class ImageRow:
    id: str
    download_url: str | None
    preview_url: str | None = None
    image_width: int | None = None
    image_height: int | None = None
    fg_photo_id: str | None = None
    security_level: str | None = None
    motive: Motive | None = None

    @property
    def link(self) -> str:
        if self.fg_photo_id and self.motive and self.motive.fg_motive_id:
            fg_motive_id = self.motive.fg_motive_id
            modal = json.dumps({"modalType": "searchMotive", "motiveId": fg_motive_id, "photoId": self.fg_photo_id}, separators=(",", ":"))
            return f"{SITE_URL}/motive/{fg_motive_id}?photoViewModal={quote(modal, safe='')}"
        return self.preview_url or ""


def images_by_id(image_ids: List[str]) -> List[ImageRow]:
    rows = (
        supabase.table("images")
        .select("id, preview_url, download_url, image_width, image_height, fg_photo_id, security_level, "
                "motives(fg_motive_id, title, date)")
        .in_("id", image_ids)
        .execute()
    ).data or []
    result = []
    for row in rows:
        motive = row.pop("motives")
        result.append(ImageRow(**row, motive=Motive(**motive) if motive else None))
    return result
