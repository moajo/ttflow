from ttflow import Client, RunContext, state_trigger
from ttflow.core import _enque_event


def test_変数の変化イベントが正しくトリガーされること(client: Client):
    ttflow = client

    value = []

    @ttflow.workflow(trigger=state_trigger("hoge"))
    def fuga(c: RunContext, arg: int):
        value.append(arg)

    @ttflow.workflow()
    def hoge(c: RunContext, args: dict):
        c.set_state("hoge", args["value"])

    results = client.run("hoge", {"value": 1})
    assert len(results) == 2
    assert results[0].workflow_name == "hoge"
    assert results[0].status == "succeeded"
    assert len(results[0].logs) == 0
    assert value == [{"new": 1, "old": None}]

    results = client.run("hoge", {"value": 3})
    assert value == [
        {"new": 1, "old": None},
        {"new": 3, "old": 1},
    ]
    results = client.run("hoge", {"value": 3})
    assert value == [
        {"new": 1, "old": None},
        {"new": 3, "old": 1},
    ]


def test_変数の変化イベントが正しくトリガーされること2(client: Client):
    ttflow = client

    value = []

    @ttflow.workflow(trigger=state_trigger("hoge"))
    def fuga(c: RunContext, arg: int):
        value.append(c.get_state("hoge"))

    @ttflow.workflow()
    def hoge(c: RunContext, args: dict):
        c.add_list_state("hoge", args["value"])

    results = client.run("hoge", {"value": 1})
    assert len(results) == 2
    assert results[0].workflow_name == "hoge"
    assert results[0].status == "succeeded"
    assert len(results[0].logs) == 0
    assert value == [[1]]

    results = client.run("hoge", {"value": 3})
    assert value == [
        [1],
        [1, 3],
    ]
    results = client.run("hoge", {"value": 3})
    assert value == [
        [1],
        [1, 3],
        [1, 3, 3],
    ]


def test_変数の変化イベントが正しくトリガーされること3(client: Client):
    ttflow = client

    value = []

    @ttflow.workflow(trigger=state_trigger("hoge"))
    def fuga(c: RunContext, arg: int):
        value.append(c.get_state("hoge"))

    @ttflow.workflow()
    def hoge(c: RunContext, args: dict):
        c.set_state("hoge", [1, 2, 3])

    @ttflow.workflow()
    def hoge2(c: RunContext, args: dict):
        a: list[int] = c.get_state("hoge")
        print(a)
        a.remove(2)
        c.set_state("hoge", a)

    results = client.run("hoge")
    assert len(results) == 2
    assert results[0].status == "succeeded"
    assert value == [[1, 2, 3]]

    results = client.run("hoge2")
    assert value == [
        [1, 2, 3],
        [1, 3],
    ]
