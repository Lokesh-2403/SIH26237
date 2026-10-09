import json
import tempfile
from pathlib import Path

from backend.ledger import ledger


event = {
    "document_id": "DOC-TEST-001",
    "recipient_id": "OFFICER-003",
    "session_id": "SESSION-TEST-001",
    "watermark_id": "WM-TEST-001",
    "timestamp": "2026-09-18T00:00:00Z",
    "signature": "TEST-SIGNATURE"
}


# Use a temporary ledger so the real project ledger is untouched
with tempfile.TemporaryDirectory() as temp_dir:

    test_ledger = Path(temp_dir) / "ledger.json"
    ledger.LEDGER_FILE = test_ledger

    # 1. Create a valid entry
    entry = ledger.add_ledger_entry(event)

    print("Ledger entry created:")
    print(entry)

    # 2. Verify original ledger
    assert ledger.verify_ledger() is True
    print("ORIGINAL LEDGER TEST: SUCCESS")

    # 3. Tamper with the stored data
    entries = json.loads(
        test_ledger.read_text(encoding="utf-8")
    )

    entries[-1]["event"]["recipient_id"] = "TAMPERED-OFFICER"

    test_ledger.write_text(
        json.dumps(entries, indent=4),
        encoding="utf-8"
    )

    # 4. Verify tampering is detected
    assert ledger.verify_ledger() is False
    print("TAMPER DETECTION TEST: SUCCESS")