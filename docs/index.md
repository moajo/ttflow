# ttflow

軽量なPythonワークフローエンジンです。

ペライチのPythonスクリプトがそのままワークフローエンジンとして動きます。
サーバープロセスは不要なので、待機コストが0になります。

## 特徴

- **サーバー不要** — 常駐プロセスなし。スクリプトを実行するだけ
- **中断と再開** — 数日〜数週間にわたるワークフローを、途中で中断して後から再開できる
- **冪等な再実行** — 再開時は最初から再実行されるが、副作用は1回しか実行されない
- **イベント駆動** — ワークフロー間をイベントで疎結合に連携
- **永続化バックエンドを選択可能** — ローカルファイル、S3、DynamoDB、オンメモリ

## クイックスタート

### インストール

```bash
pip install ttflow
```

### 最小限のワークフロー

```python
from ttflow import RunContext, setup
from ttflow.powerup.run_by_cli import run_by_cli

ttflow = setup(state_repository="local:state.json")

@ttflow.workflow()
def hello(c: RunContext, args: dict):
    c.log("Hello, ttflow!")

run_by_cli(ttflow)
```

```bash
python hello.py run hello
```

## ドキュメント

- [イベントシステム](guide/events.md) — イベント駆動の仕組みを解説
- [StateRepository](guide/state_repository.md) — 永続化バックエンドの選択と設定
- [API リファレンス](api/ttflow.md) — 全APIの自動生成ドキュメント
