# Nginx Reverse Proxy

## 역할

공개된 Web EC2의 Nginx가 HTTP 요청을 받아 프라이빗 WAS EC2의 FastAPI(8000)로 전달합니다. Web/WAS를 분리하여 WAS의 직접적인 인터넷 노출을 피합니다.

## 설정 예시 (실제 IP는 예시값으로 대체)

```nginx
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://WAS_PRIVATE_IP:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

원본 설정의 `X-Real_IP`는 일반적인 `X-Real-IP` 헤더명과 다릅니다. 이 수정은 실제 Nginx 설정에서 별도로 확인해야 하며, 공개 문서에만 예시를 작성했습니다.

## 검증

```bash
sudo nginx -t
curl -i http://127.0.0.1/health
```

`HTTP 200` 및 `{"status":"ok"}` 응답을 확인했습니다. HTTPS/443은 아직 적용하지 않았습니다.
