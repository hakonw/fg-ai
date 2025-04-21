from dataclasses import dataclass


@dataclass
class ImageData:
    motive: str
    place: str
    date: str
    download_link: str
    arkiv: str
    thumb: str
