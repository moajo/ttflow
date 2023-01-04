from ..state_repository.base import StateRepository
from ..state_repository.local_file_state import LocalFileStateRepository


class Registerer:
    def __init__(self):
        self.workflows = []

    def reset(self):
        self.workflows = []

class Global:
    def __init__(self):
        self.registerer = Registerer()
        self.state:StateRepository = LocalFileStateRepository()

        # イベントキュー
        self.events = []
_global = Global()

def reset_global_registerer():
    _global.registerer.reset()

def reset_global():
    _global.registerer.reset()
    _global.events = []


def _get_state()->StateRepository:
    return _global.state
