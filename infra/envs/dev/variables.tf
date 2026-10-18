variable "aws_region" {
  type        = string
  description = "AWS region to deploy into."

  validation {
    condition     = can(regex("^[a-z]{2}(-gov)?-[a-z]+-[0-9]$", var.aws_region))
    error_message = "aws_region must look like eu-west-1."
  }
}

variable "project" {
  type        = string
  description = "Project name, used as the first part of every resource name."
  default     = "taskboard"

  validation {
    condition     = can(regex("^[a-z][a-z0-9]{2,14}$", var.project))
    error_message = "project must be 3-15 lowercase letters or digits."
  }
}

variable "environment" {
  type        = string
  description = "Environment name."
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "environment must be dev, staging or prod."
  }
}

variable "vpc_cidr" {
  type        = string
  description = "IPv4 CIDR block of the VPC."
  default     = "10.40.0.0/16"

  validation {
    condition     = can(cidrhost(var.vpc_cidr, 0))
    error_message = "vpc_cidr must be a valid IPv4 CIDR."
  }
}

variable "availability_zones" {
  type        = list(string)
  description = "Two availability zones in aws_region."

  validation {
    condition     = length(var.availability_zones) == 2
    error_message = "Provide exactly two availability zones."
  }
}

variable "public_hostname" {
  type        = string
  description = "Public DNS name users reach the UI at (used for reset-password links)."

  validation {
    condition     = can(regex("^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)+$", var.public_hostname))
    error_message = "public_hostname must be a DNS name such as taskboard.example.com."
  }
}

variable "certificate_arn" {
  type        = string
  description = "ACM certificate ARN covering public_hostname, for the HTTPS listener."

  validation {
    condition     = can(regex("^arn:aws[a-z-]*:acm:[a-z0-9-]+:[0-9]{12}:certificate/.+$", var.certificate_arn))
    error_message = "certificate_arn must be an ACM certificate ARN."
  }
}

variable "allowed_ingress_cidrs" {
  type        = list(string)
  description = "Client CIDRs allowed to reach the public load balancer."
  default     = ["0.0.0.0/0"]

  validation {
    condition     = length(var.allowed_ingress_cidrs) > 0 && alltrue([for c in var.allowed_ingress_cidrs : can(cidrhost(c, 0))])
    error_message = "allowed_ingress_cidrs must be a non-empty list of IPv4 CIDRs."
  }
}

variable "ui_image_tag" {
  type        = string
  description = "Immutable tag of the UI image in ECR (for example a git SHA)."

  validation {
    condition     = can(regex("^[A-Za-z0-9._-]{1,128}$", var.ui_image_tag)) && var.ui_image_tag != "latest"
    error_message = "ui_image_tag must be a valid tag other than latest."
  }
}

variable "api_image_tag" {
  type        = string
  description = "Immutable tag of the API image in ECR (for example a git SHA)."

  validation {
    condition     = can(regex("^[A-Za-z0-9._-]{1,128}$", var.api_image_tag)) && var.api_image_tag != "latest"
    error_message = "api_image_tag must be a valid tag other than latest."
  }
}

variable "ui_instance_type" {
  type        = string
  description = "Instance type for the UI servers."
  default     = "t3.small"

  validation {
    condition     = can(regex("^[a-z][a-z0-9]*\\.[a-z0-9]+$", var.ui_instance_type))
    error_message = "ui_instance_type must look like t3.small."
  }
}

variable "api_instance_type" {
  type        = string
  description = "Instance type for the API servers."
  default     = "t3.small"

  validation {
    condition     = can(regex("^[a-z][a-z0-9]*\\.[a-z0-9]+$", var.api_instance_type))
    error_message = "api_instance_type must look like t3.small."
  }
}

variable "instances_per_service" {
  type        = number
  description = "Minimum number of instances per service (one per AZ is the sensible minimum)."
  default     = 2

  validation {
    condition     = var.instances_per_service >= 1 && var.instances_per_service <= 10
    error_message = "instances_per_service must be between 1 and 10."
  }
}

variable "db_instance_class" {
  type        = string
  description = "RDS instance class."
  default     = "db.t4g.small"

  validation {
    condition     = can(regex("^db\\.[a-z0-9]+\\.[a-z0-9]+$", var.db_instance_class))
    error_message = "db_instance_class must look like db.t4g.small."
  }
}

variable "db_multi_az" {
  type        = bool
  description = "Run the database with a standby in a second AZ."
  default     = false
}

variable "deletion_protection" {
  type        = bool
  description = "Protect the load balancer and database from deletion."
  default     = true
}

variable "log_level" {
  type        = string
  description = "Log level for both services."
  default     = "info"

  validation {
    condition     = contains(["debug", "info", "warning", "error"], var.log_level)
    error_message = "log_level must be debug, info, warning or error."
  }
}
