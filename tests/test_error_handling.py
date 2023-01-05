from ttflow import Client, Context, event_trigger
from ttflow.system_states.completed import _get_completed_runs_log


def test_ワークフロー内の例外対応(client: Client):
    @client.workflow(trigger=event_trigger("workflows_changed"))
    def ワークフローのデプロイイベント(context: Context, args: dict):
        raise ValueError("hoge")

    assert len(client._global.workflows) == 1

    results = client.run()

    assert len(results) == 1
    assert results[0].workflow_name == "ワークフローのデプロイイベント"
    assert results[0].status == "failed"
    assert results[0].error_message == "ValueError('hoge')"

    assert len(_get_completed_runs_log(client._global)) == 1
    assert _get_completed_runs_log(client._global)[0]["status"] == "failed"
