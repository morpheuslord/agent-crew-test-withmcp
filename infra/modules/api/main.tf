data "aws_region" "current" {}

data "aws_ssm_parameter" "ami" {
  name = var.ami_ssm_parameter
}

# ---------------------------------------------------------------------------------------------
# Internal load balancer: the only way to reach the API, and only from the UI security group.
# ---------------------------------------------------------------------------------------------

resource "aws_security_group" "lb" {
  name        = "${var.name}-api-lb"
  description = "Internal API load balancer: reachable only from the UI instances."
  vpc_id      = var.vpc_id
  tags        = merge(var.tags, { Name = "${var.name}-api-lb" })
}

resource "aws_vpc_security_group_ingress_rule" "lb_from_ui" {
  security_group_id            = aws_security_group.lb.id
  description                  = "HTTP from the UI instances"
  referenced_security_group_id = var.client_security_group_id
  ip_protocol                  = "tcp"
  from_port                    = 80
  to_port                      = 80
}

resource "aws_vpc_security_group_egress_rule" "lb_to_api" {
  security_group_id            = aws_security_group.lb.id
  description                  = "To the API instances"
  referenced_security_group_id = aws_security_group.api.id
  ip_protocol                  = "tcp"
  from_port                    = var.port
  to_port                      = var.port
}

resource "aws_lb" "internal" {
  name                       = "${var.name}-api"
  load_balancer_type         = "application"
  internal                   = true
  security_groups            = [aws_security_group.lb.id]
  subnets                    = var.subnet_ids
  drop_invalid_header_fields = true
  tags                       = var.tags
}

resource "aws_lb_target_group" "api" {
  name                 = "${var.name}-api"
  port                 = var.port
  protocol             = "HTTP"
  vpc_id               = var.vpc_id
  target_type          = "instance"
  deregistration_delay = 30
  tags                 = var.tags

  health_check {
    path                = "/healthz"
    matcher             = "200"
    interval            = 15
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 5
  }
}

resource "aws_lb_listener" "api" {
  load_balancer_arn = aws_lb.internal.arn
  port              = 80
  protocol          = "HTTP"
  tags              = var.tags

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.api.arn
  }
}

# ---------------------------------------------------------------------------------------------
# API instances
# ---------------------------------------------------------------------------------------------

resource "aws_security_group" "api" {
  name        = "${var.name}-api"
  description = "API instances: traffic only from the internal load balancer."
  vpc_id      = var.vpc_id
  tags        = merge(var.tags, { Name = "${var.name}-api" })
}

resource "aws_vpc_security_group_ingress_rule" "api_from_lb" {
  security_group_id            = aws_security_group.api.id
  description                  = "API port from the internal load balancer"
  referenced_security_group_id = aws_security_group.lb.id
  ip_protocol                  = "tcp"
  from_port                    = var.port
  to_port                      = var.port
}

resource "aws_vpc_security_group_egress_rule" "api_to_postgres" {
  security_group_id = aws_security_group.api.id
  description       = "PostgreSQL inside the VPC"
  cidr_ipv4         = var.vpc_cidr_block
  ip_protocol       = "tcp"
  from_port         = 5432
  to_port           = 5432
}

resource "aws_vpc_security_group_egress_rule" "api_to_cache" {
  security_group_id = aws_security_group.api.id
  description       = "Cache inside the VPC"
  cidr_ipv4         = var.vpc_cidr_block
  ip_protocol       = "tcp"
  from_port         = 6379
  to_port           = 6379
}

resource "aws_vpc_security_group_egress_rule" "api_https" {
  security_group_id = aws_security_group.api.id
  description       = "HTTPS to AWS APIs (S3, ECR, SSM, CloudWatch) and to https webhook receivers"
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "tcp"
  from_port         = 443
  to_port           = 443
}

resource "aws_launch_template" "api" {
  name_prefix   = "${var.name}-api-"
  image_id      = data.aws_ssm_parameter.ami.value
  instance_type = var.instance_type
  user_data = base64encode(templatefile("${path.module}/templates/user_data.sh.tftpl", {
    region    = data.aws_region.current.region
    registry  = split("/", var.image_uri)[0]
    image     = var.image_uri
    ssm_path  = var.ssm_path
    log_group = var.log_group_name
  }))

  iam_instance_profile {
    name = var.instance_profile_name
  }

  network_interfaces {
    associate_public_ip_address = false
    security_groups             = [aws_security_group.api.id]
  }

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
    tags          = merge(var.tags, { Name = "${var.name}-api" })
  }

  tags = merge(var.tags, { ConfigVersion = var.config_version })
}

resource "aws_autoscaling_group" "api" {
  name                      = "${var.name}-api"
  vpc_zone_identifier       = var.subnet_ids
  min_size                  = var.min_size
  max_size                  = var.max_size
  desired_capacity          = var.min_size
  target_group_arns         = [aws_lb_target_group.api.arn]
  health_check_type         = "ELB"
  health_check_grace_period = 180

  launch_template {
    id      = aws_launch_template.api.id
    version = aws_launch_template.api.latest_version
  }

  instance_refresh {
    strategy = "Rolling"
    preferences {
      min_healthy_percentage = 50
    }
  }

  dynamic "tag" {
    for_each = merge(var.tags, { Name = "${var.name}-api" })
    content {
      key                 = tag.key
      value               = tag.value
      propagate_at_launch = true
    }
  }
}
