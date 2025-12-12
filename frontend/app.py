import gradio as gr
from deepface import DeepFace
from supabase import create_client
from qdrant_client import QdrantClient
import os
import cv2

# Secrets (Set these in HF Settings or .env if local)
try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
qdrant = QdrantClient(url=os.getenv("QDRANT_URL"), api_key=os.getenv("QDRANT_KEY"))

# MUST match Worker config
MODEL = "Buffalo_L"
DETECTOR = "retinaface"
COLLECTION = "samfundet_faces"

def search(image):
    if image is None: return None

    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    try:
        embeds = DeepFace.represent(
            img_path=image,
            model_name=MODEL,
            detector_backend=DETECTOR,
            align=True,
            enforce_detection=True
        )
        query_vector = embeds[0]["embedding"]
        
        # 2. Search Qdrant
        # Use a higher similarity threshold to avoid surfacing weak matches as high-% results
        hits = qdrant.query_points(
            collection_name=COLLECTION,
            query=query_vector,
            limit=12,
            with_payload=True,
            score_threshold=0.90,
        )

        if not hits:
            return []
        
        # 3. Hydrate from Supabase
        # Map {image_id: score}
        hit_map = {}
        for hit in hits.points:
            img_id = hit.payload['image_id']
            hit_map[img_id] = max(hit_map.get(img_id, 0), hit.score)

        image_ids = list(hit_map.keys())
        
        # Fetch metadata
        response = (supabase.table("images")
                    .select("preview_url, motive, date, id")
                    .in_("id", image_ids)
                    .execute())
        
        # Format for Gallery
        results = []
        for row in response.data:
            sim = hit_map[row['id']]
            percent = round(sim * 100, 1)
            caption = f"{percent}% | {row['motive']} ({row['date']})"
            results.append((row['preview_url'], caption, sim))

        # Sort by similarity desc (use the raw float, not parsed text)
        results.sort(key=lambda x: x[2], reverse=True)

        # Drop the raw similarity from the tuple for the Gallery component
        return [(img, cap) for img, cap, _ in results]

    except Exception as e:
        raise gr.Error(f"Error: {str(e)}")

with gr.Blocks(title="Samfundet Search") as demo:
    gr.Markdown("# 📸 Samfundet Face Search")
    
    with gr.Row():
        with gr.Column():
            inp = gr.Image(type="numpy", label="Your Selfie")
            btn = gr.Button("Search", variant="primary")
        
        with gr.Column():
            gallery = gr.Gallery(label="Results")
            
    btn.click(search, [inp], gallery)

if __name__ == "__main__":
    demo.launch()
