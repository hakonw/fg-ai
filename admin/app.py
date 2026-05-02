import gradio as gr
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


def create_photo_session():
    session = requests.Session()
    session.auth = HTTPBasicAuth(os.getenv("SAMF_USER"), os.getenv("SAMF_PASS"))
    #session.cookies.update({"csrftoken": "aa", "sessionid": "aa"})
    return session


def validate_auth(image_url):
    try:
        session = create_photo_session()
        resp = session.get(image_url, timeout=20, stream=True)
        first_bytes = resp.raw.read(16)
        return "\n".join([
            f"status={resp.status_code}",
            f"content_type={resp.headers.get('content-type')}",
            f"content_length={resp.headers.get('content-length')}",
            f"final_url={resp.url}",
            f"first_bytes={first_bytes!r}",
        ])
    except Exception as e:
        return f"Validation failed: {e}"

def scrape_pages(start_page, end_page):
    base_url = "https://foto.samfundet.no/arkiv/"
    total_queued = 0
    logs = []

    session = create_photo_session()

    for i in range(int(start_page), int(end_page) + 1):
        try:
            resp = session.get(base_url, params={"page_num": i}, timeout=10)
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
                logs.append(f"Page {i}: No images found.")
                
        except Exception as e:
            logs.append(f"Page {i} Error: {str(e)}")

    return f"Total Added: {total_queued}\n" + "\n".join(logs)

with gr.Blocks(title="Samfundet Admin") as demo:
    gr.Markdown("# Admin Dashboard")
    
    with gr.Row():
        with gr.Column():
            gr.Markdown("### 📊 Queue Stats")
            stat_disp = gr.JSON(value=get_stats)
            refresh_btn = gr.Button("Refresh Stats")
            refresh_btn.click(get_stats, outputs=stat_disp)
        
        with gr.Column():
            gr.Markdown("### 🕷️ Scraper")
            s_in = gr.Number(value=1, label="Start Page")
            e_in = gr.Number(value=5, label="End Page")
            scrape_btn = gr.Button("Add Pages to Queue", variant="primary")
            log_out = gr.Textbox(label="Logs", lines=10)
            
            scrape_btn.click(scrape_pages, [s_in, e_in], log_out)

        with gr.Column():
            gr.Markdown("###  Auth Validation")
            auth_url_in = gr.Textbox(
                value="https://foto.samfundet.no/media/husfolk/web/DIGGJ/diggj2697.jpg",
                label="Auth Test URL",
            )
            auth_btn = gr.Button("Validate Auth")
            auth_out = gr.Textbox(label="Auth Result", lines=6)
            auth_btn.click(validate_auth, [auth_url_in], auth_out)

if __name__ == "__main__":
    demo.launch()
