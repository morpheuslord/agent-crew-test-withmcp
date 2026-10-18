# Runtime configuration for the instances, stored in SSM Parameter Store under
# /<project>/<environment>/{ui,api}. Secrets are generated here (never typed into tfvars), stored
# as SecureString with the config KMS key, and read at boot by each service's instance role. The
# Terraform state therefore holds secrets: the S3 backend must be encrypted and access-restricted
# (see backend.hcl.example and docs/DEPLOYMENT.md).

resource "random_password" "service_auth" {
  length  = 48
  special = false
}

resource "random_password" "cookie" {
  length  = 48
  special = false
}

resource "random_password" "webhook_signing" {
  length  = 48
  special = false
}

resource "random_password" "cache_auth" {
  length  = 48
  special = false
}

resource "random_password" "db_app" {
  length  = 40
  special = false
}

locals {
  db_app_user = "taskboard_app"
  ui_plain = {
    NODE_ENV         = "production"
    PORT             = "3000"
    API_BASE_URL     = module.api.internal_url
    COOKIE_SECURE    = "true"
    TRUST_PROXY_HOPS = "1"
    LOG_LEVEL        = var.log_level == "warning" ? "warn" : var.log_level
  }
  ui_secret = {
    SERVICE_AUTH_SECRET = random_password.service_auth.result
    COOKIE_SECRET       = random_password.cookie.result
  }
  api_plain = {
    ENVIRONMENT     = "production"
    LOG_LEVEL       = upper(var.log_level)
    PUBLIC_BASE_URL = "https://${var.public_hostname}"
    STORAGE_BACKEND = "s3"
    S3_BUCKET       = module.storage.bucket_name
    AWS_REGION      = var.aws_region
  }
  api_secret = {
    SERVICE_AUTH_SECRET    = random_password.service_auth.result
    WEBHOOK_SIGNING_SECRET = random_password.webhook_signing.result
    DATABASE_URL = format(
      "postgresql+psycopg://%s:%s@%s:%d/%s?sslmode=verify-full&sslrootcert=/etc/ssl/rds-ca.pem",
      local.db_app_user,
      random_password.db_app.result,
      module.database.address,
      module.database.port,
      module.database.database_name,
    )
    REDIS_URL = format(
      "rediss://:%s@%s:%d/0",
      random_password.cache_auth.result,
      module.cache.primary_endpoint,
      module.cache.port,
    )
  }
}

resource "aws_ssm_parameter" "ui" {
  for_each = merge(local.ui_plain, local.ui_secret)
  name     = "${local.ssm_prefix}/ui/${each.key}"
  type     = contains(keys(local.ui_secret), each.key) ? "SecureString" : "String"
  key_id   = contains(keys(local.ui_secret), each.key) ? module.iam.config_kms_key_arn : null
  value    = each.value
}

resource "aws_ssm_parameter" "api" {
  for_each = merge(local.api_plain, local.api_secret)
  name     = "${local.ssm_prefix}/api/${each.key}"
  type     = contains(keys(local.api_secret), each.key) ? "SecureString" : "String"
  key_id   = contains(keys(local.api_secret), each.key) ? module.iam.config_kms_key_arn : null
  value    = each.value
}

# Read only by operators running migrations (no instance role can read this path): the password
# for the least-privilege application role that the migration step creates.
resource "aws_ssm_parameter" "db_app_password" {
  name   = "${local.ssm_prefix}/migrate/DB_APP_PASSWORD"
  type   = "SecureString"
  key_id = module.iam.config_kms_key_arn
  value  = random_password.db_app.result
}
