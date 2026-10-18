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
  description = "VPC for the cache."
}

variable "subnet_ids" {
  type        = list(string)
  description = "Data subnets (no internet route) in at least two AZs."

  validation {
    condition     = length(var.subnet_ids) >= 2
    error_message = "Provide subnets in at least two availability zones."
  }
}

variable "allowed_security_group_ids" {
  type        = list(string)
  description = "Security groups allowed to connect on 6379 (the API only)."

  validation {
    condition     = length(var.allowed_security_group_ids) > 0
    error_message = "At least one client security group is required."
  }
}

variable "engine" {
  type        = string
  description = "Cache engine: valkey or redis."
  default     = "valkey"

  validation {
    condition     = contains(["valkey", "redis"], var.engine)
    error_message = "engine must be valkey or redis."
  }
}

variable "engine_version" {
  type        = string
  description = "Engine version, e.g. 8.0 for Valkey or 7.1 for Redis OSS."
  default     = "8.0"

  validation {
    condition     = can(regex("^[0-9]+\\.[0-9]+$", var.engine_version))
    error_message = "engine_version must look like 8.0."
  }
}

variable "parameter_group_family" {
  type        = string
  description = "Parameter group family matching engine and version, e.g. valkey8 or redis7."
  default     = "valkey8"

  validation {
    condition     = can(regex("^(valkey|redis)[0-9]+$", var.parameter_group_family))
    error_message = "parameter_group_family must look like valkey8 or redis7."
  }
}

variable "node_type" {
  type        = string
  description = "Cache node type."
  default     = "cache.t4g.micro"

  validation {
    condition     = can(regex("^cache\\.[a-z0-9]+\\.[a-z0-9]+$", var.node_type))
    error_message = "node_type must look like cache.t4g.micro."
  }
}

variable "num_cache_clusters" {
  type        = number
  description = "Number of nodes (1 primary plus replicas)."
  default     = 1

  validation {
    condition     = var.num_cache_clusters >= 1 && var.num_cache_clusters <= 6
    error_message = "num_cache_clusters must be between 1 and 6."
  }
}

variable "auth_token" {
  type        = string
  description = "AUTH token clients must present (16-128 printable characters)."
  sensitive   = true

  validation {
    condition     = length(var.auth_token) >= 16 && length(var.auth_token) <= 128
    error_message = "auth_token must be 16-128 characters."
  }
}

variable "tags" {
  type        = map(string)
  description = "Tags added to every resource."
  default     = {}
}
