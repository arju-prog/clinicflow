# Deploying ClinicFlow to AWS (Terraform → EKS → GitHub Actions)

> **Cost warning.** While it is running, this creates billable resources: the EKS control plane (~$0.10/h), two m7i-flex.large nodes, a NAT gateway, a Network Load Balancer and small EBS volumes. Budget roughly **$0.30/hour (~$7/day)** in `ap-south-1`. **Run `terraform destroy` as soon as you have your screenshots.**

## 0. Prerequisites

- AWS CLI v2 logged in to an account where you can create IAM, VPC and EKS resources: `aws sts get-caller-identity` must work. Use `aws configure sso` or `aws login`; never commit access keys.
- Terraform ≥ 1.9, kubectl, Helm ≥ 3.17 (Helm 4 recommended)
- The GitHub repository already pushed, with at least one green pipeline run so the images exist in GHCR.

## 1. Make the GHCR images pullable

GHCR packages are private by default. Either:

- **(simplest)** GitHub → your profile → *Packages* → `clinicflow-backend` → *Package settings* → *Change visibility* → **Public**. Repeat for `clinicflow-frontend`; or
- keep them private and create a pull secret (a PAT with `read:packages`):
  ```bash
  kubectl create namespace clinicflow
  kubectl -n clinicflow create secret docker-registry ghcr-pull \
    --docker-server=ghcr.io --docker-username=<github-user> --docker-password=<PAT>
  # then deploy with: --set imagePullSecrets[0].name=ghcr-pull
  ```

## 2. Provision the infrastructure

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars      # check github_repository = "<owner>/<repo>"
terraform init
terraform fmt -check && terraform validate
terraform plan -out tfplan                         # 📸 screenshot: "Plan: N to add, 0 to change, 0 to destroy"
terraform apply tfplan                             # ~15 minutes
terraform output
```

If your account already has a GitHub OIDC provider (`token.actions.githubusercontent.com`), set `create_github_oidc_provider = false`.

📸 **AWS Console screenshots** (region *Asia Pacific (Mumbai)*):
- VPC → *Your VPCs* → `clinicflow-vpc`, and *Subnets* showing 2 public + 2 private subnets
- EKS → *Clusters* → `clinicflow-eks` (Active) → *Compute* tab showing the `default` node group

## 3. Connect kubectl and install the cluster add-ons

```bash
aws eks update-kubeconfig --region ap-south-1 --name clinicflow-eks
kubectl get nodes                                  # 2 Ready nodes
../scripts/bootstrap-cluster.sh eks                # gp3 StorageClass, Traefik (NLB), metrics-server, Prometheus+Grafana
```

## 4. Let GitHub Actions deploy

In GitHub → repo → *Settings* → *Secrets and variables* → *Actions* → **Variables** tab, add:

| Variable | Value |
|---|---|
| `AWS_DEPLOY_ROLE_ARN` | `terraform output -raw github_actions_role_arn` |
| `AWS_REGION` | `ap-south-1` |
| `EKS_CLUSTER_NAME` | `clinicflow-eks` |

These are not secrets: OIDC needs no stored keys. Now trigger a deploy: push any commit to `main`, or *Actions* → *ClinicFlow CI/CD* → *Run workflow*. The `Deploy · Helm → EKS` job runs `helm upgrade --install` with the commit's SHA tag.

To deploy by hand instead:

```bash
SHA=$(git rev-parse HEAD)
helm upgrade --install clinicflow ./helm/clinicflow -n clinicflow --create-namespace \
  -f helm/clinicflow/values-prod.yaml \
  --set backend.image.repository=ghcr.io/<owner>/clinicflow-backend --set backend.image.tag=$SHA \
  --set frontend.image.repository=ghcr.io/<owner>/clinicflow-frontend --set frontend.image.tag=$SHA \
  --wait
```

## 5. Verify and collect evidence

```bash
kubectl get pods -n clinicflow            # 📸 all Running (2 backend, 2 frontend, 1 postgres)
kubectl get svc -n clinicflow             # 📸 ClusterIP services
helm list -n clinicflow                   # 📸
kubectl get ingress -n clinicflow
kubectl get hpa -n clinicflow
helm test clinicflow -n clinicflow

# The public URL is the Traefik load balancer:
kubectl get svc -n traefik traefik -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'; echo
# 📸 open http://<that-hostname>/ in a browser (DNS can take 2–3 minutes to resolve)
```

Monitoring:

```bash
kubectl -n monitoring port-forward svc/kube-prometheus-stack-prometheus 9090:9090
#   📸 http://localhost:9090/targets?search=clinicflow → clinicflow-backend UP
kubectl -n monitoring port-forward svc/kube-prometheus-stack-grafana 3001:80
kubectl -n monitoring get secret kube-prometheus-stack-grafana -o jsonpath='{.data.admin-password}' | base64 -d; echo
#   📸 http://localhost:3001 → Dashboards → ClinicFlow → "ClinicFlow · Service overview"
kubectl -n clinicflow port-forward svc/clinicflow-backend 8000:8000
#   📸 curl http://localhost:8000/metrics | head -40
```

HPA demo:

```bash
./scripts/load-test.sh
kubectl get hpa -n clinicflow -w          # 📸 replicas climb from 2 towards 6
```

## 6. Tear down (do not skip)

```bash
# Delete the load balancer and volumes Kubernetes created, *before* Terraform removes the VPC
helm uninstall clinicflow -n clinicflow
kubectl delete pvc --all -n clinicflow
helm uninstall traefik -n traefik
helm uninstall kube-prometheus-stack -n monitoring
kubectl get svc -A | grep LoadBalancer    # should print nothing

cd terraform
terraform destroy                          # 📸 "Destroy complete! Resources: N destroyed."
```

Then remove the `AWS_DEPLOY_ROLE_ARN` repository variable, so later pushes skip the deploy job instead of failing.

**Why uninstall first?** The NLB and EBS volumes were created by Kubernetes controllers, not by Terraform. If they still exist, they keep the VPC's subnets and network interfaces in use and `terraform destroy` gets stuck deleting the VPC.

## Troubleshooting

| Symptom | Fix |
|---|---|
| Pods `ImagePullBackOff` with `403/denied` | GHCR packages are private: make them public or use a pull secret (step 1) |
| `clinicflow-postgres-0` Pending, PVC Pending | `kubectl get sc`: gp3 must exist and be the default; check the `aws-ebs-csi-driver` addon is ACTIVE |
| HPA shows `<unknown>/60%` | metrics-server not ready yet; wait one minute, or check `kubectl top pods -n clinicflow` |
| Deploy job: `Not authorized to perform sts:AssumeRoleWithWebIdentity` | `github_repository` in tfvars must exactly match `<owner>/<repo>` |
| Deploy job: `the server has asked for the client to provide credentials` | the EKS access entry for the role is missing; re-run `terraform apply` |
