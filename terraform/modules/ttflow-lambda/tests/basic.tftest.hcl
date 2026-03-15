# terraform-aws-modules/lambda内部のdata sourceがmock環境で有効なJSONを返すようにする
override_data {
  target = module.lambda.data.aws_iam_policy_document.assume_role[0]
  values = {
    json = "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Principal\":{\"Service\":\"lambda.amazonaws.com\"},\"Action\":\"sts:AssumeRole\"}]}"
  }
}

override_data {
  target = module.lambda.data.aws_iam_policy_document.logs[0]
  values = {
    json = "{\"Version\":\"2012-10-17\",\"Statement\":[]}"
  }
}

mock_provider "aws" {}

# デフォルト値での基本テスト
run "basic_defaults" {
  command = plan

  variables {
    s3_bucket_name = "test-ttflow-bucket"
    source_path    = "./tests/fixtures"
  }

  # S3バケット名が正しいこと
  assert {
    condition     = aws_s3_bucket.ttflow.bucket == "test-ttflow-bucket"
    error_message = "S3バケット名が正しくない"
  }

  # S3 ownership controlsがBucketOwnerEnforcedであること
  assert {
    condition     = aws_s3_bucket_ownership_controls.ttflow.rule[0].object_ownership == "BucketOwnerEnforced"
    error_message = "S3 ownership controlsがBucketOwnerEnforcedでない"
  }

  # EventBridgeルールが作成されないこと（schedule_expression未指定）
  assert {
    condition     = length(aws_cloudwatch_event_rule.ttflow) == 0
    error_message = "schedule_expression未指定時にEventBridgeルールが作成されている"
  }

  # EventBridgeターゲットが作成されないこと
  assert {
    condition     = length(aws_cloudwatch_event_target.ttflow) == 0
    error_message = "schedule_expression未指定時にEventBridgeターゲットが作成されている"
  }
}

# カスタム値でのテスト
run "custom_values" {
  command = plan

  variables {
    function_name  = "my-workflow"
    description    = "カスタムワークフロー"
    s3_bucket_name = "my-custom-bucket"
    source_path    = "./tests/fixtures"
    handler        = "app.lambda_handler"
    runtime        = "python3.12"
    timeout        = 600
    memory_size    = 2048
    environment_variables = {
      ENV = "production"
    }
  }

  assert {
    condition     = aws_s3_bucket.ttflow.bucket == "my-custom-bucket"
    error_message = "カスタムS3バケット名が反映されていない"
  }
}

# スケジュール実行を有効にした場合のテスト
run "with_schedule" {
  command = plan

  variables {
    s3_bucket_name      = "test-ttflow-bucket"
    source_path         = "./tests/fixtures"
    schedule_expression = "cron(*/5 * * * ? *)"
  }

  # EventBridgeルールが作成されること
  assert {
    condition     = length(aws_cloudwatch_event_rule.ttflow) == 1
    error_message = "EventBridgeルールが作成されていない"
  }

  assert {
    condition     = aws_cloudwatch_event_rule.ttflow[0].schedule_expression == "cron(*/5 * * * ? *)"
    error_message = "スケジュール式が正しくない"
  }

  # EventBridgeターゲットが作成されること
  assert {
    condition     = length(aws_cloudwatch_event_target.ttflow) == 1
    error_message = "EventBridgeターゲットが作成されていない"
  }
}

# Function URL無効化のテスト
run "without_function_url" {
  command = plan

  variables {
    s3_bucket_name             = "test-ttflow-bucket"
    source_path                = "./tests/fixtures"
    create_lambda_function_url = false
  }

  # mock環境ではnullではなく空文字が返るため、nullまたは空文字を許容する
  assert {
    condition     = output.lambda_function_url == null || output.lambda_function_url == ""
    error_message = "Function URLが無効化されていない"
  }
}
