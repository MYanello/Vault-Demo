import base64
import os

import requests
from flask import Flask

app = Flask(__name__)

VAULT_ADDR = os.getenv(
    "VAULT_ADDR", "http://vault.vault.svc.cluster.local:8200"
)
VAULT_TOKEN = os.getenv("VAULT_TOKEN", "root")
VAULT_HEADERS = {
    "X-Vault-Token": VAULT_TOKEN,
    "Content-Type": "application/json",
}


@app.route("/.well-known/jwks.json")
def get_vault_public_key(key_name="django"):
    url = f"{VAULT_ADDR}/v1/transit/keys/{key_name}"
    response = requests.get(url, headers=VAULT_HEADERS, timeout=10)
    data = response.json()["data"]
    pubkey_b64 = data["keys"]["1"]["public_key"]
    decoded_bytes = base64.b64decode(pubkey_b64)
    enc_pubkey_b64 = (
        base64.urlsafe_b64encode(decoded_bytes).decode().rstrip("=")
    )
    # Convert to JWKS format
    jwks = {
        "keys": [
            {
                "kty": "OKP",
                "crv": "Ed25519",
                "use": "sig",
                "kid": f"{key_name}-1",
                "x": enc_pubkey_b64,
                "alg": "EdDSA",
            }
        ]
    }
    return jwks


@app.route("/health")
def get_health():
    return "OK", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
