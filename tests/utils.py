from ttflow import setup
from ttflow.state_repository.on_memory_state import OnMemoryStateRepository


def create_client_for_test():
    c = setup()
    c._global.events = []
    c._global.state = OnMemoryStateRepository()
    return c
