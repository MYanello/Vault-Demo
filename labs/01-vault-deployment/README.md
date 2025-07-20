# Lab 01: Vault Deployment

We will start with a basic Vault deployment. It will be exposed via our Metallb loadbalancer on port 8080.
In production there will be various improvements we'd need to make such as HA, https, and auto unseal / unseal keys.

Let's start with
```bash
kubectl get nodes
``` 
to verify we're using our local K3D cluster, and not about to deploy to prod-infra.

To deploy Vault simply run:
```bash
kubectl apply -f ./labs/01-vault-deployment/vault.yaml
```
Then wait for the pod to be ready:
```bash
kubectl rollout status -n vault deployment/vault
```
And when it is ready we can get the URL to access it with:
```bash
kubectl get svc -n vault vault -o jsonpath='http://{.status.loadBalancer.ingress[0].ip}:{.spec.ports[0].port}{"\n"}'
```
The default login token is simply `root`.