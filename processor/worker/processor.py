import database
import worker.downloader
import worker.embedder
from image_data import ImageData
import celery_base


@celery_base.app.task(ignore_result=True)
def processImage(image_data: ImageData):
    if database.contains(image_data.download_link):
        print("Skipping image", image_data.download_link)
        return

    imageBytes = worker.downloader.downloadImage(image_data)
    if imageBytes is None:
        # TODO move this code
        return
    image = worker.downloader.as_numpy(imageBytes)

    embeddings = worker.embedder.calculateEmbeddings(image)

    db_image = database.Image.create(motive=image_data.motive,
                                     place=image_data.place,
                                     data=image_data.date,
                                     download_link=image_data.download_link,
                                     arkiv=image_data.arkiv,
                                     thumbnail=image_data.thumb)

    for embedding in embeddings:
        # Possibly remove face it "face_confidence" is too low
        database.EmbeddingFacenet.create(image_id=db_image.id, embedding=embedding["embedding"])

# Running the runner:
# celery -A celery_base worker -l info --concurrency=3
