import base64
import json
import requests
import os
from flask import Flask, jsonify

app = Flask(__name__)

VAULT_ADDR = "http://172.18.0.2:8080" #"vault.vault.svc.cluster.local"
VAULT_TOKEN = "root"
VAULT_HEADERS = {'X-Vault-Token': VAULT_TOKEN, 'Content-Type': 'application/json'}

def get_vault_public_key(key_name="django"):
    """Get public key from Vault transit engine"""
    url = f"{VAULT_ADDR}/v1/transit/keys/{key_name}"
    response = requests.get(url, headers=VAULT_HEADERS)
    data = response.json()['data']
    pubkey_b64 = data['keys']['1']['public_key']
    
    # Convert to JWKS format
    jwks = {
        "keys": [
            {
                "kty": "OKP",
                "crv": "Ed25519", 
                "use": "sig",
                "kid": f"{key_name}-1",
                "x": pubkey_b64.replace('=', ''),  # Remove padding for JWK format
                "alg": "EdDSA"
            }
        ]
    }
    return jwks

@app.route('/.well-known/jwks.json')
def jwks_endpoint():
    """Standard JWKS endpoint"""
    return jsonify(get_vault_public_key())

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)