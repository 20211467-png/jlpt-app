# JLPT N1 日本語単語帳 Web アプリケーション

[日本語](README.md) | [한국어](README.ko.md)

## プロジェクト概要

日本語学習のために作成した単語帳・4択テストのWebアプリケーションです。AWSでのネットワーク設計、Web/AP/DBの分離、運用と復旧を実践的に学ぶために構築しました。

## 主な機能

- JLPT N1 単語の一覧表示とページネーション
- 漢字の読み方・韓国語の意味を使った4択テスト（最大20問）
- `/health` によるアプリケーションの死活確認

## システム構成

```text
Internet
  |
Web EC2 (Public subnet, Nginx :80)
  |
WAS EC2 (Private subnet, FastAPI :8000, systemd)
  |
RDS for PostgreSQL (Private DB subnets, :5432)
```

Webサーバーのみをパブリックサブネットに配置し、WASとRDSをプライベートネットワークに配置しています。通信はSecurity Groupで制限しています。

## 技術スタック

Python / FastAPI / Jinja2 / JavaScript / CSS / PostgreSQL / Amazon EC2 / Amazon RDS / Amazon VPC / Nginx / systemd

## 設計意図

- **Web/AP分離:** Nginxで外部HTTPリクエストを受け取り、内部のFastAPIにリバースプロキシします。
- **RDS採用:** データベースをアプリケーションから分離し、マネージドサービスの運用機能を活用します。
- **アクセス制御:** WebからWAS、WASからRDSへの必要な通信のみを許可する構成を目指します。
- **ALBを未導入:** 現段階は小規模な個人開発のため、費用と構成の複雑さを考慮しました。

## 動作確認

Web EC2から `/health` にアクセスし、`{"status":"ok"}` の応答を確認しました。RDSスナップショット復元後、接続設定を見直してアプリケーションの動作を確認しました。

## セキュリティと設定

データベースのパスワードはソースコードに直接記述せず、`DB_PASSWORD` 環境変数から読み込みます。公開用サンプルでは `DB_HOST` も環境変数にしています。実行時に両方を設定してください。`*.pem` や `.env` をGitにコミットしないでください。

## ドキュメント

- [Nginxリバースプロキシ](docs/nginx.md)
- [ネットワーク・Security Group](docs/security.md)
- [RDSバックアップ・復元](docs/rds-backup.md)

## 今後の改善

Route 53、HTTPS、CI/CD、CloudWatch、Docker、ALB / Auto Scaling、負荷テストを段階的に導入する予定です。未実装の機能は導入済みとして記載していません。
