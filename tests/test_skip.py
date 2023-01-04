from ttflow.core import _enque_event, _enque_webhook
from ttflow.ttflow import Client, Context, webhook_trigger


def test_中断機能が正しく動くこと(client: Client):
    ttflow = client

    value = []

    @ttflow.subeffect()
    def subefect(context: Context, arg: int):
        value.append(arg)

    @ttflow.workflow(trigger=webhook_trigger("test"))
    def CI(context: Context, webhook_args: dict):
        subefect(context, 1)
        承認待ち(context)
        subefect(context, 2)

    @ttflow.subeffect()
    def 承認待ち(context: Context):
        ttflow.wait_event(context, "承認")

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
    _enque_event(client._global, "承認", None)
    results = client.run()
    assert value == [1, 2]


def test_abort(client: Client):
    ttflow = client

    @ttflow.workflow(trigger=webhook_trigger("test1"))
    def wf1(context: Context, webhook_args: dict):
        wf2(context)

    @ttflow.workflow(trigger=webhook_trigger("test2"))
    def wf2(context: Context):
        ttflow.log(context, "test")

    _enque_webhook(client._global, "test1", {"値": "hoge"})
    results = client.run()

    assert len(results) == 1
    assert results[0].workflow_name == "wf1"
    assert results[0].status == "failed"
    assert len(results[0].logs) == 0
    # TODO: エラーメッセージも取れるようにする
