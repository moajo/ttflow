from dataclasses import dataclass
from typing import Any, Optional

from ..core.context import Context
from ..core.global_env import Global

# run_idに紐づくrunの実行状態を保持する
# TODO: この状態は、run_idに紐づくrunが完了したときに削除される


def _log_key(run_id):
    return f"_run_state:{run_id}"


@dataclass
class ExecutedCache:
    value: Any


def _is_already_executed(g: Global, c: Context) -> Optional[ExecutedCache]:
    c._use()
    run_state_token = f"{c.run_id}:{c.used_count}"
    run_states = g.state.read_state(_log_key(c.run_id), default=[])
    for a in run_states:
        if a["token"] == run_state_token:
            return ExecutedCache(a["value"])
    return None


def _mark_as_executed(g: Global, c: Context, value: Any):
    run_state_token = f"{c.run_id}:{c.used_count}"
    run_states = g.state.read_state(_log_key(c.run_id), default=[])
    run_states.append(
        {
            "token": run_state_token,
            "value": value,
        }
    )
    g.state.save_state(_log_key(c.run_id), run_states)
    return value


def _delete_run_state(g: Global, run_id: str):
    g.state.save_state(_log_key(run_id), [])
