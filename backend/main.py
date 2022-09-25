import functions_framework
import flask
import PIL.Image
import face_recognition.api as face_recognition
import pickle
import numpy as np
from dataclasses import dataclass
from flask import jsonify
import base64
import re
from io import BytesIO


functions_framework.MAX_CONTENT_LENGTH = 32 * 1024 * 1024

@dataclass
class ImageData:
    motive: str
    place: str
    date: str
    download_link: str
    arkiv: str 
    thumb: str

# temp hack
class CustomUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        try:
            return super().find_class(__name__, name)
        except AttributeError:
            return super().find_class(module, name)

# functions_framework.app.app.config['MAX_CONTENT_LENGTH'] = 128 * 1024 * 1024

@functions_framework.http
def recognize(request: flask.Request):
    """HTTP Cloud Function.
    Args:
        request (flask.Request): The request object.
        <https://flask.palletsprojects.com/en/1.1.x/api/#incoming-request-data>
    Returns:
        The response text, or any set of values that can be turned into a
        Response object using `make_response`
        <https://flask.palletsprojects.com/en/1.1.x/api/#flask.make_response>.
    Note:
        For more information on how Flask integrates with Cloud
        Functions, see the `Writing HTTP functions` page.
        <https://cloud.google.com/functions/docs/writing/http#http_frameworks>
    """

    # For more information about CORS and CORS preflight requests, see:
    # https://developer.mozilla.org/en-US/docs/Glossary/Preflight_request

    # Set CORS headers for the main request
    headers = {
        'Access-Control-Allow-Origin': '*',
    }

    # Set CORS headers for the preflight request
    if request.method == 'OPTIONS':
        # Allows GET requests from any origin with the Content-Type
        # header and caches preflight response for an 3600s
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Max-Age': '3600'
        }
        print("Options")
        return ('', 204, headers)

    content_type = request.headers.get('Content-Type')
    if (content_type != 'application/json'):
        return (jsonify('Need json as type'), 415, headers)

    data = request.get_json()
    if "image" not in data:
        return (jsonify('bad request! Could not find the image'), 400, headers)
    
    image_base64 = data["image"]
    tolerance= float(data["sensitivity"])/100
    print(tolerance)

    # TODO Limit
    # filename = file.filename  # TODO validate metadata

    image_data = base64.b64decode(re.sub('^data:image/.+;base64,', '', image_base64))

    img = PIL.Image.open(BytesIO(image_data)).convert("RGB")
    img_arr = np.array(img)
    encodings = face_recognition.face_encodings(img_arr)

    if len(encodings) > 1:
        return (jsonify('bad request! Found multiple faes'), 400, headers)
    if len(encodings) == 0:
        return (jsonify('bad request! Found no faces'), 400, headers)
    
    known_face_encodings = [encodings[0]]

    with open('pickld', 'rb') as fp:
        faces = pickle.load(fp)

    matches = []

    for img_ref, unknown_encodings in faces.items():
        distances = face_recognition.face_distance(unknown_encodings, encodings[0])
        result = list(distances <= tolerance)

        if True in result:
            matches.append(img_ref)

    # TODO map matches back to URLs
    # This is because i am lazy. Instead of creating a updated system, i just translate back

    refs = CustomUnpickler(open('refs.pickle', 'rb')).load()

    translated = []

    # ImageData(motive='VK Vårball', place='Klubben', date='12.05.19', download_link='/arkiv/api/download/1234/', arkiv='/arkiv/DIGF/12/55/', thumb='/media/husfolk/web/DIGF/1255.jpg')]
    # "images/diggc229.jpg",
    for match in matches:
        # String replacing magic.. (html based)
        match = match.replace("ø", "%C3%B8")
        match = match.replace("Ø", "%C3%98")
        match = match.replace("å", "%C3%A5")
        match = match.replace("Å", "%C3%86")
        match = match.replace("æ", "%C3%A6")
        match = match.replace("Æ", "%C3%86")
        # print(match)
        image_name = match.split("images/")[1]
        # Look for link back to ImageData
        image_datas = list(filter(lambda id: image_name.lower() in id.thumb.lower(), refs))
        # arkivs = list(map(lambda id: id.arkiv, image_datas))
        if len(image_datas) == 0:
            print("arkivs failed for", match) 
        #assert(len(list(arkivs)) > 0)
        # print(image_datas)
        dupe_list = []
        for arkiv in image_datas:
            if arkiv.thumb in dupe_list:
                continue
            translated.append(arkiv)
            dupe_list.append(arkiv.thumb)



    print("Found", len(translated))
    return (translated, 200, headers)