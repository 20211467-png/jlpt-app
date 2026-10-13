# 네트워크 및 보안 그룹 설계

Web 서버만 퍼블릭 서브넷에, WAS 및 RDS를 프라이빗 서브넷에 배치합니다. 같은 VPC 내부 통신은 일반적으로 `local` 라우트를 사용하며, NAT 게이트웨이는 내부 Web→WAS→RDS 요청 전달에 필요하지 않습니다.

| 대상 | 인바운드 허용 권장값 | 소스 |
|---|---|---|
| Web EC2 | TCP 80 (HTTPS 도입 시 443) | 인터넷 사용자 |
| Web EC2 SSH | TCP 22 (사용하는 경우) | 관리자 공인 IP /32 |
| WAS EC2 | TCP 8000 | Web EC2 보안 그룹 |
| RDS PostgreSQL | TCP 5432 | WAS EC2 보안 그룹 |

위 표는 **권장 설계**입니다. 실제 AWS 콘솔의 보안 그룹 규칙과 동일한지는 아직 검증하지 않았습니다. SSH 관리에는 Session Manager를 고려할 수 있습니다.
