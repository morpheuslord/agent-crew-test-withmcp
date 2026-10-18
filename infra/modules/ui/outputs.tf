output "security_group_id" {
  description = "Security group of the UI instances (the only allowed caller of the API)."
  value       = aws_security_group.ui.id
}

output "autoscaling_group_name" {
  description = "Auto Scaling group running the UI instances."
  value       = aws_autoscaling_group.ui.name
}
