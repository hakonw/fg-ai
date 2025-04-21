import functions_framework
import flask

from flask import jsonify
import base64
import re

import PIL.Image
import numpy as np
import io

import time

from deepface import DeepFace

import db

MODEL = "Facenet512"
normalization = "Facenet"
FACE_DETECTION = "retinaface"

@functions_framework.http
def recognize(request) -> flask.typing.ResponseReturnValue:
    print("Got request")
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
    tolerance = float(data["sensitivity"])

    if (tolerance < 0.1):
        print(tolerance)
        return (jsonify('too low sensitivity'), 400, headers)
    # if (tolerance > 7):
    #     print(tolerance)
    #     return (jsonify('too high sensitivity'), 400, headers)


    image_data = base64.b64decode(re.sub('^data:image/.+;base64,', '', image_base64))
    image = PIL.Image.open(io.BytesIO(image_data))
    image_array = np.array(image)

    try:

        uploadedEmbeddings = DeepFace.represent(img_path=image_array,
                                                enforce_detection=True,
                                                model_name=MODEL,
                                                normalization=normalization,
 #                                               detector_backend=FACE_DETECTION
                                                )
        # If there are multiple faces, we will just use the first one for now
        print(f"Image embedding took {time.time() - startTime:.2f} seconds")

        if len(uploadedEmbeddings) > 1:
            print("Found multiple faces")
        uploadedEmbeddings = uploadedEmbeddings[0]["embedding"]
    except ValueError as e:
        print(e)
        return (jsonify('bad request! Could not find faces'), 400, headers)

    images = db.get_results_from_db(uploadedEmbeddings, tolerance, limit=100)

    print(f"Found {len(images)} at {tolerance} sensitivity. Took {time.time() - startTime:.2f} seconds")

    return (images, 200, headers)