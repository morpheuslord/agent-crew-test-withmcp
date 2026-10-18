variable "name" {
  type        = string
  description = "Name prefix for every resource, e.g. taskboard-dev."

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{2,30}$", var.name))
    error_message = "name must be 3-31 lowercase letters, digits or hyphens."
  }
}

variable "ssm_prefix" {
  type        = string
  description = "SSM Parameter Store path holding runtime configuration, e.g. /taskboard/dev."

  validation {
    condition     = can(regex("^/[a-z0-9/_-]+[a-z0-9]$", var.ssm_prefix))
    error_message = "ssm_prefix must start with / and contain only lowercase letters, digits, /, _ and -."
  }
}

variable "ui_repository_arn" {
  type        = string
  description = "ARN of the ECR repository the UI instances pull from."
}

variable "api_repository_arn" {
  type        = string
  description = "ARN of the ECR repository the API instances pull from."
}

variable "attachments_bucket_arn" {
  type        = string
  description = "ARN of the S3 bucket holding attachments."
}

variable "attachments_kms_key_arn" {
  type        = string
  description = "ARN of the KMS key encrypting the attachments bucket."
}

variable "log_retention_days" {
  type        = number
  description = "Days to keep container logs in CloudWatch Logs."
  default     = 90

  validation {
    condition     = contains([30, 60, 90, 120, 150, 180, 365, 400, 545, 731], var.log_retention_days)
    error_message = "log_retention_days must be a CloudWatch Logs retention value between 30 and 731."
  }
}

variable "tags" {
  type        = map(string)
  description = "Tags added to every resource."
  default     = {}
}
