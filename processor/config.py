import os

from dotenv import load_dotenv

load_dotenv()

samf_username = os.getenv("SAMF_USERNAME")
if samf_username is None:
    raise Exception("SAMF_USERNAME is not set")

samf_password = os.getenv("SAMF_PASSWORD")
if samf_password is None:
    raise Exception("SAMF_PASSWORD is not set")

postgres_password = os.getenv("POSTGRES_PASSWORD")
if postgres_password is None:
    raise Exception("POSTGRES_PASSWORD is not set")

postgres_host = os.getenv("POSTGRES_HOST")
if postgres_host is None:
    raise Exception("POSTGRES_HOST is not set")

postgres_port = 5432

def auth():
    from requests.auth import HTTPBasicAuth
    return HTTPBasicAuth(samf_username, samf_password)
