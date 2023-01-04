import pytest
from ttflow.core import _global
from ttflow.state_repository.on_memory_state import OnMemoryStateRepository


@pytest.fixture
def reset_global():
    s = OnMemoryStateRepository()
    _global.state = s
    _global.events = []
