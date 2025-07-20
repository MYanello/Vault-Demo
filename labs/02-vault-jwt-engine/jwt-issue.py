import base64
import json
import os
import time
from textwrap import indent

import requests
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

VAULT_ADDR = os.getenv("VAULT_ADDR")
VAULT_TOKEN = os.getenv("VAULT_TOKEN")
VAULT_HEADERS = {
    "X-Vault-Token": VAULT_TOKEN,
    "Content-Type": "application/json",
}


def get_public_key(key_name="django") -> str:
    url = f"{VAULT_ADDR}/v1/transit/keys/{key_name}"
    response = requests.get(url, headers=VAULT_HEADERS, timeout=10)
    print(f"Public key response {response.json()}")
    pubkey_b64 = response.json()["data"]["keys"]["1"]["public_key"]
    print(f"Public key for {key_name} JWTs:\n  {pubkey_b64}")

    # For ED25519, create proper PEM format
    # ED25519 public keys from Vault are raw
    # 32-byte keys that need ASN.1 wrapping
    raw_key_bytes = base64.b64decode(pubkey_b64)
    # Create Ed25519 public key object from raw bytes
    ed25519_pubkey = ed25519.Ed25519PublicKey.from_public_bytes(raw_key_bytes)
    pubkey_pem = ed25519_pubkey.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()

    print("Public PEM Key:")
    print(f"{indent(pubkey_pem, '  ')}")
    return pubkey_pem


def sign_jwt(signing_input, key_name="django") -> str:
    url = f"{VAULT_ADDR}/v1/transit/sign/{key_name}"
    signing_input_b64 = base64.b64encode(signing_input.encode()).decode()
    payload = {"input": signing_input_b64}
    response = requests.post(
        url, headers=VAULT_HEADERS, json=payload, timeout=10
    )
    signature = response.json()["data"]["signature"]

    raw_signature = signature.replace("vault:v1:", "")
    signature_bytes = base64.b64decode(raw_signature)
    signature_b64url = (
        base64.urlsafe_b64encode(signature_bytes).decode().rstrip("=")
    )
    return signature_b64url


def form_jwt(payload, key_name="django") -> str:
    header = {
        "alg": "EdDSA",  # ed25519
        "typ": "JWT",
    }
    print(f"JWT Header: {json.dumps(header, indent=2)}")
    print(f"JWT Payload: {json.dumps(payload, indent=2)}")
    header_b64 = base64url_encode(header)
    payload_b64 = base64url_encode(payload)

    signing_input = f"{header_b64}.{payload_b64}"
    print(f"Signing Input: \n  {signing_input}")
    signature_b64 = sign_jwt(signing_input)
    print(f"JWT Signature:\n  {signature_b64}")
    full_jwt = f"{header_b64}.{payload_b64}.{signature_b64}"
    print(f"Fully formed JWT Header:\n  {full_jwt}")
    return full_jwt


def base64url_encode(data) -> str:
    data = json.dumps(data, separators=(",", ":")).encode()
    return (
        base64.urlsafe_b64encode(data).decode().rstrip("=")
    )  # jwt spec says no padding


def validate_jwt(jwt_token, public_key_pem) -> bool:
    parts = jwt_token.split(".")
    if len(parts) != 3:  # need header, payload, and sig
        print("Invalid JWT format")
        return False

    header_b64, payload_b64, signature_b64 = parts
    signing_input = f"{header_b64}.{payload_b64}"
    signature_padded = signature_b64 + "=" * (
        4 - len(signature_b64) % 4
    )  # re add the padding if needed
    signature_bytes = base64.urlsafe_b64decode(signature_padded)

    public_key = serialization.load_pem_public_key(public_key_pem.encode())
    if isinstance(public_key, ed25519.Ed25519PublicKey):
        public_key.verify(signature_bytes, signing_input.encode())
        print("JWT signature validation PASSED!")
        return True
    else:
        print("Unable to validate JWT")
        return False


if __name__ == "__main__":
    payload = {
        "sub": "demo-user",  # subject
        "name": "Marcus Yanello",
        "org": "Rescale",
        "is_admin": True,
        "iat": int(time.time()),  # issued at
        "exp": int(time.time()) + 3600,  # expires after an hour
        "iss": "vault-demo",  # issued by, should typically be a url that we can
        # access the jwks endpoint at, but for this demo we can use this
        "aud": "my-demo-service",  # audience / consumer
    }
    print(f"Payload: {json.dumps(payload, indent=2)}")
    input()
    pubkey_pem = get_public_key()
    input()
    jwt = form_jwt(payload)
    input()
    validate_jwt(jwt, pubkey_pem)
