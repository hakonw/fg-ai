import time
import requests
import numpy as np
import cv2
import uuid
import os
import threading
import queue
from supabase import create_client
from qdrant_client import QdrantClient
from qdrant_client.http import models
from insightface.app import FaceAnalysis
from dotenv import load_dotenv
import sys
import signal

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

job_queue = queue.Queue(maxsize=5)

def init_qdrant():
    print("checking if collection exists...")
    if not qdrant.collection_exists(COLLECTION):
        print("Creating collection...")
        qdrant.create_collection(
            collection_name=COLLECTION,
            vectors_config=models.VectorParams(size=512, distance=models.Distance.COSINE)
        )

shutdown_event = threading.Event()

def fetch_worker():
    print("📡 Fetcher Thread Started")
    while not shutdown_event.is_set():
        try:
            # 1. Fetch Job
            #job_res = supabase.table("images").select("*").eq("status", "pending").limit(1).execute()
            job_res = supabase.rpc("get_pending_images", params={"limit_count": 1}).execute()
            if not job_res.data:
                for _ in range(15):
                    if shutdown_event.is_set():
                        break
                    time.sleep(2)
                continue

            job = job_res.data[0]
            
            supabase.table("images").update({"status": "processing"}).eq("id", job['id']).execute()
            
            print(f"Fetcher: Downloading {job['motive']}")
            t1 = time.time()
            resp = session.get(job['download_url'], stream=True, timeout=30)
            if resp.status_code != 200:
                supabase.table("images").update({"status": "failed"}).eq("id", job['id']).execute()
                raise Exception(f"Download failed for {job['id']}")

            arr = np.asarray(bytearray(resp.content), dtype=np.uint8)
            img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            print(f"Fetcher: Download took {time.time() - t1:.2f}s")

            job_queue.put({"job": job, "img": img})

        except Exception as e:
            print(f"❌ Fetcher Error: {e}")
            time.sleep(5)
    print("Stopped queuing new jobs. Thread done")

def process_worker():
    print("🧠 Processor Thread Started")
    init_qdrant()

    while not (shutdown_event.is_set() and job_queue.empty()):
        item = job_queue.get()

        job = item["job"]
        img = item["img"]

        print(f"Processor: Processing {job['motive']}")

        try:
            # 3. Detect and embed with InsightFace
            t1 = time.time()

            try:
                faces = face_app.get(img)
            except Exception:
                faces = []
            print(f"Processor: InsightFace took {time.time() - t1:.2f}s for {len(faces)} faces")

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
                print(f"✅ Processor: Indexed {len(points)} faces")
            else:
                print("⚠️ Processor: No faces found")

            supabase.table("images").update({"status": "indexed"}).eq("id", job['id']).execute()

        except Exception as e:
            print(f"❌ Processor Error: {e}")
            supabase.table("images").update({"status": "failed"}).eq("id", job['id']).execute()
        finally:
            job_queue.task_done()
    print(f"Shut down. Leaving {job_queue.qsize()} jobs in incorrect state")

if __name__ == "__main__":
    print("🚀 Worker Started")
    
    # Start Fetcher Threads
    t_fetch1 = threading.Thread(target=fetch_worker, daemon=True)
    t_fetch2 = threading.Thread(target=fetch_worker, daemon=True)

    t_fetch1.start()
    t_fetch2.start()

    def signal_handler(sig, frame):
        print("⚠️ Stopping worker gracefully...")
        if shutdown_event.is_set():
            sys.exit(1)
        shutdown_event.set()

    signal.signal(signal.SIGINT, signal_handler)

    process_worker()

