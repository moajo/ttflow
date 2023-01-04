from pathlib import Path

import fire
import ttflow

from .core.workflow import load_workflows
from .state_repository.local_file_state import LocalFileStateRepository
from .ttflow import do_ttflow


# python cli.py reset_state
def reset_state():
    s = LocalFileStateRepository()
    return s.clear_state()


# python cli.py webhook
def webhook(name: str, arg: dict):
    if load_workflows(Path("workflows")):
        do_ttflow()
        ttflow.exec_webhook(name, arg)


# python cli.py event "ほげ"
def event(name: str, arg: dict):
    s = LocalFileStateRepository()
    if load_workflows(Path("workflows")):
        ttflow._trigger_event(s, name, arg)
        do_ttflow()


# python cli.py event "ほげ"
def run():
    if load_workflows(Path("workflows")):
        do_ttflow()


def main() -> None:
    fire.Fire()


if __name__ == "__main__":
    main()
