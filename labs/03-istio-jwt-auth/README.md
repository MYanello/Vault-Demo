Now we'll deploy Istio to sit in front of our service and validate the JWT was signed by Vault before allowing the request to pass.

First let's set up a service to provide the JWKs formatted keys and verify it's working:
```
kubectl apply -f jwks.yaml -n vault
export JWKS_ADDR=$(kubectl get svc -n jwks jwks -o jsonpath='http://{.status.loadBalancer.ingress[0].ip}:{.spec.ports[0].port}')
curl $JWKS_ADDR/.well-known/jwks.json
```

```
kubectl apply -f istio.yaml -n istio-system
```

Deploy some basic workloads with istio-injection enabled to test with
```
kubectl apply -f test-workloads.yaml
```

Validate that our workloads can communicate through the Istio sidecar
```
kubectl exec "$(kubectl get pod -l app=curl -n client -o jsonpath={.items..metadata.name})" -c curl -n client -- curl "http://httpbin.backend:8000/ip" -sS
```

Now setup Istio to check the JWT before allowing the request:
```
kubectl apply -f auth.yaml -n backend
```
```
kubectl rollout restart -n backend deploy httpbin
```
```
kubectl exec "$(kubectl get pod -l app=curl -n client -o jsonpath={.items..metadata.name})" -c curl -n client -- curl "http://httpbin.backend:8000/headers" -sS
```

Let's get a JWT so we can access our service!
```
export ADMIN_TOKEN=$(python jwt-issue.py --is-admin)
```
```
kubectl exec "$(kubectl get pod -l app=curl -n client -o jsonpath={.items..metadata.name})" -c curl -n client -- curl "http://httpbin.backend:8000/headers" -sS  -H "Authorization: Bearer $ADMIN_TOKEN"
```
```
export USER_TOKEN=$(python jwt-issue.py)
```
```
kubectl exec "$(kubectl get pod -l app=curl -n client -o jsonpath={.items..metadata.name})" -c curl -n client -- curl "http://httpbin.backend:8000/headers" -sS  -H "Authorization: Bearer $USER_TOKEN"
```
We should see that our admin token is able to auth and get the response, while the user token 403s.