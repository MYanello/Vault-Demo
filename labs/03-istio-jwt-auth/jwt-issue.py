import base64
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519
import os
import requests
import time
import json
import argparse

VAULT_ADDR = os.getenv("VAULT_ADDR")
VAULT_TOKEN = os.getenv("VAULT_TOKEN")
VAULT_HEADERS = {'X-Vault-Token': VAULT_TOKEN, 'Content-Type': 'application/json'}

def get_public_key(key_name="django") -> str:
    url = f"{VAULT_ADDR}/v1/transit/keys/{key_name}"
    response = requests.get(url, headers=VAULT_HEADERS)
    pubkey_b64 = response.json()['data']['keys']['1']['public_key']

    # For ED25519, create proper PEM format
    # ED25519 public keys from Vault are raw 32-byte keys that need ASN.1 wrapping
    raw_key_bytes = base64.b64decode(pubkey_b64)
    # Create Ed25519 public key object from raw bytes
    ed25519_pubkey = ed25519.Ed25519PublicKey.from_public_bytes(raw_key_bytes)
    pubkey_pem = ed25519_pubkey.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode()

    return pubkey_pem

def sign_jwt(signing_input, key_name="django") -> str:
    url = f"{VAULT_ADDR}/v1/transit/sign/{key_name}"
    signing_input_b64 = base64.b64encode(signing_input.encode()).decode()
    payload = {
        "input": signing_input_b64
    }
    response = requests.post(url, headers=VAULT_HEADERS, json=payload)
    signature = response.json()['data']['signature']

    raw_signature = signature.replace('vault:v1:', '')
    signature_bytes = base64.b64decode(raw_signature)
    signature_b64url = base64.urlsafe_b64encode(signature_bytes).decode().rstrip('=')
    return signature_b64url

def form_jwt(payload, key_name="django") -> str:
    header = {
        "alg": "EdDSA", # ed25519
        "typ": "JWT"
    }
    header_b64 = base64url_encode(header)
    payload_b64 = base64url_encode(payload)

    signing_input = f"{header_b64}.{payload_b64}"
    signature_b64 = sign_jwt(signing_input)
    full_jwt = f"{header_b64}.{payload_b64}.{signature_b64}"
    return full_jwt

def base64url_encode(data) -> str:
    data = json.dumps(data, separators=(',', ':')).encode()
    return base64.urlsafe_b64encode(data).decode().rstrip('=') # jwt spec says no padding

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--is-admin', action='store_true', help='Set is_admin claim to true')
    args = parser.parse_args()
    payload = {
        "sub": "demo-user", # subject
        "name": "Marcus Yanello",
        "org": "Rescale",
        "is_admin": str(args.is_admin),
        "iat": int(time.time()), # issued at
        "exp": int(time.time()) + 3600, # expires after an hour
        "iss": "vault-demo", # issued by
        "aud": "my-demo-service" # audience / consumer
    }
    pubkey_pem = get_public_key()
    jwt = form_jwt(payload)
    print(jwt)
