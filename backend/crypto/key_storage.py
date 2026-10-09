from pathlib import Path


KEY_DIR = Path("backend/crypto/keys")


# =========================================================
# ML-DSA SECRET KEY
# =========================================================

def save_secret_key(
    recipient_id: str,
    secret_key: bytes,
):
    KEY_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    key_file = KEY_DIR / f"{recipient_id}.key"

    key_file.write_bytes(secret_key)

    return key_file


def load_secret_key(recipient_id: str):
    key_file = KEY_DIR / f"{recipient_id}.key"

    if not key_file.exists():
        return None

    return key_file.read_bytes()


def key_exists(recipient_id: str):
    key_file = KEY_DIR / f"{recipient_id}.key"

    return key_file.exists()


# =========================================================
# ML-KEM KEY STORAGE
# =========================================================

def save_mlkem_keys(
    recipient_id: str,
    public_key: bytes,
    secret_key: bytes,
):
    """
    Save an ML-KEM-768 public/private key pair.
    """

    KEY_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    public_file = KEY_DIR / f"{recipient_id}_kem_public.key"
    secret_file = KEY_DIR / f"{recipient_id}_kem.key"

    public_file.write_bytes(public_key)
    secret_file.write_bytes(secret_key)

    return public_file, secret_file


def load_mlkem_public_key(recipient_id: str):
    public_file = KEY_DIR / f"{recipient_id}_kem_public.key"

    if not public_file.exists():
        return None

    return public_file.read_bytes()


def load_mlkem_secret_key(recipient_id: str):
    secret_file = KEY_DIR / f"{recipient_id}_kem.key"

    if not secret_file.exists():
        return None

    return secret_file.read_bytes()


def mlkem_key_exists(recipient_id: str):
    public_file = KEY_DIR / f"{recipient_id}_kem_public.key"
    secret_file = KEY_DIR / f"{recipient_id}_kem.key"

    return (
        public_file.exists()
        and secret_file.exists()
    )


# =========================================================
# BACKWARDS-COMPATIBLE ML-KEM SECRET-KEY API
# =========================================================

def save_kem_secret_key(
    recipient_id: str,
    secret_key: bytes,
):
    KEY_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    key_file = KEY_DIR / f"{recipient_id}_kem.key"

    key_file.write_bytes(secret_key)

    return key_file


def load_kem_secret_key(recipient_id: str):
    return load_mlkem_secret_key(recipient_id)


def kem_key_exists(recipient_id: str):
    return load_mlkem_secret_key(recipient_id) is not None