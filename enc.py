import secrets

# Generate a 256-bit key (32 bytes)
secret_key = secrets.token_hex(32)
print(secret_key)
