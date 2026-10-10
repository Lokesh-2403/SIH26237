import base64
import uuid
from datetime import datetime, timezone

from fastapi import (
    FastAPI,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response


# ============================================================
# AES-GCM
# ============================================================

from backend.crypto.aes_gcm import (
    generate_key,
    encrypt_data,
    decrypt_data,
)


# ============================================================
# ML-DSA
# ============================================================

from backend.crypto.mldsa import (
    generate_keys as generate_signing_keys,
    sign_message,
    verify_signature,
    create_event_message,
)


# ============================================================
# ML-KEM
# ============================================================

from backend.crypto.mlkem import (
    generate_keys as generate_kem_keys,
    encapsulate,
    decapsulate,
)


# ============================================================
# KEY STORAGE
# ============================================================

from backend.crypto.key_storage import (
    save_secret_key,
    load_secret_key,
    key_exists,
    save_kem_secret_key,
    load_kem_secret_key,
    kem_key_exists,
)


# ============================================================
# KEY WRAPPING
# ============================================================

from backend.crypto.key_wrap import (
    derive_key_encryption_key,
    wrap_document_key,
    unwrap_document_key,
)


# ============================================================
# DATABASE
# ============================================================

from backend.database.db import (
    init_database,
    add_recipient,
    get_recipient,
    get_all_recipients,
    add_document,
    get_document,
    add_document_recipient,
    get_document_recipient,
    add_decryption_event,
    get_decryption_event_by_watermark,
)


# ============================================================
# WATERMARK
# ============================================================

from backend.watermark.pdf_watermark import (
    embed_watermark,
    extract_watermark,
    generate_watermark_id,
)


# ============================================================
# LEDGER
# ============================================================

from backend.ledger.ledger import (
    add_ledger_entry,
    verify_ledger,
    get_ledger_entries,
    LEDGER_FILE,
    NODE_IDS,
)


# ============================================================
# APPLICATION
# ============================================================

app = FastAPI(
    title="SIH26237",
    description=(
        "Post-quantum document distribution, "
        "forensic watermarking and immutable provenance system."
    ),
    version="1.0.0",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://sih-26237.vercel.app",
],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=[
        "X-Document-ID",
        "X-Recipient-ID",
        "X-Session-ID",
        "X-Watermark-ID",
        "X-Timestamp",
    ],
)


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

init_database()


# ============================================================
# HELPERS
# ============================================================

def utc_timestamp():
    return datetime.now(timezone.utc).isoformat()


def generate_document_id():
    return f"DOC-{uuid.uuid4().hex[:8].upper()}"


def generate_session_id():
    return f"SESSION-{uuid.uuid4().hex[:8].upper()}"


def decode_stored_bytes(value):
    """
    Convert a database value into bytes.

    Supports:
        bytes
        bytearray
        memoryview
        hexadecimal strings
        Base64 strings
    """

    if value is None:
        return None

    if isinstance(value, bytes):
        return value

    if isinstance(value, bytearray):
        return bytes(value)

    if isinstance(value, memoryview):
        return value.tobytes()

    if not isinstance(value, str):
        try:
            return bytes(value)
        except Exception as exc:
            raise ValueError(
                f"Unable to convert database value to bytes: {exc}"
            )

    value = value.strip()

    if not value:
        return b""

    # Try hexadecimal first.
    try:
        if len(value) % 2 == 0:
            return bytes.fromhex(value)
    except ValueError:
        pass

    # Try Base64.
    try:
        return base64.b64decode(
            value,
            validate=True,
        )
    except Exception:
        pass

    raise ValueError(
        "Database value is neither valid hexadecimal nor Base64"
    )


def decode_public_key(value, expected_size=None):
    key = decode_stored_bytes(value)

    if key is None:
        raise ValueError("Public key is missing")

    if expected_size is not None and len(key) != expected_size:
        raise ValueError(
            f"Invalid public key size: expected "
            f"{expected_size} bytes, got {len(key)} bytes"
        )

    return key


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {
        "project": "SIH26237",
        "status": "Backend is running",
        "crypto": {
            "document_encryption": "AES-256-GCM",
            "key_establishment": "ML-KEM-768",
            "digital_signature": "ML-DSA-65",
            "key_derivation": "HKDF-SHA-256",
        },
        "ledger": "Offline tamper-evident distributed ledger",
    }


# ============================================================
# CREATE RECIPIENT
# ============================================================

@app.post("/recipients")
def create_recipient(
    recipient_id: str = Form(...),
    name: str = Form(...),
    email: str = Form(...),
):
    """
    Create an authorized recipient.

    Generates:
        ML-DSA-65 signing key pair
        ML-KEM-768 encryption key pair

    Private keys remain locally stored.
    """

    existing = get_recipient(recipient_id)

    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Recipient {recipient_id} already exists",
        )

    # --------------------------------------------------------
    # ML-DSA keys
    # --------------------------------------------------------

    try:
        signing_public_key, signing_secret_key = (
            generate_signing_keys()
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"ML-DSA key generation failed: {exc}",
        )

    # --------------------------------------------------------
    # ML-KEM keys
    # --------------------------------------------------------

    try:
        kem_public_key, kem_secret_key = (
            generate_kem_keys()
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"ML-KEM key generation failed: {exc}",
        )

    # --------------------------------------------------------
    # Store private keys locally
    # --------------------------------------------------------

    save_secret_key(
        recipient_id,
        signing_secret_key,
    )

    save_kem_secret_key(
        recipient_id,
        kem_secret_key,
    )

    # --------------------------------------------------------
    # Store public keys in database
    # --------------------------------------------------------

    add_recipient(
        recipient_id=recipient_id,
        name=name,
        email=email,
        public_key=base64.b64encode(
            signing_public_key
        ).decode("utf-8"),
        kem_public_key=base64.b64encode(
            kem_public_key
        ).decode("utf-8"),
    )

    return {
        "status": "success",
        "recipient_id": recipient_id,
        "name": name,
        "email": email,
        "signature_algorithm": "ML-DSA-65",
        "key_establishment_algorithm": "ML-KEM-768",
        "signing_public_key_size": len(signing_public_key),
        "kem_public_key_size": len(kem_public_key),
        "message": (
            "Recipient created with ML-DSA-65 "
            "and ML-KEM-768 keys"
        ),
    }


# ============================================================
# LIST RECIPIENTS
# ============================================================

@app.get("/recipients")
def list_recipients():
    recipients = get_all_recipients()

    result = []

    for recipient in recipients:
        result.append(
            {
                "recipient_id": recipient[0],
                "name": recipient[1],
                "email": recipient[2],
                "has_signing_private_key": key_exists(
                    recipient[0]
                ),
                "has_kem_private_key": kem_key_exists(
                    recipient[0]
                ),
            }
        )

    return {
        "status": "success",
        "count": len(result),
        "recipients": result,
    }


# ============================================================
# PROTECT DOCUMENT
# ============================================================

@app.post("/protect")
async def protect_document(
    file: UploadFile = File(...),
    recipient_ids: str | None = Form(None),
):
    """
    Encrypt a PDF using AES-256-GCM.

    The AES document key is protected for each recipient
    using ML-KEM-768 + HKDF + AES-GCM key wrapping.
    """

    # --------------------------------------------------------
    # Validate file FIRST
    # --------------------------------------------------------

    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported",
        )

    file_data = await file.read()

    if not file_data:
        raise HTTPException(
            status_code=400,
            detail="Uploaded PDF is empty",
        )

    # --------------------------------------------------------
    # Determine recipients
    # --------------------------------------------------------

    if recipient_ids:
        requested_ids = [
            item.strip()
            for item in recipient_ids.split(",")
            if item.strip()
        ]
    else:
        all_recipients = get_all_recipients()

        requested_ids = [
            recipient[0]
            for recipient in all_recipients
        ]

    if not requested_ids:
        raise HTTPException(
            status_code=400,
            detail="No recipients registered",
        )

    # --------------------------------------------------------
    # Validate recipients
    # --------------------------------------------------------

    recipients = []

    for current_recipient_id in requested_ids:

        recipient = get_recipient(
            current_recipient_id
        )

        if not recipient:
            raise HTTPException(
                status_code=404,
                detail=(
                    f"Recipient not found: "
                    f"{current_recipient_id}"
                ),
            )

        if len(recipient) < 5 or not recipient[4]:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Recipient {current_recipient_id} "
                    "does not have an ML-KEM public key"
                ),
            )

        recipients.append(recipient)

    # --------------------------------------------------------
    # Generate document ID and AES key
    # --------------------------------------------------------

    document_id = generate_document_id()

    document_key = generate_key()

    # --------------------------------------------------------
    # AES-256-GCM encryption
    # --------------------------------------------------------

    try:
        nonce, ciphertext = encrypt_data(
            file_data,
            document_key,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Document encryption failed: {exc}",
        )

    # --------------------------------------------------------
    # Store encrypted document
    # --------------------------------------------------------

    add_document(
        document_id=document_id,
        filename=file.filename or "document.pdf",
        encrypted_data=ciphertext,
        nonce=nonce,
        encryption_key=document_key,
    )

    # --------------------------------------------------------
    # Protect AES key for each recipient
    # --------------------------------------------------------

    recipient_results = []

    for recipient in recipients:

        current_recipient_id = recipient[0]

        # ----------------------------------------------------
        # Decode ML-KEM public key
        # ML-KEM-768 public key = 1184 bytes
        # ----------------------------------------------------

        try:
            kem_public_key = decode_public_key(
                recipient[4],
                expected_size=1184,
            )
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=(
                    f"Invalid ML-KEM public key for "
                    f"{current_recipient_id}: {exc}"
                ),
            )

        # ----------------------------------------------------
        # ML-KEM encapsulation
        # ----------------------------------------------------

        try:
            kem_ciphertext, shared_secret = encapsulate(
                kem_public_key
            )
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=(
                    f"ML-KEM-768 encapsulation failed "
                    f"for {current_recipient_id}: {exc}"
                ),
            )

        # ----------------------------------------------------
        # Derive key-encryption key
        # ----------------------------------------------------

        try:
            key_encryption_key = derive_key_encryption_key(
                shared_secret,
                document_id,
                current_recipient_id,
            )
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Key derivation failed: {exc}",
            )

        # ----------------------------------------------------
        # Wrap AES document key
        # ----------------------------------------------------

        try:
            wrapped_key, wrap_nonce = wrap_document_key(
                document_key,
                key_encryption_key,
            )
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Document key wrapping failed: {exc}",
            )

        # ----------------------------------------------------
        # Store recipient crypto material
        # ----------------------------------------------------

        add_document_recipient(
            document_id=document_id,
            recipient_id=current_recipient_id,
            kem_ciphertext=kem_ciphertext,
            wrapped_key=wrapped_key,
            wrap_nonce=wrap_nonce,
        )

        recipient_results.append(
            {
                "recipient_id": current_recipient_id,
                "name": recipient[1],
                "email": recipient[2],
            }
        )

    return {
        "status": "success",
        "document_id": document_id,
        "filename": file.filename,
        "message": (
            "Document encrypted and distributed "
            "using ML-KEM-768 protected AES key"
        ),
        "encryption_algorithm": "AES-256-GCM",
        "key_establishment_algorithm": "ML-KEM-768",
        "key_derivation": "HKDF-SHA-256",
        "recipient_count": len(recipient_results),
        "recipients": recipient_results,
        "encrypted_size": len(ciphertext),
        "nonce_size": len(nonce),
        "document_key_size": len(document_key),
    }


# ============================================================
# DECRYPT DOCUMENT
# ============================================================

@app.get("/decrypt/{document_id}")
def decrypt_document(
    document_id: str,
    recipient_id: str,
):
    """
    Decrypt an authorized document.

    On successful decryption:
        AES document key
            ↓
        PDF plaintext
            ↓
        forensic watermark
            ↓
        ML-DSA signed event
            ↓
        distributed ledger
    """

    # --------------------------------------------------------
    # Get document
    # --------------------------------------------------------

    document = get_document(
        document_id
    )

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    # --------------------------------------------------------
    # Get recipient
    # --------------------------------------------------------

    recipient = get_recipient(
        recipient_id
    )

    if not recipient:
        raise HTTPException(
            status_code=404,
            detail="Recipient not found",
        )

    # --------------------------------------------------------
    # Check authorization
    # --------------------------------------------------------

    document_recipient = get_document_recipient(
        document_id,
        recipient_id,
    )

    if not document_recipient:
        raise HTTPException(
            status_code=403,
            detail=(
                "This recipient is not authorized "
                "to decrypt this document"
            ),
        )

    # --------------------------------------------------------
    # Load ML-KEM private key
    # --------------------------------------------------------

    kem_secret_key = load_kem_secret_key(
        recipient_id
    )

    if not kem_secret_key:
        raise HTTPException(
            status_code=500,
            detail=(
                "Recipient ML-KEM private key "
                "was not found locally"
            ),
        )

    # --------------------------------------------------------
    # Decode stored crypto values
    # --------------------------------------------------------

    try:
        kem_ciphertext = decode_stored_bytes(
            document_recipient[2]
        )

        wrapped_key = decode_stored_bytes(
            document_recipient[3]
        )

        wrap_nonce = decode_stored_bytes(
            document_recipient[4]
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to decode stored "
                f"cryptographic values: {exc}"
            ),
        )

    # --------------------------------------------------------
    # ML-KEM decapsulation
    # --------------------------------------------------------

    try:
        shared_secret = decapsulate(
            kem_ciphertext,
            kem_secret_key,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "ML-KEM-768 decapsulation failed: "
                f"{exc}"
            ),
        )

    # --------------------------------------------------------
    # Derive KEK
    # --------------------------------------------------------

    try:
        key_encryption_key = derive_key_encryption_key(
            shared_secret,
            document_id,
            recipient_id,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Key derivation failed: {exc}",
        )

    # --------------------------------------------------------
    # Unwrap AES document key
    # --------------------------------------------------------

    try:
        document_key = unwrap_document_key(
            wrapped_key,
            wrap_nonce,
            key_encryption_key,
        )
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to unwrap document encryption key",
        )

    # --------------------------------------------------------
    # Decode encrypted document
    # --------------------------------------------------------

    try:
        encrypted_data = decode_stored_bytes(
            document[2]
        )

        document_nonce = decode_stored_bytes(
            document[3]
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to decode encrypted "
                f"document data: {exc}"
            ),
        )

    # --------------------------------------------------------
    # AES-GCM decryption
    # --------------------------------------------------------

    try:
        decrypted_data = decrypt_data(
            document_nonce,
            encrypted_data,
            document_key,
        )
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Document decryption failed",
        )

    # --------------------------------------------------------
    # Create access session
    # --------------------------------------------------------

    session_id = generate_session_id()

    timestamp = utc_timestamp()

    # --------------------------------------------------------
    # Generate forensic watermark
    # --------------------------------------------------------

    watermark_id = generate_watermark_id(
        document_id,
        recipient_id,
        session_id,
    )

    # --------------------------------------------------------
    # Embed watermark
    # --------------------------------------------------------

    try:
        watermarked_pdf = embed_watermark(
            decrypted_data,
            watermark_id,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "PDF watermarking failed: "
                f"{exc}"
            ),
        )

    # --------------------------------------------------------
    # Load ML-DSA signing key
    # --------------------------------------------------------

    signing_secret_key = load_secret_key(
        recipient_id
    )

    if not signing_secret_key:
        raise HTTPException(
            status_code=500,
            detail=(
                "Recipient ML-DSA private key "
                "was not found locally"
            ),
        )

    # --------------------------------------------------------
    # Create signed event
    # --------------------------------------------------------

    event_message = create_event_message(
        document_id,
        recipient_id,
        session_id,
        watermark_id,
        timestamp,
    )

    try:
        signature = sign_message(
            event_message,
            signing_secret_key,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"ML-DSA signing failed: {exc}",
        )

    # --------------------------------------------------------
    # Store database event
    # --------------------------------------------------------

    add_decryption_event(
        document_id=document_id,
        recipient_id=recipient_id,
        session_id=session_id,
        watermark_id=watermark_id,
        timestamp=timestamp,
        signature=signature,
    )

    # --------------------------------------------------------
    # Store distributed ledger event
    # --------------------------------------------------------

    ledger_event = {
        "document_id": document_id,
        "recipient_id": recipient_id,
        "session_id": session_id,
        "watermark_id": watermark_id,
        "timestamp": timestamp,
        "signature": base64.b64encode(
            signature
        ).decode("utf-8"),
    }

    try:
        add_ledger_entry(
            ledger_event
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Ledger write failed: {exc}",
        )

    # --------------------------------------------------------
    # Return watermarked PDF
    # --------------------------------------------------------

    filename = document[1] or "document.pdf"

    return Response(
        content=watermarked_pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'attachment; '
                f'filename="watermarked_{filename}"'
            ),
            "X-Document-ID": document_id,
            "X-Recipient-ID": recipient_id,
            "X-Session-ID": session_id,
            "X-Watermark-ID": watermark_id,
            "X-Timestamp": timestamp,
        },
    )


# ============================================================
# INVESTIGATE LEAKED DOCUMENT
# ============================================================

@app.post("/investigate")
async def investigate_document(
    file: UploadFile = File(...),
):
    """
    Investigate a leaked PDF.
    """

    # --------------------------------------------------------
    # Validate PDF
    # --------------------------------------------------------

    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported",
        )

    leaked_pdf = await file.read()

    if not leaked_pdf:
        raise HTTPException(
            status_code=400,
            detail="Uploaded PDF is empty",
        )

    # --------------------------------------------------------
    # Extract watermark
    # --------------------------------------------------------

    try:
        watermark_id = extract_watermark(
            leaked_pdf
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to read PDF watermark: "
                f"{exc}"
            ),
        )

    # --------------------------------------------------------
    # No watermark
    # --------------------------------------------------------

    if watermark_id is None:
        return {
            "status": "failed",
            "watermark_match": False,
            "message": "No forensic watermark found",
        }

    # --------------------------------------------------------
    # Find matching database event
    # --------------------------------------------------------

    event = get_decryption_event_by_watermark(
        watermark_id
    )

    if not event:
        return {
            "status": "not_found",
            "watermark_match": True,
            "watermark_id": watermark_id,
            "message": (
                "Watermark found, but no matching "
                "decryption event exists"
            ),
        }

    # --------------------------------------------------------
    # Event fields
    # --------------------------------------------------------

    document_id = event[0]
    recipient_id = event[1]
    session_id = event[2]
    stored_watermark_id = event[3]
    timestamp = event[4]
    signature = event[5]

    # --------------------------------------------------------
    # Decode signature
    # --------------------------------------------------------

    try:
        signature = decode_stored_bytes(
            signature
        )
    except Exception:
        signature = b""

    # --------------------------------------------------------
    # Get recipient
    # --------------------------------------------------------

    recipient = get_recipient(
        recipient_id
    )

    if not recipient:
        return {
            "status": "verification_failed",
            "watermark_match": True,
            "watermark_id": watermark_id,
            "message": (
                "Recipient associated with the event "
                "could not be found"
            ),
        }

    # --------------------------------------------------------
    # ML-DSA public key
    # --------------------------------------------------------

    public_key_text = recipient[3]

    if not public_key_text:
        return {
            "status": "verification_failed",
            "watermark_match": True,
            "watermark_id": watermark_id,
            "message": (
                "Recipient has no stored "
                "ML-DSA public key"
            ),
        }

    try:
        public_key = decode_public_key(
            public_key_text,
            expected_size=1952,
        )
    except Exception as exc:
        return {
            "status": "verification_failed",
            "watermark_match": True,
            "watermark_id": watermark_id,
            "message": (
                "Invalid ML-DSA public key: "
                f"{exc}"
            ),
        }

    # --------------------------------------------------------
    # Recreate signed event
    # --------------------------------------------------------

    event_message = create_event_message(
        document_id,
        recipient_id,
        session_id,
        stored_watermark_id,
        timestamp,
    )

    # --------------------------------------------------------
    # Verify ML-DSA signature
    # --------------------------------------------------------

    try:
        signature_valid = verify_signature(
            event_message,
            signature,
            public_key,
        )
    except Exception:
        signature_valid = False

    # --------------------------------------------------------
    # Verify distributed ledger
    # --------------------------------------------------------

    ledger_valid = verify_ledger()

    # --------------------------------------------------------
    # Final verification
    # --------------------------------------------------------

    watermark_match = (
        watermark_id == stored_watermark_id
    )

    verification_success = (
        watermark_match
        and signature_valid
        and ledger_valid
    )

    if verification_success:
        status = "success"

        message = (
            "Watermark matched and cryptographic "
            "provenance verified"
        )
    else:
        status = "verification_failed"

        message = (
            "Watermark matched, but cryptographic "
            "or ledger verification failed"
        )

    return {
        "status": status,
        "watermark_match": watermark_match,
        "watermark_id": watermark_id,
        "document_id": document_id,
        "recipient_id": recipient_id,
        "recipient_name": recipient[1],
        "recipient_email": recipient[2],
        "session_id": session_id,
        "timestamp": timestamp,
        "signature_valid": signature_valid,
        "signature_algorithm": "ML-DSA-65",
        "ledger_valid": ledger_valid,
        "ledger_file": str(LEDGER_FILE),
        "message": message,
    }


# ============================================================
# GET LEDGER
# ============================================================

@app.get("/ledger")
def get_ledger():
    """
    Return the current distributed ledger.

    The ledger entries are stored across NODE-01,
    NODE-02 and NODE-03.

    The ledger module returns the quorum-agreed chain.
    """

    try:
        entries = get_ledger_entries()

        ledger_valid = verify_ledger()

        return {
            "status": "success",
            "ledger_valid": ledger_valid,
            "entry_count": len(entries),
            "entries": entries,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to read ledger: {exc}",
        )


# ============================================================
# CLEAR LEDGER
# ============================================================

@app.delete("/ledger")
def clear_ledger():
    """
    Clear all distributed ledger records.

    Removes all replica files so the next successful
    decryption starts a fresh ledger chain from GENESIS.
    """

    try:
        cleared_files = []

        # ----------------------------------------------------
        # Remove distributed node ledgers
        # ----------------------------------------------------

        for node_id in NODE_IDS:

            node_file = (
                LEDGER_FILE.parent
                / f"{node_id}.json"
            )

            if node_file.exists():
                node_file.unlink()
                cleared_files.append(
                    str(node_file)
                )

        # ----------------------------------------------------
        # Remove legacy ledger file if present
        # ----------------------------------------------------

        if LEDGER_FILE.exists():
            LEDGER_FILE.unlink()

            cleared_files.append(
                str(LEDGER_FILE)
            )

        return {
            "status": "success",
            "ledger_valid": True,
            "entries": [],
            "entry_count": 0,
            "cleared_files": cleared_files,
            "message": (
                "Ledger cleared successfully. "
                "Future decryption operations will be "
                "recorded again from GENESIS."
            ),
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to clear ledger: {error}",
        )


# ============================================================
# RUN DIRECTLY
# ============================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )