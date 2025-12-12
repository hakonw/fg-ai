import gradio as gr
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from postgrest import CountMethod
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize Supabase
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

def scrape_pages(start_page, end_page):
    base_url = "https://foto.samfundet.no/arkiv/"
    total_queued = 0
    logs = []

    for i in range(int(start_page), int(end_page) + 1):
        try:
            # Public scrape (No auth needed just to see links)
            resp = requests.get(base_url, params={"page_num": i}, auth=(os.getenv("SAMF_USER"), os.getenv("SAMF_PASS")),  timeout=10)
            soup = BeautifulSoup(resp.content, "html.parser")
            
            page_images = []
            for block in soup.find_all("li", {"class": "image-box"}):
                try:
                    meta = block.find("a", {"class": "photo-swipe-image"})
                    btn = block.find("a", {"class": "btn"}) # Download button
                    
                    if meta and btn:
                        page_images.append({
                            "download_url": urljoin(base_url, btn["href"]),
                            "preview_url": urljoin(base_url, meta["href"]),
                            "motive": meta.get("motive", "").strip(),
                            "place": meta.get("place", "").strip(),
                            "date": meta.get("date", "").strip(),
                            "status": "pending"
                        })
                except:
                    continue
            
            if page_images:
                # Upsert: Ignores duplicates based on 'download_url' unique constraint
                res = supabase.table("images").upsert(
                    page_images, on_conflict="download_url", ignore_duplicates=True
                ).execute()
                count = len(res.data) if res.data else 0
                total_queued += count
                logs.append(f"Page {i}: Found {len(page_images)}, New Queued: {count}")
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

if __name__ == "__main__":
    demo.launch()
