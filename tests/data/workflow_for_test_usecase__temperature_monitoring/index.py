import ttflow

# 外部から温度変化を受信する
@ttflow.workflow(trigger=ttflow.webhook("温度変化"))
def 温度変化受信(context:ttflow.Context,webhook_args:dict):
    ttflow.set_state(context, "温度",webhook_args["温度"])


# 15度未満で赤、20度以上で緑
# 14->16->14となっても連続でアラートは発行しない
@ttflow.workflow(trigger=ttflow.state("温度"))
def 温度変化(context:ttflow.Context, data:dict):
    t = data["new"]
    state = ttflow.get_state(context, "温度状態")
    if t > 20:
        if state == "green":
            return
        notification_to_app(context, "温度が正常に戻りました")
        ttflow.set_state(context, "温度状態","green")
    if t < 15:
        if state == "red":
            return
        notification_to_app(context, "温度が低すぎます")
        ttflow.set_state(context, "温度状態","red")

@ttflow.workflow()
def notification_to_app(context:ttflow.Context, message:str):
    # ここでアプリに通知を送信する
    ttflow.log(context,f"通知ダミー: {message}")
