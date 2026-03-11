# イベントシステム

ttflowはイベント駆動でワークフローを実行する。すべてのトリガーは内部的にイベントとして扱われる。

## イベントの分類

イベントは大きく **システムイベント** と **ユーザーイベント** に分かれる。

- **システムイベント**: `_` プレフィックス付き。イベントログに記録されない
- **ユーザーイベント**: プレフィックスなし。イベントログに記録される

---

## 組み込みイベント一覧

### `_every` — 毎回実行

| 項目 | 内容 |
|------|------|
| 種別 | システムイベント |
| 発火条件 | `client.run()` が呼ばれるたびに自動発火 |
| args | `None` |
| 処理タイミング | 即時（同じrun内） |

**ユーザー向けAPI**:

```python
from ttflow import every_trigger

@client.workflow(trigger=every_trigger())
def my_workflow(c, args):
    ...
```

---

### `_trigger_<name>` — 手動トリガー

| 項目 | 内容 |
|------|------|
| 種別 | システムイベント |
| 発火条件 | `client.run(trigger_name, args)` で明示的に指定 |
| args | `client.run()` の第2引数 |
| 処理タイミング | 即時（同じrun内） |

トリガー省略時は関数名が自動的にトリガー名になる。

```python
# 以下は同等
@client.workflow()
def my_wf(c, args): ...
client.run("my_wf")

@client.workflow(trigger="my_wf")
def handler(c, args): ...
client.run("my_wf")
```

---

### `_pause` — 中断・再開

| 項目 | 内容 |
|------|------|
| 種別 | システムイベント |
| 発火条件 | ワークフロー内で `PauseException` が発生（`c.pause_once()` / `c.wait_event()`） |
| args | `PauseEvent`（`workflow_name`, `run_id`, `pause_id`, `args`, `timestamp`） |
| 処理タイミング | **次回のrun以降**（遅延処理） |

ユーザーが直接使うことはない。`c.pause_once()` や `c.wait_event()` を通じて間接的に利用される。

```python
@client.workflow()
def my_wf(c, args):
    c.pause_once("step1")  # ここで中断。次回のrun()で再開
    do_something()
```

---

### `workflows_changed` — ワークフロー変更検知

| 項目 | 内容 |
|------|------|
| 種別 | ユーザーイベント |
| 発火条件 | ワークフロー定義のハッシュが前回実行時と異なる場合（初回実行含む） |
| args | `None` |
| 処理タイミング | 即時（同じrun内） |

デプロイ時の初期化処理などに使える。

```python
from ttflow import event_trigger

@client.workflow(trigger=event_trigger("workflows_changed"))
def on_deploy(c, args):
    c.log("ワークフローが更新されました")
```

---

### `state_changed_<name>` — 状態変更検知

| 項目 | 内容 |
|------|------|
| 種別 | ユーザーイベント |
| 発火条件 | `c.set_state(name, value)` で値が**変更された**場合（同じ値の場合は発火しない） |
| args | `{"old": 旧値, "new": 新値}` |
| 処理タイミング | 即時（同じrun内） |

```python
from ttflow import state_trigger

@client.workflow(trigger=state_trigger("temperature"))
def on_temp_change(c, args):
    old = args["old"]
    new = args["new"]
    c.log(f"温度が {old} → {new} に変化")
```

---

## ユーザー定義イベント

ワークフロー内から `c.event()` で任意のイベントを発火できる。

```python
@client.workflow()
def wf1(c, args):
    c.event("my_custom_event", {"key": "value"})

@client.workflow(trigger=event_trigger("my_custom_event"))
def wf2(c, args):
    # wf1からのイベントで起動
    ...
```

---

## イベント処理フロー

```
client.run(trigger_name) 呼び出し
│
├─ ロック取得
├─ バッファリングモード開始
│
├─ _every イベントを追加
├─ workflows_changed チェック（ハッシュ比較）
├─ 永続化された未処理イベントをロード
│
├─ イベントループ開始
│  │
│  ├─ _pause イベント → 中断ワークフローを再開
│  ├─ _ プレフィックス → システムイベント処理（ログ記録なし）
│  └─ その他 → ユーザーイベント処理（ログ記録あり）
│
├─ 遅延イベントを永続化
├─ バッファflush
└─ ロック解放
```

## イベントの即時処理と遅延処理

| モード | 対象 | 動作 |
|--------|------|------|
| 即時（`process_immediately=True`） | `_every`, `_trigger_*`, `workflows_changed`, `state_changed_*`, ユーザー定義 | 同じrun内のイベントループで処理される |
| 遅延（`process_immediately=False`） | `_pause` | 状態に永続化され、次回のrun以降で処理される |
