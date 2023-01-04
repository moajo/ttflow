import json 
from pathlib import Path
from typing import Any

from .base import StateRepository

STATE_FILE = Path("state.json")


class LocalFileStateRepository(StateRepository):
    def save_state(self,name:str, value):
        state = {}
        if STATE_FILE.exists():
            with open(STATE_FILE, "r") as f:
                state = json.load(f)
        state [name]=value
        with open(STATE_FILE, "w") as f:
            json.dump(state, f,sort_keys=True, ensure_ascii=False,indent=2)

    def clear_state(self):
        with open(STATE_FILE, "w") as f:
            json.dump({}, f,sort_keys=True, ensure_ascii=False,indent=2)


    def read_state(self,name:str,default=None)->Any:
        state = {}
        if STATE_FILE.exists():
            with open(STATE_FILE, "r") as f:
                state = json.load(f)
        return state.get(name,default)
