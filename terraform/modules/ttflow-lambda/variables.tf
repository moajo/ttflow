variable "function_name" {
  description = "Lambda関数名"
  type        = string
  default     = "ttflow"
}

variable "description" {
  description = "Lambda関数の説明"
  type        = string
  default     = "ttflowワークフロー"
}

variable "handler" {
  description = "Lambdaハンドラ"
  type        = string
  default     = "main.handler"
}

variable "runtime" {
  description = "Lambdaランタイム"
  type        = string
  default     = "python3.9"
}

variable "timeout" {
  description = "Lambdaタイムアウト（秒）"
  type        = number
  default     = 300
}

variable "memory_size" {
  description = "Lambdaメモリサイズ（MB）"
  type        = number
  default     = 1024
}

variable "source_path" {
  description = "Lambdaデプロイパッケージのパス"
  type        = string
}

variable "s3_bucket_name" {
  description = "ttflow状態保存用S3バケット名"
  type        = string
}

variable "schedule_expression" {
  description = "EventBridgeスケジュール式（設定するとスケジュール実行が有効になる）"
  type        = string
  default     = null
}

variable "create_lambda_function_url" {
  description = "Lambda Function URLを作成するか"
  type        = bool
  default     = true
}

variable "lambda_function_url_authorization_type" {
  description = "Lambda Function URLの認証タイプ"
  type        = string
  default     = "NONE"
}

variable "environment_variables" {
  description = "Lambda環境変数"
  type        = map(string)
  default     = {}
}
