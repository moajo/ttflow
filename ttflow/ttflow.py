import logging
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Optional, Union

from .core.context import Context
from .core.event import (
    _enque_event,
    _enque_trigger,
    flush_events_for_next_run_to_state,
    iterate_events,
    load_events_from_state,
)
from .core.global_env import Global
from .core.system_events.every import SYSTEM_EVENT__EVERY, _enque_every_event
from .core.system_events.pause import try_parse_pause_event
from .core.trigger import EventTrigger, Trigger
from .core.workflow import (
    WorkflowRunResult,
    _find_event_triggered_workflows,
    _find_workflow,
    exec_workflow,
    sideeffect,
    workflow,
)
from .state_repository.buffer_cache_proxy import BufferCacheStateRepositoryProxy
from .system_states.event_log import _add_event_log
from .utils import workflow_hash

logger = logging.getLogger(__name__)


def event_trigger(name: str) -> Trigger:
    """イベントトリガー"""
    return EventTrigger(name)


def every_trigger() -> Trigger:
    """イベントトリガー"""
    return EventTrigger(SYSTEM_EVENT__EVERY)


def state_trigger(state_name: str) -> Trigger:
    """状態変化を監視するトリガー

    Args:
        state_name (str): _description_

    Returns:
        Trigger: _description_
    """
    return EventTrigger(f"state_changed_{state_name}")


@contextmanager
def _lock_state(g: Global):
    if g.state.is_locked():
        logger.info("state is locked. skip run.")
        raise ValueError("state is locked")
    g.state.lock_state()
    try:
        yield
    finally:
        g.state.unlock_state()


class Client:
    """
    # コンセプト
    - ワークフローはトリガーによって実行される
    - トリガーは実行時に手動で指定するものの他に、いろいろな種類がある
    - トリガーは実際にはすべてイベントトリガーである。イベントの種類で多様性が作られている
    - イベントに基づいてワークフローが実行されるとき、run_idが発行される
    - run_idはワークフローの実行を一意に識別する
    - ワークフローは中断可能である
    - 中断したワークフローは常に再試行される
    - 再試行されても副作用がなければ問題はない。副作用ははrun_idを使って透過的に管理される
        - 値の保存にはstateを使う。stateにアクセスする際にはrun_idが必要。同じrun_idから何度も実行されても問題ない
            - get_stateは2回目以降はキャッシュされるので、初回アクセス時の値を再現できる
            - set_stateは2回目以降は何もしないので、不要な副作用を産まない。
        - それ以外の副作用には@sideeffectを使う
            - sideeffectは初回実行時のみ実行される。2回目以降はスキップされる
    - 中断とは、PauseExceptionをraiseすることである
      - 中断されたワークフローは_pauseイベントとなり、次回以降の実行時に再試行される
    - 従って、ルールは以下のようになる
        - ワークフロー中では乱数を使わない。乱数を使う場合はsideeffect関数内で実行して再現可能にする
        - ワークフロー中では副作用を使わない。副作用を使う場合はsideeffect関数内で実行して再現可能にする
        - ワークフロー中では外部状態を読み取らない。外部状態を読み取る場合はsideeffect関数内で実行して再現可能にするか、stateから読み取る
        - ワークフロー中では外部状態を書き込まない。外部状態を書き込む場合はsideeffect関数内で実行して再現可能にするか、stateに書き込む

    """

    def __init__(self, _global: Global):
        self._global = _global

    def workflow(self, trigger: Optional[Union[Trigger, str]] = None):
        return workflow(self._global, trigger)

    def sideeffect(self):
        return sideeffect(self._global)

    def run(self, trigger_name: Optional[str] = None, args: Any = None):
        """
        トリガーに基づいてワークフローを実行します

        Args:
            name (str): _description_
            args (Any): _description_
        """
        if trigger_name is not None:
            _enque_trigger(self._global, trigger_name, args)
        with _lock_state(self._global):
            with self._global.state.buffering():
                return self.__run()

    def __run(self) -> list[WorkflowRunResult]:
        logger.info("check registered workflows")

        # 毎回実行するイベントを追加
        _enque_every_event(self._global)

        # デプロイイベントの対応
        h = workflow_hash(self._global.workflows)
        current_hash = self._global.state.read_state("workflows_hash")
        if current_hash != h:
            logger.info(
                f"workflow is changed from last run. hash: {current_hash} -> {h}"
            )
            _enque_event(self._global, "workflows_changed", None)
            self._global.state.save_state("workflows_hash", h)

        # 未処理イベントをロードする
        load_events_from_state(self._global)

        logger.info("start event loop")
        workflow_run_results: list[WorkflowRunResult] = []
        for e in iterate_events(self._global):
            event_name = e.event_name
            args = e.args
            # NOTE: system eventは数が多くユーザがあまりhookするべきではないのでevent logには記録しない
            if (pause_event := try_parse_pause_event(e)) is not None:
                c = Context(
                    pause_event.workflow_name,
                    run_id=pause_event.run_id,
                    paused_info=args,
                )
                wf = _find_workflow(self._global, pause_event.workflow_name)
                if wf is not None:
                    logger.info(f"workflow '{wf.f.__name__}' resuming")
                    print()
                    print(f"{wf.f.__name__}: 中断した点から再開します")
                    workflow_run_results.append(
                        exec_workflow(self._global, c, wf, args["args"])
                    )
            elif event_name.startswith("_"):
                logger.info(f"processing system event '{event_name}'")
                for wf in _find_event_triggered_workflows(self._global, event_name):
                    logger.info(f"'{wf.f.__name__}' triggered by event '{event_name}'")
                    print()
                    print(f"{wf.f.__name__}: イベント'{event_name}'により実行されます")
                    c = Context(wf.f.__name__)
                    workflow_run_results.append(
                        exec_workflow(self._global, c, wf, args)
                    )
            else:
                logger.info(f"processing event '{event_name}'")
                print(f"イベント[{event_name}]が発生しました")
                _add_event_log(
                    self._global,
                    event_name,
                    args,
                )
                for wf in _find_event_triggered_workflows(self._global, event_name):
                    print()
                    print(f"{wf.f.__name__}: イベント[{event_name}]により実行されます")
                    logger.info(
                        f"run workflow '{wf.f.__name__}' triggered by event '{event_name}'"
                    )
                    c = Context(wf.f.__name__)
                    workflow_run_results.append(
                        exec_workflow(self._global, c, wf, args)
                    )

        logger.info("do post processes")
        # eventを永続化してメモリ上から消す
        flush_events_for_next_run_to_state(self._global)
        self._global.purge_events()
        return workflow_run_results


def setup(
    state_repository: str = "local:state.json",
) -> Client:
    if state_repository.startswith("local:"):
        from .state_repository.local_file_state import LocalFileStateRepository

        s = LocalFileStateRepository(state_file=Path(state_repository[len("local:") :]))
    elif state_repository.startswith("dynamodb:"):
        from .state_repository.dynamodb import DynamoDBStateRepository

        s = DynamoDBStateRepository(
            table_name=state_repository[len("dynamodb:") :],
        )
    elif state_repository.startswith("s3:"):
        from .state_repository.s3 import S3StateRepository

        s3_path = state_repository[len("s3:") :]
        if "/" not in s3_path:
            bucket = s3_path
            prefix = ""
        else:
            bucket, prefix = s3_path.split("/", maxsplit=1)

        s = S3StateRepository(
            bucket_name=bucket,
            prefix=prefix,
        )
    elif state_repository.startswith("onmemory"):
        from .state_repository.on_memory_state import OnMemoryStateRepository

        s = OnMemoryStateRepository()
    else:
        raise Exception("Unknown repository: ", state_repository)

    return Client(
        Global(
            state=BufferCacheStateRepositoryProxy(s),
        )
    )
