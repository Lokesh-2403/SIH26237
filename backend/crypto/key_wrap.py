import os

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def derive_key_encryption_key(
    shared_secret: bytes,
    document_id: str,
    recipient_id: str
):
    """
    Derive a 256-bit key-encryption key from the ML-KEM
    shared secret using HKDF-SHA-256.
    """

    context = (
        f"SIH26237|{document_id}|{recipient_id}"
    ).encode("utf-8")

    return HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=context
    ).derive(shared_secret)


def wrap_document_key(
    document_key: bytes,
    key_encryption_key: bytes
):
    """
    Encrypt/wrap the AES document key using AES-256-GCM.
    """

    nonce = os.urandom(12)

    aesgcm = AESGCM(
        key_encryption_key
    )

    wrapped_key = aesgcm.encrypt(
        nonce,
        document_key,
        None
    )

    return wrapped_key, nonce


def unwrap_document_key(
    wrapped_key: bytes,
    nonce: bytes,
    key_encryption_key: bytes
):
    """
    Recover the original AES document key.
    """

    aesgcm = AESGCM(
        key_encryption_key
    )

    return aesgcm.decrypt(
        nonce,
        wrapped_key,
        None
    )