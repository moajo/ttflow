import json

from ttflow.core import _enque_event, _enque_webhook
from ttflow.state_repository.on_memory_state import OnMemoryStateRepository
from ttflow.system_states.logs import _get_logs
from ttflow.ttflow import Client, Context, webhook_trigger


def _define_workflow_for_test(ttflow: Client):
    @ttflow.workflow(trigger=webhook_trigger("デプロイCD"))
    def CI(context: Context, webhook_args: dict):
        c = ttflow.get_state(context, "CD開始回数")
        if c is None:
            c = 0
        ttflow.set_state(context, "CD開始回数", c + 1)
        hoge = webhook_args["値"]
        notification_to_app(context, f"{c}回目のCDを開始します: {hoge}")
        承認待ち(context)

        c = ttflow.get_state(context, "CD完了回数")
        if c is None:
            c = 0
        ttflow.set_state(context, "CD完了回数", c + 1)
        notification_to_app(context, "CD完了")

    @ttflow.workflow()
    def notification_to_app(context: Context, message: str):
        # ここでアプリに通知を送信する
        ttflow.log(context, f"通知ダミー: {message}")

    @ttflow.workflow()
    def 承認待ち(context: Context):
        notification_to_app(context, f"承認事項がが1件あります:{context.run_id}")
        ttflow.wait_event(context, f"承認:{context.run_id}")
        ttflow.log(context, "承認されました")


def test_中断機能が正しく動くこと(client: Client):
    _define_workflow_for_test(client)
    s = client._global.state
    assert isinstance(s, OnMemoryStateRepository)
    assert len(client._global.registerer.workflows) == 3

    assert s.read_state("CD開始回数") is None
    assert s.read_state("CD完了回数") is None

    _enque_webhook(client._global, "デプロイCD", {"値": "hoge"})
    client.run()
    assert len(s.read_state("paused_workflows", default=[])) == 1
    assert s.read_state("paused_workflows", default=[])[0]["workflow_name"] == "CI"
    run_id = s.read_state("paused_workflows", default=[])[0]["run_id"]
    assert s.read_state("paused_workflows", default=[])[0]["pause_id"] == f"{run_id}:7"
    assert s.read_state("paused_workflows", default=[])[0]["args"] == {"値": "hoge"}
    assert s.read_state("CD開始回数") == 1
    assert s.read_state("CD完了回数") is None
    assert _get_logs(client._global, run_id) == [
        "[ワークフローのログ]通知ダミー: 0回目のCDを開始します: hoge",
        f"[ワークフローのログ]通知ダミー: 承認事項がが1件あります:{run_id}",
    ]

    current = json.dumps(s.state, indent=2, sort_keys=True, ensure_ascii=False)
    client.run()
    assert (
        json.dumps(s.state, indent=2, sort_keys=True, ensure_ascii=False) == current
    ), "stateが変化していないこと"
    assert _get_logs(client._global, run_id) == [
        "[ワークフローのログ]通知ダミー: 0回目のCDを開始します: hoge",
        f"[ワークフローのログ]通知ダミー: 承認事項がが1件あります:{run_id}",
    ]

    # 承認する
    _enque_event(client._global, f"承認:{run_id}", None)
    client.run()
    client.run()  # イベントループより先に中断再開判定が入るので、2回実行する
    assert len(s.read_state("paused_workflows", default=[])) == 0
    assert s.read_state("CD開始回数") == 1
    assert s.read_state("CD完了回数") == 1
    assert _get_logs(client._global, run_id) == [
        "[ワークフローのログ]通知ダミー: 0回目のCDを開始します: hoge",
        f"[ワークフローのログ]通知ダミー: 承認事項がが1件あります:{run_id}",
        "[ワークフローのログ]承認されました",
        "[ワークフローのログ]通知ダミー: CD完了",
    ]


# TODO: 実装
# def test_中断機能が正しく動くこと_2重実行ケース():
#     s = OnMemoryS
