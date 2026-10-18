output "ui_instance_profile_name" {
  description = "Instance profile for the UI instances."
  value       = aws_iam_instance_profile.service["ui"].name
}

output "api_instance_profile_name" {
  description = "Instance profile for the API instances."
  value       = aws_iam_instance_profile.service["api"].name
}

output "ui_role_arn" {
  description = "IAM role of the UI instances."
  value       = aws_iam_role.service["ui"].arn
}

output "api_role_arn" {
  description = "IAM role of the API instances."
  value       = aws_iam_role.service["api"].arn
}

output "config_kms_key_arn" {
  description = "KMS key that must encrypt the SecureString parameters under ssm_prefix."
  value       = aws_kms_key.config.arn
}

output "log_group_names" {
  description = "CloudWatch log groups per service."
  value       = { for k, g in aws_cloudwatch_log_group.service : k => g.name }
}
