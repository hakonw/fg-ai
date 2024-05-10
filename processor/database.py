import peewee
from pgvector.peewee import VectorField
from playhouse.psycopg3_ext import Psycopg3Database

import config

db = Psycopg3Database(
    "postgres",
    host=config.postgres_host,
    port=config.postgres_port,
    user="postgres",
    password=config.postgres_password
)


class Image(peewee.Model):
    id = peewee.PrimaryKeyField(primary_key=True)
    motive = peewee.TextField(null=False)
    place = peewee.TextField(null=False)
    date = peewee.TextField(null=True)
    download_link = peewee.TextField(null=False, unique=True, index=True)
    arkiv = peewee.TextField(null=False)
    thumbnail = peewee.TextField(null=False)

    class Meta:
        database = db

class EmbeddingFacenet(peewee.Model):
    image = peewee.ForeignKeyField(Image)
    embedding = VectorField(dimensions=512, null=False)

    class Meta:
        database = db
        primary_key = False



db.connect()
db.execute_sql('CREATE EXTENSION IF NOT EXISTS vector')
db.create_tables([Image, EmbeddingFacenet])


def contains(download_link):
    return Image.select().where(Image.download_link == download_link).exists()

