from pathlib import Path

from ttflow.core import _global,load_workflows
from ttflow.ttflow import do_ttflow
from ttflow.state_repository.on_memory_state import OnMemoryStateRepository
from ttflow.system_states.completed import _get_completed_runs_log

def test_正常系():
    s = OnMemoryStateRepository()
    _global.state=s
    assert load_workflows(Path(__file__).parent / "data/workflow_for_test_load_1")
    assert len(_global.registerer.workflows)==1
    assert s.read_state("workflow_loaded_successfull") == True

    do_ttflow()

    assert [
        a["event_name"] for a in s.read_state("event_log",default=[])
    ] == [
        "state_changed_workflow_loaded_successfull", # 初回なので発行される
        'workflows_changed', # 初回なので発行される
         'state_changed_デプロイ回数', # 初回なので発行される
         'state_changed_completed',
        ]
    assert len(_get_completed_runs_log()) == 1

def test_正常系2():
    s = OnMemoryStateRepository()
    _global.state=s
    assert load_workflows(Path(__file__).parent / "data/workflow_for_test_load_2")
    assert len(_global.registerer.workflows)==1
    assert s.read_state("workflow_loaded_successfull") == True

    do_ttflow()

    assert [
        a["event_name"] for a in s.read_state("event_log",default=[])
    ] == [
        "state_changed_workflow_loaded_successfull", # 初回なので発行される
        'workflows_changed', # 初回なので発行される
         'state_changed_デプロイ回数', # 初回なので発行される
         'state_changed_completed',
        ]
    assert len(_get_completed_runs_log()) == 1


def test_空のワークフロー():
    s = OnMemoryStateRepository()
    _global.state=s
    assert load_workflows(Path(__file__).parent / "data/workflow_empty1")
    assert len(_global.registerer.workflows)==0
    assert s.read_state("workflow_loaded_successfull") == True

    s = OnMemoryStateRepository()
    _global.state=s
    assert not load_workflows(Path(__file__).parent / "data/workflow_empty2")
    assert s.read_state("workflow_loaded_successfull") == False

def test_不正なワークフロー():
    s = OnMemoryStateRepository()
    _global.state=s
    assert not load_workflows(Path(__file__).parent / "data/workflow_broken")
    assert s.read_state("workflow_loaded_successfull") == False
