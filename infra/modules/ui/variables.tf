variable "name" {
  type        = string
  description = "Name prefix for every resource."

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{2,24}$", var.name))
    error_message = "name must be 3-25 lowercase letters, digits or hyphens."
  }
}

variable "vpc_id" {
  type        = string
  description = "VPC for the instances."
}

variable "vpc_cidr_block" {
  type        = string
  description = "VPC CIDR, used to scope egress to data stores and internal load balancers."

  validation {
    condition     = can(cidrhost(var.vpc_cidr_block, 0))
    error_message = "vpc_cidr_block must be a valid IPv4 CIDR."
  }
}

variable "subnet_ids" {
  type        = list(string)
  description = "Private app subnets in at least two AZs; instances get no public IPs."

  validation {
    condition     = length(var.subnet_ids) >= 2
    error_message = "Provide private subnets in at least two availability zones."
  }
}

variable "instance_profile_name" {
  type        = string
  description = "IAM instance profile from the iam module."
}

variable "image_uri" {
  type        = string
  description = "Full image reference to run, e.g. <account>.dkr.ecr.<region>.amazonaws.com/taskboard-dev/ui:1.0.0. Use an immutable tag or digest."

  validation {
    condition     = can(regex("^[0-9]{12}\\.dkr\\.ecr\\.[a-z0-9-]+\\.amazonaws\\.com/[a-z0-9._/-]+(:[A-Za-z0-9._-]+|@sha256:[a-f0-9]{64})$", var.image_uri)) && !endswith(var.image_uri, ":latest")
    error_message = "image_uri must be an ECR image with an explicit tag (not latest) or digest."
  }
}

variable "ssm_path" {
  type        = string
  description = "SSM path whose parameters become the container's environment, e.g. /taskboard/dev/ui."

  validation {
    condition     = can(regex("^/[a-z0-9/_-]+[a-z0-9]$", var.ssm_path))
    error_message = "ssm_path must start with / and contain only lowercase letters, digits, /, _ and -."
  }
}

variable "log_group_name" {
  type        = string
  description = "CloudWatch log group for the container (created by the iam module)."
}

variable "instance_type" {
  type        = string
  description = "EC2 instance type."
  default     = "t3.small"

  validation {
    condition     = can(regex("^[a-z][a-z0-9]*\\.[a-z0-9]+$", var.instance_type))
    error_message = "instance_type must look like t3.small."
  }
}

variable "ami_ssm_parameter" {
  type        = string
  description = "Public SSM parameter naming the AMI (Amazon Linux 2023 by default)."
  default     = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64"
}

variable "min_size" {
  type        = number
  description = "Minimum number of instances."
  default     = 2

  validation {
    condition     = var.min_size >= 1 && var.min_size <= 20
    error_message = "min_size must be between 1 and 20."
  }
}

variable "max_size" {
  type        = number
  description = "Maximum number of instances."
  default     = 4

  validation {
    condition     = var.max_size >= 1 && var.max_size <= 20
    error_message = "max_size must be between 1 and 20."
  }
}

variable "config_version" {
  type        = string
  description = "Fingerprint of the service's SSM configuration. Changing it creates a new launch template version, so the instance refresh rolls the new configuration out; it also orders instance creation after the parameters exist."

  validation {
    condition     = length(var.config_version) > 0
    error_message = "config_version must not be empty."
  }
}

variable "tags" {
  type        = map(string)
  description = "Tags added to every resource."
  default     = {}
}

variable "alb_security_group_id" {
  type        = string
  description = "Security group of the public ALB; the only allowed source of traffic."
}

variable "target_group_arn" {
  type        = string
  description = "ALB target group the instances register with."
}

variable "port" {
  type        = number
  description = "Port the UI container listens on."
  default     = 3000

  validation {
    condition     = var.port >= 1024 && var.port < 65536
    error_message = "port must be an unprivileged TCP port."
  }
}
