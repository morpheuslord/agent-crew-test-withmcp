locals {
  name       = "${var.project}-${var.environment}"
  ssm_prefix = "/${var.project}/${var.environment}"
}

module "network" {
  source               = "../../modules/network"
  name                 = local.name
  cidr_block           = var.vpc_cidr
  availability_zones   = var.availability_zones
  single_nat_gateway   = true
  flow_log_kms_key_arn = module.iam.config_kms_key_arn
}

module "registry" {
  source = "../../modules/registry"
  name   = local.name
}

module "storage" {
  source = "../../modules/storage"
  name   = local.name
}

module "iam" {
  source                  = "../../modules/iam"
  name                    = local.name
  ssm_prefix              = local.ssm_prefix
  ui_repository_arn       = module.registry.repository_arns["ui"]
  api_repository_arn      = module.registry.repository_arns["api"]
  attachments_bucket_arn  = module.storage.bucket_arn
  attachments_kms_key_arn = module.storage.kms_key_arn
}

module "alb" {
  source                = "../../modules/alb"
  name                  = local.name
  vpc_id                = module.network.vpc_id
  vpc_cidr_block        = module.network.vpc_cidr_block
  public_subnet_ids     = module.network.public_subnet_ids
  certificate_arn       = var.certificate_arn
  allowed_ingress_cidrs = var.allowed_ingress_cidrs
  deletion_protection   = var.deletion_protection
}

module "ui" {
  source                = "../../modules/ui"
  name                  = local.name
  vpc_id                = module.network.vpc_id
  vpc_cidr_block        = module.network.vpc_cidr_block
  subnet_ids            = module.network.app_subnet_ids
  alb_security_group_id = module.alb.security_group_id
  target_group_arn      = module.alb.target_group_arn
  instance_profile_name = module.iam.ui_instance_profile_name
  image_uri             = "${module.registry.repository_urls["ui"]}:${var.ui_image_tag}"
  ssm_path              = "${local.ssm_prefix}/ui"
  log_group_name        = module.iam.log_group_names["ui"]
  instance_type         = var.ui_instance_type
  min_size              = var.instances_per_service
  max_size              = var.instances_per_service * 2
  config_version        = sha256(join(",", [for k, p in aws_ssm_parameter.ui : "${k}=${p.version}"]))
}

module "api" {
  source                   = "../../modules/api"
  name                     = local.name
  vpc_id                   = module.network.vpc_id
  vpc_cidr_block           = module.network.vpc_cidr_block
  subnet_ids               = module.network.app_subnet_ids
  client_security_group_id = module.ui.security_group_id
  instance_profile_name    = module.iam.api_instance_profile_name
  image_uri                = "${module.registry.repository_urls["api"]}:${var.api_image_tag}"
  ssm_path                 = "${local.ssm_prefix}/api"
  log_group_name           = module.iam.log_group_names["api"]
  instance_type            = var.api_instance_type
  min_size                 = var.instances_per_service
  max_size                 = var.instances_per_service * 2
  config_version           = sha256(join(",", [for k, p in aws_ssm_parameter.api : "${k}=${p.version}"]))
}

module "database" {
  source                     = "../../modules/database"
  name                       = local.name
  vpc_id                     = module.network.vpc_id
  subnet_ids                 = module.network.data_subnet_ids
  allowed_security_group_ids = [module.api.security_group_id]
  instance_class             = var.db_instance_class
  multi_az                   = var.db_multi_az
  deletion_protection        = var.deletion_protection
}

module "cache" {
  source                     = "../../modules/cache"
  name                       = local.name
  vpc_id                     = module.network.vpc_id
  subnet_ids                 = module.network.data_subnet_ids
  allowed_security_group_ids = [module.api.security_group_id]
  auth_token                 = random_password.cache_auth.result
}
