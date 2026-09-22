# 게이트웨이 경로 규칙 (프론트 외부 경로 → 백엔드 내부 경로)

출처: 요구사항정의서 엑셀 2행(REQ-BACKEND-FUNC-01) 원문 — 2026-09-21 개정 전 버전(`git show HEAD:요구사항정의서_엑셀양식_v3_1_3.xlsx`)에서 복구.
소스 코드에는 없는 정보다(Config Server 주입). `.claude/skills/api-catalog/scripts/routes.py` 는 `_local/gateway-routes.yml` 을 읽는데 이 PC 에는 그 파일이 없다.

```
프론트가 부르는 외부 경로는 내부 경로와 다르다.
  /{권한}/{서비스}/**  →  rewrite  →  내부 경로
  권한   auth-anon → /anonymous/    auth-user → /
         auth-manager → /manager/   auth-admin → /admin/
  서비스 api=Backend-Core  ai=AI  yml=Global-Config
         search=Engine-Fire  hub=Broker-Hub
  예외   /dwr/** 는 Backend-Core 로 변환 없이 전달. *-api/** 는 스웨거.
         auth-anon 계열은 쿠키를 떼고(RemoveRequestHeader=Cookie) 넘긴다.
```

## 이번 작업에 대한 함의

- Backend-Core 카탈로그와 대조 가능한 것은 **서비스 세그먼트가 `api` 인 호출**뿐이다.
  `ai`·`yml`·`search`·`hub` 는 대조 상대 카탈로그가 없다 → "대상 외 서비스".
- **`api` 여도 Backend-Core 가 아닌 구간이 있다.** Middle-Proxy 가 다음 4개 외부 basePath 를
  자기 컨트롤러로 직접 처리한다 (`fe_be_gaps.py` 가 Middle-Proxy 소스를 읽어 자동 판별):
  `/auth-user/api/aichat` · `/auth-user/api/aichat/recommended-cards` ·
  `/auth-user/api/arms/reqAdd/sync` · `/auth-user/api/arms/reqAdd/async`
- 변환 예
  | 프론트 외부 경로 | Backend-Core 내부 경로 |
  |---|---|
  | `/auth-user/api/arms/reqAdd/getNode.do` | `/arms/reqAdd/getNode.do` |
  | `/auth-admin/api/arms/analysis/cost/calculation` | `/admin/arms/analysis/cost/calculation` |
  | `/auth-anon/api/arms/landing/list` | `/anonymous/arms/landing/list` |
  | `/dwr/**` | `/dwr/**` (변환 없음) |
