import io

import numpy as np
import requests
from PIL import Image

from common import config
from common.image_data import ImageData

auth = config.auth()


def downloadImage(image_data: ImageData) -> bytes:
    # Trouble files
    # First does not exist, second has incorrect channels
    if image_data.download_link in ["/arkiv/api/download/2208000/", "/arkiv/api/download/2197598/"]:
        return None

    # Download image
    download_url = "https://foto.samfundet.no" + image_data.download_link  # /arkiv/api/download/1234/
    response = requests.get(download_url, auth=auth)

    if 'Content-Disposition' not in response.headers:
        raise Exception(f"Could not download {image_data.download_link}")

    return response.content


def as_numpy(image_bytes):
    image = Image.open(io.BytesIO(image_bytes))
    image_array = np.asarray(image)
    return image_array
