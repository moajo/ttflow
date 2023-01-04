from pathlib import Path
import json

import pytest

from ttflow.ttflow import do_ttflow
from ttflow.core import _global,load_workflows
from ttflow.core.global_env import _get_state
from ttflow.core import _enque_webhook,_enque_event
from ttflow.system_states.logs import _get_logs

def test_中断機能が正しく動くこと(reset_global):
    s=_get_state()
    assert load_workflows(Path(__file__).parent / "data/workflow_for_test_pause")
    assert len(_global.registerer.workflows)==3
    assert s.read_state("workflow_loaded_successfull") == True

    assert s.read_state("CD開始回数") is None
    assert s.read_state("CD完了回数") is None

    _enque_webhook("デプロイCD",{"値":"hoge"}) 
    do_ttflow()
    assert len(s.read_state("paused_workflows",default=[]))==1
    assert s.read_state("paused_workflows",default=[])[0]["workflow_name"] == "CI"
    run_id = s.read_state("paused_workflows",default=[])[0]["run_id"]
    assert s.read_state("paused_workflows",default=[])[0]["pause_id"] == f"{run_id}:7"
    assert s.read_state("paused_workflows",default=[])[0]["args"] == {"値":"hoge"}
    assert s.read_state("CD開始回数") == 1
    assert s.read_state("CD完了回数") is None
    assert _get_logs(run_id) == [
        '[ワークフローのログ]通知ダミー: 0回目のCDを開始します: hoge',
         f'[ワークフローのログ]通知ダミー: 承認事項がが1件あります:{run_id}',
    ]

    current = json.dumps(_global.state.state,indent=2,sort_keys=True,ensure_ascii=False)
    do_ttflow()
    assert json.dumps(_global.state.state,indent=2,sort_keys=True,ensure_ascii=False) == current, "stateが変化していないこと"
    assert _get_logs(run_id) == [
        '[ワークフローのログ]通知ダミー: 0回目のCDを開始します: hoge',
         f'[ワークフローのログ]通知ダミー: 承認事項がが1件あります:{run_id}',
    ]

    # 承認する
    _enque_event(f"承認:{run_id}",None)
    do_ttflow()
    assert len(s.read_state("paused_workflows",default=[]))==0
    assert s.read_state("CD開始回数") == 1
    assert s.read_state("CD完了回数") == 1
    assert _get_logs(run_id) == [
        '[ワークフローのログ]通知ダミー: 0回目のCDを開始します: hoge',
         f'[ワークフローのログ]通知ダミー: 承認事項がが1件あります:{run_id}',
          '[ワークフローのログ]承認されました',
           '[ワークフローのログ]通知ダミー: CD完了',
    ]
    
# TODO: 実装
# def test_中断機能が正しく動くこと_2重実行ケース():
#     s = OnMemoryS
