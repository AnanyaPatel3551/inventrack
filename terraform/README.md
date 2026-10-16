# InvenTrack – Terraform (AWS VPC + EKS)

This folder provisions the AWS infrastructure for InvenTrack as code: a VPC and an EKS cluster with managed worker nodes in `ap-south-1` (Mumbai) by default.

## What gets created

```text
AWS (ap-south-1)
 └── VPC inventrack-vpc (10.20.0.0/16)
      ├── 2 public subnets   10.20.101.0/24, 10.20.102.0/24   tag: kubernetes.io/role/elb = 1
      ├── 2 private subnets  10.20.1.0/24,   10.20.2.0/24     tag: kubernetes.io/role/internal-elb = 1
      ├── Internet gateway
      ├── 1 NAT gateway (shared by both private subnets)
      └── EKS cluster inventrack-eks (Kubernetes 1.36)
           ├── add-ons: vpc-cni, kube-proxy, coredns, eks-pod-identity-agent
           └── managed node group "main"
                └── t3.medium, min 2 / desired 2 / max 4, in the private subnets
```

The subnets are spread over the first two availability zones of the region. Worker nodes live in the private subnets and reach the internet (for pulling images from GHCR) through the NAT gateway. The ELB subnet tags tell Kubernetes where to place load balancers created for Services/Ingress.

Every resource is tagged through the provider's `default_tags`:

| Tag | Value |
|-----|-------|
| Project | inventrack |
| Environment | dev |
| Owner | ananya-patel |
| ManagedBy | terraform |

## Files

| File | Purpose |
|------|---------|
| `versions.tf` | Terraform and AWS provider versions, provider config and `default_tags` |
| `variables.tf` | Typed input variables with descriptions and defaults |
| `main.tf` | VPC module (`terraform-aws-modules/vpc/aws` 6.7.3) and EKS module (`terraform-aws-modules/eks/aws` 21.29.0) |
| `outputs.tf` | VPC/subnet IDs, cluster name, endpoint, version and the `configure_kubectl` command |
| `terraform.tfvars.example` | Example variable values – contains **no credentials** |

## Prerequisites

- Terraform >= 1.7
- AWS CLI v2, configured with `aws configure` (or `AWS_PROFILE` / environment variables)
- kubectl

AWS credentials are never stored in this folder. `terraform.tfvars`, `.terraform/` and all `*.tfstate` files are git-ignored.

## Usage

```bash
cd terraform

# optional: customise values
cp terraform.tfvars.example terraform.tfvars

terraform init
terraform fmt -check
terraform validate
terraform plan
terraform apply
```

Creating the EKS cluster takes roughly 15 minutes.

When it finishes, configure kubectl with the command from the outputs:

```bash
terraform output -raw configure_kubectl
# aws eks update-kubeconfig --region ap-south-1 --name inventrack-eks

kubectl get nodes
```

Then deploy the application with Helm from the repository root:

```bash
kubectl apply -f k8s/namespace.yaml
helm upgrade --install inventrack ./helm/inventrack -n inventrack
```

## Outputs

| Output | Description |
|--------|-------------|
| `region` | AWS region used |
| `vpc_id` | VPC ID |
| `public_subnets` / `private_subnets` | Subnet IDs |
| `nat_gateway_ids` | NAT gateway IDs |
| `cluster_name` | EKS cluster name |
| `cluster_endpoint` | Kubernetes API endpoint |
| `cluster_version` | Kubernetes version |
| `configure_kubectl` | Ready-to-run `aws eks update-kubeconfig` command |

## Cost and clean-up

> **Cost warning:** the EKS control plane, two t3.medium nodes and the NAT gateway are billed per hour while they exist. Destroy the infrastructure as soon as the evaluation is done.

```bash
terraform destroy
```

If you installed an Ingress controller with a `LoadBalancer` Service, uninstall it first (`helm uninstall ...`) so AWS deletes the load balancer before Terraform removes the VPC – otherwise the destroy can get stuck on the subnets.

## Screenshots for grading (M7)

- `terraform plan` output
- AWS Console: VPC `inventrack-vpc` and EKS cluster `inventrack-eks` in ap-south-1
- `terraform destroy` completing with `Destroy complete!`
