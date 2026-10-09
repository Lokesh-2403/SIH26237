from backend.ledger.ledger import (
    add_ledger_entry,
    verify_ledger,
    get_ledger_status,
)


event = {
    "document_id": "DOC-DLT-TEST",
    "recipient_id": "OFFICER-DLT",
    "session_id": "SESSION-DLT-TEST",
    "watermark_id": "WM-DLT-TEST",
    "timestamp": "2026-09-19T00:00:00Z",
    "signature": "TEST-SIGNATURE",
}


print("Creating distributed ledger entry...")

entry = add_ledger_entry(event)

print("Ledger entry created:")
print(entry)

print()
print("Ledger status:")

status = get_ledger_status()

for key, value in status.items():
    print(key, ":", value)

print()

if not verify_ledger():
    raise RuntimeError(
        "DISTRIBUTED LEDGER INTEGRITY TEST FAILED"
    )

print("DISTRIBUTED LEDGER INTEGRITY TEST: SUCCESS")

# ============================================================
# TAMPER TEST
# ============================================================

from pathlib import Path
import json


node_file = Path(
    "backend/ledger/nodes/NODE-01.json"
)

original = json.loads(
    node_file.read_text(
        encoding="utf-8"
    )
)

if not original:
    raise RuntimeError(
        "Ledger test produced no entries."
    )


# Tamper with NODE-01
original[0]["event"]["document_id"] = (
    "TAMPERED-DOCUMENT"
)

node_file.write_text(
    json.dumps(
        original,
        indent=4,
    ),
    encoding="utf-8",
)


# Check individual node status.
status_after_tamper = get_ledger_status()

node_01_status = status_after_tamper["NODE-01"]

if node_01_status["valid"]:
    raise RuntimeError(
        "TAMPER DETECTION FAILED: NODE-01 still appears valid"
    )

print(
    "DISTRIBUTED LEDGER TAMPER DETECTION: SUCCESS"
)


# The remaining two nodes should still provide quorum.
if not verify_ledger():
    raise RuntimeError(
        "QUORUM FAILED AFTER SINGLE-NODE TAMPER"
    )

print(
    "QUORUM SURVIVAL AFTER SINGLE-NODE TAMPER: SUCCESS"
)


# ============================================================
# RESTORE NODE-01
# ============================================================

node_02 = Path(
    "backend/ledger/nodes/NODE-02.json"
)

node_file.write_text(
    node_02.read_text(
        encoding="utf-8"
    ),
    encoding="utf-8",
)


if not verify_ledger():
    raise RuntimeError(
        "Ledger did not recover after test restoration."
    )

print(
    "DISTRIBUTED LEDGER RESTORATION: SUCCESS"
)