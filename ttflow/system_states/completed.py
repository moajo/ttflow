from ..core.context import Context
from ..core.global_env import Global
from ..core.state import get_state, set_state

# 完了したrunのログを保持する


def _log_key():
    return "completed"


def add_completed_runs_log(g: Global, c: Context):
    logs = get_state(g, c, _log_key(), [])
    logs.append(
        {
            "run_id": c.run_id,
        }
    )
    set_state(g, c, _log_key(), logs)


def get_completed_runs_log(g: Global, c: Context):
    return get_state(g, c, _log_key(), [])


def _get_completed_runs_log(g: Global):
    return g.state.read_state(_log_key(), [])