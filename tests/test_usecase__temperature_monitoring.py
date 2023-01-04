import pytest
from ttflow import Client, RunContext, state_trigger
from ttflow.system_states.completed import _get_completed_runs_log
from ttflow.system_states.event_log import _get_event_logs


def _define_workflow_for_test(client: Client):
    ttflow = client

    # 外部から温度変化を受信する
    @ttflow.workflow(trigger="温度変化")
    def 温度変化受信(c: RunContext, args: dict):
        c.set_state("温度", args["温度"])

    # 15度未満で赤、20度以上で緑
    # 14->16->14となっても連続でアラートは発行しない
    @ttflow.workflow(trigger=state_trigger("温度"))
    def 温度変化(c: RunContext, data: dict):
        t = data["new"]
        state = c.get_state("温度状態")
        if t > 20:
            if state == "green":
                return
            notification_to_app(c, "温度が正常に戻りました")
            c.set_state("温度状態", "green")
        if t < 15:
            if state == "red":
                return
            notification_to_app(c, "温度が低すぎます")
            c.set_state("温度状態", "red")

    @ttflow.subeffect()
    def notification_to_app(c: RunContext, message: str):
        # ここでアプリに通知を送信する
        c.log(f"通知ダミー: {message}")


def test_温度監視ユースケースの処理1(client: Client):
    _define_workflow_for_test(client)
    assert len(client._global.workflows) == 2

    client.run()
    client.run("温度変化", {"温度": 20})  # 20なので温度状態は変化しない
    assert [a.event_name for a in client._global.events] == []
    assert len(_get_completed_runs_log(client._global)) == 2, "実行されたのは2回"
    assert [a["event_name"] for a in _get_event_logs(client._global)] == [
        "workflows_changed",
        "state_changed_温度",  # 実行によってstateが更新される
    ]


@pytest.mark.parametrize(
    "t, expect",
    [
        (20, "none"),
        (15, "none"),
        (21, "high"),
        (14, "low"),
    ],
)
def test_温度監視ユースケースの処理__温度状態が正しく変化する(t: int, expect: str, client: Client):
    _define_workflow_for_test(client)

    client.run()
    client.run("温度変化", {"温度": t})
    if expect == "none":
        assert len(_get_completed_runs_log(client._global)) == 2
        assert [a["event_name"] for a in _get_event_logs(client._global)] == [
            "workflows_changed",
            "state_changed_温度",
        ]
    elif expect == "high":
        assert len(_get_completed_runs_log(client._global)) == 2
        assert [a["event_name"] for a in _get_event_logs(client._global)] == [
            "workflows_changed",
            "state_changed_温度",
            "state_changed_温度状態",
        ]
        assert _get_event_logs(client._global)[2]["args"] == {
            "old": None,
            "new": "green",
        }
    elif expect == "low":
        assert len(_get_completed_runs_log(client._global)) == 2
        assert [a["event_name"] for a in _get_event_logs(client._global)] == [
            "workflows_changed",
            "state_changed_温度",
            "state_changed_温度状態",
        ]
        assert _get_event_logs(client._global)[2]["args"] == {
            "old": None,
            "new": "red",
        }


def test_温度監視ユースケースの処理__温度状態の読み書きが正しく動くこと(client: Client):
    _define_workflow_for_test(client)
    s = client._global.state

    assert s.read_state("温度状態") is None

    # client.run("")
    client.run("温度変化", {"温度": 20})
    event_log = [
        "workflows_changed",
        "state_changed_温度",
    ]
    assert [a["event_name"] for a in _get_event_logs(client._global)] == event_log
    assert s.read_state("温度状態") is None

    # stateが変化し、温度状態も変化
    client.run("温度変化", {"温度": 21})
    _get_completed_runs_log(client._global)[-1]["run_id"]
    event_log.extend(
        [
            "state_changed_温度",
            "state_changed_温度状態",
        ]
    )
    assert [a["event_name"] for a in _get_event_logs(client._global)] == event_log
    assert s.read_state("温度状態") == "green"

    # stateが変化するが、温度状態は変化しない
    client.run("温度変化", {"温度": 25})
    event_log.extend(
        [
            "state_changed_温度",
        ]
    )
    assert [a["event_name"] for a in _get_event_logs(client._global)] == event_log
    assert s.read_state("温度状態") == "green"

    # 同じ値なのでstateは変化しない
    client.run("温度変化", {"温度": 25})
    event_log.extend([])
    assert [a["event_name"] for a in _get_event_logs(client._global)] == event_log
    assert s.read_state("温度状態") == "green"

    # 温度は変わるが低すぎではない
    client.run("温度変化", {"温度": 15})
    event_log.extend(
        [
            "state_changed_温度",
        ]
    )
    assert [a["event_name"] for a in _get_event_logs(client._global)] == event_log
    assert s.read_state("温度状態") == "green"

    # 温度は低すぎ
    client.run("温度変化", {"温度": 10})
    event_log.extend(
        [
            "state_changed_温度",
            "state_changed_温度状態",
        ]
    )
    assert [a["event_name"] for a in _get_event_logs(client._global)] == event_log
    assert s.read_state("温度状態") == "red"

    # 温度は普通に戻るが高すぎない
    client.run("温度変化", {"温度": 18})
    event_log.extend(
        [
            "state_changed_温度",
        ]
    )
    assert [a["event_name"] for a in _get_event_logs(client._global)] == event_log
    assert s.read_state("温度状態") == "red"
