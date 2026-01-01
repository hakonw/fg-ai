import gradio as gr
from insightface.app import FaceAnalysis
from supabase import create_client
from qdrant_client import QdrantClient
import os
import cv2

try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
qdrant = QdrantClient(url=os.getenv("QDRANT_URL"), api_key=os.getenv("QDRANT_KEY"))

# MUST match Worker config
MODEL = "buffalo_l"
COLLECTION = "samfundet_faces"

face_app = FaceAnalysis(name=MODEL, providers=["CPUExecutionProvider"])
face_app.prepare(ctx_id=-1)


def search(image):
    imageHash = "ima-" + str(hash(image.tobytes()))

    print(f"{imageHash}: Running search...")
    if image is None: return None

    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    try:
        faces = face_app.get(image)
        if not faces:
            print(f"{imageHash}: No faces detected")
            return []

        # Use first face
        query_vector = faces[0].normed_embedding.astype(float).tolist()
        
        # Search Qdrant
        hits = qdrant.query_points(
            collection_name=COLLECTION,
            query=query_vector,
            limit=100,
            with_payload=True,
            score_threshold=0.35,
        )

        print(f"{imageHash}: Found {len(hits.points)} hits")

        if not hits:
            return []
        
        # Take best match per image
        hit_map = {}
        for hit in hits.points:
            img_id = hit.payload['image_id']
            bbox = hit.payload.get('bbox')
            if img_id not in hit_map or hit.score > hit_map[img_id][0]:
                hit_map[img_id] = (hit.score, bbox)

        image_ids = list(hit_map.keys())
        
        # Fetch metadata
        response = (supabase.table("images")
                    .select("preview_url, page_url, motive, date, id")
                    .in_("id", image_ids)
                    .execute())
        
        # Format for Gallery
        results = []
        for row in response.data:
            sim = hit_map[row['id']]
            caption = f"{round(sim, 3)*100}% | {row['motive']} ({row['date']})"
            results.append((row['preview_url'], caption, sim))

        # Sort by similarity
        results.sort(key=lambda x: x[2], reverse=True)

        # Drop the raw similarity from the tuple
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
