import json

from ttflow.core import _enque_event, _enque_webhook
from ttflow.core.event import _read_events_from_state
from ttflow.state_repository.on_memory_state import OnMemoryStateRepository
from ttflow.system_states.logs import _get_logs
from ttflow.ttflow import Client, Context, webhook_trigger

from .utils import create_client_for_test


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

    @ttflow.subeffect()
    def notification_to_app(context: Context, message: str):
        # ここでアプリに通知を送信する
        ttflow.log(context, f"通知ダミー: {message}")

    @ttflow.subeffect()
    def 承認待ち(context: Context):
        notification_to_app(context, f"承認事項がが1件あります:{context.run_id}")
        ttflow.wait_event(context, f"承認:{context.run_id}")
        ttflow.log(context, "承認されました")


def test_中断機能が正しく動くこと(client: Client):
    _define_workflow_for_test(client)
    s = client._global.state
    assert isinstance(s, OnMemoryStateRepository)
    assert len(client._global.workflows) == 1

    assert s.read_state("CD開始回数") is None
    assert s.read_state("CD完了回数") is None

    _enque_webhook(client._global, "デプロイCD", {"値": "hoge"})
    results = client.run()
    assert len(results) == 1
    assert results[0].workflow_name == "CI"
    assert results[0].status == "paused"
    assert len(results[0].logs) == 2
    assert results[0].logs == [
        "通知ダミー: 0回目のCDを開始します: hoge",
        f"通知ダミー: 承認事項がが1件あります:{results[0].run_id}",
    ]

    paused_event = _read_events_from_state(client._global)
    assert len(client._global.events_for_next_run) == 0, "commitされてるので0"
    assert len(paused_event) == 1
    assert s.read_state("CD開始回数") == 1
    assert s.read_state("CD完了回数") is None
    run_id = paused_event[0].args["run_id"]
    assert _get_logs(client._global, run_id) == [
        "通知ダミー: 0回目のCDを開始します: hoge",
        f"通知ダミー: 承認事項がが1件あります:{run_id}",
    ]

    current = json.loads(
        json.dumps(s.state, indent=2, sort_keys=True, ensure_ascii=False)
    )
    current["_events"] = []  # paused eventは更新されるので無視する
    results = client.run()
    assert len(results) == 1
    assert results[0].workflow_name == "CI"
    assert results[0].status == "paused"
    assert len(results[0].logs) == 2
    assert results[0].logs == [
        "通知ダミー: 0回目のCDを開始します: hoge",
        f"通知ダミー: 承認事項がが1件あります:{results[0].run_id}",
    ]
    paused_event = _read_events_from_state(client._global)
    assert len(client._global.events_for_next_run) == 0, "commitされてるので0"
    assert len(paused_event) == 1
    new_state = json.loads(
        json.dumps(s.state, indent=2, sort_keys=True, ensure_ascii=False)
    )
    new_state["_events"] = []  # paused eventは更新されるので無視する
    assert new_state == current, "stateが変化していないこと"
    assert _get_logs(client._global, run_id) == [
        "通知ダミー: 0回目のCDを開始します: hoge",
        f"通知ダミー: 承認事項がが1件あります:{run_id}",
    ]

    # 承認する
    _enque_event(client._global, f"承認:{run_id}", None)
    results = client.run()
    assert len(results) == 1
    assert results[0].workflow_name == "CI"
    assert results[0].status == "succeeded"
    assert len(results[0].logs) == 4
    assert results[0].logs == [
        "通知ダミー: 0回目のCDを開始します: hoge",
        f"通知ダミー: 承認事項がが1件あります:{results[0].run_id}",
        "承認されました",
        "通知ダミー: CD完了",
    ]

    assert len(s.read_state("paused_workflows", default=[])) == 0
    assert s.read_state("CD開始回数") == 1
    assert s.read_state("CD完了回数") == 1
    assert _get_logs(client._global, run_id) == [
        "通知ダミー: 0回目のCDを開始します: hoge",
        f"通知ダミー: 承認事項がが1件あります:{run_id}",
        "承認されました",
        "通知ダミー: CD完了",
    ]


def test_中断イベントは永続化される():
    client = create_client_for_test()
    _define_workflow_for_test(client)

    _enque_webhook(client._global, "デプロイCD", {"値": "hoge"})
    client.run()
    assert len(client._global.events_for_next_run) == 0, "commitされてるので0"
    paused_event = _read_events_from_state(client._global)
    assert len(paused_event) == 1

    # reloadする
    client._global.purge_events()
    _define_workflow_for_test(client)
    client.run()
    assert len(client._global.events_for_next_run) == 0, "commitされてるので0"
    paused_event = _read_events_from_state(client._global)
    assert len(paused_event) == 1
    run_id = paused_event[0].args["run_id"]

    # 承認する
    _enque_event(client._global, f"承認:{run_id}", None)
    client.run()
    assert client._global.state.read_state("CD開始回数") == 1
    assert client._global.state.read_state("CD完了回数") == 1
    assert _get_logs(client._global, run_id) == [
        "通知ダミー: 0回目のCDを開始します: hoge",
        f"通知ダミー: 承認事項がが1件あります:{run_id}",
        "承認されました",
        "通知ダミー: CD完了",
    ]


# TODO: 実装
# def test_中断機能が正しく動くこと_2重実行ケース():
#     s = OnMemoryS
