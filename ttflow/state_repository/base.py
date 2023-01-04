import abc
from typing import Any


class StateRepository(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def save_state(self, name: str, value: Any) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    def clear_state(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def read_state(self, name: str, default=None) -> Any:
        raise NotImplementedError()
