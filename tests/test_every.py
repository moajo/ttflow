from ttflow import Client, RunContext, every_trigger
from ttflow.core import _enque_event


def test_everyイベントの挙動テスト(client: Client):
    ttflow = client

    @ttflow.workflow(trigger=every_trigger())
    def main(c: RunContext, arg: int):
        c.log(f"hoge")

    results = client.run()

    assert len(results) == 1
    assert results[0].workflow_name == "main"
    assert results[0].status == "succeeded"
    assert len(results[0].logs) == 1

    results = client.run()

    assert len(results) == 1
    assert results[0].workflow_name == "main"
    assert results[0].status == "succeeded"
    assert len(results[0].logs) == 1
