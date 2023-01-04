from ttflow.system_states.completed import _get_completed_runs_log
from ttflow.ttflow import Client, Context


def test_正常系(client: Client):

    # 外部から温度変化を受信する
    @client.workflow(trigger=client.event("workflows_changed"))
    def ワークフローのデプロイイベント(context: Context, webhook_args: dict):
        print("ワークフローのデプロイイベントが発生しました")
        c = client.get_state(context, "デプロイ回数")
        if c is None:
            c = 0
        client.set_state(context, "デプロイ回数", c + 1)

    assert len(client._global.registerer.workflows) == 1

    client.run()

    assert [
        a["event_name"]
        for a in client._global.state.read_state("event_log", default=[])
    ] == [
        # "state_changed_workflow_loaded_successfull",  # 初回なので発行される
        "workflows_changed",  # 初回なので発行される
        "state_changed_デプロイ回数",  # 初回なので発行される
        "state_changed_completed",
    ]
    assert len(_get_completed_runs_log(client._global)) == 1


def test_正常系2(client: Client):

    # 外部から温度変化を受信する
    @client.workflow(trigger=client.event("workflows_changed"))
    def ワークフローのデプロイイベント(context: Context, webhook_args: dict):
        print("ワークフローのデプロイイベントが発生しました")
        c = client.get_state(context, "デプロイ回数")
        if c is None:
            c = 0
        client.set_state(context, "デプロイ回数", c + 1)

    assert len(client._global.registerer.workflows) == 1

    client.run()

    assert [
        a["event_name"]
        for a in client._global.state.read_state("event_log", default=[])
    ] == [
        "workflows_changed",  # 初回なので発行される
        "state_changed_デプロイ回数",  # 初回なので発行される
        "state_changed_completed",
    ]
    assert len(_get_completed_runs_log(client._global)) == 1


def test_空のワークフロー(client: Client):
    assert len(client._global.registerer.workflows) == 0
