output "security_group_id" {
  description = "Security group of the API instances (allowed into PostgreSQL and the cache)."
  value       = aws_security_group.api.id
}

output "internal_url" {
  description = "Base URL the UI uses to call the API (internal load balancer, VPC-only)."
  value       = "http://${aws_lb.internal.dns_name}"
}

output "autoscaling_group_name" {
  description = "Auto Scaling group running the API instances."
  value       = aws_autoscaling_group.api.name
}
