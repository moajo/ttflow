# Contributing to ttflow

ttflow への貢献を歓迎します。バグ報告、機能要望、PRいずれも気軽に送ってください。

## 開発環境セットアップ

### 必要なツール

- Python 3.11 以上
- [uv](https://docs.astral.sh/uv/) — パッケージ管理
- [git-cliff](https://git-cliff.org/) — リリース時のCHANGELOG生成（メンテナのみ必要）

### セットアップ手順

```bash
git clone https://github.com/moajo/ttflow.git
cd ttflow
uv sync --extra web
```

これで開発に必要な依存パッケージがすべてインストールされます。

## 開発フロー

### よく使うコマンド

```bash
make test    # pytestを実行
make fmt     # ruffでフォーマット＋自動修正
make lint    # ruffでリント＋フォーマットチェック
make all     # fmt + lint + test（CIと同じチェック）
make docs    # ドキュメントサイトをローカル起動（mkdocs）
```

### 単一テスト実行

```bash
uv run pytest tests/test_pause.py -v
uv run pytest tests/test_pause.py::test_pause_once -v
```

### ネットワーク依存テスト

ネットワークが必要なテストは `@pytest.mark.network` マーカーで分離されており、通常は自動でスキップされます。実行したい場合は：

```bash
uv run pytest -m network
```

## ブランチとPR

### ブランチ運用

- `main` を直接いじらず、フィーチャーブランチを切ってPRを出してください
- ブランチ名は自由ですが、`feat/xxx`, `fix/xxx` など内容がわかる名前を推奨します

### PRを出すとき

- 小さい単位で出してください（レビューしやすく、マージも早くなります）
- PRテンプレートに沿って記入してください（自動で表示されます）
- CIが緑になっていることを確認してください

### レビュー

メンテナは moajo です。気長にお待ちください。

## ドキュメント

- ドキュメントは `docs/` 配下にあり、[mkdocs-material](https://squidfunk.github.io/mkdocs-material/) でビルドします
- ローカルプレビュー: `make docs`
- API変更を伴うPRはドキュメントの更新もお願いします

## リリースフロー（メンテナ向け）

1. `main` がリリース可能な状態であることを確認
2. 次のバージョン番号を決める（[Semantic Versioning](https://semver.org/) に従う）
3. リリースコマンドを実行：
   ```bash
   make release VERSION=v0.6.3
   ```
   これで以下が自動実行されます：
   - `git-cliff` で CHANGELOG.md を再生成
   - CHANGELOG.md をコミット
   - タグを作成
4. push：
   ```bash
   git push && git push origin v0.6.3
   ```
5. タグの push をフックに `python-package.yml` が走り、PyPI 公開と GitHub Release 作成が自動で行われます

### 開発中だけ CHANGELOG を再生成したい場合

```bash
make changelog   # 直近のmainの状態でCHANGELOG.mdを上書き再生成
```

## 行動規範

OSSコミュニティの一員として、互いに敬意を持って接してください。

## ライセンス

このプロジェクトへの貢献は、リポジトリと同じ [MIT License](LICENSE) のもとで公開されることに同意したものとみなされます。
