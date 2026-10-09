from fastapi.testclient import TestClient
from backend.main import app


client = TestClient(app)


def test_protect_rejects_non_pdf():
    response = client.post(
        "/protect",
        files={
            "file": (
                "test.txt",
                b"This is not a PDF",
                "text/plain"
            )
        }
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Only PDF files are supported"
