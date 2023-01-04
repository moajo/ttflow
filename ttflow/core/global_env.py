from ..state_repository.base import StateRepository


class Registerer:
    def __init__(self):
        self.workflows = []

    def reset(self):
        self.workflows = []


class Global:
    def __init__(self, state: StateRepository):
        self.state = state
        self.registerer = Registerer()

        # イベントキュー
        self.events = []
