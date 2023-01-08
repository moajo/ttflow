from ttflow import Client, RunContext, event_trigger
from ttflow.system_states.completed import _get_completed_runs_log
from ttflow.system_states.event_log import _get_event_logs


def _define_workflow_for_test(client: Client):
    @client.workflow(trigger=event_trigger("workflows_changed"))
    def ワークフローのデプロイイベント(c: RunContext, args: dict):
        """外部から温度変化を受信する"""
        c.log("デプロイイベントを受信しました")
        count = c.get_state("デプロイ回数")
        if count is None:
            count = 0
        c.set_state("デプロイ回数", count + 1)


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
    wfs = client.list_registered_workflows()
    assert len(wfs) == 1
    assert wfs[0].name == "ワークフローのデプロイイベント"
    assert wfs[0].description == "外部から温度変化を受信する"


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
