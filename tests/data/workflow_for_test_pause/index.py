import ttflow

@ttflow.workflow(trigger=ttflow.webhook("デプロイCD"))
def CI(context:ttflow.Context,webhook_args:dict):
    c = ttflow.get_state(context, "CD開始回数")
    if c is None:
        c = 0
    ttflow.set_state(context, "CD開始回数",c+1)
    hoge=webhook_args["値"]
    notification_to_app(context, f"{c}回目のCDを開始します: {hoge}")
    承認待ち(context)

    c = ttflow.get_state(context, "CD完了回数")
    if c is None:
        c = 0
    ttflow.set_state(context, "CD完了回数",c+1)
    notification_to_app(context, "CD完了")
    

@ttflow.workflow()
def notification_to_app(context:ttflow.Context, message:str):
    # ここでアプリに通知を送信する
    ttflow.log(context,f"通知ダミー: {message}")

@ttflow.workflow()
def 承認待ち(context:ttflow.Context):
    notification_to_app(context, f"承認事項がが1件あります:{context.run_id}")
    ttflow.wait_event(context, f"承認:{context.run_id}")
    ttflow.log(context,f"承認されました")
