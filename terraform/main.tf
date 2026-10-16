data "aws_availability_zones" "available" {
  state = "available"

  filter {
    name   = "opt-in-status"
    values = ["opt-in-not-required"]
  }
}

data "aws_caller_identity" "current" {}

locals {
  azs = slice(data.aws_availability_zones.available.names, 0, var.az_count)

  # 10.30.0.0/16 -> public 10.30.0.0/24, 10.30.1.0/24 ; private 10.30.10.0/24, 10.30.11.0/24
  public_subnets  = [for i, _ in local.azs : cidrsubnet(var.vpc_cidr, 8, i)]
  private_subnets = [for i, _ in local.azs : cidrsubnet(var.vpc_cidr, 8, i + 10)]

  tags = {
    Project     = var.project
    Environment = var.environment
    ManagedBy   = "terraform"
    Repository  = var.github_repository
  }
}

# ───────────────────────────── Networking ─────────────────────────────
#
#   VPC 10.30.0.0/16
#   ├── public subnets  (one per AZ)  -> Internet Gateway, load balancers, NAT gateway
#   └── private subnets (one per AZ)  -> EKS worker nodes; outbound via NAT
#
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 6.7"

  name = "${var.project}-vpc"
  cidr = var.vpc_cidr
  azs  = local.azs

  public_subnets  = local.public_subnets
  private_subnets = local.private_subnets

  # A single NAT gateway keeps classroom costs down (production would use one per AZ).
  enable_nat_gateway   = true
  single_nat_gateway   = true
  enable_dns_hostnames = true
  enable_dns_support   = true

  # These tags tell Kubernetes which subnets to place load balancers in.
  public_subnet_tags = {
    "kubernetes.io/role/elb" = 1
  }
  private_subnet_tags = {
    "kubernetes.io/role/internal-elb" = 1
  }
}
