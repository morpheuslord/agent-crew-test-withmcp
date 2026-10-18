variable "name" {
  type        = string
  description = "Name prefix for every resource, e.g. taskboard-dev."

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{2,30}$", var.name))
    error_message = "name must be 3-31 lowercase letters, digits or hyphens, starting with a letter."
  }
}

variable "cidr_block" {
  type        = string
  description = "IPv4 CIDR block for the VPC."

  validation {
    condition     = can(cidrhost(var.cidr_block, 0)) && tonumber(split("/", var.cidr_block)[1]) <= 20
    error_message = "cidr_block must be a valid IPv4 CIDR of /20 or larger."
  }
}

variable "availability_zones" {
  type        = list(string)
  description = "Exactly two availability zones to spread subnets across."

  validation {
    condition     = length(var.availability_zones) == 2
    error_message = "Provide exactly two availability zones."
  }
}

variable "single_nat_gateway" {
  type        = bool
  description = "Use one NAT gateway for both AZs (cheaper, less resilient). Set false for one per AZ."
  default     = true
}

variable "flow_log_retention_days" {
  type        = number
  description = "Days to keep VPC flow logs in CloudWatch Logs."
  default     = 90

  validation {
    condition     = contains([30, 60, 90, 120, 150, 180, 365, 400, 545, 731], var.flow_log_retention_days)
    error_message = "flow_log_retention_days must be a CloudWatch Logs retention value between 30 and 731."
  }
}

variable "flow_log_kms_key_arn" {
  type        = string
  description = "Optional KMS key ARN to encrypt the flow log group; null uses the CloudWatch default."
  default     = null
}

variable "tags" {
  type        = map(string)
  description = "Tags added to every resource."
  default     = {}
}
