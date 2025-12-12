import time
import requests
import numpy as np
import cv2
import uuid
import os
from supabase import create_client
from qdrant_client import QdrantClient
from qdrant_client.http import models
from deepface import DeepFace
from dotenv import load_dotenv

load_dotenv()

# Config
MODEL = "Buffalo_L"
DETECTOR = "retinaface"
COLLECTION = "samfundet_faces"

# Init DBs
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
qdrant = QdrantClient(url=os.getenv("QDRANT_URL"), api_key=os.getenv("QDRANT_KEY"))

def init_qdrant():
    if not qdrant.collection_exists(COLLECTION):
        qdrant.create_collection(
            collection_name=COLLECTION,
            vectors_config=models.VectorParams(size=512, distance=models.Distance.COSINE)
        )

def process_queue():
    print("🚀 Worker Started")
    init_qdrant()
    
    while True:
        # 1. Fetch Job
        job_res = supabase.table("images").select("*").eq("status", "pending").limit(1).execute()
        if not job_res.data:
            print("💤 Queue empty. Sleeping 10s...")
            time.sleep(10)
            continue
            
        job = job_res.data[0]
        print(f"Processing: {job['motive']}")
        
        try:
            supabase.table("images").update({"status": "processing"}).eq("id", job['id']).execute()
            
            resp = requests.get(
                job['download_url'], 
                auth=(os.getenv("SAMF_USER"), os.getenv("SAMF_PASS")), 
                stream=True, timeout=30
            )
            if resp.status_code != 200: raise Exception("Download failed")
            
            arr = np.asarray(bytearray(resp.content), dtype=np.uint8)
            img = cv2.imdecode(arr, cv2.IMREAD_COLOR)

            # 3. Embed
            try:
                results = DeepFace.represent(
                    img_path=img,
                    model_name=MODEL,
                    detector_backend=DETECTOR,
                    align=True,
                    enforce_detection=True
                )
            except:
                results = []

            
            # 4. Save to Qdrant
            points = []
            for face in results:
                print(face["embedding"])

                points.append(models.PointStruct(
                    id=str(uuid.uuid4()),
                    vector=face["embedding"],
                    payload={
                        "image_id": job['id'],
                    }
                ))
            
            if points:
                qdrant.upsert(COLLECTION, points=points)
                print(f"✅ Indexed {len(points)} faces")
            else:
                print("⚠️ No faces found")

            supabase.table("images").update({"status": "indexed"}).eq("id", job['id']).execute()

        except Exception as e:
            print(f"❌ Error: {e}")
            supabase.table("images").update({"status": "failed"}).eq("id", job['id']).execute()

if __name__ == "__main__":
    process_queue()
