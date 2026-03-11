# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## プロジェクト概要

ttflowは軽量なPythonワークフローエンジン。イベント駆動でワークフローを実行し、pause/resumeによる長時間ワークフローをサポートする。状態はStateRepositoryに永続化され、ワークフロー関数自体はステートレスかつ再実行可能。

## 開発コマンド

```bash
make test          # pytest実行
make fmt           # ruffでフォーマット＋自動修正
make lint          # ruffでリント＋フォーマットチェック

# 単一テスト実行
uv run pytest tests/test_pause.py -v
uv run pytest tests/test_pause.py::test_pause_once -v

# ネットワークテスト（通常スキップ）を含める場合
uv run pytest -m network
```

## アーキテクチャ

### 実行モデル

`client.run(trigger_name)` が呼ばれると:
1. StateRepositoryのロックを取得
2. バッファリングモード開始（状態読み書きをキャッシュ）
3. イベントキューにトリガーイベントを追加し、キューが空になるまで処理
4. バッファをflushしてロック解放

### コア構造

- **`ttflow/ttflow.py`** — `Client`クラスと`setup()`。エントリポイント
- **`ttflow/core/workflow.py`** — `@workflow`/`@sideeffect`デコレータ、`exec_workflow()`
- **`ttflow/core/pause.py`** — `PauseException`によるpause/resume機構
- **`ttflow/core/state.py`** — `get_state`/`set_state`（再実行時はキャッシュから返す）
- **`ttflow/core/event.py`** — イベントキューイングと永続化
- **`ttflow/core/run_context.py`** — ワークフロー内で使うAPI（`c.get_state`, `c.log`, `c.pause_once`等）
- **`ttflow/state_repository/`** — 永続化バックエンド（local file, S3, DynamoDB, on-memory）
- **`ttflow/state_repository/buffer_cache_proxy.py`** — 読み取りキャッシュ＋書き込みバッファのプロキシ層

### 冪等性の仕組み

ワークフローはpause/resume時に最初から再実行される。安全に再実行するため:
- `set_state()` — 初回のみ実行、再実行時はno-op
- `get_state()` — 初回でキャッシュ、再実行時はキャッシュ値を返す
- `@sideeffect()` — 副作用関数を`run_id`ごとに1回だけ実行

### トリガー種別

- `event_trigger(name)` — 名前付きイベントで発火
- `every_trigger()` — 毎回の`client.run()`で発火
- `state_trigger(state_name)` — 状態変更時に発火

## コーディング規約

- コメント・ドキュメントは日本語
- コミットメッセージは日本語
- パッケージ管理: uv
- フォーマッタ/リンタ: ruff
- テストには`@pytest.mark.network`マーカーでネットワーク依存テストを分離

## ドキュメント運用

- **リファクタリング計画**: `docs/refactor_and_modernize.md` に全体計画を記載
- **開発メモ**: `docs/開発メモ/` に議事録を連番で蓄積する（例: `01_開発再開.md`, `02_xxx.md`）
  - 議論と方針決定があるたびに新しいファイルを作成する
  - 決定事項・経緯・背景を記録する
