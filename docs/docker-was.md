# FastAPI（WAS）のDockerコンテナ化と動作検証

## 概要

2026年10月13日、JLPT単語帳アプリケーションのWAS EC2にDockerを導入し、既存FastAPIアプリをコンテナイメージとしてビルドした。既存のsystemdサービスを稼働させたまま、Docker版を別ポートで起動し、`/health` エンドポイントの正常応答を確認した。

**検証済みなのはDockerコンテナの起動とHTTPヘルスチェックまで。** Docker版のRDSへの接続・DB利用機能、および本番トラフィックのDockerへの切り替えは未検証・未実施。

## 現在の構成

```text
利用者
  |
  | HTTPS
  v
Web EC2（Nginx）
  |
  | HTTP :8000（既存の公開経路）
  v
WAS EC2（プライベートサブネット）
  +-- 既存: systemd / uvicorn / FastAPI :8000
  +-- 試験: Docker / FastAPI（ホスト127.0.0.1:8001 -> コンテナ:8000）
  |
  v
Amazon RDS for PostgreSQL（既存DB）
```

Web EC2、Nginx、RDSの構成は変更していない。DockerコンテナはWAS EC2のループバックアドレスでのみ公開し、既存の8000番サービスとポート競合しないようにした。

## 既存WASの構成

- OS：Amazon Linux 2023（x86_64）
- プロジェクト：`/home/ec2-user/app`
- 既存サービス：`jlpt-app.service`
- 実行コマンド：`/home/ec2-user/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000`
- systemd環境変数ファイル：`/home/ec2-user/app/.env`（機密情報のため内容は記載しない）
- アプリの主な依存ライブラリ：FastAPI 0.128.8、Uvicorn 0.39.0、Jinja2 3.1.6、psycopg2-binary 2.9.11。実際のイメージ構築には仮想環境から出力した`requirements.txt`を使用。

## Docker導入

WAS EC2にDockerをインストールし、サービスを起動・自動起動に設定。

```bash
sudo dnf install -y docker
sudo systemctl enable --now docker
sudo docker version
```

実測結果：
- Docker Client / Server：**25.0.14**
- `docker.service`：**active (running)** / **enabled**

**ネットワーク上の注意：** WASは本来プライベートサブネット。パッケージとベースイメージのダウンロードに必要なネットワーク接続は別途確保が必要。作業中は一時的なインターネット到達経路を使用した。インターネット向けの設定を恒久的に開放しないよう、検証終了後にルーティングとElastic IPの取り扱いを確認する。

## Dockerfile

WAS上で作成した構成例：

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .
COPY templates/ ./templates/
COPY static/ ./static/

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

`requirements.txt`は既存venvの`pip freeze`から生成した。

```bash
/home/ec2-user/venv/bin/pip freeze > requirements.txt
```

`.dockerignore`では`.env`、仮想環境、キャッシュ、swapファイル、Git管理ファイルなどをビルドコンテキストから除外する。上記Dockerfileも必要なファイルのみを明示的にコピーし、DB認証情報をイメージに埋め込まない。

## イメージビルドと実行

```bash
cd /home/ec2-user/app
sudo docker build -t jlpt-app:v1 .

# 既存のsystemdサービスを停止せず、WAS内の127.0.0.1:8001で試験
sudo docker run -d \
  --name jlpt-test \
  --env-file /home/ec2-user/app/.env \
  -p 127.0.0.1:8001:8000 \
  jlpt-app:v1

sudo docker ps
curl -i http://127.0.0.1:8001/health
```

イメージビルド結果：

| 項目 | 結果 |
| --- | --- |
| Image | `jlpt-app:v1` |
| Image ID | `30dbb94f832b` |
| サイズ | **164 MB** |
| コンテナ名 | `jlpt-test` |
| Port Mapping | `127.0.0.1:8001->8000/tcp` |
| Dockerコンテナ状態 | **Up** |

ヘルスチェック結果：

```http
HTTP/1.1 200 OK
server: uvicorn
content-type: application/json

{"status":"ok"}
```

この結果から、Dockerコンテナ内でUvicorn/FastAPIが起動し、ローカルHTTPリクエストを正常に処理したことを確認した。

## 安全性・運用上の注意

- `127.0.0.1:8001` にバインドしているため、テストポートをWASインスタンスの外部に公開しない。
- `--env-file` は起動時の環境変数引き渡しに使用する。**機密の`.env`をDockerイメージやGitHubに含めない。**
- `/health` のHTTP 200のみではRDS接続の正常性を証明できない。DBアクセスを伴うエンドポイントで別途検証が必要。
- テスト用コンテナには再起動ポリシーを指定していない。継続運用時は起動・再起動管理を再設計する。
- 本番のNginx upstreamはまだ既存systemd版（WAS :8000）を参照しており、Docker版へは切り替えていない。

## 今後の課題

1. Docker版のRDS接続を実際のDB読み込み機能で確認。
2. 正常動作確認後、本番切り替え・ロールバック手順を準備する。
3. WASの一時的なインターネット公開経路／Elastic IPを必要に応じて解除・解放し、元のネットワーク境界を確認。
4. Dockerfile・requirements.txt・.dockerignoreの正式なソース管理（現時点ではWAS EC2での作成・ビルドを確認）。
