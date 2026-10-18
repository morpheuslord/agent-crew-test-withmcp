output "vpc_id" {
  description = "ID of the VPC."
  value       = aws_vpc.this.id
}

output "vpc_cidr_block" {
  description = "CIDR block of the VPC."
  value       = aws_vpc.this.cidr_block
}

output "public_subnet_ids" {
  description = "Public subnets (ALB and NAT gateways only)."
  value       = aws_subnet.public[*].id
}

output "app_subnet_ids" {
  description = "Private subnets for the UI and API instances."
  value       = aws_subnet.app[*].id
}

output "data_subnet_ids" {
  description = "Private subnets without internet routes, for RDS and ElastiCache."
  value       = aws_subnet.data[*].id
}

output "nat_public_ips" {
  description = "Public IPs of the NAT gateways (the source address of outbound webhooks)."
  value       = aws_eip.nat[*].public_ip
}
