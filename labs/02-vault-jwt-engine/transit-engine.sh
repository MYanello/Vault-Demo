#!/bin/bash -ex

echo "Setting up Vault to issue JWTs for Django application (simplified)..."

if [ -z "$VAULT_ADDR" ]; then
    export VAULT_ADDR=$(kubectl get svc -n vault vault -o jsonpath='http://{.status.loadBalancer.ingress[0].ip}:{.spec.ports[0].port}')
fi
if [ -z "$VAULT_TOKEN" ]; then
    export VAULT_TOKEN=root
fi

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
    
# Get our public key
export PUBLIC_KEY=$(vault read -format=json transit/export/signing-key/django/latest | jq -r '.data.keys["1"]')