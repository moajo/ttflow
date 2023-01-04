from ..core.context import Context
from ..core.global_env import Global
from ..core.state import get_state, set_state

# ログの実態は単にrun_idに紐づくstateである


def _log_key(run_id):
    return f"logs:{run_id}"


def log(g: Global, c: Context, message: str):
    logs = get_state(g, c, _log_key(c.run_id), [])
    logs.append(f"[ワークフローのログ]{message}")
    set_state(g, c, _log_key(c.run_id), logs)


def get_logs(g: Global, c: Context):
    return get_state(g, c, _log_key(c.run_id), [])


def _get_logs(g: Global, run_id: str):
    s = g.state
    return s.read_state(_log_key(run_id), [])
