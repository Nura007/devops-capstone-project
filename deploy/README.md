# Deploy the Accounts service

The application listens on port 8080 as a non-root user. The Deployment reads
database credentials from a `postgresql` Secret and the session key from an
`accounts-config` Secret; no live credentials belong in this repository.

In the IBM lab, provision PostgreSQL using the supplied
`postgresql-ephemeral-template.json` and retain its generated `postgresql` Secret.
Its required keys are `database-user`, `database-password`, and `database-name`.
For a local cluster, create a Secret with those keys, then apply
`deploy/postgresql.yaml`. This optional local database uses a PVC with the
cluster's default storage class.

Create the application secret using a generated random value:

```sh
oc create secret generic accounts-config \
  --from-literal=secret-key="$(python -c 'import secrets; print(secrets.token_hex(32))')"
```

Build, tag and push an actual image, then substitute its complete name into the
Deployment before applying it:

```sh
docker build -t accounts:1 .
docker tag accounts:1 us.icr.io/$SN_ICR_NAMESPACE/accounts:1
docker push us.icr.io/$SN_ICR_NAMESPACE/accounts:1
oc set image --local -f deploy/deployment.yaml \
  accounts=us.icr.io/$SN_ICR_NAMESPACE/accounts:1 -o yaml | oc apply -f -
oc apply -f deploy/service.yaml
oc rollout status deployment/accounts --timeout=180s
oc get deployments,pods,replicasets,services -l app=accounts
oc port-forward service/accounts 8080:8080
```

Open `http://localhost:8080/` and `/health`. Save actual `docker images` and
`oc get deployments,pods,replicasets,services` output as grading evidence. For a
local Kubernetes cluster, replace `oc` with `kubectl` and use its reachable image
registry. The sample Deployment uses `accounts:1` until the real image is supplied.
