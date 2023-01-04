import pytest
from ttflow.core import _enque_webhook
from ttflow.system_states.completed import _get_completed_runs_log
from ttflow.ttflow import Client, Context


def _define_workflow_for_test(client: Client):
    ttflow = client

    # 外部から温度変化を受信する
    @ttflow.workflow(trigger=ttflow.webhook("温度変化"))
    def 温度変化受信(context: Context, webhook_args: dict):
        ttflow.set_state(context, "温度", webhook_args["温度"])

    # 15度未満で赤、20度以上で緑
    # 14->16->14となっても連続でアラートは発行しない
    @ttflow.workflow(trigger=ttflow.state("温度"))
    def 温度変化(context: Context, data: dict):
        t = data["new"]
        state = ttflow.get_state(context, "温度状態")
        if t > 20:
            if state == "green":
                return
            notification_to_app(context, "温度が正常に戻りました")
            ttflow.set_state(context, "温度状態", "green")
        if t < 15:
            if state == "red":
                return
            notification_to_app(context, "温度が低すぎます")
            ttflow.set_state(context, "温度状態", "red")

    @ttflow.workflow()
    def notification_to_app(context: Context, message: str):
        # ここでアプリに通知を送信する
        ttflow.log(context, f"通知ダミー: {message}")


def test_温度監視ユースケースの処理1(client: Client):
    _define_workflow_for_test(client)
    s = client._global.state
    assert len(client._global.registerer.workflows) == 3

    client.run()
    _enque_webhook(client._global, "温度変化", {"温度": 20})  # 20なので温度状態は変化しない
    client.run()
    assert [a["event_name"] for a in client._global.events] == []
    assert len(_get_completed_runs_log(client._global)) == 2, "実行されたのは2回"
    assert [a["event_name"] for a in s.read_state("event_log", default=[])] == [
        "workflows_changed",
        "_webhook_温度変化",
        "state_changed_温度",  # 実行によってstateが更新される
        "state_changed_completed",
        "state_changed_completed",
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
    _enque_webhook(client._global, "温度変化", {"温度": t})
    client.run()
    s = client._global.state
    if expect == "none":
        assert len(_get_completed_runs_log(client._global)) == 2
        assert [
            a["event_name"]
            for a in client._global.state.read_state("event_log", default=[])
        ] == [
            "workflows_changed",
            "_webhook_温度変化",
            "state_changed_温度",
            "state_changed_completed",
            "state_changed_completed",
        ]
    elif expect == "high":
        assert len(_get_completed_runs_log(client._global)) == 2
        run_id = _get_completed_runs_log(client._global)[-1]["run_id"]
        assert [
            a["event_name"]
            for a in client._global.state.read_state("event_log", default=[])
        ] == [
            "workflows_changed",
            "_webhook_温度変化",
            "state_changed_温度",
            "state_changed_completed",
            f"state_changed_logs:{run_id}",
            "state_changed_温度状態",
            "state_changed_completed",
        ]
        assert client._global.state.read_state("event_log")[5]["args"] == {
            "old": None,
            "new": "green",
        }
    elif expect == "low":
        assert len(_get_completed_runs_log(client._global)) == 2
        run_id = _get_completed_runs_log(client._global)[-1]["run_id"]
        assert [a["event_name"] for a in s.read_state("event_log", default=[])] == [
            "workflows_changed",
            "_webhook_温度変化",
            "state_changed_温度",
            "state_changed_completed",
            f"state_changed_logs:{run_id}",
            "state_changed_温度状態",
            "state_changed_completed",
        ]
        assert s.read_state("event_log")[5]["args"] == {
            "old": None,
            "new": "red",
        }


def test_温度監視ユースケースの処理__温度状態の読み書きが正しく動くこと(client: Client):
    _define_workflow_for_test(client)
    s = client._global.state

    assert s.read_state("温度状態") is None

    client.run()
    _enque_webhook(client._global, "温度変化", {"温度": 20})
    client.run()
    event_log = [
        "workflows_changed",
        "_webhook_温度変化",
        "state_changed_温度",
        "state_changed_completed",
        "state_changed_completed",
    ]
    assert [a["event_name"] for a in s.read_state("event_log", default=[])] == event_log
    assert s.read_state("温度状態") is None

    # stateが変化し、温度状態も変化
    _enque_webhook(client._global, "温度変化", {"温度": 21})
    client.run()
    run_id = _get_completed_runs_log(client._global)[-1]["run_id"]
    event_log.extend(
        [
            "_webhook_温度変化",
            "state_changed_温度",
            "state_changed_completed",
            f"state_changed_logs:{run_id}",
            "state_changed_温度状態",
            "state_changed_completed",
        ]
    )
    assert [a["event_name"] for a in s.read_state("event_log", default=[])] == event_log
    assert s.read_state("温度状態") == "green"

    # stateが変化するが、温度状態は変化しない
    _enque_webhook(client._global, "温度変化", {"温度": 25})
    client.run()
    event_log.extend(
        [
            "_webhook_温度変化",
            "state_changed_温度",
            "state_changed_completed",
            "state_changed_completed",
        ]
    )
    assert [a["event_name"] for a in s.read_state("event_log", default=[])] == event_log
    assert s.read_state("温度状態") == "green"

    # 同じ値なのでstateは変化しない
    _enque_webhook(client._global, "温度変化", {"温度": 25})
    client.run()
    event_log.extend(
        [
            "_webhook_温度変化",
            "state_changed_completed",
        ]
    )
    assert [a["event_name"] for a in s.read_state("event_log", default=[])] == event_log
    assert s.read_state("温度状態") == "green"

    # 温度は変わるが低すぎではない
    _enque_webhook(client._global, "温度変化", {"温度": 15})
    client.run()
    event_log.extend(
        [
            "_webhook_温度変化",
            "state_changed_温度",
            "state_changed_completed",
            "state_changed_completed",
        ]
    )
    assert [a["event_name"] for a in s.read_state("event_log", default=[])] == event_log
    assert s.read_state("温度状態") == "green"

    # 温度は低すぎ
    _enque_webhook(client._global, "温度変化", {"温度": 10})
    client.run()
    run_id = _get_completed_runs_log(client._global)[-1]["run_id"]
    event_log.extend(
        [
            "_webhook_温度変化",
            "state_changed_温度",
            "state_changed_completed",
            f"state_changed_logs:{run_id}",
            "state_changed_温度状態",
            "state_changed_completed",
        ]
    )
    assert [a["event_name"] for a in s.read_state("event_log", default=[])] == event_log
    assert s.read_state("温度状態") == "red"

    # 温度は普通に戻るが高すぎない
    _enque_webhook(client._global, "温度変化", {"温度": 18})
    client.run()
    event_log.extend(
        [
            "_webhook_温度変化",
            "state_changed_温度",
            "state_changed_completed",
            "state_changed_completed",
        ]
    )
    assert [a["event_name"] for a in s.read_state("event_log", default=[])] == event_log
    assert s.read_state("温度状態") == "red"