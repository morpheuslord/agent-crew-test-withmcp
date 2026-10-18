resource "aws_kms_key" "cache" {
  description             = "${var.name} cache at-rest encryption"
  enable_key_rotation     = true
  deletion_window_in_days = 30
  tags                    = var.tags
}

resource "aws_security_group" "cache" {
  name        = "${var.name}-cache"
  description = "Cache, reachable only from the API instances."
  vpc_id      = var.vpc_id
  tags        = merge(var.tags, { Name = "${var.name}-cache" })
}

resource "aws_vpc_security_group_ingress_rule" "cache" {
  for_each                     = toset(var.allowed_security_group_ids)
  security_group_id            = aws_security_group.cache.id
  description                  = "Cache from the API"
  referenced_security_group_id = each.value
  ip_protocol                  = "tcp"
  from_port                    = 6379
  to_port                      = 6379
}

resource "aws_elasticache_subnet_group" "this" {
  name       = "${var.name}-cache"
  subnet_ids = var.subnet_ids
  tags       = var.tags
}

resource "aws_elasticache_parameter_group" "this" {
  name   = "${var.name}-cache"
  family = var.parameter_group_family
  tags   = var.tags

  # Bounded memory: evict least-recently-used keys rather than failing writes. Every cache key
  # also has a TTL, so filter-combination keys cannot grow without limit.
  parameter {
    name  = "maxmemory-policy"
    value = "allkeys-lru"
  }
}

resource "aws_elasticache_replication_group" "this" {
  replication_group_id = "${var.name}-cache"
  description          = "${var.name} read cache and rate-limit counters"
  engine               = var.engine
  engine_version       = var.engine_version
  node_type            = var.node_type
  num_cache_clusters   = var.num_cache_clusters
  port                 = 6379
  parameter_group_name = aws_elasticache_parameter_group.this.name
  subnet_group_name    = aws_elasticache_subnet_group.this.name
  security_group_ids   = [aws_security_group.cache.id]

  automatic_failover_enabled = var.num_cache_clusters > 1
  multi_az_enabled           = var.num_cache_clusters > 1

  at_rest_encryption_enabled = true
  kms_key_id                 = aws_kms_key.cache.arn
  transit_encryption_enabled = true
  transit_encryption_mode    = "required"
  auth_token                 = var.auth_token

  auto_minor_version_upgrade = true
  snapshot_retention_limit   = 1
  tags                       = var.tags
}
