from ttflow import Client, RunContext
from ttflow.core import _enque_event


def test_中断時の実行スキップが正しく動くこと(client: Client):
    ttflow = client

    value = []

    @ttflow.sideeffect()
    def sideefect(c: RunContext, arg: int):
        value.append(arg)

    @ttflow.workflow()
    def CI(c: RunContext, args: dict):
        sideefect(c, 1)
        承認待ち(c)
        sideefect(c, 2)

    @ttflow.sideeffect()
    def 承認待ち(c: RunContext):
        c.wait_event("承認")

    results = client.run("CI", {"値": "hoge"})

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


def test_中断時の実行スキップが正しく動くこと2(client: Client):
    ttflow = client

    value = []

    @ttflow.sideeffect()
    def sideefect(c: RunContext, arg: int):
        c.log(f"sideefect {arg}")
        value.append(arg)
        sideefect2(c, arg * 10)

    @ttflow.sideeffect()
    def sideefect2(c: RunContext, arg: int):
        c.log(f"sideefect2 {arg}")
        value.append(arg)

    @ttflow.workflow()
    def CI(c: RunContext, args: dict):
        sideefect(c, 1)
        承認待ち(c)
        sideefect(c, 2)

    @ttflow.sideeffect()
    def 承認待ち(c: RunContext):
        c.wait_event("承認")

    results = client.run("CI", {"値": "hoge"})

    assert len(results) == 1
    assert results[0].workflow_name == "CI"
    assert results[0].status == "paused"
    assert results[0].logs == [
        "sideefect 1",
        "sideefect2 10",
    ]
    assert value == [1, 10]

    results = client.run()
    assert value == [1, 10]

    # 承認する
    _enque_event(client._global, "承認", None)
    results = client.run()
    assert value == [1, 10, 2, 20]


def test_abort(client: Client):
    ttflow = client

    @ttflow.workflow(trigger="test1")
    def wf1(c: RunContext, args: dict):
        wf2(c)

    @ttflow.workflow(trigger="test2")
    def wf2(c: RunContext):
        c.log("test")

    results = client.run("test1", {"値": "hoge"})

    assert len(results) == 1
    assert results[0].workflow_name == "wf1"
    assert results[0].status == "failed"
    assert (
        results[0].error_message
        == "RuntimeError('workflow can not be called directly')"
    )
    assert len(results[0].logs) == 0


def test_無限ループ対応(client: Client):
    ttflow = client

    @ttflow.workflow()
    def loop(c: RunContext, args: dict):
        count = 0
        while True:
            c.log(f"A:{count}")
            c.pause_once()
            c.log(f"B:{count}")
            count += 1
            if count > 3:
                break

    results = client.run("loop")

    logs = ["A:0"]

    assert len(results) == 1
    assert results[0].workflow_name == "loop"
    assert results[0].status == "paused"
    assert results[0].logs == logs

    results = client.run()
    assert results[0].workflow_name == "loop"
    assert results[0].status == "paused"
    logs.extend(["B:0", "A:1"])
    assert results[0].logs == logs

    results = client.run()
    assert results[0].workflow_name == "loop"
    assert results[0].status == "paused"
    logs.extend(["B:1", "A:2"])
    assert results[0].logs == logs

    results = client.run()
    assert results[0].workflow_name == "loop"
    assert results[0].status == "paused"
    logs.extend(["B:2", "A:3"])
    assert results[0].logs == logs

    results = client.run()
    assert results[0].workflow_name == "loop"
    assert results[0].status == "succeeded"
    logs.extend(["B:3"])
    assert results[0].logs == logs
