from dataclasses import dataclass
from typing import Any

from ..state_repository.base import StateRepository
from .trigger import Trigger


@dataclass
class Event:
    event_name: str
    args: Any


class Workflow:
    def __init__(self, trigger: Trigger, f):
        self.trigger = trigger
        self.f = f


class Global:
    def __init__(self, state: StateRepository):
        self.state = state

        # 登録されたワークフロー
        self.workflows: list[Workflow] = []

        # イベントキュー
        self.events: list[Event] = []

        # 実行中にエンキューされたイベント。
        self.events_for_next_run: list[Event] = []

    def purge_events(self):
        self.events = []
        self.events_for_next_run = []
