# StateRepository バックエンド

ttflowの状態永続化を担うバックエンドの解説。すべての実装は `BufferCacheStateRepositoryProxy` でラップされ、読み取りキャッシュと書き込みバッファリングが自動的に適用される。

## バックエンド一覧

| バックエンド | 指定方法 | 永続化 | ロック | 用途 |
|------------|---------|--------|-------|------|
| OnMemory | `onmemory` | なし | なし | テスト・開発 |
| LocalFile | `local:<path>` | ファイル | なし | ローカル実行 |
| S3 | `s3:<bucket>/<prefix>` | S3 | 簡易 | 本番運用 |
| DynamoDB | `dynamodb:<table>` | DynamoDB | 厳密 | 本番運用 |

---

## OnMemory

テスト・開発用のインメモリ実装。プロセス終了で状態は消える。

```python
client = setup("onmemory")
```

- ロック機能なし（`is_locked()` は常に `False`）
- JSON互換性チェックあり（`json.dumps/loads` を通す）

---

## LocalFile

単一のJSONファイルに全状態を保存する。ローカルでの開発・個人利用向け。

```python
client = setup("local:state.json")
client = setup("local:path/to/state.json")  # ディレクトリは自動作成
```

- ファイル形式: インデント付きJSON（日本語対応、キーソート済み）
- ロック機能なし — 単一プロセスからの実行を想定
- ファイルが存在しない場合は空の状態から開始

---

## S3

AWS S3バケットに各状態を個別オブジェクトとして保存する。複数インスタンスからの共有が可能。

```python
client = setup("s3:my-bucket/workflow-state")
client = setup("s3:my-bucket")  # prefix なし
```

### データ構造

各stateが独立したS3オブジェクトとして保存される:

```
s3://my-bucket/workflow-state/state_name_1  → JSON値
s3://my-bucket/workflow-state/state_name_2  → JSON値
s3://my-bucket/workflow-state/_system_lock   → ロック用
```

### ロック機構

`_system_lock` キーの存在有無で排他制御を行う簡易的な方式。

- `lock_state()`: `_system_lock` キーを書き込み
- `unlock_state()`: `_system_lock` キーを削除
- `is_locked()`: `_system_lock` キーの存在を確認

**制約**: 2つのプロセスが同時に `is_locked() → False` を確認した場合、両方がロックを取得できてしまう（レースコンディション）。cronで定期実行する程度の頻度であれば実用上問題ないが、高頻度・高並行の環境では競合が発生しうる。

### 前提条件

- AWS認証情報が設定されていること（環境変数、IAMロール等）
- 指定したS3バケットへの読み書き権限

---

## DynamoDB

AWS DynamoDBテーブルに状態を保存する。条件付き書き込みによる厳密な排他ロックをサポート。

```python
client = setup("dynamodb:my-table")
```

リージョンはboto3のデフォルト設定（`AWS_DEFAULT_REGION` 環境変数、`~/.aws/config` 等）に従う。

### テーブルスキーマ

| 属性 | 型 | 説明 |
|------|-----|------|
| `pk` | String (Partition Key) | アイテムの一意キー |
| `value` | String | JSON文字列 |

stateアイテムの `pk` は `state:<name>` の形式。ロックアイテムの `pk` は `_system_lock`。

### ロック機構

DynamoDBの条件付き書き込み（`ConditionExpression: attribute_not_exists(pk)`）を使った厳密な排他ロック。

- `lock_state()`: `_system_lock` アイテムを条件付き書き込み。既にロック済みなら `StateLockedError`
- `unlock_state()`: `_system_lock` アイテムを削除
- `is_locked()`: `_system_lock` アイテムの存在を確認

S3バックエンドと異なり、2つのプロセスが同時にロックを取得することはできない。

### テーブル作成例

```bash
aws dynamodb create-table \
  --table-name ttflow-state \
  --attribute-definitions AttributeName=pk,AttributeType=S \
  --key-schema AttributeName=pk,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST
```

### 前提条件

- AWS認証情報が設定されていること（環境変数、IAMロール等）
- 指定したDynamoDBテーブルへの読み書き権限

---

## バックエンドの選び方

```
テスト・CI              → onmemory
ローカル開発             → local:state.json
本番（手軽に始めたい）    → s3:<bucket>/<prefix>
本番（厳密なロックが必要） → dynamodb:<table>
```
