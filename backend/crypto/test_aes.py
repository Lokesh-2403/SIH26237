from aes_gcm import generate_key, encrypt_data, decrypt_data


message = b"SIH26237 Confidential Document"

key = generate_key()

nonce, ciphertext = encrypt_data(message, key)

decrypted = decrypt_data(nonce, ciphertext, key)

print("Original :", message)
print("Encrypted:", ciphertext)
print("Decrypted:", decrypted)

if decrypted == message:
    print("AES-256-GCM TEST: SUCCESS")
else:
    print("AES-256-GCM TEST: FAILED")