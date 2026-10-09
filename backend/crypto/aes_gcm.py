import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def generate_key():
    """Generate a secure 256-bit AES key."""
    return AESGCM.generate_key(bit_length=256)


def encrypt_data(data: bytes, key: bytes):
    """Encrypt data using AES-256-GCM."""
    nonce = os.urandom(12)
    aesgcm = AESGCM(key)

    ciphertext = aesgcm.encrypt(nonce, data, None)

    return nonce, ciphertext


def decrypt_data(nonce: bytes, ciphertext: bytes, key: bytes):
    """Decrypt AES-256-GCM encrypted data."""
    aesgcm = AESGCM(key)

    return aesgcm.decrypt(nonce, ciphertext, None)
def encrypt_file(file_data: bytes, key: bytes):
    """Encrypt an entire file using AES-256-GCM."""
    nonce, ciphertext = encrypt_data(file_data, key)

    return {
        "nonce": nonce,
        "ciphertext": ciphertext
    }