#!/bin/bash -ex

export VAULT_ADDR=$(kubectl get svc -n vault vault -o jsonpath='http://{.status.loadBalancer.ingress[0].ip}:{.spec.ports[0].port}')
export VAULT_TOKEN=root

# Enable Vault transit engine
vault secrets enable transit

# Create a key for Django to use for signing JWTs
vault write -f transit/keys/django \
    type="ed25519" \
    exportable="true"

# Sign our data
DATA_B64=$(echo -n "Hello World" | base64)
RSA_SIG=$(vault write -field=signature transit/sign/django input="$DATA_B64")

# Verify signature
vault write transit/verify/django \
    input="$DATA_B64" \
    signature="$RSA_SIG" && echo "RSA signature test succeed" || echo "RSA signature test failed"
