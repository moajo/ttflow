from pathlib import Path

from ttflow.core import _get_state, _global, load_workflows
from ttflow.ttflow import do_ttflow


def test_ワークフローハッシュが計算されること(reset_global):
    s = _get_state()
    assert load_workflows(
        Path(__file__).parent / "data/workflow_for_test_load_workflow_hash_1"
    )
    assert len(_global.registerer.workflows) == 1
    assert s.read_state("workflow_loaded_successfull")
    assert s.read_state("workflows_hash") is not None
    do_ttflow()
    assert (
        len(
            [
                a
                for a in s.read_state("event_log", default=[])
                if a["event_name"] == "workflows_changed"
            ]
        )
        == 1
    ), "workflows_changedが発行されていること"

    h = s.read_state("workflows_hash")
    do_ttflow()
    assert s.read_state("workflows_hash") == h
    assert (
        len(
            [
                a
                for a in s.read_state("event_log", default=[])
                if a["event_name"] == "workflows_changed"
            ]
        )
        == 1
    ), "workflows_changedが2回発行されていないこと"


def test_workflows_changedイベントが正しく処理されること(reset_global):
    s = _get_state()
    assert load_workflows(
        Path(__file__).parent / "data/workflow_for_test_load_workflow_hash_1"
    )

    assert s.read_state("デプロイ回数", default=0) == 0
    do_ttflow()
    assert s.read_state("デプロイ回数") == 1
    do_ttflow()
    assert s.read_state("デプロイ回数") == 1
