import uuid


class Context:
    """
    ワークフローの実行時に渡されるコンテキスト
    """

    def __init__(
        self,
        workflow_name: str,
        run_id: str | None = None,
        paused_info: dict | None = None,
    ):
        self.workflow_name = workflow_name
        self.paused_info = (
            paused_info  # このrunがpauseからの再開だった場合、そのpause情報が入る
        )
        if run_id is None:
            run_id = uuid.uuid4().hex
        self.run_id = run_id
        self.used_count = 0

    def _use(self):
        self.used_count += 1

    def get_run_state_token(self):
        return f"{self.run_id}:{self.used_count}"
