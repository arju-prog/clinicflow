# ───────────────────────────── EKS cluster ─────────────────────────────
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 21.29"

  name               = var.cluster_name
  kubernetes_version = var.kubernetes_version

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets # worker nodes live in private subnets

  # Public API endpoint so kubectl works from a laptop and from GitHub Actions.
  endpoint_public_access = true

  # Whoever runs `terraform apply` gets cluster-admin via an EKS access entry.
  enable_cluster_creator_admin_permissions = true

  # The GitHub Actions deploy role (see github-oidc.tf) may run `helm upgrade`.
  access_entries = {
    github_actions = {
      principal_arn = aws_iam_role.github_actions.arn
      policy_associations = {
        admin = {
          policy_arn = "arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy"
          access_scope = {
            type = "cluster"
          }
        }
      }
    }
  }

  addons = {
    # before_compute: install before the node group so nodes boot with these settings.
    vpc-cni = {
      before_compute = true
      # Prefix delegation raises the pod limit on a t3.medium from 17 to 110, enough
      # headroom for the app + Prometheus stack + HPA scale-out on two small nodes.
      configuration_values = jsonencode({
        env = {
          ENABLE_PREFIX_DELEGATION = "true"
          WARM_PREFIX_TARGET       = "1"
        }
      })
    }
    eks-pod-identity-agent = {
      before_compute = true
    }
    kube-proxy = {}
    coredns    = {}
    # EBS CSI driver lets the PostgreSQL PersistentVolumeClaim get an EBS volume.
    aws-ebs-csi-driver = {
      pod_identity_association = [{
        role_arn        = module.ebs_csi_pod_identity.iam_role_arn
        service_account = "ebs-csi-controller-sa"
      }]
    }
  }

  eks_managed_node_groups = {
    default = {
      ami_type       = "AL2023_x86_64_STANDARD"
      instance_types = var.node_instance_types
      capacity_type  = var.node_capacity_type

      min_size     = var.node_min_size
      desired_size = var.node_desired_size
      max_size     = var.node_max_size

      labels = {
        workload = "general"
      }
    }
  }
}

# IAM role for the EBS CSI controller, granted through EKS Pod Identity (no static keys).
module "ebs_csi_pod_identity" {
  source  = "terraform-aws-modules/eks-pod-identity/aws"
  version = "~> 2.9"

  name                      = "${var.project}-ebs-csi"
  attach_aws_ebs_csi_policy = true
}
