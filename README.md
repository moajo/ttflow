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

```
Hello, ttflow!

---------RUN SUMMARY---------
1件のワークフローが実行されました
	1件目
	  ワークフロー名: hello
	  run_id: ...
	  状態: succeeded
	  ログ:
	    - Hello, ttflow!
```

## コアコンセプト

### ワークフローとトリガー

`@workflow()` でワークフローを定義し、`client.run(トリガー名)` で実行します。

```python
@ttflow.workflow()
def 処理1(c: RunContext, args: dict):
    c.log("処理1を実行します")
    c.event("event1", 42)  # イベントを発火

@ttflow.workflow(trigger=event_trigger("event1"))
def 処理2(c: RunContext, args: int):
    c.log(f"処理2も実行します: {args}")
```

`処理1` を実行すると `event1` が発火し、次回の `run()` で `処理2` が自動的にトリガーされます。

トリガーを省略すると、関数名がそのままトリガー名になります（`client.run("処理1")` で実行可能）。

### 中断と再開

`c.pause_once()` でワークフローを中断し、次回の `run()` で続きから再開できます。

```python
@ttflow.workflow()
def loop(c: RunContext, args: dict):
    count = 0
    while True:
        c.log(f"loop: {count}週目開始")
        c.pause_once()  # ここで中断。次回のrun()で再開
        c.log(f"loop: {count}週目おわり")
        count += 1
        if count > 10:
            break
```

`c.wait_event(event_name)` を使えば、特定のイベントが発行されるまで中断することもできます。承認フローなどに便利です。

```python
@ttflow.sideeffect()
def 承認待ち(c: RunContext):
    c.wait_event(f"承認:{c.get_context_data().run_id}")
```

### 冪等な再実行の仕組み

中断から再開するとき、ワークフローは**関数の最初から再実行**されます。メモリ上の状態を保存しているわけではありません。

このままでは副作用が重複して実行されてしまいますが、ttflowは以下の仕組みで冪等性を保証します。

#### `@sideeffect()` — 副作用を1回だけ実行

```python
@ttflow.sideeffect()
def send_notification(c: RunContext, message: str):
    # 外部APIへの通知など。再実行時はスキップされる
    requests.post("https://...", json={"message": message})
```

`@sideeffect()` で修飾された関数は、同じ `run_id` で2回目以降の実行時には自動的にスキップされます。

#### `get_state()` / `set_state()` — 再実行に安全な状態管理

```python
@ttflow.workflow()
def wf(c: RunContext, args: dict):
    c.set_state("count", 1)        # 初回のみ書き込み。再実行時はno-op
    value = c.get_state("count")   # 初回の値がキャッシュされ、再実行時も同じ値を返す
```

- `set_state()` — 初回のみ実行され、再実行時には何もしない
- `get_state()` — 初回アクセス時の値をキャッシュし、再実行時も同じ値を返す

これらの仕組みにより、ワークフローは何度再実行されても、あたかも中断地点から再開したかのように振る舞います。

## ユースケース例

### 値段監視

商品の値段を定期的にチェックし、希望価格以下になったら通知するワークフローです。

```python
@ttflow.workflow()
def 買いたいもの追加(c: RunContext, args: dict):
    item_name = args["item_name"]
    price = args["price"]

    count = 1
    while True:
        current_price = 値段を取得(c, item_name)
        if current_price <= price:
            c.log(f"{count}回目: {item_name}は{current_price}円!")
            return
        c.log(f"{count}回目: {item_name}は{current_price}で買えませんでした")
        count += 1
        c.pause_once()  # 次回のrun()まで待機

@ttflow.sideeffect()
def 値段を取得(c: RunContext, item_name: str) -> int:
    # 実際にはここで外部APIから価格を取得する
    return fetch_price_from_api(item_name)
```

```bash
python watch_price.py run 買いたいもの追加 '{"item_name":"レモン","price":150}'
python watch_price.py run  # 定期実行（cronなどで）
```

`pause_once()` のたびに中断されるので、cronやCloudWatchスケジューラで定期的に `run` を呼べば、値段が下がるまで繰り返しチェックできます。複数の商品を同時に監視することもできます。

### 承認フロー

外部からのイベントを待って再開するパターンです。

```python
@ttflow.workflow()
def デプロイ(c: RunContext, args: dict):
    notification(c, "デプロイを開始します")
    承認待ち(c)
    # ↑ 「承認」イベントが来るまで中断される
    notification(c, "承認されました。デプロイを続行します")

@ttflow.sideeffect()
def 承認待ち(c: RunContext):
    c.wait_event(f"承認:{c.get_context_data().run_id}")

@ttflow.sideeffect()
def notification(c: RunContext, message: str):
    c.log(message)
```

```bash
python deploy.py run デプロイ            # 中断される
python deploy.py run 承認:<run_id>       # 承認イベントを発行 → 再開
```

## StateRepository（永続化バックエンド）

`setup()` の `state_repository` 引数でバックエンドを選択します。

| 指定                      | 用途                                 |
| ------------------------- | ------------------------------------ |
| `"local:state.json"`      | ローカルファイル。開発・個人利用向け |
| `"s3:bucket-name/prefix"` | S3。Lambda等のサーバーレス環境向け   |
| `"dynamodb:table-name"`   | DynamoDB                             |
| `"onmemory"`              | オンメモリ。テスト向け               |

```python
ttflow = setup(state_repository="s3:my-bucket/workflows")
```

## 運用方法

ワークフローは実行してすぐ終了するただのスクリプトなので、様々な運用方法が考えられます。

### ローカル実行

```bash
python my_workflow.py run トリガー名
python my_workflow.py run  # 中断中のワークフローを再開
```

`run_by_cli()` を使うと、[python-fire](https://github.com/google/python-fire) ベースのCLIが利用できます。

### AWS Lambda

Lambda上で動かすのが最も簡単な運用方法です。

```python
from ttflow import setup
from ttflow.powerup.run_by_lambda import run_by_lambda

ttflow = setup(state_repository="s3:my-bucket/state")

# ワークフロー定義...

handler = run_by_lambda(ttflow)
```

- Lambda関数URLやAPI Gatewayからトリガー名を指定して実行
- CloudWatchスケジューラで定期的に `run()` を呼んで中断中のワークフローを再開
- 永続化バックエンドにはS3やDynamoDBを使用
