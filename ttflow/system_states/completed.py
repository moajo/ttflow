from ..core.context import Context
from ..core.global_env import _get_state
from ..core.state import get_state,set_state

# 完了したrunのログを保持する

def _log_key():
    return f"completed"

def add_completed_runs_log(c:Context):
    logs = get_state(c, _log_key(),[])
    logs.append({
        "run_id":c.run_id,
    })
    set_state(c, _log_key(),logs)

def get_completed_runs_log(c:Context):
    return  get_state(c, _log_key(),[])

def _get_completed_runs_log():
    s=_get_state()
    return  s.read_state( _log_key(),[])

