
import celery_base
import worker.processor
from image_data import ImageData

def queue(imagedata: ImageData):
    worker.processor.processImage.delay(imagedata)
