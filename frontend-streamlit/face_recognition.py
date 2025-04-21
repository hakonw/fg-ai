print("Loading DeepFace...")
from deepface import DeepFace
print("Loaded DeepFace")

from PIL import Image
import numpy as np
import streamlit as st


MODEL = "Facenet512"
normalization = "Facenet"
FACE_DETECTION = "retinaface"

@st.cache_data(show_spinner="Behandler bilde")
def embed(image):
    image_np = np.array(Image.open(image))
    try:
        image_embedding = DeepFace.represent(
            img_path=image_np,
            enforce_detection=True,
            model_name=MODEL,
            normalization=normalization,
            detector_backend=FACE_DETECTION
        )
    except ValueError:
        return None
    return image_embedding