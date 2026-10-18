variable "name" {
  type        = string
  description = "Name prefix; the bucket is named <name>-attachments-<account id>."

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{2,30}$", var.name))
    error_message = "name must be 3-31 lowercase letters, digits or hyphens."
  }
}

variable "noncurrent_version_days" {
  type        = number
  description = "Days to keep overwritten or deleted object versions before they expire."
  default     = 30

  validation {
    condition     = var.noncurrent_version_days >= 1 && var.noncurrent_version_days <= 365
    error_message = "noncurrent_version_days must be between 1 and 365."
  }
}

variable "force_destroy" {
  type        = bool
  description = "Allow Terraform to delete the bucket while it still holds objects. Keep false outside throwaway environments."
  default     = false
}

variable "tags" {
  type        = map(string)
  description = "Tags added to every resource."
  default     = {}
}
