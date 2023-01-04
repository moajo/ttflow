from ttflow.system_states.completed import _get_completed_runs_log
from ttflow.system_states.event_log import _get_event_logs
from ttflow.ttflow import Client, Context, event_trigger


def _define_workflow_for_test(client: Client):
    # 外部から温度変化を受信する
    @client.workflow(trigger=event_trigger("workflows_changed"))
    def ワークフローのデプロイイベント(context: Context, webhook_args: dict):
        client.log(context, "デプロイイベントを受信しました")
        c = client.get_state(context, "デプロイ回数")
        if c is None:
            c = 0
        client.set_state(context, "デプロイ回数", c + 1)


def test_正常系(client: Client):
    _define_workflow_for_test(client)

    assert len(client._global.workflows) == 1

    results = client.run()

    assert len(results) == 1
    assert results[0].workflow_name == "ワークフローのデプロイイベント"
    assert results[0].status == "succeeded"
    assert len(results[0].logs) == 1
    assert results[0].logs[0] == "デプロイイベントを受信しました"

    assert [a["event_name"] for a in _get_event_logs(client._global)] == [
        "workflows_changed",  # 初回なので発行される
        "state_changed_デプロイ回数",  # 初回なので発行される
    ]
    assert len(_get_completed_runs_log(client._global)) == 1


def test_正常系2(client: Client):
    _define_workflow_for_test(client)

    assert len(client._global.workflows) == 1

    client.run()

    assert [a["event_name"] for a in _get_event_logs(client._global)] == [
        "workflows_changed",  # 初回なので発行される
        "state_changed_デプロイ回数",  # 初回なので発行される
    ]
    assert len(_get_completed_runs_log(client._global)) == 1


def test_空のワークフロー(client: Client):
    assert len(client._global.workflows) == 0
