from fastapi.testclient import TestClient
from backend.main import app


client = TestClient(app)


def test_investigate_normal_pdf():
    # Use an actual PDF without a forensic watermark.
    pdf_path = "backend/watermark/Block-Chain_Based_Certificate_Issuance_amp_and_Verification.pdf"

    with open(pdf_path, "rb") as f:
        response = client.post(
            "/investigate",
            files={
                "file": (
                    "normal.pdf",
                    f,
                    "application/pdf"
                )
            }
        )

    print("STATUS:", response.status_code)
    print("BODY:", response.text)

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "failed"
    assert data["message"] == "No forensic watermark found"