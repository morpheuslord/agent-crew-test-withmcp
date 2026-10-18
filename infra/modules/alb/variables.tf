variable "name" {
  type        = string
  description = "Name prefix for every resource."

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{2,24}$", var.name))
    error_message = "name must be 3-25 lowercase letters, digits or hyphens (ALB names are limited to 32 characters)."
  }
}

variable "vpc_id" {
  type        = string
  description = "VPC the load balancer belongs to."
}

variable "vpc_cidr_block" {
  type        = string
  description = "VPC CIDR; the load balancer may only send traffic to targets inside it."

  validation {
    condition     = can(cidrhost(var.vpc_cidr_block, 0))
    error_message = "vpc_cidr_block must be a valid IPv4 CIDR."
  }
}

variable "public_subnet_ids" {
  type        = list(string)
  description = "Public subnets in at least two AZs."

  validation {
    condition     = length(var.public_subnet_ids) >= 2
    error_message = "An ALB needs subnets in at least two availability zones."
  }
}

variable "certificate_arn" {
  type        = string
  description = "ACM certificate ARN for the HTTPS listener."

  validation {
    condition     = can(regex("^arn:aws[a-z-]*:acm:[a-z0-9-]+:[0-9]{12}:certificate/.+$", var.certificate_arn))
    error_message = "certificate_arn must be an ACM certificate ARN."
  }
}

variable "ssl_policy" {
  type        = string
  description = "TLS policy for the HTTPS listener (TLS 1.2+ only)."
  default     = "ELBSecurityPolicy-TLS13-1-2-2021-06"

  validation {
    condition     = contains(["ELBSecurityPolicy-TLS13-1-2-2021-06", "ELBSecurityPolicy-TLS13-1-3-2021-06", "ELBSecurityPolicy-TLS13-1-2-Res-2021-06"], var.ssl_policy)
    error_message = "ssl_policy must be one of the TLS 1.2+/1.3 policies."
  }
}

variable "target_port" {
  type        = number
  description = "Port the UI server listens on."
  default     = 3000

  validation {
    condition     = var.target_port > 0 && var.target_port < 65536
    error_message = "target_port must be a valid TCP port."
  }
}

variable "allowed_ingress_cidrs" {
  type        = list(string)
  description = "Client CIDRs allowed to reach the load balancer (an internal tool may restrict this to office ranges)."
  default     = ["0.0.0.0/0"]

  validation {
    condition     = length(var.allowed_ingress_cidrs) > 0 && alltrue([for c in var.allowed_ingress_cidrs : can(cidrhost(c, 0))])
    error_message = "allowed_ingress_cidrs must be a non-empty list of IPv4 CIDRs."
  }
}

variable "deletion_protection" {
  type        = bool
  description = "Protect the load balancer from accidental deletion."
  default     = true
}

variable "access_logs_bucket" {
  type        = string
  description = "Optional S3 bucket for ALB access logs; empty disables access logging."
  default     = ""
}

variable "tags" {
  type        = map(string)
  description = "Tags added to every resource."
  default     = {}
}
