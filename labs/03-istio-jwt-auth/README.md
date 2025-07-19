Now we'll deploy Istio to sit in front of our service and validate the JWT was signed by Vault before allowing the request to pass.

First let's set up a service to provide the JWKs formatted keys:
```
kubectl apply -f jwks.yaml -n vault
```

```
kubectl apply -f istio.yaml
```

Deploy some basic workloads with istio-injection enabled to test with
```
kubectl apply -f test-workloads.yaml
```

Validate that our workloads can communicate through the Istio sidecar
```
kubectl exec "$(kubectl get pod -l app=curl -n client -o jsonpath={.items..metadata.name})" -c curl -n client -- curl "http://httpbin.backend:8000/ip" -sS -o /dev/null -w "%{http_code}\n"
```