import pytest

from .utils import create_client_for_test


@pytest.fixture
def client():
    return create_client_for_test()
