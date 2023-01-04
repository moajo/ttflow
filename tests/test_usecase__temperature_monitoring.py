from pathlib import Path

import pytest
from ttflow.core import _enque_webhook, _get_state
from ttflow.core.workflow import _global, load_workflows
from ttflow.system_states.completed import _get_completed_runs_log
from ttflow.ttflow import do_ttflow


def test_温度監視ユースケースの処理1(reset_global):
    s = _get_state()
    assert load_workflows(
        Path(__file__).parent / "data/workflow_for_test_usecase__temperature_monitoring"
    )
    assert len(_global.registerer.workflows) == 3
    assert s.read_state("workflow_loaded_successfull")

    _enque_webhook("温度変化", {"温度": 20})  # 20なので温度状態は変化しない
    do_ttflow()
    assert [a["event_name"] for a in _global.events] == []
    assert len(_get_completed_runs_log()) == 2, "実行されたのは2回"
    assert [a["event_name"] for a in s.read_state("event_log", default=[])] == [
        "state_changed_workflow_loaded_successfull",
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
def test_温度監視ユースケースの処理__温度状態が正しく変化する(t: int, expect: str, reset_global):
    s = _get_state()
    assert load_workflows(
        Path(__file__).parent / "data/workflow_for_test_usecase__temperature_monitoring"
    )

    _enque_webhook("温度変化", {"温度": t})
    do_ttflow()
    if expect == "none":
        assert len(_get_completed_runs_log()) == 2
        assert [a["event_name"] for a in s.read_state("event_log", default=[])] == [
            "state_changed_workflow_loaded_successfull",
            "workflows_changed",
            "_webhook_温度変化",
            "state_changed_温度",
            "state_changed_completed",
            "state_changed_completed",
        ]
    elif expect == "high":
        assert len(_get_completed_runs_log()) == 2
        run_id = _get_completed_runs_log()[-1]["run_id"]
        assert [a["event_name"] for a in s.read_state("event_log", default=[])] == [
            "state_changed_workflow_loaded_successfull",
            "workflows_changed",
            "_webhook_温度変化",
            "state_changed_温度",
            "state_changed_completed",
            f"state_changed_logs:{run_id}",
            "state_changed_温度状態",
            "state_changed_completed",
        ]
        assert s.read_state("event_log")[6]["args"] == {
            "old": None,
            "new": "green",
        }
    elif expect == "low":
        assert len(_get_completed_runs_log()) == 2
        run_id = _get_completed_runs_log()[-1]["run_id"]
        assert [a["event_name"] for a in s.read_state("event_log", default=[])] == [
            "state_changed_workflow_loaded_successfull",
            "workflows_changed",
            "_webhook_温度変化",
            "state_changed_温度",
            "state_changed_completed",
            f"state_changed_logs:{run_id}",
            "state_changed_温度状態",
            "state_changed_completed",
        ]
        assert s.read_state("event_log")[6]["args"] == {
            "old": None,
            "new": "red",
        }


def test_温度監視ユースケースの処理__温度状態の読み書きが正しく動くこと(reset_global):
    s = _get_state()
    assert load_workflows(
        Path(__file__).parent / "data/workflow_for_test_usecase__temperature_monitoring"
    )

    assert s.read_state("温度状態") is None

    _enque_webhook("温度変化", {"温度": 20})
    do_ttflow()
    event_log = [
        "state_changed_workflow_loaded_successfull",
        "workflows_changed",
        "_webhook_温度変化",
        "state_changed_温度",
        "state_changed_completed",
        "state_changed_completed",
    ]
    assert [a["event_name"] for a in s.read_state("event_log", default=[])] == event_log
    assert s.read_state("温度状態") is None

    # stateが変化し、温度状態も変化
    _enque_webhook("温度変化", {"温度": 21})
    do_ttflow()
    run_id = _get_completed_runs_log()[-1]["run_id"]
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
    _enque_webhook("温度変化", {"温度": 25})
    do_ttflow()
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
    _enque_webhook("温度変化", {"温度": 25})
    do_ttflow()
    event_log.extend(
        [
            "_webhook_温度変化",
            "state_changed_completed",
        ]
    )
    assert [a["event_name"] for a in s.read_state("event_log", default=[])] == event_log
    assert s.read_state("温度状態") == "green"

    # 温度は変わるが低すぎではない
    _enque_webhook("温度変化", {"温度": 15})
    do_ttflow()
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
    _enque_webhook("温度変化", {"温度": 10})
    do_ttflow()
    run_id = _get_completed_runs_log()[-1]["run_id"]
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
    _enque_webhook("温度変化", {"温度": 18})
    do_ttflow()
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
