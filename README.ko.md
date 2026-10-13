# JLPT N1 일본어 단어장 웹 애플리케이션

[日本語](README.md) | [한국어](README.ko.md)

## 개요

일본어 학습용 단어 조회 및 객관식 테스트 애플리케이션입니다. AWS에서 Web/WAS/DB를 분리한 아키텍처를 구축하고 운영 경험을 쌓는 것을 목적으로 개발했습니다.

## 주요 기능

- JLPT N1 단어 조회 및 페이지네이션
- 읽는 법·한국어 뜻을 활용하는 4지선다 테스트(최대 20문항)
- `/health` 정상 동작 확인 API

## 인프라 구성

```text
인터넷 → Web EC2(퍼블릭, Nginx:80) → WAS EC2(프라이빗, FastAPI:8000)
                                       → RDS PostgreSQL(프라이빗, 5432)
```

Web 서버만 퍼블릭 서브넷에 배치하고, WAS 및 RDS는 프라이빗 서브넷에 배치했습니다. 서버 간 통신은 보안 그룹으로 제한합니다.

## 기술 선택 이유

- **Nginx:** 리버스 프록시를 통한 외부 요청 전달 및 Web/WAS 분리
- **RDS:** DB와 애플리케이션의 관리 분리 및 관리형 DB 기능 활용
- **systemd:** FastAPI 서비스의 지속 실행 및 재시작 관리
- **ALB 미사용:** 현재 단일 서버·낮은 트래픽을 고려한 비용 및 복잡도 선택

## 구현 및 검증

Web EC2에서 `/health` 호출 시 `{"status":"ok"}` 응답을 확인했습니다. RDS 스냅샷 복원 후 연결 설정을 수정하여 애플리케이션 정상 동작을 확인했습니다.

비밀번호는 `DB_PASSWORD` 환경변수로 분리했고, 공개용 예제에서는 RDS 주소도 `DB_HOST` 환경변수로 사용합니다.

## 문서

- [Nginx 설정](docs/nginx.md)
- [보안 그룹 및 네트워크](docs/security.md)
- [RDS 스냅샷 및 복원](docs/rds-backup.md)

## 향후 계획

도메인, HTTPS, GitHub Actions, CloudWatch, Docker, ALB 및 Auto Scaling, 부하 테스트를 단계적으로 추가할 예정입니다.
