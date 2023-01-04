import random

class Context:
    """
    ワークフローの実行時に渡されるコンテキスト
    """
    def __init__(self, workflow_name:str,run_id=None):
        self.workflow_name = workflow_name
        if run_id is None:
            self.run_id = random.randint(0,1000000000)# TODO: UUIDにする
        else:
            self.run_id = run_id
        self.used_count=0
    
    def _use(self):
        self.used_count+=1
