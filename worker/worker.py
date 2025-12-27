import time
import requests
import numpy as np
import cv2
import uuid
import os
from supabase import create_client
from qdrant_client import QdrantClient
from qdrant_client.http import models
from insightface.app import FaceAnalysis
from dotenv import load_dotenv

load_dotenv()

MODEL = "buffalo_l"
COLLECTION = "samfundet_faces"

# Init DBs
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
qdrant = QdrantClient(url=os.getenv("QDRANT_URL"), api_key=os.getenv("QDRANT_KEY"))

session = requests.Session()
session.auth = (os.getenv("SAMF_USER"), os.getenv("SAMF_PASS"))

face_app = FaceAnalysis(name=MODEL, providers=["CPUExecutionProvider"])
face_app.prepare(ctx_id=-1)

def init_qdrant():
    print("checking if collection exists...")
    if not qdrant.collection_exists(COLLECTION):
        print("Creating collection...")
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
            print("💤 Queue empty. Sleeping 30s...")
            time.sleep(30)
            continue

        job = job_res.data[0]
        print(f"Processing: {job['motive']}")

        try:
            supabase.table("images").update({"status": "processing"}).eq("id", job['id']).execute()

            t1 = time.time()
            resp = session.get(job['download_url'],stream=True, timeout=30)
            print(f"Download took {time.time() - t1:.2f}s")
            if resp.status_code != 200:
                raise Exception("Download failed")

            arr = np.asarray(bytearray(resp.content), dtype=np.uint8)
            img = cv2.imdecode(arr, cv2.IMREAD_COLOR)

            # 3. Detect and embed with InsightFace
            t1 = time.time()

            try:
                faces = face_app.get(img)
            except Exception:
                faces = []
            print(f"InsightFace took {time.time() - t1:.2f}s for {len(faces)} faces")


            # 4. Save to Qdrant
            points = []
            # Sort faces by bbox to make face_index stable across retries
            faces_sorted = sorted(
                faces,
                key=lambda f: (
                    float(f.bbox[0]),
                    float(f.bbox[1]),
                    float(f.bbox[2]),
                    float(f.bbox[3]),
                ),
            )
            for idx, face in enumerate(faces_sorted):
                # use L2-normalized embedding for cosine distance
                embedding = face.normed_embedding.astype(float).tolist()
                points.append(models.PointStruct(
                    id=str(uuid.uuid5(uuid.NAMESPACE_URL, f"{job['id']}-{MODEL}-face-{idx}")),
                    vector=embedding,
                    payload={
                        "image_id": job['id'],
                        "model": MODEL,
                        "face_index": idx,
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
