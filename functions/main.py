import functions_framework

from dataclasses import dataclass
import pickle
from typing import List, Set, Dict, Tuple, Optional
from flask import jsonify
import base64
import re

import PIL.Image
import numpy as np
import io

import time

from deepface.commons import distance
from deepface import DeepFace

MODEL = "Facenet512"


@dataclass
class ImageData:
    motive: str
    place: str
    date: str
    download_link: str
    arkiv: str
    thumb: str
    embeddings: Optional[List[float]]
    score: Optional[float]


# temp hack
class CustomUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        try:
            return super().find_class(__name__, name)
        except AttributeError:
            return super().find_class(module, name)


db = CustomUnpickler(open('db.pkl', 'rb')).load()


@functions_framework.http
def recognize(request):
    startTime = time.time()
    if request.method == "OPTIONS":
        headers = {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Max-Age": "3600"
        }

        return ("", 204, headers)

    # Set CORS headers for the main request
    headers = {
        "Access-Control-Allow-Origin": "*"
    }

    content_type = request.headers.get('Content-Type')
    if (content_type != 'application/json'):
        return (jsonify('Need json as type'), 415)

    data = request.get_json()
    if "image" not in data:
        return (jsonify('bad request! Could not find the image'), 400)

    print("Starting")

    image_base64 = data["image"]
    tolerance = float(data["sensitivity"]) / 100

    if (tolerance < 0.1):
        return (jsonify('too low sensitivity'), 400, headers)
    if (tolerance > 0.7):
        return (jsonify('too high sensitivity'), 400, headers)

    # TODO Limit
    # filename = file.filename  # TODO validate metadata

    image_data = base64.b64decode(re.sub('^data:image/.+;base64,', '', image_base64))
    image = PIL.Image.open(io.BytesIO(image_data))  # .convert("RGB")
    image_array = np.array(image)

    try:
        uploadedEmbeddings = DeepFace.represent(img_path=image_array, enforce_detection=True, model_name=MODEL)
        # If there are multiple faces, we will just use the first one for now
        if len(uploadedEmbeddings) > 1:
            print("Found multiple faces")
        uploadedFaceEmbedding = uploadedEmbeddings[0]["embedding"]
    except ValueError:
        return (jsonify('bad request! Could not find faces'), 400, headers)

    # if len(encodings) > 1:
    #     return (jsonify('bad request! Found multiple faces'), 400)

    matches = []

    for imageData in db:
        if imageData.embeddings is not None:
            bestDistance = 100
            for imageDataEmbedding in imageData.embeddings:
                dist = distance.findCosineDistance(uploadedFaceEmbedding, imageDataEmbedding["embedding"])
                if dist < bestDistance:
                    bestDistance = dist
            if (bestDistance <= tolerance):
                imageData.score = bestDistance
                imageData.embeddings = None
                matches.append(imageData)

    matches.sort(key=lambda t: t.score)

    # for match in matches:
    #     # String replacing magic.. (html based)
    #     match = match.replace("ø", "%C3%B8")
    #     match = match.replace("Ø", "%C3%98")
    #     match = match.replace("å", "%C3%A5")
    #     match = match.replace("Å", "%C3%86")
    #     match = match.replace("æ", "%C3%A6")
    #     match = match.replace("Æ", "%C3%86")

    print(f"Found {len(matches)} at {tolerance} sensitivity. Took {time.time() - startTime:.2f} seconds")
    if len(matches) > 200:
        matches = matches[:200]
    return (matches, 200, headers)