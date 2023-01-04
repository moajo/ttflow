from typing import Any
import json

from .base import StateRepository


class OnMemoryStateRepository(StateRepository):
    def __init__(self):
        self.state = {}
    def save_state(self,name:str, value):
        self.state[name]=json.loads(json.dumps(value))

    def clear_state(self):
        self.state={}

    def read_state(self,name:str,default=None)->Any:
        value=self.state.get(name,default)
        return json.loads(json.dumps(value))
