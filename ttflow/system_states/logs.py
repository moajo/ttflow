from ..core.context import Context
from ..core.global_env import Global
from ..core.state import get_state
from ..system_states.run_state import _execute_once

# ログの実態は単にrun_idに紐づくstateである


def _log_key(run_id):
    return f"_logs:{run_id}"


def log(g: Global, c: Context, message: str):
    @_execute_once(g, c)
    def a():
        processed = f"    [{c.workflow_name}]{message}"
        print(processed)
        logs = g.state.read_state(_log_key(c.run_id), default=[])
        logs.append(message)
        g.state.save_state(_log_key(c.run_id), logs)

    return a()


def get_logs(g: Global, c: Context):
    return get_state(g, c, _log_key(c.run_id), [])


def _get_logs(g: Global, run_id: str) -> list[str]:
    s = g.state
    return s.read_state(_log_key(run_id), [])
