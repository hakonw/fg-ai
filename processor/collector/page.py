import requests
from bs4 import BeautifulSoup

import config
import database
from image_data import ImageData

url_root = "https://foto.samfundet.no/arkiv/"

auth = config.auth()


def get(page: int):
    params = {
        "page_num": str(page),
    }

    response = requests.get(url_root, params=params, auth=auth)
    content = response.content.decode("utf-8")
    return content


def process(content):
    """

    :param content: html str
    :return: list of ImageData found on page
    """
    html = BeautifulSoup(content, features="html.parser")

    pictures = []

    # Each images
    # <li class="span3 image-box">
    image_block = html.find_all("li", {"class": "span3 image-box"})
    for block in image_block:
        # print(block)

        # Metadata:
        # <a class="photo-swipe-image" date=" 10.05.22" href="/media/husfolk/web/DIGGD/diggd8426.jpg" image-view="/arkiv/DIGGD/84/26/" motive="SIT Vaarball" place="Hele huset" rel="gallery">
        meta_data = block.find("a", {"class": "photo-swipe-image"})
        motive = meta_data["motive"].strip()
        place = meta_data["place"].strip()
        date = meta_data["date"].strip()
        arkiv = meta_data["image-view"].strip()
        thumb = meta_data["href"].strip()

        # DownloadLink
        # <a class="btn" href="/arkiv/api/download/2261676/" onclick="$('#download-modal-2261676').modal('hide');">Ok</a>
        download_link = block.find("a", {"class": "btn"})["href"]

        imageData = ImageData(motive, place, date, download_link, arkiv, thumb)
        pictures.append(imageData)
        # print(data)
    return pictures


def remove_seen(images: list[ImageData]):
    unprocessed = []

    for image in images:
        if not database.contains(image.download_link):
            unprocessed.append(image)

    return unprocessed


if __name__ == "__main__":
    h = get(1)
    imgs = process(h)
    imgs = remove_seen(imgs)
    print(imgs)
