# Continuous delivery

The pipeline runs **init → clone → lint/tests → build → deploy**. Lint and tests
must both pass before Buildah can build and push the image. Deployment waits for a
successful Kubernetes rollout. Runtime inputs are `repo-url`, `branch`, and
`build-image`; `registry-tls-verify` defaults to `true` and is changed only for an
isolated local HTTP registry. Tests use a disposable SQLite database, while the
application deployed by the pipeline uses PostgreSQL.

## Local Kubernetes environment

The project supports the local Kubernetes option described in IBM's starter
repository. The local environment uses k3d 5.9.0, a dedicated `capstone` cluster,
registry `capstone-registry:5000` (host port 32000), namespace `capstone`, and
Tekton Pipelines 1.18.0. Keep its kubeconfig separate from other clusters.

Install Tekton from its official pinned release, then install the catalog Tasks:

```sh
kubectl apply -f https://infra.tekton.dev/tekton-releases/pipeline/previous/v1.18.0/release.yaml
kubectl -n tekton-pipelines rollout status deployment/tekton-pipelines-controller
kubectl -n tekton-pipelines rollout status deployment/tekton-pipelines-webhook
kubectl create namespace capstone
kubectl -n capstone apply -f https://raw.githubusercontent.com/tektoncd/catalog/main/task/git-clone/0.9/git-clone.yaml
kubectl -n capstone apply -f https://raw.githubusercontent.com/tektoncd/catalog/main/task/flake8/0.1/flake8.yaml
kubectl -n capstone apply -f https://raw.githubusercontent.com/tektoncd/catalog/main/task/buildah/0.9/buildah.yaml
kubectl -n capstone apply -f tekton/tasks.yaml -f tekton/pipeline.yaml -f tekton/rbac.yaml -f tekton/pvc-local.yaml
```

Provision PostgreSQL and the application secret as described in `deploy/README.md`.
The `pipeline` service account gets only the namespace permissions required to
manage the application Deployment and Service and inspect rollout status.
The official Buildah Task runs a privileged build container inside this isolated
local cluster; the deployed application itself runs as a non-root user.

Start a run and inspect its real result:

```sh
kubectl -n capstone create -f tekton/pipelinerun-local.yaml
kubectl -n capstone get pipelineruns,taskruns,pods
# Replace RUN_NAME with the name returned by the create command.
kubectl -n capstone wait --for=condition=Succeeded pipelinerun/RUN_NAME --timeout=1800s
tkn -n capstone pipelinerun logs RUN_NAME --all > pipelinerun.txt
kubectl -n capstone get deployments,pods,replicasets,services -l app=accounts
```

`pipelinerun.txt` must contain the actual logs from one successful PipelineRun.
Logs can also be collected with `kubectl logs` for every step container of that
run's TaskRun pods.

## IBM Skills Network OpenShift

The same pipeline can run in a lab namespace **when Tekton is installed**.
Use `oc` instead of `kubectl`, the namespace's existing service account and
registry permissions, `tekton/pvc.yaml` for the lab storage class, and an image
such as `us.icr.io/$SN_ICR_NAMESPACE/accounts:1`. Keep TLS verification enabled.
The pipeline uses the supported namespaced `buildah` Task, not the removed
`ClusterTask` resource. The lab user cannot install missing cluster-level Tekton
CRDs; use the supported local Kubernetes option when the cluster lacks Tekton.
