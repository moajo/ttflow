import hashlib
from collections.abc import Sequence

from .core.global_env import Workflow


def workflow_hash(workflows: Sequence[Workflow]) -> str:
    hash = hashlib.sha1()
    for wf in workflows:
        hash.update(wf.f.__code__.co_code)
    return hash.hexdigest()
