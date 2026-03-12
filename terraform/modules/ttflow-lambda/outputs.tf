output "lambda_function_arn" {
  description = "Lambda関数のARN"
  value       = module.lambda.lambda_function_arn
}

output "lambda_function_name" {
  description = "Lambda関数名"
  value       = module.lambda.lambda_function_name
}

output "lambda_function_url" {
  description = "Lambda Function URL"
  value       = try(module.lambda.lambda_function_url, null)
}

output "lambda_layer_arn" {
  description = "依存ライブラリ用Lambda LayerのARN"
  value       = module.dependencies_layer.lambda_layer_arn
}

output "s3_bucket_name" {
  description = "状態保存用S3バケット名"
  value       = aws_s3_bucket.ttflow.id
}

output "s3_bucket_arn" {
  description = "状態保存用S3バケットARN"
  value       = aws_s3_bucket.ttflow.arn
}

output "lambda_role_arn" {
  description = "Lambda実行ロールのARN"
  value       = module.lambda.lambda_role_arn
}
