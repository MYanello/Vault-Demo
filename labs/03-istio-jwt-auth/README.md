Now we'll deploy Istio to sit in front of our service and validate the JWT was signed by Vault before allowing the request to pass.

Make sure we still have our Vault env vars set up correctly:
```bash
export VAULT_ADDR=$(kubectl get svc -n vault vault -o jsonpath='http://{.status.loadBalancer.ingress[0].ip}:{.spec.ports[0].port}')
if [ -z "$VAULT_TOKEN" ]; then
    export VAULT_TOKEN=root
fi
```

First let's set up a service to provide the JWKs formatted keys and verify it's working. If we use the Vault OIDC Engine instead of Transit Engine this step isn't necessary.
```bash
kubectl apply -f ./labs/03-istio-jwt-auth/jwks.yaml -n vault
```
```bash
export JWKS_ADDR=$(kubectl get svc -n vault jwks -o jsonpath='http://{.status.loadBalancer.ingress[0].ip}:{.spec.ports[0].port}')
echo "JWKS address: ${JWKS_ADDR}"
```
Test it's working:
```bash
curl $JWKS_ADDR/.well-known/jwks.json
```

Deploy Istiod and Istio-Base with no modifications to the upstream yaml. Source info can be found in `./labs/03/istio-jwt-auth/kustomization.yaml`.
```bash
kubectl apply -f ./labs/03-istio-jwt-auth/istio.yaml -n istio-system
```

Deploy some basic workloads with istio sidecar injection enabled to test with. This is two namespaces labeled istio-injection=true. The *client* namespace has a *curl* pod, and the *backend* namespace has an *httpbin* pod that responds to various curl requests with info. In our case we'll use the **/headers** endpoint to have our http requests headers sent back to us to see what our service is getting.
```bash
kubectl apply -f ./labs/03-istio-jwt-auth/test-workloads.yaml
```

Validate that our workloads can communicate through the Istio sidecar:
```bash
kubectl exec "$(kubectl get pod -l app=curl -n client -o jsonpath={.items..metadata.name})" -c curl -n client -- curl "http://httpbin.backend:8000/headers" -sS
```

Now setup Istio to check the JWT before allowing the request:
```bash
kubectl apply -f ./labs/03-istio-jwt-auth/auth.yaml -n backend
```

Check that now we are being blocked from our backend:
```bash
kubectl exec "$(kubectl get pod -l app=curl -n client -o jsonpath={.items..metadata.name})" -c curl -n client -- curl "http://httpbin.backend:8000/headers" -sS
```

Let's get a JWT so we can access our service again!
```bash
export ADMIN_TOKEN=$(python ./labs/03-istio-jwt-auth/jwt-issue.py --is-admin)
echo "Admin JWT: ${ADMIN_TOKEN}"
```
```bash
kubectl exec "$(kubectl get pod -l app=curl -n client -o jsonpath={.items..metadata.name})" -c curl -n client -- curl "http://httpbin.backend:8000/headers" -sS  -H "Authorization: Bearer $ADMIN_TOKEN"
```
What happens if we provide a valid, signed JWT that doesn't match our rules?
```bash
export USER_TOKEN=$(python ./labs/03-istio-jwt-auth/jwt-issue.py)
echo "User JWT: ${USER_TOKEN}"
```
```bash
kubectl exec "$(kubectl get pod -l app=curl -n client -o jsonpath={.items..metadata.name})" -c curl -n client -- curl "http://httpbin.backend:8000/headers" -sS  -H "Authorization: Bearer $USER_TOKEN"
```
We should see that our admin token is able to pass authz and get the response, while the user token 403s.  
Finally, what if we have a signed JWT but it's not signed by us? Let's use a JWT from https://jwt.io/
```bash
export BAD_TOKEN=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiYWRtaW4iOnRydWUsImlhdCI6MTUxNjIzOTAyMn0.KMUFsIDTnFmyG3nMiGM6H9FNFUROf3wh7SmqJp-QV30
kubectl exec "$(kubectl get pod -l app=curl -n client -o jsonpath={.items..metadata.name})" -c curl -n client -- curl "http://httpbin.backend:8000/headers" -sS  -H "Authorization: Bearer $BAD_TOKEN"
```
We see that the Issuer is not configured. If we were to decide "Hey we trust these guys at jwt.io, let's accept their tokens" we could tell Istio about their JWKS endpoint or add their public key to our own JWKS endpoint. Of course, we shouldn't do that because jwt.io does no validation at all of who is forming the payload, whereas on our frontend we can be sure you've logged into a valid account before crafting your JWT payload to sign and use for requests.