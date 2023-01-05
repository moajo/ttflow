import time
from dataclasses import asdict, dataclass
from typing import Any, Optional

from dacite import from_dict

from ..event import Event, _enque_event
from ..global_env import Global

# _pause イベントは、ワークフローの中断を表すイベントです。
# 中断されたワークフローは、即時ではなく次回の実行まで待機します。


def _event_name():
    return "_pause"


@dataclass
class PauseEvent:
    workflow_name: str  # 実行してるワークフロー名
    run_id: str  # run_id
    pause_id: str  # 中断のID
    args: Any  # 実行時の引数
    timestamp: float  # 中断時刻


def _enque_pause_event(
    g: Global,
    workflow_name: str,
    run_id: str,
    pause_id: str,
    args: Any,
):
    _enque_event(
        g,
        event_name=_event_name(),
        args=asdict(
            PauseEvent(
                workflow_name=workflow_name,
                run_id=run_id,
                pause_id=pause_id,
                args=args,
                timestamp=time.time(),
            )
        ),
        process_immediately=False,
    )


def try_parse_pause_event(event_raw: Event) -> Optional[PauseEvent]:
    if event_raw.event_name != _event_name():
        return None
    return from_dict(data_class=PauseEvent, data=event_raw.args)
