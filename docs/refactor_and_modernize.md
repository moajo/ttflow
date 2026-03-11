# リファクタリング・モダナイズ計画

Phase 1〜4 は完了済み。以下は残りの作業。

---

## Phase 5: 未実装・不完全な箇所の対応

| 箇所                          | 状況                              |
| ----------------------------- | --------------------------------- |
| `dynamodb.py` `clear_state()` | `pass # TODO: implement` のまま   |
| `workflow.py:95`              | ワークフロー実行後イベント未実装  |
| `tests/test_notations.py:24`  | `# TODO: 対応する` でテスト無効化 |

---

## Phase 6: テスト強化

- StateRepository のI/Oエラー系テスト追加

---

## スコープ外（過剰設計になるため見送り）

- async/await対応（プロセスがワンショット実行なので実益が薄い）
- Webダッシュボード
- Redis/PostgreSQLバックエンド（現状の用途で不要）
- Sphinxドキュメント生成
- ワークフロー可視化
