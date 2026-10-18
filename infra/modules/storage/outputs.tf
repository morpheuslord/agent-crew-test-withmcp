output "bucket_name" {
  description = "Name of the attachments bucket (S3_BUCKET for the API)."
  value       = aws_s3_bucket.attachments.bucket
}

output "bucket_arn" {
  description = "ARN of the attachments bucket."
  value       = aws_s3_bucket.attachments.arn
}

output "kms_key_arn" {
  description = "KMS key encrypting the attachments."
  value       = aws_kms_key.attachments.arn
}
