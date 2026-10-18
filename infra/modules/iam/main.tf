data "aws_caller_identity" "current" {}
data "aws_region" "current" {}
data "aws_partition" "current" {}

locals {
  account   = data.aws_caller_identity.current.account_id
  region    = data.aws_region.current.region
  partition = data.aws_partition.current.partition
  services  = toset(["ui", "api"])
}

data "aws_iam_policy_document" "config_key" {
  statement {
    sid       = "AccountAdministration"
    actions   = ["kms:*"]
    resources = ["*"]
    principals {
      type        = "AWS"
      identifiers = ["arn:${local.partition}:iam::${local.account}:root"]
    }
  }

  statement {
    sid = "CloudWatchLogsEncryption"
    actions = [
      "kms:Encrypt",
      "kms:Decrypt",
      "kms:ReEncrypt*",
      "kms:GenerateDataKey*",
      "kms:Describe*",
    ]
    resources = ["*"]
    principals {
      type        = "Service"
      identifiers = ["logs.${local.region}.amazonaws.com"]
    }
    condition {
      test     = "ArnLike"
      variable = "kms:EncryptionContext:aws:logs:arn"
      values   = ["arn:${local.partition}:logs:${local.region}:${local.account}:log-group:*"]
    }
  }
}

# Customer-managed key for the SecureString parameters holding each service's secrets, and for
# the CloudWatch log groups.
resource "aws_kms_key" "config" {
  description             = "${var.name} runtime configuration and logs"
  enable_key_rotation     = true
  deletion_window_in_days = 30
  policy                  = data.aws_iam_policy_document.config_key.json
  tags                    = var.tags
}

resource "aws_kms_alias" "config" {
  name          = "alias/${var.name}-config"
  target_key_id = aws_kms_key.config.key_id
}

resource "aws_cloudwatch_log_group" "service" {
  for_each          = local.services
  name              = "/${var.name}/${each.key}"
  retention_in_days = var.log_retention_days
  kms_key_id        = aws_kms_key.config.arn
  tags              = var.tags
}

data "aws_iam_policy_document" "ec2_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "service" {
  for_each           = local.services
  name               = "${var.name}-${each.key}"
  assume_role_policy = data.aws_iam_policy_document.ec2_assume.json
  tags               = var.tags
}

# Shell access goes through SSM Session Manager (audited) instead of SSH keys and open ports.
# Deliberately not AmazonSSMManagedInstanceCore: that managed policy also allows
# ssm:GetParameter(s) on every parameter, which would let one service read the other's secrets
# (F-090). Only the agent's own control channels are granted here.
data "aws_iam_policy_document" "session_manager" {
  statement {
    sid       = "SsmAgentRegistration"
    actions   = ["ssm:UpdateInstanceInformation"]
    resources = ["arn:${local.partition}:ec2:${local.region}:${local.account}:instance/*"]
  }

  statement {
    sid = "SessionChannels"
    actions = [
      "ssmmessages:CreateControlChannel",
      "ssmmessages:CreateDataChannel",
      "ssmmessages:OpenControlChannel",
      "ssmmessages:OpenDataChannel",
      "ec2messages:AcknowledgeMessage",
      "ec2messages:DeleteMessage",
      "ec2messages:FailMessage",
      "ec2messages:GetEndpoint",
      "ec2messages:GetMessages",
      "ec2messages:SendReply",
    ]
    resources = ["*"] # These actions do not support resource-level permissions.
  }
}

resource "aws_iam_role_policy" "session_manager" {
  for_each = local.services
  name     = "session-manager"
  role     = aws_iam_role.service[each.key].id
  policy   = data.aws_iam_policy_document.session_manager.json
}

data "aws_iam_policy_document" "common" {
  for_each = local.services

  statement {
    sid       = "EcrAuth"
    actions   = ["ecr:GetAuthorizationToken"]
    resources = ["*"] # GetAuthorizationToken does not support resource-level permissions.
  }

  statement {
    sid = "EcrPullOwnImage"
    actions = [
      "ecr:BatchGetImage",
      "ecr:GetDownloadUrlForLayer",
      "ecr:BatchCheckLayerAvailability",
    ]
    resources = [each.key == "ui" ? var.ui_repository_arn : var.api_repository_arn]
  }

  statement {
    sid     = "ReadOwnConfig"
    actions = ["ssm:GetParametersByPath", "ssm:GetParameters", "ssm:GetParameter"]
    resources = [
      "arn:${local.partition}:ssm:${local.region}:${local.account}:parameter${var.ssm_prefix}/${each.key}",
      "arn:${local.partition}:ssm:${local.region}:${local.account}:parameter${var.ssm_prefix}/${each.key}/*",
    ]
  }

  statement {
    sid       = "DecryptOwnConfig"
    actions   = ["kms:Decrypt"]
    resources = [aws_kms_key.config.arn]
    condition {
      test     = "StringEquals"
      variable = "kms:ViaService"
      values   = ["ssm.${local.region}.amazonaws.com"]
    }
    # Decrypt only this service's own parameters, whatever other policies allow reading.
    condition {
      test     = "StringLike"
      variable = "kms:EncryptionContext:PARAMETER_ARN"
      values   = ["arn:${local.partition}:ssm:${local.region}:${local.account}:parameter${var.ssm_prefix}/${each.key}/*"]
    }
  }

  statement {
    sid       = "WriteOwnLogs"
    actions   = ["logs:CreateLogStream", "logs:PutLogEvents"]
    resources = ["${aws_cloudwatch_log_group.service[each.key].arn}:*"]
  }
}

resource "aws_iam_role_policy" "common" {
  for_each = local.services
  name     = "runtime"
  role     = aws_iam_role.service[each.key].id
  policy   = data.aws_iam_policy_document.common[each.key].json
}

# Only the API touches attachments, and only under the attachments/ prefix.
data "aws_iam_policy_document" "api_storage" {
  statement {
    sid       = "AttachmentObjects"
    actions   = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"]
    resources = ["${var.attachments_bucket_arn}/attachments/*"]
  }

  statement {
    sid       = "BucketReadiness"
    actions   = ["s3:ListBucket"]
    resources = [var.attachments_bucket_arn]
  }

  statement {
    sid       = "AttachmentEncryption"
    actions   = ["kms:Encrypt", "kms:Decrypt", "kms:GenerateDataKey"]
    resources = [var.attachments_kms_key_arn]
    condition {
      test     = "StringEquals"
      variable = "kms:ViaService"
      values   = ["s3.${local.region}.amazonaws.com"]
    }
  }
}

resource "aws_iam_role_policy" "api_storage" {
  name   = "attachments"
  role   = aws_iam_role.service["api"].id
  policy = data.aws_iam_policy_document.api_storage.json
}

resource "aws_iam_instance_profile" "service" {
  for_each = local.services
  name     = "${var.name}-${each.key}"
  role     = aws_iam_role.service[each.key].name
  tags     = var.tags
}
