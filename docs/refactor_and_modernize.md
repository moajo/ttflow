# リファクタリング・モダナイズ計画

## 背景

ttflowは一気に書き上げて未完成のまま放置されていた。依存ツールが古く、未実装箇所やTODOも残っている。
本ドキュメントでは、モダナイズとリファクタリングの計画を優先度順にまとめる。

---

## Phase 1: ツールチェーン刷新

### pysen → ruff 移行

- pysen（py37設定のまま）を廃止し、ruffに一本化
- black, flake8, isort を個別管理する必要がなくなる
- Makefile の `fmt`/`lint` ターゲットも更新

### 依存関係の更新

| パッケージ | 現状 | 方針 |
|---|---|---|
| `black` | `^22.12.0` | ruffに統合、削除 |
| `flake8` | `^6.0.0` | ruffに統合、削除 |
| `isort` | `^5.11.4` | ruffに統合、削除 |
| `pysen` | `^0.10.2` | 削除 |
| `mypy` | `^0.991` | `^1.8+` に更新、CIで有効化 |
| `pytest` | `^7.2.0` | `^8.x` に更新 |
| `boto3` | `^1.26.42` | `^1.34+` に更新 |
| `boto3-stubs`, `types-boto3`, `botostubs` | 3つ重複 | 1つに統合 |
| `fire` | `^0.5.0`（メンテ停滞） | `typer` or `click` への移行を検討 |

### Python バージョン

- `>=3.9` → `>=3.11` に引き上げ

### CI更新

- `actions/checkout@v2` → `@v4`
- `actions/setup-python@v4` → `@v5`
- Python 3.12, 3.13 をテストマトリクスに追加
- mypy をCIパイプラインに追加

---

## Phase 2: コード品質の修正（即時対応可能）

| 箇所 | 問題 | 修正 |
|---|---|---|
| `context.py:19` | `run_id = random.randint(...)` + TODOコメント | `uuid.uuid4()` に変更 |
| `state.py:54,70` | `type(values) != list` | `isinstance(values, list)` に変更 |
| `__init__.py` | `from .ttflow import *` ワイルドカード | 明示的な `__all__` 定義 |
| `ttflow.py:226` | `raise Exception(...)` | カスタム例外に変更 |
| 各所 | `"_events"`, `"_pause"` 等のマジック文字列 | 定数モジュールに集約 |

---

## Phase 3: 型安全性の向上

- `StateRepository` の `read_state`/`save_state` に型ヒント追加
- `Union[A, B]` → `A | B` 構文に統一
- `Optional[X]` → `X | None` に統一
- mypy strict モードの段階的導入
- `RunContext` のメソッドに戻り値型を追加

---

## Phase 4: エラーハンドリング整備

`ttflow/errors.py` を新設し、カスタム例外階層を定義:

```python
class TtflowError(Exception): ...
class StateLockedError(TtflowError): ...
class WorkflowPausedError(TtflowError): ...
class StateRepositoryError(TtflowError): ...
class UnknownRepositoryError(TtflowError): ...
```

現在 `ValueError`, `RuntimeError`, `Exception` を使っている箇所を置き換える。

---

## Phase 5: 未実装・不完全な箇所の対応

| 箇所 | 状況 |
|---|---|
| `dynamodb.py` `clear_state()` | `pass # TODO: implement` のまま |
| `workflow.py:95` | ワークフロー実行後イベント未実装 |
| `tests/test_pause.py:150` | `# TODO: 実装` でテスト未完成 |
| `tests/test_notations.py:24` | `# TODO: 対応する` でテスト無効化 |
| `cli.py` | ほぼ空（7行） |

---

## Phase 6: テスト強化

- `pytest-cov` 導入でカバレッジ計測
- StateRepository のI/Oエラー系テスト追加
- ロック競合のテスト追加
- CIでカバレッジレポート出力

---

## スコープ外（過剰設計になるため見送り）

- async/await対応（プロセスがワンショット実行なので実益が薄い）
- Webダッシュボード
- Redis/PostgreSQLバックエンド（現状の用途で不要）
- Sphinxドキュメント生成
- ワークフロー可視化
