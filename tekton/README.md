# Continuous delivery

This pipeline targets the IBM Skills Network OpenShift lab. It uses the lab's
`buildah` ClusterTask and its existing pipeline service account/registry access.
The workspace is cleaned, the chosen Git revision is cloned, lint and tests run,
the image is built and pushed, then the deployment is applied and its rollout
checked. Build cannot begin unless both lint and tests succeed. Tests use an
isolated SQLite database; the deployed service uses PostgreSQL.

Install the namespaced catalog tasks and project resources:

```sh
oc apply -f https://raw.githubusercontent.com/tektoncd/catalog/main/task/git-clone/0.9/git-clone.yaml
oc apply -f https://raw.githubusercontent.com/tektoncd/catalog/main/task/flake8/0.1/flake8.yaml
oc apply -f tekton/tasks.yaml
oc apply -f tekton/pipeline.yaml
oc apply -f tekton/pvc.yaml
```

Provision PostgreSQL and the application secret as described in `deploy/README.md`
before starting. Confirm that `oc get clustertask buildah` succeeds. If the cluster
uses a namespaced `buildah` Task, remove `kind: ClusterTask` from the build task
reference. The task and service account must already be permitted to build/push
images and update Deployments/Services in this namespace.

```sh
tkn pipeline start cd-pipeline \
  -p repo-url=https://github.com/Nura007/devops-capstone-project.git \
  -p branch=main \
  -p build-image=us.icr.io/$SN_ICR_NAMESPACE/accounts:1 \
  -w name=pipeline-workspace,claimName=pipelinerun-pvc \
  --serviceaccount=pipeline --showlog
tkn pipelinerun logs --last --all > pipelinerun.txt
tkn pipelinerun describe --last
```

Only the output of an actual successful run is suitable for submission. On a local
cluster, use that cluster's storage class in `pvc.yaml`, install a Buildah Task,
configure registry credentials, and choose the corresponding service account.
