import PIL.Image
import face_recognition.api as face_recognition
import pickle
import numpy as np
from dataclasses import dataclass
from flask import jsonify
import base64
import re
from io import BytesIO
from flask import Flask, request
import os
from flask_cors import CORS, cross_origin

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

with open('pickld', 'rb') as fp:
    faces = pickle.load(fp)

refs = CustomUnpickler(open('refs.pickle', 'rb')).load()



app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] =  32 * 1024 * 1024
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'


@app.route("/", methods=["POST"])
@cross_origin()
def recognize():
    # For more information about CORS and CORS preflight requests, see:
    # https://developer.mozilla.org/en-US/docs/Glossary/Preflight_request


    content_type = request.headers.get('Content-Type')
    if (content_type != 'application/json'):
        return (jsonify('Need json as type'), 415)

    data = request.get_json()
    if "image" not in data:
        return (jsonify('bad request! Could not find the image'), 400)
    
    image_base64 = data["image"]
    tolerance= float(data["sensitivity"])/100

    if (tolerance < 0.1):
        return (jsonify('too low sensitivity'), 400)
    if (tolerance > 0.7):
        return (jsonify('too high sensitivity'), 400)

    # TODO Limit
    # filename = file.filename  # TODO validate metadata

    image_data = base64.b64decode(re.sub('^data:image/.+;base64,', '', image_base64))

    img = PIL.Image.open(BytesIO(image_data)).convert("RGB")
    img_arr = np.array(img)
    encodings = face_recognition.face_encodings(img_arr)

    if len(encodings) > 1:
        return (jsonify('bad request! Found multiple faces'), 400)
    if len(encodings) == 0:
        return (jsonify('bad request! Found no faces'), 400)

    matches = []

    for img_ref, unknown_encodings in faces.items():
        distances = face_recognition.face_distance(unknown_encodings, encodings[0])
        result = list(distances <= tolerance)

        if True in result:
            matches.append(img_ref)

    # TODO map matches back to URLs
    # This is because i am lazy. Instead of creating a updated system, i just translate back

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

    print("Found", len(translated), "at", tolerance)
    return (translated, 200)

if __name__ == '__main__':
    app.run(threaded=True,host='0.0.0.0',port=int(os.environ.get("PORT", 8080)))