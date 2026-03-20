# S3バケット（状態永続化用）
resource "aws_s3_bucket" "ttflow" {
  bucket = var.s3_bucket_name
}

# ACLを無効化し、バケットオーナーが全オブジェクトの所有者となる設定。
# 2023年4月以降に作成されたS3バケットではデフォルトでこの挙動だが、
# Terraformで明示的に設定しないとdriftが発生する可能性があるため定義しておく。
resource "aws_s3_bucket_ownership_controls" "ttflow" {
  bucket = aws_s3_bucket.ttflow.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

# Lambda関数
module "lambda" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "~> 8.0"

  function_name = var.function_name
  description   = var.description
  handler       = var.handler
  runtime       = var.runtime

  timeout     = var.timeout
  memory_size = var.memory_size

  source_path = var.source_path

  environment_variables = var.environment_variables

  # S3アクセス用IAMポリシー
  attach_policy_json = true
  policy_json = jsonencode({
    "Version" : "2012-10-17",
    "Statement" : [
      {
        "Effect" : "Allow",
        "Action" : ["s3:*"],
        "Resource" : [
          aws_s3_bucket.ttflow.arn,
          "${aws_s3_bucket.ttflow.arn}/*",
        ]
      },
    ]
  })

  # Lambda Function URL
  create_lambda_function_url = var.create_lambda_function_url
  authorization_type         = var.lambda_function_url_authorization_type

  # EventBridgeスケジュール実行
  create_current_version_allowed_triggers = false
  allowed_triggers = var.schedule_expression != null ? {
    ScheduleRule = {
      principal  = "events.amazonaws.com"
      source_arn = aws_cloudwatch_event_rule.ttflow[0].arn
    }
  } : {}
}

# EventBridgeスケジュールルール（schedule_expressionが指定された場合のみ作成）
resource "aws_cloudwatch_event_rule" "ttflow" {
  count = var.schedule_expression != null ? 1 : 0

  name                = var.function_name
  description         = var.description
  schedule_expression = var.schedule_expression
}

resource "aws_cloudwatch_event_target" "ttflow" {
  count = var.schedule_expression != null ? 1 : 0

  rule = aws_cloudwatch_event_rule.ttflow[0].name
  arn  = module.lambda.lambda_function_arn
}
