# 요구사항 원문 — REQ-MAPPING-FUNC-01

<!-- 엑셀 시트 변경 감지 기준선. 손으로 고치지 말 것. -->
<!-- 출처: 요구사항정의서_엑셀양식_v3_1_3.xlsx / 시트 요구사항정의서 / 4행 (2026-09-22 시트분할 문구 정정판) -->

## 요구사항 ID
REQ-MAPPING-FUNC-01
## 대분류
MAPPING
## 중분류
FUNC
## 소분류
None
## 요구사항명
FrontEnd-Backend API 매핑 분석
## 상세 내용
[개요]
FrontEnd 의 엔드포인트 와  Backend의 엔드포인트가 부합되는것끼리 매핑한다. 서로 사용하지 않는 값을 찾아내기 위함이다

[상세 기능 요구사항]
FrontEnd 와 Backend 의 서로의 엔드포인트가 매핑 되는부분을 찾아서 매핑이 되었는지 안되었는지 체크를 해야한다.
menu 별로 나타내면 되며 매핑이 안되는 것만 체크한다. 
ex) backendurl,frontendurl, no mapping

1. 경로 대조는 게이트웨이 rewrite 규칙을 적용한 뒤에 한다.
   /{권한}/{서비스}/** → 내부 경로. auth-anon→/anonymous, auth-user→(없음), auth-manager→/manager, auth-admin→/admin
   서비스 세그먼트가 api 인 것만 Backend-Core 대상. ai·yml·search·hub 는 대상 외로 분류한다.
   api 여도 Middle-Proxy 가 직접 처리하는 구간(/auth-user/api/aichat/**,
   /auth-user/api/arms/reqAdd/(sync|async)/**)이 있으므로 note 에 그 사실을 남긴다.
2. 상속으로 생긴 URL 은 provider 컬럼에 상속(<부모클래스>) 로 표기한다.
   TreeAbstractController · TreeMapAbstractController 상속분은 프레임워크 공통 트리 CRUD 라
   프론트가 호출하지 않는 것이 정상이다. 목록에서 빼지 말고 표기해 구분만 한다.
   프론트가 Tree CRUD 액션을 부르는 호출도 같은 기준으로 상속 표기한다.
   상속 액션 목록은 손으로 적지 말고 백엔드 카탈로그의 상속 행에서 읽는다.
3. 메뉴명은 추정하지 않는다. js 는 html 폴더와 1:1 이므로 그 구조로 확정한다.
   순서 = 네비게이션(page-navigation.html · page-sidebar.html) 라벨
        → html/<page>/content-header.html 의 breadcrumb·h3
        → 공통 모듈 → 페이지 키. 어느 것으로 정했는지 menusource 컬럼에 남긴다.
   한 이름이 여러 페이지를 덮으면 이름 (page) 로 구분한다.
4. 백엔드 쪽 미호출 행의 메뉴명은 같은 basePath 를 실제 호출하는 프론트 메뉴를
   건수 순으로 전부 적는다. 호출이 없으면 (호출 메뉴 없음) <basePath> 로 둔다.

[입력 / 출력]
- 입력 : backend-core_endpoints_flat.csv,frontend-web_api-calls_flat.csv
- 출력 : CSV
         엑셀은 한 시트에 menuname 기준 정렬로 낸다 (시트 분할하지 않는다)

[제약 조건 / 비기능 요구사항]
- 읽기 전용. 코드 수정·실행 금지.
- 레퍼런스 문서다. 구조 비평·결함 지적·개선 권고는 이 요구사항의 산출물이 아니다.
- 설명 문단을 늘리지 않는다. 표로 표현할 수 있으면 표로 한다.

[검증 기준]
- url을 추론해서 검증하며, 애매한경우에는 note에 남긴다
- 매핑이 성립한 행은 산출물에 싣지 않는다 (미매핑만).
- menuname 에 추정 표현이 0건이어야 한다.
- 상속으로 생긴 URL 이 provider 로 구분돼 있어야 한다.

[작업 대상]
Java-Service-Tree-Framework-Frontend-Web/arms/js/,
Java-Service-Tree-Framework-Frontend-Web/backoffice/js/
Java-Service-Tree-Framework-Backend-Core
(경로 판정 참조용으로 Java-Service-Tree-Framework-Middle-Proxy 읽기)

[Worker Settings]
- MainWorker : claude-main
- SubWorker : codex-critic
- MainWorker-SubAgent : frontend-expert
## 요청자
개발팀 이민규
## 수용 여부
수용
## 우선순위
High
## 담당자
개발팀 이민규
## 진행 현황
분석중
## 비고
None
