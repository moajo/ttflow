# Changelog

このプロジェクトの変更履歴です。フォーマットは [Keep a Changelog](https://keepachangelog.com/) に準拠しています。

## [0.6.3] - 2026-04-09

### その他

- BufferCacheProxyの読み取りキャッシュと書き込みバッファを分離 (#17) ([df31161](https://github.com/moajo/ttflow/commit/df311617551c8a8a9f42e96c5c335816329db1c0))

### 追加

- Add MIT License to the project ([3dc3b9e](https://github.com/moajo/ttflow/commit/3dc3b9e1a817054e97d393d29c9f07ebd6fe08ee))
- ライセンスメタデータをpyprojectとREADMEに反映 (#19) ([ee646e8](https://github.com/moajo/ttflow/commit/ee646e8392e91259e369fcf6da59f15ee7289ea7))
- READMEにPyPI版・対応Python・CIのバッジを追加 ([4fa2693](https://github.com/moajo/ttflow/commit/4fa26939b7d62a6803dd6d6f36b6d10e759f0d13))
- IssueテンプレートとPRテンプレートを追加 (#20) ([dc54137](https://github.com/moajo/ttflow/commit/dc54137939bf9539efb2b75589dff3ba25f23572))
- git-cliff設定とリリース用Makefileを追加しCHANGELOGを整備 ([d4369cd](https://github.com/moajo/ttflow/commit/d4369cd6e700d528c415493ba24197dbb4707497))
## [0.6.2] - 2026-04-09

### 追加

- AWS Lambda デプロイ用 Terraform モジュールの追加 (#13) ([6b48d22](https://github.com/moajo/ttflow/commit/6b48d22a66ce515462c2f26e7992168797de5320))
- ダッシュボードのRunボタン修正とサンプル追加 (#14) ([28edac2](https://github.com/moajo/ttflow/commit/28edac21dc2b78f7acbe8fa1e35236974a736aa0))
- ダッシュボードに実行トレース可視化を追加 (#15) ([f5a18e6](https://github.com/moajo/ttflow/commit/f5a18e6cef66728bf6d42ca240586014adf31f09))
- 完了したrunの実行状態をバックエンドから削除する (#16) ([5f15056](https://github.com/moajo/ttflow/commit/5f15056fead6f2482ffb3330da0385692ad6acb3))
## [0.6.1] - 2026-03-12

### 修正

- action-gh-releaseのバージョンをv3からv2に修正 ([eb4def1](https://github.com/moajo/ttflow/commit/eb4def1d55e10ba8f1e8db7a9627a9bf20d4bfbc))

### 変更

- バージョン管理をhatch-vcsに移行しGitタグからバージョンを自動取得するように変更 ([9d181c6](https://github.com/moajo/ttflow/commit/9d181c625af26f00162bc3a8e55f477358a67b8d))
## [0.6.0] - 2026-03-12

### その他

- パッケージ管理をpoetry/pysenからuv/ruffに移行し、CI・開発ツールチェーンを刷新 ([37c456b](https://github.com/moajo/ttflow/commit/37c456b06c316deb6399f98655fb35c718790a53))
- ワークフロー関数のargs引数を省略可能にし、中断2重実行テストを実装、無効化テストを有効化 ([dd01dd2](https://github.com/moajo/ttflow/commit/dd01dd281c8c70fb264b5f2f0be99913f36b1462))

### 修正

- 不要なimport・未使用スクリプトの削除とlint警告の修正（変数名`l`→`entry`等） ([25d8e79](https://github.com/moajo/ttflow/commit/25d8e799ed69951b0536c623a5fffd300099b0dd))

### 削除

- テストファイルの余分な空行を削除 ([32c3aaa](https://github.com/moajo/ttflow/commit/32c3aaac6a5334c4ae282420e7bb29e7d2110a68))
- 未使用のCLIモジュールとスクリプトエントリポイントを削除 ([89b6517](https://github.com/moajo/ttflow/commit/89b651757c41c3ebc57c5fd6905f65cc767237af))
- 不要なTODOコメントとリファクタリング計画の完了済み項目を削除 ([294d213](https://github.com/moajo/ttflow/commit/294d213b812c451842fa5573c41d0ddf2831512a))
- 完了済みリファクタリング計画ドキュメントを削除 ([7a65db6](https://github.com/moajo/ttflow/commit/7a65db6b1c0c225c26f0157614da02d3d1cc4518))

### 変更

- update readme ([ca0eb8f](https://github.com/moajo/ttflow/commit/ca0eb8f0a0a2bff75444eeac9dcf2544651a2eb9))
- CIワークフローのGitHub Actionsを最新メジャーバージョンに更新 ([732f860](https://github.com/moajo/ttflow/commit/732f860ead794a74d3e7974834b896268bb882f5))
- DynamoDBバックエンドの再実装（厳密なロック機構付き） (#7) ([8a8166f](https://github.com/moajo/ttflow/commit/8a8166ff79d9003e1e3b1c9f785805f688880184))

### 追加

- CLAUDE.md・リファクタリング計画・開発メモを追加し、開発再開の方針を整理 ([4e7efb2](https://github.com/moajo/ttflow/commit/4e7efb297b01a89e1b6942742a9e48dcf77a563d))
- 型ヒント追加・カスタム例外導入・マジック文字列の定数化・ワイルドカードimport廃止などコード品質を改善（Phase 2〜4） ([ade26b1](https://github.com/moajo/ttflow/commit/ade26b111afd9e3fd489d692c57f7bb43b4dc034))
- ワークフローエンジンの主要機能（中断再開・状態管理・副作用・ロック・トリガー等）を網羅する新規テストスイートを追加 ([2941d0f](https://github.com/moajo/ttflow/commit/2941d0fe5f63a43abe1fcf06c43d008ed23458c9))
- CIワークフローをlint-all.ymlからci.ymlに統合し、マルチバージョンテストジョブを追加 ([e581c39](https://github.com/moajo/ttflow/commit/e581c3988745cc0e8251f1d6965af9b900bb230e))
- Add code coverage tracking with pytest-cov and Codecov integration (#1) ([1a62164](https://github.com/moajo/ttflow/commit/1a6216428998639f0300a00c3af50c817988e0be))
- ロック競合テストの追加とCI/ドキュメントの軽微な修正 ([e254a4b](https://github.com/moajo/ttflow/commit/e254a4bbb7c8a19d76f294736c36c1d36edb7856))
- Makefileにコメント追加とallターゲット追加、リファクタリング計画の完了済み項目を削除 ([5954fc2](https://github.com/moajo/ttflow/commit/5954fc2b2f43d354772e1c10e7065c2bd3155f2b))
- イベントシステムのドキュメントを追加 ([aad0e79](https://github.com/moajo/ttflow/commit/aad0e791c8025bd850526bc53a46c55e5707514c))
- async/awaitワークフロー対応 (#5) ([171d17f](https://github.com/moajo/ttflow/commit/171d17f343cd88aad5f41e04f3c4b793454f9de9))
- S3クライアントのキャッシュ化とStateRepositoryドキュメント追加 (#6) ([86e0594](https://github.com/moajo/ttflow/commit/86e059489c0c45ea00389596d7f73e92c0445ff5))
- Add comprehensive documentation and docs deployment setup (#9) ([b209961](https://github.com/moajo/ttflow/commit/b209961d4f80646e57cae612a2f9124bd6272533))
- Add web dashboard for ttflow workflow management (#10) ([586d0ab](https://github.com/moajo/ttflow/commit/586d0ab607b5c83c44e73b8e21c5844a9d4859be))
- CIにPyPI公開ジョブを追加しリリースワークフローを分離 ([ed9a377](https://github.com/moajo/ttflow/commit/ed9a377791f66d4ac36ffc0bdba1a3a845a3c616))
## [0.5.8] - 2023-01-17

### その他

- v0.5.8 ([db7fd39](https://github.com/moajo/ttflow/commit/db7fd397586a94fb19e794c7f90bd56f24c9aa8f))

### 修正

- fix bug ([822abde](https://github.com/moajo/ttflow/commit/822abde9755cfc07460e1853325943f5f6221af5))
## [0.5.7] - 2023-01-15

### その他

- v0.5.7 ([edde2f4](https://github.com/moajo/ttflow/commit/edde2f456465d2627fe74606af66f24daa8f2b9d))

### 修正

- fix bug ([9592b68](https://github.com/moajo/ttflow/commit/9592b68cf8b7c7530e46e1b9105b99fbdc118b4c))
## [0.5.6] - 2023-01-08

### その他

- feat: list_registered_workflows ([231b143](https://github.com/moajo/ttflow/commit/231b14375d138fa75d3278190bc6ef6d197b4b0e))
- v0.5.6 ([f47ffee](https://github.com/moajo/ttflow/commit/f47ffeeaa5cda56a64294f38ba5246c6a78d2fc6))
## [0.5.5] - 2023-01-08

### その他

- feat: get_completed_runs_log ([b04ef22](https://github.com/moajo/ttflow/commit/b04ef22fd66784dcc18d534f3e4a7a0897f150bc))
- v0.5.5 ([10047d2](https://github.com/moajo/ttflow/commit/10047d23aad03c81d798953f953b9034d505ebc9))
## [0.5.4] - 2023-01-08

### その他

- v0.5.4 ([b560002](https://github.com/moajo/ttflow/commit/b560002d82aa786b8fb15c17c5332c94db168dda))

### 追加

- add args to add_list_state: max_length ([c7f088a](https://github.com/moajo/ttflow/commit/c7f088a70176d653088d319329b013e5511f3700))
## [0.5.3] - 2023-01-06

### その他

- v0.5.3 ([9a5eb7d](https://github.com/moajo/ttflow/commit/9a5eb7df2020925d0c3ac2a821cf1ed5b46f6866))

### 追加

- fix: add_list_state ([e8fc445](https://github.com/moajo/ttflow/commit/e8fc4458c6916e04fb943f904514ab2b33c1ccf9))
## [0.5.2] - 2023-01-06

### その他

- chore ([a81ff25](https://github.com/moajo/ttflow/commit/a81ff255afe366637babbed0d641d80efc2bdec7))
- every trigger ([f6fc528](https://github.com/moajo/ttflow/commit/f6fc528491f4c284919899b1ed4844ae2c417d45))
- v0.5.2 ([029bbd3](https://github.com/moajo/ttflow/commit/029bbd3196fa872bca512ed47a09c3605e8f07d8))

### 修正

- fix s3 client ([4a7c2e3](https://github.com/moajo/ttflow/commit/4a7c2e3a95065dfee3c3e4d88a46fcc044b6d145))

### 変更

- refactor ([b9d146f](https://github.com/moajo/ttflow/commit/b9d146fa5db3c64724deb9c1fd0f0a5cd82bbba8))

### 追加

- add sample ([52ca1fa](https://github.com/moajo/ttflow/commit/52ca1fae73f5bc8a500757980bf4ede3d71bb105))
- add test ([842d938](https://github.com/moajo/ttflow/commit/842d93849abb016b9374c16ba09b680836f969d1))
- add docs ([16d2c12](https://github.com/moajo/ttflow/commit/16d2c12fd44798034d2ba094125cb4788e4a6381))
## [0.5.1] - 2023-01-05

### その他

- ログは最新1000件のみ保持するようにした ([14c9d13](https://github.com/moajo/ttflow/commit/14c9d1369875eb8c0788194f090144311bf4ce4d))
- v0.5.1 ([1f26eb0](https://github.com/moajo/ttflow/commit/1f26eb0f81091943452028630a9e9a7e0af4f582))

### 修正

- fix: mkdir local state ([8db0ac5](https://github.com/moajo/ttflow/commit/8db0ac50c0c33048d0a5f4ff895c04397598f5b7))
- fix samples ([9bce1c4](https://github.com/moajo/ttflow/commit/9bce1c4bb8d84329e8ff23bdd3331d225be23a57))
- skip処理の修正 ([6ac1dee](https://github.com/moajo/ttflow/commit/6ac1dee496bd26142a0da94d5ba1e375cf7954e3))
## [0.5.0] - 2023-01-05

### その他

- feat: 例外情報をrunのレスポンスに含めた ([ac592d2](https://github.com/moajo/ttflow/commit/ac592d21120fa11e3f430e6787327e90b1eaca89))
- feat: cache and buffer ([94e18c5](https://github.com/moajo/ttflow/commit/94e18c58a5ba7c3d156d1e4bf72c53f03f5e8ae8))
- feat: run_by_cli ([f91f681](https://github.com/moajo/ttflow/commit/f91f68100ef30ae19bac5a02c05102ed3619efef))
- v0.5.0 ([c84bb2c](https://github.com/moajo/ttflow/commit/c84bb2c85a8580ac6c9730c024b37ec6780a4e14))
## [0.4.0] - 2023-01-04

### その他

- feat: @subeffect ([f62807c](https://github.com/moajo/ttflow/commit/f62807c276af2fca5faad681f8dfb5be0563697f))
- improve interface ([89d2e43](https://github.com/moajo/ttflow/commit/89d2e432ac4f80fe90211f86e81aea705907939c))
- v0.4.0 ([0c317b0](https://github.com/moajo/ttflow/commit/0c317b0be85e6b6744137d31c8f095cd99091d01))
## [0.3.1] - 2023-01-04

### その他

- v0.3.1 ([5c6b801](https://github.com/moajo/ttflow/commit/5c6b8014cb70a76301832780bb425bae1417fb36))

### 修正

- fix skip bug ([919acb5](https://github.com/moajo/ttflow/commit/919acb579a80a1293eab23fd669589675c2e5de1))
## [0.3.0] - 2023-01-04

### その他

- feat: run result ([f2dc691](https://github.com/moajo/ttflow/commit/f2dc6915c2bd8643663206a47e5cd4b849f8207f))
- v0.3.0 ([446baae](https://github.com/moajo/ttflow/commit/446baaee40f5badae904e895803df4fadb2f3f0c))

### 修正

- fix lock ([92b3970](https://github.com/moajo/ttflow/commit/92b397098796211962cd4ef2a957d494f354bf0b))
- feat: s3 prefix ([07e43c4](https://github.com/moajo/ttflow/commit/07e43c42924d05a2d7d9ce09f7df9cecc90259bf))
## [0.2.1] - 2023-01-04

### その他

- v0.2.1 ([c3f265f](https://github.com/moajo/ttflow/commit/c3f265f43c14f44d9226e7b0378ff0c56e9e4887))

### 変更

- change python version ([cdc173a](https://github.com/moajo/ttflow/commit/cdc173abf00520b7d3ef6089a8343e8e24fc4ac4))
## [0.2.0] - 2023-01-04

### その他

- initial commit ([1f8deb8](https://github.com/moajo/ttflow/commit/1f8deb8afbd04fcaa9de598128d278934312e344))
- format ([aea64fd](https://github.com/moajo/ttflow/commit/aea64fdfbca9be1028cd5617601d72e90b4c4531))
- configurable state backend ([fda497a](https://github.com/moajo/ttflow/commit/fda497a50d7616683924cb8fcff9d52f265019cb))
- improve logging ([b0d178f](https://github.com/moajo/ttflow/commit/b0d178f51341d750e826f6a3e214444fa3e733e5))
- lock ([fd4e7d3](https://github.com/moajo/ttflow/commit/fd4e7d3553fd4a7dc5327b42a60465625ae07fc2))
- ci ([3707138](https://github.com/moajo/ttflow/commit/37071387abeebf4c41f1120a83ccebb03d3710d8))

### 修正

- fix run_state ([83cfaa0](https://github.com/moajo/ttflow/commit/83cfaa0f9dc8e1af63806cfbf8a5162748af49ae))

### 変更

- change interface ([b4abfb3](https://github.com/moajo/ttflow/commit/b4abfb328b5a49ab4a3cc4b120c715725933870f))
- refactor ([221dfc2](https://github.com/moajo/ttflow/commit/221dfc2d3ad078f569fbc405b99c548e93db2d29))
- refactor pause system ([9c3e2bd](https://github.com/moajo/ttflow/commit/9c3e2bd2a290ab40544beea1e349f5d34cae28d7))

