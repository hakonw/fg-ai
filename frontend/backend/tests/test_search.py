from pathlib import Path

from robyn.testing import TestClient

from main import app

IMAGE = Path(__file__).parent / "fixtures" / "known_face.jpg"

def test_search_finds_known_face():
    with TestClient(app) as client:
        response = client.post(
            "/search",
            files={"known_face.jpg": IMAGE.read_bytes()},
            form_data={"max_images": "10"}
        )
        assert response.status_code == 200, response.text
        assert len(response.json()["results"]) > 0
