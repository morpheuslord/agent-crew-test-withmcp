output "alb_dns_name" {
  description = "Public DNS name of the load balancer; point public_hostname at it (CNAME or alias)."
  value       = module.alb.dns_name
}

output "alb_zone_id" {
  description = "Hosted zone ID of the load balancer, for a Route 53 alias record."
  value       = module.alb.zone_id
}

output "ecr_repository_urls" {
  description = "Where to push the ui and api images."
  value       = module.registry.repository_urls
}

output "attachments_bucket" {
  description = "S3 bucket holding attachments."
  value       = module.storage.bucket_name
}

output "database_address" {
  description = "RDS endpoint (private)."
  value       = module.database.address
}

output "database_master_secret_arn" {
  description = "Secrets Manager secret with the RDS master credentials, used only by the migration step."
  value       = module.database.master_user_secret_arn
}

output "cache_endpoint" {
  description = "ElastiCache primary endpoint (private, TLS)."
  value       = module.cache.primary_endpoint
}

output "api_internal_url" {
  description = "Internal URL of the API (reachable only from the UI instances)."
  value       = module.api.internal_url
}

output "ssm_prefix" {
  description = "SSM Parameter Store prefix holding runtime configuration."
  value       = local.ssm_prefix
}

output "autoscaling_groups" {
  description = "Auto Scaling groups to refresh after pushing new images."
  value = {
    ui  = module.ui.autoscaling_group_name
    api = module.api.autoscaling_group_name
  }
}

output "nat_public_ips" {
  description = "Source IPs of outbound webhook calls (for receivers that allow-list callers)."
  value       = module.network.nat_public_ips
}
