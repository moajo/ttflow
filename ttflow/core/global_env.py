from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from ..state_repository.buffer_cache_proxy import BufferCacheStateRepositoryProxy
from .trigger import Trigger

if TYPE_CHECKING:
    from ..system_states.execution_trace import ExecutionTraceRecorder


@dataclass
class Event:
    event_name: str
    args: Any


class Workflow:
    def __init__(self, trigger: Trigger, f: Callable):
        self.trigger = trigger
        self.f = f

    @property
    def name(self) -> str:
        return self.f.__name__

    @property
    def description(self) -> str | None:
        return self.f.__doc__


class Global:
    def __init__(self, state: BufferCacheStateRepositoryProxy):
        self.state = state

        # 登録されたワークフロー
        self.workflows: list[Workflow] = []

        # イベントキュー
        self.events: list[Event] = []

        # 実行中にエンキューされたイベント。
        self.events_for_next_run: list[Event] = []

        # 実行トレース記録用（__run中のみ設定される）
        self.trace_recorder: ExecutionTraceRecorder | None = None

    def purge_events(self) -> None:
        self.events = []
        self.events_for_next_run = []
