import pytest
from ttflow import setup
from ttflow.state_repository.on_memory_state import OnMemoryStateRepository


@pytest.fixture
def client():
    c = setup()
    c._global.events = []
    c._global.state = OnMemoryStateRepository()
    return c
