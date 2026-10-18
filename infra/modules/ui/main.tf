data "aws_region" "current" {}

data "aws_ssm_parameter" "ami" {
  name = var.ami_ssm_parameter
}

resource "aws_security_group" "ui" {
  name        = "${var.name}-ui"
  description = "UI instances: traffic only from the public ALB."
  vpc_id      = var.vpc_id
  tags        = merge(var.tags, { Name = "${var.name}-ui" })
}

resource "aws_vpc_security_group_ingress_rule" "from_alb" {
  security_group_id            = aws_security_group.ui.id
  description                  = "UI port from the public load balancer"
  referenced_security_group_id = var.alb_security_group_id
  ip_protocol                  = "tcp"
  from_port                    = var.port
  to_port                      = var.port
}

resource "aws_vpc_security_group_egress_rule" "to_vpc_http" {
  security_group_id = aws_security_group.ui.id
  description       = "To the internal API load balancer"
  cidr_ipv4         = var.vpc_cidr_block
  ip_protocol       = "tcp"
  from_port         = 80
  to_port           = 80
}

resource "aws_vpc_security_group_egress_rule" "to_aws_https" {
  security_group_id = aws_security_group.ui.id
  description       = "HTTPS to AWS APIs (ECR, SSM, CloudWatch) via NAT"
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "tcp"
  from_port         = 443
  to_port           = 443
}

resource "aws_launch_template" "ui" {
  name_prefix   = "${var.name}-ui-"
  image_id      = data.aws_ssm_parameter.ami.value
  instance_type = var.instance_type
  user_data = base64encode(templatefile("${path.module}/templates/user_data.sh.tftpl", {
    region    = data.aws_region.current.region
    registry  = split("/", var.image_uri)[0]
    image     = var.image_uri
    ssm_path  = var.ssm_path
    log_group = var.log_group_name
    port      = var.port
  }))

  iam_instance_profile {
    name = var.instance_profile_name
  }

  network_interfaces {
    associate_public_ip_address = false
    security_groups             = [aws_security_group.ui.id]
  }

  # IMDSv2 only; a hop limit of 1 keeps bridge-networked containers away from the metadata service.
  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
    instance_metadata_tags      = "disabled"
  }

  block_device_mappings {
    device_name = "/dev/xvda"
    ebs {
      volume_size           = 20
      volume_type           = "gp3"
      encrypted             = true
      delete_on_termination = true
    }
  }

  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags          = merge(var.tags, { Name = "${var.name}-ui" })
  }

  tags = merge(var.tags, { ConfigVersion = var.config_version })
}

resource "aws_autoscaling_group" "ui" {
  name                      = "${var.name}-ui"
  vpc_zone_identifier       = var.subnet_ids
  min_size                  = var.min_size
  max_size                  = var.max_size
  desired_capacity          = var.min_size
  target_group_arns         = [var.target_group_arn]
  health_check_type         = "ELB"
  health_check_grace_period = 180

  launch_template {
    id      = aws_launch_template.ui.id
    version = aws_launch_template.ui.latest_version
  }

  # A new image or configuration rolls through the fleet without downtime.
  instance_refresh {
    strategy = "Rolling"
    preferences {
      min_healthy_percentage = 50
    }
  }

  dynamic "tag" {
    for_each = merge(var.tags, { Name = "${var.name}-ui" })
    content {
      key                 = tag.key
      value               = tag.value
      propagate_at_launch = true
    }
  }
}
