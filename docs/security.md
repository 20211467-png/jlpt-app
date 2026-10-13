# ネットワークとセキュリティグループの設計

## 構成概要

Web EC2のみをパブリックサブネットに配置し、FastAPIが動作するWAS EC2とRDS for PostgreSQLをプライベートサブネットに配置しています。Web→WAS→RDSの通信は同一VPC内のローカルルートを利用します。

以下は2026年10月13日にコンソール画面およびAWS CLIの確認結果に基づき整理した内容です。

## セキュリティグループ

| 用途 | Security Group ID | インバウンドルール | 送信元 |
|---|---|---|---|
| Web EC2 | `sg-0ff68861513c7696a` | TCP 80, TCP 443 | `0.0.0.0/0` |
| Web EC2 (SSH) | 同上 | TCP 22 | 管理者のグローバルIP `/32` |
| WAS EC2 | `sg-0c226579246f8a209` | TCP 8000 | Web SG |
| WAS EC2 (SSH) | 同上 | TCP 22 | Bastion SG |
| RDS PostgreSQL | `sg-0b2f792ee8404c018` | TCP 5432 | WAS SG |

- Bastion SG: `sg-04baf915d25a160e2`
- WASは外部から直接アプリケーションのポート8000へアクセスできないようにしています。
- RDSの5432番ポートはWAS SGのみに許可し、Bastion SGからRDSへの例外ルールは削除しました。
- Web EC2の443番ポートは許可されていますが、2026年10月13日時点ではNginxのHTTPSリスナーは未設定です。HTTPS通信が稼働していることを意味しません。

## RDSへの適用確認

`aws rds describe-db-instances --db-instance-identifier db-jlpt --region ap-northeast-2 --query 'DBInstances[0].VpcSecurityGroups' --output table`

確認結果: `sg-0b2f792ee8404c018` が `active`。旧 `default` SGはRDSのアタッチ一覧にはありません。アプリケーションからのDBアクセスも動作確認済みです。

## アウトバウンドルールと今後の改善

コンソールで確認したWeb、WAS、Bastion、および別途作成したDB SGは、アウトバウンドが `0.0.0.0/0` に許可されています。現在は動作を維持するため、この設定を変更していません。必要に応じて管理用通信、SSM、CloudWatchなどを検証したうえで送信先とポートを限定します。

セキュリティグループはステートフルであり、許可した通信への応答について逆方向のルールを追加する必要はありません。ルートテーブルとNACLも通信成立に影響します。

> 注: ここでは確認したセキュリティグループのルールを記載しています。すべてのルーティング、NACL、実際のリソースアタッチを網羅的に監査したものではありません。
