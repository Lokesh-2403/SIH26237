from backend.crypto.mlkem import MLKEM
from backend.crypto.key_storage import (
    save_mlkem_keys,
    load_mlkem_public_key,
    load_mlkem_secret_key,
    mlkem_key_exists,
)


RECIPIENT_ID = "OFFICER_TEST"


def main():
    print("Generating ML-KEM-768 key pair...")

    mlkem = MLKEM()
    keypair = mlkem.generate_keypair()

    save_mlkem_keys(
        RECIPIENT_ID,
        keypair.public_key,
        keypair.secret_key,
    )

    print("Keys saved.")
    print(
        "Key pair exists:",
        mlkem_key_exists(RECIPIENT_ID),
    )

    public_key = load_mlkem_public_key(RECIPIENT_ID)
    secret_key = load_mlkem_secret_key(RECIPIENT_ID)

    if public_key is None:
        raise RuntimeError("ML-KEM public key was not loaded.")

    if secret_key is None:
        raise RuntimeError("ML-KEM secret key was not loaded.")

    print("Public key loaded:", True)
    print("Secret key loaded:", True)
    print("Public key size:", len(public_key))
    print("Secret key size:", len(secret_key))

    print("\nTesting encapsulation...")

    ciphertext, sender_secret = mlkem.encapsulate(
        public_key
    )

    print("KEM ciphertext size:", len(ciphertext))

    print("Testing decapsulation...")

    recipient_secret = mlkem.decapsulate(
        secret_key,
        ciphertext,
    )

    print(
        "Shared secrets match:",
        sender_secret == recipient_secret,
    )

    if sender_secret != recipient_secret:
        raise RuntimeError(
            "ML-KEM key exchange verification failed."
        )

    print("\nML-KEM STORAGE TEST: PASS")


if __name__ == "__main__":
    main()
