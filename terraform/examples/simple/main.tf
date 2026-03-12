provider "aws" {
  region = "ap-northeast-1"
}

module "ttflow" {
  source = "github.com/moajo/ttflow//terraform/modules/ttflow-lambda"

  function_name     = "ttflow"
  s3_bucket_name    = "ttflow-main"
  source_path       = "${path.module}/src"              # ワークフロー.pyファイル群
  pip_requirements_path = "${path.module}/requirements.txt" # 依存定義（ttflow含む）

  # 5分おきにスケジュール実行する場合
  # schedule_expression = "cron(*/5 * * * ? *)"
}

output "function_url" {
  value = module.ttflow.lambda_function_url
}
