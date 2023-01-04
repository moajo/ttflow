import fire
from ttflow import Client, Context, event_trigger, setup, state_trigger, webhook_trigger


def _define_workflow(ttflow: Client):
    # 外部から温度変化を受信する
    @ttflow.workflow(trigger=event_trigger("workflows_changed"))
    def ワークフローのデプロイイベント(context: Context, webhook_args: dict):
        ttflow.log(context, "ワークフローのデプロイイベントが発生した")
        c = ttflow.get_state(context, "デプロイ回数")
        if c is None:
            c = 0
        ttflow.set_state(context, "デプロイ回数", c + 1)

    # 外部から温度変化を受信する
    @ttflow.workflow(trigger=webhook_trigger("温度変化"))
    def 温度変化受信(context: Context, webhook_args: dict):
        ttflow.set_state(context, "温度", webhook_args["温度"])

    # 15度未満で赤、20度以上で緑
    # 14->16->14となっても連続でアラートは発行しない
    @ttflow.workflow(trigger=state_trigger("温度"))
    def 温度変化(context: Context, data: dict):
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
            承認待ち(context)

    def notification_to_app(context: Context, message: str):
        # ここでアプリに通知を送信する
        ttflow.log(context, f"通知ダミー: {message}")

    @ttflow.workflow()
    def 承認待ち(context: Context):
        notification_to_app(context, f"承認事項がが1件あります:{context.run_id}")
        ttflow.wait_event(context, f"承認:{context.run_id}")
        ttflow.log(context, "承認待ち終了")

    @ttflow.workflow(trigger=webhook_trigger("承認"))
    def 承認受信(context: Context, webhook_args: dict):
        auth_id = webhook_args.get("id")
        if auth_id is None:
            ttflow.log(context, "不明なIDの承認が発生した")
            return

        ttflow.euqueue_event(f"承認:{auth_id}", None)


def webhook(name: str, arg: dict, state_rpository: str = "local:state.json"):
    ttflow = setup(
        state_repository=state_rpository,
    )
    ttflow.euqueue_webhook(name, arg)
    _define_workflow(ttflow)
    ttflow.run()


def run(state_rpository: str = "local:state.json"):
    ttflow = setup(
        state_repository=state_rpository,
    )
    _define_workflow(ttflow)
    ttflow.run()


def main() -> None:
    fire.Fire()


if __name__ == "__main__":
    main()
