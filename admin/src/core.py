import re
import uuid
from dataclasses import dataclass
from datetime import date
from urllib.parse import quote, unquote, urljoin

from dotenv import load_dotenv
import os
import requests
from requests.auth import HTTPBasicAuth

load_dotenv()

import db

SITE_URL = "https://foto.samfundet.no"
API_URL = f"{SITE_URL}/api"
LOGIN_URL = f"{API_URL}/auth/login"
PAGE_SIZE = 50
SECURITY_LEVELS = ["ALLE", "HUSFOLK"]


def samf_login(session):
    resp = session.post(LOGIN_URL, json={}, timeout=10)
    token = resp.json().get("token") if resp.ok else None
    if token:
        session.cookies.set("fgToken", token, domain="foto.samfundet.no")
        return True
    print(f"Login failed: HTTP {resp.status_code} (check SAMF_USER / SAMF_PASS)")
    return False


def create_photo_session():
    session = requests.Session()
    session.auth = HTTPBasicAuth(os.getenv("SAMF_USER"), os.getenv("SAMF_PASS"))

    if not samf_login(session):
        raise Exception("Authentication failed: unable to mint husfolk session cookie.")
    return session


@dataclass
class PageResult:
    page: int
    found: int = 0
    queued: int = 0
    end_of_archive: bool = False
    error: str | None = None


def image_key(url):
    m = re.match(r"^.*/media/([^/]+)/(?:web|prod)/(.+)\.[^./]+$", url)
    return quote(unquote(f"{m.group(1)}/{m.group(2)}"), safe="/") if m else url


def parse_photos(motive, photos):
    page_images = []
    for photo in photos:
        if photo["securityLevel"]["securityLevelType"] not in SECURITY_LEVELS:
            continue
        if not photo["imageWeb"]:
            continue
        if not photo["imageProd"]:
            raise Exception(f"No imageProd for photo {photo['photoId']['id']}, is the login working?")
        download_url = urljoin(SITE_URL, photo["imageProd"])
        preview_url = urljoin(SITE_URL, photo["imageWeb"])
        page_images.append({
            "id": str(uuid.uuid5(uuid.NAMESPACE_URL, download_url)),
            # From the web path, since prod files can have a re-upload suffix (diggy5323_XmIe0UG.jpg)
            "image_key": image_key(preview_url if not preview_url.endswith("/default.jpg") else download_url),
            "photo_id": photo["photoId"]["id"],
            "download_url": download_url,
            "page_url": f"{SITE_URL}/motive/{motive['motiveId']['id']}",
            "preview_url": preview_url,
            "motive": (motive["title"] or "").strip(),
            "place": ((motive.get("placeDto") or {}).get("name") or "").strip(),
            "date": date.fromisoformat(motive["date"]).strftime("%d.%m.%y") if motive["date"] else "",
            "status": "pending"
        })
    return page_images


def scrape_page(session, page: int) -> PageResult:
    try:
        resp = session.get(f"{API_URL}/search/motives", params={
            "securityLevels": SECURITY_LEVELS,
            "sortField": "DATE_UPLOADED",
            "sortDirection": "DESC",
            "page": page,
            "pageSize": PAGE_SIZE,
        }, timeout=30)
        if resp.status_code != 200:
            msg = f"Page {page}: HTTP {resp.status_code} ({len(resp.content)} bytes) - skipping"
            print(msg)
            return PageResult(page=page, error=msg)

        data = resp.json()
        if page > data["totalPages"]:
            print(f"Page {page}: past last page ({data['totalPages']}) - reached end of archive. Stopping.")
            return PageResult(page=page, end_of_archive=True)

        found = 0
        count = 0
        for motive in data["currentList"]:
            photos_resp = session.get(f"{API_URL}/photos/motive/{motive['motiveId']['id']}", timeout=30)
            photos_resp.raise_for_status()
            images = parse_photos(motive, photos_resp.json())
            if images:
                queue_image_response = db.queue_images(images)
                found += len(images)
                count += len(queue_image_response.data) if queue_image_response.data else 0

        print(f"Page {page}: Found {found}, New Queued: {count}")
        return PageResult(page=page, found=found, queued=count)

    except Exception as e:
        msg = f"Page {page}: Error {e} - skipping"
        print(msg)
        return PageResult(page=page, error=msg)


def scrape_pages(start_page, end_page):
    total_queued = 0
    logs = []

    session = create_photo_session()

    for i in range(int(start_page), int(end_page) + 1):
        result = scrape_page(session, i)
        logs.append(result.error or f"Page {i}: found {result.found}, queued {result.queued}")
        total_queued += result.queued

        if result.end_of_archive:
            break
        if result.error:
            continue

    return f"Total Added: {total_queued}\n" + "\n".join(logs)
