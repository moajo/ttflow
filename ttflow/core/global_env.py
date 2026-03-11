from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from ..state_repository.buffer_cache_proxy import BufferCacheStateRepositoryProxy
from .trigger import Trigger


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

    def purge_events(self) -> None:
        self.events = []
        self.events_for_next_run = []
