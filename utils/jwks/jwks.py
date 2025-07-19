import os

import requests
from flask import Flask

app = Flask(__name__)

VAULT_ADDR = (
    os.getenv("VAULT_ADDR") or "http://vault.vault.svc.cluster.local:8200"
)
VAULT_TOKEN = os.getenv("VAULT_TOKEN") or "root"
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

    # Convert to JWKS format
    jwks = {
        "keys": [
            {
                "kty": "OKP",
                "crv": "Ed25519",
                "use": "sig",
                "kid": f"{key_name}-1",
                "x": pubkey_b64.replace(
                    "=", ""
                ),  # Remove padding for JWK format
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
