import ttflow

# contextは実行IDが含まれる。read_stateとかは実行IDによってキャッシュされるので、リエントラントなワークフローを書ける
# 中断された場合、ttflow.PauseExceptionが発生する。


# 外部から温度変化を受信する
@ttflow.workflow(trigger=ttflow.event("workflows_changed"))
def ワークフローのデプロイイベント(context: ttflow.Context, webhook_args: dict):
    print("ワークフローのデプロイイベントが発生しました")
    c = ttflow.get_state(context, "デプロイ回数")
    if c is None:
        c = 0
    ttflow.set_state(context, "デプロイ回数", c + 1)


# 外部から温度変化を受信する
@ttflow.workflow(trigger=ttflow.webhook("温度変化"))
def 温度変化受信(context: ttflow.Context, webhook_args: dict):
    ttflow.set_state(context, "温度", webhook_args["温度"])


# 15度未満で赤、20度以上で緑
# 14->16->14となっても連続でアラートは発行しない
@ttflow.workflow(trigger=ttflow.state("温度"))
def 温度変化(context: ttflow.Context, data: dict):
    t = data["new"]
    state = ttflow.get_state(context, "温度状態")
    if t > 20:
        if state == "green":
            return
        notification_to_app(context, "温度が正常に戻りました")
        ttflow.set_state(context, "温度状態", "green")
    if t < 15:
        if state == "red":
            return
        notification_to_app(context, "温度が低すぎます")
        ttflow.set_state(context, "温度状態", "red")
        承認待ち(context, "温度低下アクションを承認してください")


def notification_to_app(context: ttflow.Context, message: str):
    # ここでアプリに通知を送信する
    ttflow.log(f"通知ダミー: {message}")


# @ttflow.workflow(trigger=ttflow.webhook("承認"))
# def 承認イベント(context:ttflow.Context,webhook_args:dict):
#     event_id = webhook_args["承認イベントID"]
#     ttflow.event(context, f"承認:{event_id}")

# @ttflow.workflow()
# def 承認待ち(context:ttflow.Context, message:str):
#     event_id = 1111
#     notification_to_app(context, "承認事項がが1件あります")
#     # send_承認(event_id) などとして承認依頼を送信する
#     ttflow.wait_event(context, f"承認:{event_id}")


@ttflow.workflow()
def 承認待ち(context: ttflow.Context, message: str):
    notification_to_app(context, f"承認事項がが1件あります:{context.run_id}")
    ttflow.wait_event(context, f"承認:{context.run_id}")
    print("承認待ち終了")
