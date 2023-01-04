from ..core.context import Context
from ..core.global_env import _get_state
from ..core.state import get_state,set_state

# ログの実態は単にrun_idに紐づくstateである

def _log_key(run_id):
    return f"logs:{run_id}"

def log(c:Context, message:str):
    logs = get_state(c, _log_key(c.run_id),[])
    logs.append(f"[ワークフローのログ]{message}")
    set_state(c, _log_key(c.run_id),logs)

def get_logs(c:Context):
    return  get_state(c, _log_key(c.run_id),[])

def _get_logs(run_id:str):
    s=_get_state()
    return  s.read_state(  _log_key(run_id),[])
