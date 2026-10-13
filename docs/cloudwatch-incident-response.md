# CloudWatchによる監視と通信障害の再現・復旧

## 目的
JLPT単語帳Webアプリケーションの運用練習として、NginxログをAmazon CloudWatch Logsに集約し、WebサーバーとWAS間の通信障害を意図的に再現して原因特定と復旧を検証した。

> 本記録は **2026年10月13日** の検証結果。意図的な障害試験であり、実際の本番障害ではない。

## 対象構成

```text
利用者
  │ HTTPS :443
  ▼
Web EC2 (Public subnet)
  Nginx / reverse proxy
  │ HTTP :8000
  ▼
WAS EC2 (Private subnet)
  FastAPI / systemd: jlpt-app.service
  │ PostgreSQL :5432
  ▼
Amazon RDS (Private)
```

- Web EC2：NginxでTLS終端・リバースプロキシ
- WAS EC2：FastAPIをプライベートサブネットで稼働
- Web→WAS：WAS側Security GroupでWeb側Security GroupからのTCP 8000のみを許可
- 監視：EC2のCPU使用率をCloudWatchダッシュボードに表示。Web EC2のCloudWatch AgentでNginxのアクセス・エラーログをCloudWatch Logsへ送信

## CloudWatch Logs設定・確認

Web EC2にCloudWatch Agentを導入し、適切なIAMロールを割り当てて、以下のログを収集した。

| Log group | ログファイル | 主な用途 |
| --- | --- | --- |
| `/jlpt/web/nginx/access` | `/var/log/nginx/access.log` | リクエスト、HTTPステータスの確認 |
| `/jlpt/web/nginx/error` | `/var/log/nginx/error.log` | upstreamへの接続失敗・タイムアウトの確認 |

ログ保存期間は3日として設定。エージェントは `status: running` / `configstatus: configured` を返し、CloudWatchコンソール上でもログの到着を確認した。

## 障害再現手順

1. 通常のWeb→WAS通信に使われるWAS Security Groupの **TCP 8000 / source: Web Security Group** のインバウンド許可を一時的に外した。
2. 公開Webサイトにアクセスして、WebからWASへ通信できない状態を再現した。
3. CloudWatch Logs上でNginxのアクセスログとエラーログを確認した。
4. 検証後は削除したインバウンド許可を元どおりに復元し、サービスの通信が復旧したことを確認した。

**注意：** 検証中はWebアプリに一時的な接続障害が生じる。作業前にルールを記録し、終了後には必ず復元する。

## 観測結果

### アクセスログ

2026-10-13 15:27:51 JST頃、次の状態を観測。

```text
"GET / HTTP/1.1" 499 0
```

`499` はNginx独自のステータスで、サーバーが応答を完了する前にクライアント側が接続を閉じたことを示す。**499のみではネットワーク遮断を原因と断定できない。**

### エラーログ

2026-10-13 15:28:52 JST頃、次の内容をCloudWatch Logsで確認。

```text
upstream timed out (110: Connection timed out)
while connecting to upstream
request: "GET / HTTP/1.1"
upstream: "http://172.31.77.10:8000/"
```

- `upstream`：接続先はプライベートサブネット内のWAS（TCP 8000）。
- `while connecting to upstream`：FastAPIの処理中ではなく、**WASへの接続確立時**に失敗。
- `Connection timed out`：接続試行がタイムアウト。

このログと、直前にWAS Security Groupのインバウンド許可を外した操作を照合し、Web→WAS間の通信遮断が今回の障害原因であると特定した。

## 復旧と結果

WAS Security Groupの **TCP 8000 / source: Web Security Group** を再度許可し、利用者からのWebアプリ接続が復旧したことを確認した。

| 検証項目 | 結果 |
| --- | --- |
| CloudWatch Agent導入・起動 | 確認済み |
| Nginx Access/ErrorログのCloudWatchへの転送 | 確認済み |
| Web→WAS通信遮断の再現 | 確認済み |
| Accessログの499 | 観測 |
| Errorログのupstream接続タイムアウト | 観測 |
| Security Group復元・サービス復旧 | 確認済み |

※復旧に要した正確な時間や、RTO/RPOは測定していないため記載しない。

## 学んだこと・今後の改善

- **EC2のCPUやインスタンス状態が正常でも、アプリケーション間の通信は失敗し得る。** メトリクスとログを組み合わせて確認する必要がある。
- NginxのAccessログはHTTPの結果、Errorログはupstream接続障害の具体的な調査に有効だった。
- Web EC2側のログ集中管理は実装済み。**WASのFastAPIログのCloudWatch集約は未実装**であり、プライベートサブネットからの送信経路とIAM権限を検討する必要がある。
- CloudWatch Alarm/SNSによる自動通知や、外部からのHTTPSヘルスチェックによる異常検知は今後の課題。
- 将来はメトリクスフィルターやアプリケーションの可用性監視などで検知を自動化したい。

## 再検証で使えるコマンド（例）

```bash
# 正常なHTTPS応答の確認
curl -i https://54-180-26-205.sslip.io/health

# Web EC2でのログ確認
sudo tail -n 30 /var/log/nginx/access.log
sudo tail -n 30 /var/log/nginx/error.log

# CloudWatch Agentの状態確認
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -m ec2 -a status
```

> `sslip.io` のホスト名はWeb EC2の当時のパブリックIPv4に基づく一時的な検証用アドレス。停止・再起動でIPv4が変わる場合はアクセス先を見直す。
