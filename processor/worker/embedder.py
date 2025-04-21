import numpy as np
MODEL = "Facenet512"
FACE_DETECTION = "retinaface"
normalization = "Facenet"


def calculateEmbeddings(imageArray: np.ndarray):
    from deepface import DeepFace

    try:
        embeddings = DeepFace.represent(
            img_path=imageArray,
            enforce_detection=True,
            model_name=MODEL,
            detector_backend=FACE_DETECTION,
            normalization=normalization,
        )
    except ValueError:
        # No faces found
        embeddings = []

    return embeddings
