import json

from ttflow.core import _enque_event, _enque_webhook
from ttflow.core.event import _read_events_from_state
from ttflow.state_repository.on_memory_state import OnMemoryStateRepository
from ttflow.system_states.logs import _get_logs
from ttflow.ttflow import Client, Context, webhook_trigger

from .utils import create_client_for_test


def test_中断機能が正しく動くこと(client: Client):
    ttflow = client

    value = []

    @ttflow.workflow()
    def subefect(context: Context, arg: int):
        value.append(arg)

    @ttflow.workflow(trigger=webhook_trigger("test"))
    def CI(context: Context, webhook_args: dict):
        subefect(context, 1)
        承認待ち(context)
        subefect(context, 2)

    @ttflow.workflow()
    def 承認待ち(context: Context):
        ttflow.wait_event(context, f"承認")

    _enque_webhook(client._global, "test", {"値": "hoge"})
    results = client.run()

    assert len(results) == 1
    assert results[0].workflow_name == "CI"
    assert results[0].status == "paused"
    assert len(results[0].logs) == 0
    assert value == [1]

    results = client.run()
    assert value == [1]

    # 承認する
    _enque_event(client._global, f"承認", None)
    results = client.run()
    assert value == [1, 2]
