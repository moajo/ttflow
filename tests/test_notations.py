import pytest

from ttflow import Client, RunContext, event_trigger
from ttflow.system_states.completed import _get_completed_runs_log
from ttflow.system_states.event_log import _get_event_logs


def _define_workflow_for_test_1(client: Client):
    @client.workflow(trigger=event_trigger("workflows_changed"))
    def デプロイイベント(c: RunContext, args: dict):
        c.log("デプロイイベントを受信しました")


# 第2引数の省略
def _define_workflow_for_test_2(client: Client):
    @client.workflow(trigger=event_trigger("workflows_changed"))
    def デプロイイベント(c: RunContext):
        c.log("デプロイイベントを受信しました")


@pytest.mark.parametrize(
    "definer",
    [
        _define_workflow_for_test_1,
        # _define_workflow_for_test_2, # TODO: 対応する
    ],
)
def test_イベントトリガー_表記方法のテスト(definer, client: Client):
    definer(client)

    assert len(client._global.workflows) == 1

    results = client.run()

    assert len(results) == 1
    assert results[0].workflow_name == "デプロイイベント"
    assert results[0].status == "succeeded"
    assert len(results[0].logs) == 1
    assert results[0].logs[0] == "デプロイイベントを受信しました"

    assert [a["event_name"] for a in _get_event_logs(client._global)] == [
        "workflows_changed",  # 初回なので発行される
    ]
    assert len(_get_completed_runs_log(client._global)) == 1
