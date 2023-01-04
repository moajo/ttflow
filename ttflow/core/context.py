import random
from typing import Optional


class Context:
    """
    ワークフローの実行時に渡されるコンテキスト
    """

    def __init__(
        self,
        workflow_name: str,
        run_id: Optional[str] = None,
        paused_info: Optional[dict] = None,
    ):
        self.workflow_name = workflow_name
        self.paused_info = paused_info  # このrunがpauseからの再開だった場合、そのpause情報が入る
        if run_id is None:
            run_id = str(random.randint(0, 1000000000))  # TODO: UUIDにする
        self.run_id = run_id
        self.used_count = 0

    def _use(self):
        self.used_count += 1
