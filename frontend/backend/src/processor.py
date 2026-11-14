import cv2
import numpy as np
from insightface.app import FaceAnalysis
import os
from robyn import Request


MODEL = os.getenv("FACE_MODEL", "buffalo_l")

face_app = FaceAnalysis(name=MODEL, root="./models", providers=["CPUExecutionProvider"], allowed_modules=["detection", "recognition"], static_shape_sessions=False)
face_app.prepare(ctx_id=-1, det_size=[(640, 640), (256, 256), (128, 128)])

class ProcessorError(Exception):
    pass
class NoImageError(ProcessorError):
    pass
class UnreadableImageError(ProcessorError):
    pass
class NoFaceInImageError(ProcessorError):
    pass

def image_from_request(request: Request):
    # ("name", b"image")
    images = list(request.files.items())
    image_entry = images[0][1] if images else None
    if image_entry is None:
        raise NoImageError("No image found in request")

    contents = bytes(image_entry)
    if not contents:
        raise UnreadableImageError("Unable to read uploaded image")

    arr = np.asarray(bytearray(contents), dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)

    if img is None:
        raise UnreadableImageError("Unable to decode uploaded image")
    return img

def process_image(img):
    faces = face_app.get(img)

    if len(faces) == 0:
        raise NoFaceInImageError("Could not find any face in image")

    faces_sorted = sorted(faces, key=lambda f: float(f.det_score), reverse=True)
    return faces_sorted[0]

