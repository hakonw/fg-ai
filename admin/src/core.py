import uuid
from dataclasses import dataclass
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os
import requests
from requests.auth import HTTPBasicAuth

load_dotenv()

import db

LOGIN_URL = "https://foto.samfundet.no/login/?next=/arkiv/"


def samf_login(session):
    """Establish a husfolk session by hitting /login/ with basic auth. Returns True
    once the session cookie has been minted."""
    session.get(LOGIN_URL, timeout=10)
    if session.cookies.get("sessionid"):
        return True
    print("Login failed: no session cookie minted (check SAMF_USER / SAMF_PASS)")
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


def parse_html(page, html: str, base_url: str):
    soup = BeautifulSoup(html, "html.parser")
    page_images = []
    for block in soup.find_all("li", {"class": "image-box"}):
        try:
            meta = block.find("a", {"class": "photo-swipe-image"})
            btn = block.find("a", {"class": "btn"})  # Download button

            if meta and btn:
                download_url = urljoin(base_url, btn["href"])
                image_view = meta.get("image-view")
                page_url = urljoin(base_url, image_view) if image_view else None
                page_images.append({
                    "id": str(uuid.uuid5(uuid.NAMESPACE_URL, download_url)),
                    "download_url": download_url,
                    "page_url": page_url,
                    "preview_url": urljoin(base_url, meta["href"]),
                    "motive": meta.get("motive", "").strip(),
                    "place": meta.get("place", "").strip(),
                    "date": meta.get("date", "").strip(),
                    "status": "pending"
                })
            else:
                print("Skipped")
        except:
            print(f"Error parsing page {page}: {block}")
            continue
    return page_images


def scrape_page(session, page: int) -> PageResult:
    base_url = "https://foto.samfundet.no/arkiv/"

    try:
        resp = session.get(base_url, params={"p": page}, timeout=10)
        if resp.status_code == 404:
            msg = f"Page {page}: HTTP 404 - reached end of archive (for this login). Stopping."
            print(msg)
            return PageResult(page=page, end_of_archive=True)

        if resp.status_code != 200:
            msg = f"Page {page}: HTTP {resp.status_code} ({len(resp.content)} bytes) - skipping"
            print(msg)
            return PageResult(page=page, error=msg)

        images = parse_html(page, resp.content, base_url)

        if images:
            queue_image_response = db.queue_images(images)
            count = len(queue_image_response.data) if queue_image_response.data else 0
            print(f"Page {page}: Found {len(images)}, New Queued: {count}")
            return PageResult(page=page, found=len(images), queued=count)
        else:
            msg = f"Page {page}: No images found. (HTTP {resp.status_code}, {len(resp.content)} bytes, final_url={resp.url})"
            print(msg)
            return PageResult(page=page)

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
