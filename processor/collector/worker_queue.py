import worker.processor
from common.image_data import ImageData

def queue(imagedata: ImageData):
    worker.processor.processImage.delay(imagedata)
