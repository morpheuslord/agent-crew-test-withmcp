variable "name" {
  type        = string
  description = "Name prefix; repositories are <name>/ui and <name>/api."

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{2,30}$", var.name))
    error_message = "name must be 3-31 lowercase letters, digits or hyphens."
  }
}

variable "keep_images" {
  type        = number
  description = "How many images to keep per repository; older ones are expired."
  default     = 30

  validation {
    condition     = var.keep_images >= 5 && var.keep_images <= 1000
    error_message = "keep_images must be between 5 and 1000."
  }
}

variable "tags" {
  type        = map(string)
  description = "Tags added to every resource."
  default     = {}
}
