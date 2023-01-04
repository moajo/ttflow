from ttflow.system_states.event_log import _get_event_logs
from ttflow.ttflow import Client, Context, event_trigger


def _define_workflow_for_test(client: Client):
    # 外部から温度変化を受信する
    @client.workflow(trigger=event_trigger("workflows_changed"))
    def ワークフローのデプロイイベント(context: Context, webhook_args: dict):
        c = client.get_state(context, "デプロイ回数")
        if c is None:
            c = 0
        client.set_state(context, "デプロイ回数", c + 1)


def test_ワークフローハッシュが計算されること(client: Client):
    _define_workflow_for_test(client)

    s = client._global.state
    assert len(client._global.workflows) == 1
    assert s.read_state("workflows_hash") is None
    client.run()
    assert s.read_state("workflows_hash") is not None
    assert (
        len(
            [
                a
                for a in _get_event_logs(client._global)
                if a["event_name"] == "workflows_changed"
            ]
        )
        == 1
    ), "workflows_changedが発行されていること"

    h = s.read_state("workflows_hash")
    client.run()
    assert s.read_state("workflows_hash") == h
    assert (
        len(
            [
                a
                for a in _get_event_logs(client._global)
                if a["event_name"] == "workflows_changed"
            ]
        )
        == 1
    ), "workflows_changedが2回発行されていないこと"


def test_workflows_changedイベントが正しく処理されること(client: Client):
    _define_workflow_for_test(client)
    s = client._global.state

    assert s.read_state("デプロイ回数", default=0) == 0
    client.run()
    assert s.read_state("デプロイ回数") == 1
    client.run()
    assert s.read_state("デプロイ回数") == 1
