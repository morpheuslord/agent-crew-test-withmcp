output "dns_name" {
  description = "Public DNS name of the load balancer (point the application's DNS record here)."
  value       = aws_lb.this.dns_name
}

output "zone_id" {
  description = "Route 53 hosted zone ID of the load balancer, for alias records."
  value       = aws_lb.this.zone_id
}

output "security_group_id" {
  description = "Security group of the load balancer; the UI admits traffic only from it."
  value       = aws_security_group.alb.id
}

output "target_group_arn" {
  description = "Target group that the UI instances register with."
  value       = aws_lb_target_group.ui.arn
}

output "arn" {
  description = "ARN of the load balancer."
  value       = aws_lb.this.arn
}
