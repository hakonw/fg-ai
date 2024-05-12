from dataclasses import dataclass
from typing import List, Set, Dict, Tuple, Optional, Union

@dataclass
class ImageData:
    motive: str
    place: str
    date: Optional[str]
    download_link: str
    arkiv: str
    thumb: str
    distance: float
