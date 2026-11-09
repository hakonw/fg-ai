import math
import os
import shutil
from pathlib import Path
import onnxruntime as ort
from insightface.app import FaceAnalysis
from insightface.model_zoo import coreml_cache

MODEL = "buffalo_l"

use_coreml = "CoreMLExecutionProvider" in ort.get_available_providers()
MAX_COREML_SIZES = 16
COREML_CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".coreml_cache")
coreml_cache.default_coreml_cache_root = lambda: Path(COREML_CACHE)

COREML = ("CoreMLExecutionProvider", {"ModelFormat": "MLProgram", "MLComputeUnits": "ALL"})
providers = [COREML, "CPUExecutionProvider"] if use_coreml else ["CPUExecutionProvider"]

def build_face_app(det_size):
    app = FaceAnalysis(name=MODEL, providers=providers, allowed_modules=["detection", "recognition"], static_shape_sessions=use_coreml)
    app.prepare(ctx_id=0 if use_coreml else -1, det_size=det_size)
    return app

DET_LONG_SIDE = 4800
MIN_FACE_PX = 16
LARGE_FACE_DET_SIZES = [(640, 640), (256, 256), (128, 128)]

# will be overwritten per image
def build_default_face_app():
    return build_face_app((3200, 3200))
face_app = build_default_face_app()
small_det_face_app = build_face_app(LARGE_FACE_DET_SIZES)

def quantize_32(num):
    return math.ceil(num / 32) * 32

def quantized_det_size_for(img):
    h, w = img.shape[:2]
    long_side = min(DET_LONG_SIDE, quantize_32(max(h, w)))
    aspect_ratio = min(h, w) / max(h, w)
    short = quantize_32(long_side * aspect_ratio)
    return (long_side, short) if w >= h else (short, long_side)

def box_iou(a, b):
    ax1, ay1, ax2, ay2 = a[:4]
    bx1, by1, bx2, by2 = b[:4]
    overlap = max(0, min(ax2, bx2) - max(ax1, bx1)) * max(0, min(ay2, by2) - max(ay1, by1))
    union = (ax2 - ax1) * (ay2 - ay1) + (bx2 - bx1) * (by2 - by1) - overlap
    return overlap / union if union > 0 else 0.0

def big_enough(faces):
    return [f for f in faces if f.bbox[2] - f.bbox[0] >= MIN_FACE_PX]

def clear_disk_cache():
    shutil.rmtree(COREML_CACHE, ignore_errors=True)

def detect_faces(img):
    global face_app
    if use_coreml and len(face_app.det_model.resolution_sessions) >= MAX_COREML_SIZES:
        print("Rebuilding face model to free CoreML sessions")
        face_app = None
        clear_disk_cache()
        face_app = build_default_face_app()
    face_app.det_model.input_sizes = [quantized_det_size_for(img)]
    faces = big_enough(face_app.get(img))
    large_faces = [f for f in big_enough(small_det_face_app.get(img)) if all(box_iou(f.bbox, g.bbox) < 0.3 for g in faces)]
    return faces + large_faces
