import oqs


ALGORITHM = "ML-DSA-65"


def generate_keys():
    """Generate an ML-DSA-65 signing key pair."""

    signer = oqs.Signature(ALGORITHM)

    public_key = signer.generate_keypair()
    secret_key = signer.export_secret_key()

    return public_key, secret_key


def sign_message(message: bytes, secret_key: bytes):
    """Sign a message using ML-DSA-65."""

    signer = oqs.Signature(ALGORITHM, secret_key)

    signature = signer.sign(message)

    return signature


def verify_signature(message: bytes, signature: bytes, public_key: bytes):
    """Verify an ML-DSA-65 signature."""

    verifier = oqs.Signature(ALGORITHM)

    return verifier.verify(message, signature, public_key)


def create_event_message(
    document_id: str,
    recipient_id: str,
    session_id: str,
    watermark_id: str,
    timestamp: str
):
    """Create a consistent message representing a decryption event."""

    return (
        f"{document_id}|"
        f"{recipient_id}|"
        f"{session_id}|"
        f"{watermark_id}|"
        f"{timestamp}"
    ).encode("utf-8")