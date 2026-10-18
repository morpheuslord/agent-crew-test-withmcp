output "primary_endpoint" {
  description = "TLS endpoint of the primary node."
  value       = aws_elasticache_replication_group.this.primary_endpoint_address
}

output "port" {
  description = "Cache port."
  value       = aws_elasticache_replication_group.this.port
}

output "security_group_id" {
  description = "Security group of the cache."
  value       = aws_security_group.cache.id
}
