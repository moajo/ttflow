class TtflowError(Exception):
    """ttflowの基底例外"""


class StateLockedError(TtflowError):
    """状態がロックされている"""


class UnknownRepositoryError(TtflowError):
    """不明なStateRepository指定"""


class InvalidStateError(TtflowError):
    """ステートの値が不正"""


class WorkflowDirectCallError(TtflowError):
    """ワークフロー関数を直接呼び出した"""


class SideeffectUsageError(TtflowError):
    """sideeffect関数の使い方が不正"""
