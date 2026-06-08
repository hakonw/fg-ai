import gradio as gr
import time
import requests
from requests.auth import HTTPBasicAuth
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import uuid

from postgrest import CountMethod
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

try:
    supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
except Exception as e:
    print(f"Error connecting to Supabase: {e}")
    print("Make sure .env is set up correctly.")
    import sys
    sys.exit(1)

def get_stats():
    stats = {}
    for s in ["pending", "processing", "indexed", "failed"]:
        res = (supabase.table("images")
               .select("*", count=CountMethod.exact, head=True)
               .eq("status", s)
               .execute())
        stats[s] = res.count
    return stats


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


def reset_processing():
    res = (
        supabase.table("images")
        .update({"status": "pending"})
        .eq("status", "processing")
        .execute()
    )
    count = len(res.data) if res.data else 0
    return f"Reset {count} processing jobs to pending."


def reset_failed():
    res = (
        supabase.table("images")
        .update({"status": "pending"})
        .eq("status", "failed")
        .execute()
    )
    count = len(res.data) if res.data else 0
    return f"Reset {count} failed jobs to pending."


def scrape_pages(start_page, end_page):
    base_url = "https://foto.samfundet.no/arkiv/"
    total_queued = 0
    logs = []

    session = create_photo_session()

    for i in range(int(start_page), int(end_page) + 1):
        try:
            resp = session.get(base_url, params={"p": i}, timeout=10)
            if resp.status_code == 404:
                msg = f"Page {i}: HTTP 404 - reached end of archive (for this login). Stopping."
                logs.append(msg)
                print(msg)
                break
            if resp.status_code != 200:
                msg = f"Page {i}: HTTP {resp.status_code} ({len(resp.content)} bytes) - skipping"
                logs.append(msg)
                print(msg)
                continue
            soup = BeautifulSoup(resp.content, "html.parser")
            
            page_images = []
            for block in soup.find_all("li", {"class": "image-box"}):
                try:
                    meta = block.find("a", {"class": "photo-swipe-image"})
                    btn = block.find("a", {"class": "btn"}) # Download button
                    
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
                    print(f"Error parsing page {i}: {block}")
                    continue
            
            if page_images:
                # Upsert: Ignores duplicates based on 'download_url' unique constraint
                res = supabase.table("images").upsert(
                    page_images, on_conflict="download_url", ignore_duplicates=True
                ).execute()
                count = len(res.data) if res.data else 0
                total_queued += count
                logs.append(f"Page {i}: Found {len(page_images)}, New Queued: {count}")
                print(f"Page {i}: Found {len(page_images)}, New Queued: {count}")
            else:
                msg = f"Page {i}: No images found. (HTTP {resp.status_code}, {len(resp.content)} bytes, final_url={resp.url})"
                logs.append(msg)
                print(msg)

        except Exception as e:
            logs.append(f"Page {i} Error: {str(e)}")

    return f"Total Added: {total_queued}\n" + "\n".join(logs)

with gr.Blocks(title="Samfundet Admin") as admin_page:
    gr.Markdown("# Admin Dashboard")
    
    with gr.Row():
        with gr.Column():
            gr.Markdown("### Queue Stats")
            stat_disp = gr.JSON(value=get_stats)
            refresh_btn = gr.Button("Refresh Stats")
            reset_processing_btn = gr.Button("Reset Processing", variant="stop")
            reset_failed_btn = gr.Button("Reset Failed", variant="stop")
            reset_out = gr.Textbox(label="Reset Result", lines=3)
            refresh_btn.click(get_stats, outputs=stat_disp)
            reset_processing_btn.click(reset_processing, outputs=reset_out)
            reset_failed_btn.click(reset_failed, outputs=reset_out)
        
        with gr.Column():
            gr.Markdown("### Scraper")
            s_in = gr.Number(value=1, label="Start Page")
            e_in = gr.Number(value=5, label="End Page")
            scrape_btn = gr.Button("Add Pages to Queue", variant="primary")
            log_out = gr.Textbox(label="Logs", lines=10)

            scrape_btn.click(scrape_pages, [s_in, e_in], log_out)

if __name__ == "__main__":
    admin_page.launch()
