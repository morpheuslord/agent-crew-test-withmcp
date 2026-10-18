output "repository_urls" {
  description = "Repository URLs per service, for docker push and the instances' image references."
  value       = { for k, r in aws_ecr_repository.service : k => r.repository_url }
}

output "repository_arns" {
  description = "Repository ARNs per service, for IAM pull permissions."
  value       = { for k, r in aws_ecr_repository.service : k => r.arn }
}
