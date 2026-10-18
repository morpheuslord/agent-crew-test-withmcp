variable "name" {
  type        = string
  description = "Name prefix for every resource."

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{2,30}$", var.name))
    error_message = "name must be 3-31 lowercase letters, digits or hyphens."
  }
}

variable "vpc_id" {
  type        = string
  description = "VPC for the database."
}

variable "subnet_ids" {
  type        = list(string)
  description = "Data subnets (no internet route) in at least two AZs."

  validation {
    condition     = length(var.subnet_ids) >= 2
    error_message = "RDS needs subnets in at least two availability zones."
  }
}

variable "allowed_security_group_ids" {
  type        = list(string)
  description = "Security groups allowed to connect on 5432 (the API only)."

  validation {
    condition     = length(var.allowed_security_group_ids) > 0
    error_message = "At least one client security group is required."
  }
}

variable "instance_class" {
  type        = string
  description = "RDS instance class."
  default     = "db.t4g.small"

  validation {
    condition     = can(regex("^db\\.[a-z0-9]+\\.[a-z0-9]+$", var.instance_class))
    error_message = "instance_class must look like db.t4g.small."
  }
}

variable "allocated_storage" {
  type        = number
  description = "Initial storage in GiB."
  default     = 20

  validation {
    condition     = var.allocated_storage >= 20 && var.allocated_storage <= 1000
    error_message = "allocated_storage must be between 20 and 1000 GiB."
  }
}

variable "max_allocated_storage" {
  type        = number
  description = "Storage autoscaling ceiling in GiB."
  default     = 100

  validation {
    condition     = var.max_allocated_storage >= 20 && var.max_allocated_storage <= 2000
    error_message = "max_allocated_storage must be between 20 and 2000 GiB."
  }
}

variable "multi_az" {
  type        = bool
  description = "Run a standby in a second AZ."
  default     = false
}

variable "backup_retention_days" {
  type        = number
  description = "Days of automated backups to keep."
  default     = 7

  validation {
    condition     = var.backup_retention_days >= 1 && var.backup_retention_days <= 35
    error_message = "backup_retention_days must be between 1 and 35."
  }
}

variable "deletion_protection" {
  type        = bool
  description = "Block accidental deletion of the database."
  default     = true
}

variable "database_name" {
  type        = string
  description = "Name of the application database."
  default     = "taskboard"

  validation {
    condition     = can(regex("^[a-z][a-z0-9_]{1,62}$", var.database_name))
    error_message = "database_name must be a lowercase PostgreSQL identifier."
  }
}

variable "master_username" {
  type        = string
  description = "Master (owner) user. Used only for migrations; the API connects as a separate least-privilege role."
  default     = "taskboard_owner"

  validation {
    condition     = can(regex("^[a-z][a-z0-9_]{2,62}$", var.master_username)) && var.master_username != "postgres"
    error_message = "master_username must be a lowercase identifier other than postgres."
  }
}

variable "tags" {
  type        = map(string)
  description = "Tags added to every resource."
  default     = {}
}
