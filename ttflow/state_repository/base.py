import abc
from typing import Any


class StateRepository(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def read_state(self, name: str, default=None) -> Any:
        raise NotImplementedError()

    @abc.abstractmethod
    def save_state(self, name: str, value: Any) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    def clear_state(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def lock_state(self):
        """ステートを排他的にロックします"""
        raise NotImplementedError()

    @abc.abstractmethod
    def unlock_state(self):
        """ステートのロックを開放します"""
        raise NotImplementedError()

    @abc.abstractmethod
    def is_locked(self) -> bool:
        """ロック状態を返します"""
        raise NotImplementedError()
