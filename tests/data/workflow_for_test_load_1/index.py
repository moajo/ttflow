import ttflow

# contextは実行IDが含まれる。read_stateとかは実行IDによってキャッシュされるので、リエントラントなワークフローを書ける
# 中断された場合、ttflow.PauseExceptionが発生する。

# 外部から温度変化を受信する
@ttflow.workflow(trigger=ttflow.event("workflows_changed"))
def ワークフローのデプロイイベント(context:ttflow.Context,webhook_args:dict):
    print("ワークフローのデプロイイベントが発生しました")
    c = ttflow.get_state(context, "デプロイ回数")
    if c is None:
        c = 0
    ttflow.set_state(context, "デプロイ回数",c+1)
