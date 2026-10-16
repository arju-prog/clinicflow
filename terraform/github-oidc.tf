# ─────────────── Keyless CI/CD: GitHub Actions -> AWS via OIDC ───────────────
#
# GitHub issues a short-lived signed token to each workflow run. AWS trusts that token
# only for this repository's main branch / production environment and exchanges it for
# temporary credentials. No AWS access keys are ever stored in GitHub.

resource "aws_iam_openid_connect_provider" "github" {
  count = var.create_github_oidc_provider ? 1 : 0

  url            = "https://token.actions.githubusercontent.com"
  client_id_list = ["sts.amazonaws.com"]
}

data "aws_iam_openid_connect_provider" "github" {
  count = var.create_github_oidc_provider ? 0 : 1
  url   = "https://token.actions.githubusercontent.com"
}

locals {
  # Accept the classic name-based subject and, when configured, the immutable ID-based one.
  github_oidc_subject_prefixes = compact(["repo:${var.github_repository}", var.github_oidc_subject_prefix])
  github_oidc_subjects = flatten([
    for prefix in local.github_oidc_subject_prefixes : [
      "${prefix}:environment:production",
      "${prefix}:ref:refs/heads/main",
    ]
  ])

  github_oidc_provider_arn = var.create_github_oidc_provider ? aws_iam_openid_connect_provider.github[0].arn : data.aws_iam_openid_connect_provider.github[0].arn
}

data "aws_iam_policy_document" "github_actions_trust" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [local.github_oidc_provider_arn]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }

    # The deploy job uses `environment: production`, which sets the token's subject to
    # <prefix>:environment:production. Pushes to main are also accepted.
    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:sub"
      values   = local.github_oidc_subjects
    }
  }
}

resource "aws_iam_role" "github_actions" {
  name                 = "${var.project}-github-actions-deploy"
  description          = "Assumed by GitHub Actions (${var.github_repository}) to deploy with Helm"
  assume_role_policy   = data.aws_iam_policy_document.github_actions_trust.json
  max_session_duration = 3600
}

# Just enough AWS permission to run `aws eks update-kubeconfig`; what the role may do
# *inside* Kubernetes is granted by the EKS access entry in eks.tf.
data "aws_iam_policy_document" "github_actions_eks" {
  statement {
    actions   = ["eks:DescribeCluster"]
    resources = ["arn:aws:eks:${var.aws_region}:${data.aws_caller_identity.current.account_id}:cluster/${var.cluster_name}"]
  }
}

resource "aws_iam_role_policy" "github_actions_eks" {
  name   = "eks-describe"
  role   = aws_iam_role.github_actions.id
  policy = data.aws_iam_policy_document.github_actions_eks.json
}
