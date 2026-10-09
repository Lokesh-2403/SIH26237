import oqs


ALGORITHM = "ML-KEM-768"


class MLKEMKeyPair:
    def __init__(self, public_key: bytes, secret_key: bytes):
        self.public_key = public_key
        self.secret_key = secret_key


class MLKEM:
    """
    ML-KEM-768 wrapper compatible with the project tests.
    """

    def __init__(self):
        self.algorithm = ALGORITHM

    def generate_keypair(self):
        kem = oqs.KeyEncapsulation(self.algorithm)

        public_key = kem.generate_keypair()
        secret_key = kem.export_secret_key()

        return MLKEMKeyPair(
            public_key=public_key,
            secret_key=secret_key,
        )

    def encapsulate(self, public_key: bytes):
        kem = oqs.KeyEncapsulation(self.algorithm)

        ciphertext, shared_secret = kem.encap_secret(
            public_key
        )

        return ciphertext, shared_secret

    def decapsulate(
        self,
        secret_key: bytes,
        ciphertext: bytes,
    ):
        kem = oqs.KeyEncapsulation(
            self.algorithm,
            secret_key,
        )

        return kem.decap_secret(ciphertext)


# ---------------------------------------------------------
# Backwards-compatible functional API
# ---------------------------------------------------------

def generate_keys():
    mlkem = MLKEM()
    keypair = mlkem.generate_keypair()

    return keypair.public_key, keypair.secret_key


def encapsulate(public_key: bytes):
    return MLKEM().encapsulate(public_key)


def decapsulate(ciphertext: bytes, secret_key: bytes):
    return MLKEM().decapsulate(
        secret_key,
        ciphertext,
    )