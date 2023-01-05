import logging
from typing import Optional

import fire
from ttflow import Client, RunContext, event_trigger, setup, state_trigger

logger = logging.getLogger(__name__)
# logging.basicConfig(level=logging.INFO)


def _define_workflow(ttflow: Client):
    # 外部から温度変化を受信する
    @ttflow.workflow(trigger=event_trigger("workflows_changed"))
    def ワークフロー更新(c: RunContext, args: dict):
        c.log("ワークフローのデプロイイベントが発生したよ")
        c.log("ワークフローのデプロイイベントが発生したよ")
        count = c.get_state("デプロイ回数")
        if count is None:
            count = 0
        c.set_state("デプロイ回数", count + 1)

    # 外部から温度変化を受信する
    @ttflow.workflow()
    def 温度変化受信(c: RunContext, args: dict):
        c.set_state("温度", args["温度"])

    # 15度未満で赤、20度以上で緑
    # 14->16->14となっても連続でアラートは発行しない
    @ttflow.workflow(trigger=state_trigger("温度"))
    def 温度変化(c: RunContext, data: dict):
        t = data["new"]
        state = c.get_state("温度状態")
        if t > 20:
            if state == "green":
                return
            notification_to_app(c, "温度が正常に戻りました")
            c.set_state("温度状態", "green")
        if t < 15:
            if state == "red":
                return
            notification_to_app(c, "温度が低すぎます")
            c.set_state("温度状態", "red")
            承認待ち(c)

    def notification_to_app(c: RunContext, message: str):
        # ここでアプリに通知を送信する
        c.log(f"通知ダミー: {message}")

    @ttflow.sideeffect()
    def 承認待ち(c: RunContext):
        notification_to_app(c, f"承認事項がが1件あります:{c.get_context_data().run_id}")
        c.wait_event(f"承認:{c.get_context_data().run_id}")
        c.log("承認待ち終了")

    @ttflow.workflow()
    def 承認受信(c: RunContext, args: dict):
        auth_id = args.get("id")
        if auth_id is None:
            c.log("不明なIDの承認が発生した")
            return

        c.event(f"承認:{auth_id}", None)


def run(
    name: Optional[str] = None,
    arg: dict = {},
    state_rpository: str = "local:states/sample.json",
):
    ttflow = setup(
        state_repository=state_rpository,
    )
    _define_workflow(ttflow)
    ttflow.run(name, arg)


def clear_state(state_rpository: str = "local:states/sample.json"):
    ttflow = setup(
        state_repository=state_rpository,
    )
    ttflow._global.state.clear_state()


def main() -> None:
    fire.Fire()


if __name__ == "__main__":
    main()
