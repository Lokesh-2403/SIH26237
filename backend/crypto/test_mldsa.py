from backend.crypto.mldsa import  (
    generate_keys,
    sign_message,
    verify_signature,
    create_event_message,
)


# Generate a key pair
public_key, secret_key = generate_keys()

# Create a message
message = create_event_message(
    "DOC-TEST-001",
    "OFFICER-003",
    "SESSION-TEST-001",
    "WM-TEST-001",
    "2026-09-18T00:00:00Z",
)

# Sign the original message
signature = sign_message(message, secret_key)

# Original message must verify
assert verify_signature(
    message,
    signature,
    public_key
) is True

print("ORIGINAL SIGNATURE TEST: SUCCESS")


# Modify the message
tampered_message = create_event_message(
    "DOC-TEST-001",
    "TAMPERED-OFFICER",
    "SESSION-TEST-001",
    "WM-TEST-001",
    "2026-09-18T00:00:00Z",
)

# Tampered message must fail verification
assert verify_signature(
    tampered_message,
    signature,
    public_key
) is False

print("TAMPERED SIGNATURE TEST: SUCCESS")
