# 서버 연동 계약 · 도메인 모델

## 1. 시스템 구성

```
브라우저 (arms / backoffice, 정적 파일)
   │  모든 API 는 게이트웨이 경로로
   ▼
Middle-Proxy (Spring Cloud Gateway) ── Keycloak (OAuth2 / OIDC)
   ├─ Backend-Core  (A-RMS API, Spring Boot)
   └─ Engine-Fire   (검색·집계 엔진)
```
프론트엔드는 **절대 도메인/포트를 하드코딩하지 않는다.** 항상 `/auth-*` 로 시작하는 상대 경로를 쓴다.
개발 시에는 `grunt server` 의 프록시가 이 경로들을 Stage(`313.co.kr:80`)로 넘긴다.

## 2. 게이트웨이 prefix

| prefix | 용도 |
|--------|------|
| `/auth-anon/...` | 인증 없이 접근(로케일 팩, 공개 블로그/POC/게시판) |
| `/auth-user/...` | ROLE_USER — 일반 애플리케이션 API 대부분 |
| `/auth-manager/...` | ROLE_MANAGER |
| `/auth-sche/...` | 스케줄러 |
| `/auth-admin/...` | ROLE_ADMIN — Keycloak 관리, 언어 설정 등 |
| `/login`, `/logout`, `/oauth2/authorization/middle-proxy` | 인증 진입/종료 |
| `/dwr/...` | DWR(AI 채팅) |

권한보다 낮은 prefix 를 쓰면 403, 높은 prefix 를 쓰면 불필요한 권한을 요구하게 된다.
**화면의 대상 사용자 등급에 맞춰 고른다.**

## 3. 인증 흐름

1. 페이지 진입 → `authUserCheck()` → `GET /auth-user/me`
   (응답: Keycloak userinfo — `preferred_username`, `sub`, `email`, `name`, `realm_access.roles`)
2. 통과하면 `$.authorization(userID, page)` 로 페이지 접근 권한 확인 후 렌더 시작.
3. `landing_*` 페이지는 **URL 에 `landing_` 이 있으면 인증을 건너뛴다.**
4. 쿠키는 `setCookie()` 기본 path `["/arms", "/backoffice"]` 로 두 영역이 공유한다.
   배포 도메인/경로가 이 전제를 깨면 로그인 세션이 끊긴다.

## 4. 전역 에러 처리 — 페이지에서 중복 구현하지 않는다

`ajax_setup()` 이 문서 레벨에 걸어 둔 처리:

| 상태 | 처리 |
|------|------|
| `401` | `jError` + `/oauth2/authorization/middle-proxy` 리다이렉트 |
| `403` | `jError` (이동 없음) |
| `500` | `jError` |
| 시작/종료 | `.loader` 표시/숨김, 완료 시 `Ladda.stopAll()` |

페이지에서는 **도메인 에러(빈 결과, 검증 실패)만** 처리한다.

## 5. 호출 형태

```javascript
$.ajax({
	url: "/auth-user/api/arms/pdService/getVersionList?c_id=" + pdServiceId,
	type: "GET",
	contentType: "application/json;charset=UTF-8",
	dataType: "json",
	progress: true,             // 이 저장소의 관례 플래그
	statusCode: {
		200: function (data) { /* ... */ }
	},
	error: function (e) {
		jError("버전 목록 조회 중 에러가 발생했습니다.");
	}
});
```
- 성공 처리는 `success` 보다 **`statusCode: { 200: ... }`** 을 쓰는 코드가 다수다. 주변에 맞춘다.
- POST 본문은 `JSON.stringify(...)` + `contentType: "application/json;charset=UTF-8"`.
- `common.js` 의 `ajax_sample()` 이 주석 포함 참고 템플릿이다.

## 6. 응답 봉투

두 가지가 공존한다. **호출하는 엔드포인트가 어느 쪽인지 먼저 확인**한다.

```javascript
// 구형 .do (Backend-Core)
{ "response": [ { "c_id": 14, "c_title": "A-RMS" }, ... ] }   // 또는 { "result": [...] }

// 신형 엔진 API
{ "success": true, "response": { ... } }
```
```javascript
callApi(function (data) {
	if (data && data.success && data.response) { render(data.response); }
	else { console.warn("빈 응답"); }
});
```

## 7. 실제로 쓰이는 대표 엔드포인트

사용 빈도순 발췌. 새 화면은 같은 계열의 기존 호출을 먼저 찾아 형태를 맞춘다.

| 용도 | 엔드포인트 |
|------|-----------|
| 인증 확인 | `GET /auth-user/me` |
| 사용자 조회 | `GET /auth-user/search-user/{userName}` |
| 제품 목록 | `GET /auth-user/api/arms/pdServicePure/getPdServiceMonitor.do` |
| 제품 단건 | `GET /auth-user/api/arms/pdServicePure/getNode.do` |
| 버전 목록 | `GET /auth-user/api/arms/pdService/getVersionList?c_id={제품ID}` |
| 버전 + 기간 | `GET /auth-user/api/arms/pdService/versions-with-date?c_id={제품ID}` |
| 제품 등록/수정 | `POST /auth-user/api/arms/pdService/addPdServiceNode.do` · `updateNode.do` |
| 제품 상세/첨부 | `/auth-user/api/arms/pdServiceDetail/{getNode,getNodes,updateNode,getFilesByNode,uploadFileToNode}.do` |
| 요구사항 트리 | `/auth-user/api/arms/reqAdd/{테이블명}` (+ `sync/{테이블명}`) — jstree 규약 |
| 요구사항 목록 | `GET /auth-user/api/arms/reqAdd/{테이블명}/getMonitor.do` |
| 요구사항 하위 | `GET /auth-user/api/arms/reqAdd/{테이블명}/getChildNodeWithParent.do?c_id=&c_left=&c_right=` |
| 요구사항 엑셀 업로드 | `/auth-user/api/arms/reqAdd/excel-upload/req-def/pd-service-id/{id}` |
| 요구사항 상태 | `/auth-user/api/arms/reqState/getNodesWithoutRoot.do` · `reqStateCategory/getNodesWithoutRoot.do` · `reqState/getReqStateListFilter.do` |
| ALM 서버/연결 | `/auth-user/api/arms/jiraServer/...` · `jiraServerProjectPure/...` · `globaltreemap/setConnectInfo/...` |
| 리포트 | `/auth-user/api/arms/report/full-data/assignee-list` · `report/portfolio-track-record/...` |
| KPI 대시보드 | `POST /auth-user/search/engine/kpi/dashboard/{project-status\|requirement-overview\|time-compliance\|contribution\|quality}` |
| 검색 엔진 | `/auth-user/search/engine/search/...` |
| AI 채팅 | `/auth-user/ai/chat/stream` (+ DWR `dwrChat.js`) |
| 로케일 팩 | `GET /auth-anon/yml/language-config/packs/language/{locale}` (관리는 `/auth-admin/yml/...`) |
| Keycloak 관리 | `/auth-admin/realms/master/...` (user · role · group) |

KPI 요청 본문 예:
```json
{
  "pdServiceAndIsReq": { "pdServiceLink": 14, "pdServiceVersionLinks": [58, 60, 61] },
  "assigneeEmailAddress": "user@example.com"
}
```
`assigneeEmailAddress` 는 로그인 사용자의 Keycloak `email`(= 전역 `userEmail`)이다.
백엔드가 이 이메일로 ALM assignee 를 역추적한다.

## 8. 도메인 모델

```
제품(Product)            예) "A-RMS" (id 14)
  └ 버전(Version)        분기 단위. "2026년 2분기 ( Cloud JIRA 활용 )"
       └ 작업자(Worker)  버전과 다대다 (parent="60,61,62")
```
- 제품 : 버전 = 1 : N, 버전 : 작업자 = N : M.
- **버전명은 semver 가 아니라 분기형 문자열**이다. `v2.4.0` 같은 이름을 만들지 않는다.
- `versionId` 는 백엔드 실제 `c_id` 를 그대로 쓴다. 가짜 ID 를 발급하지 않는다.
- "현재 분기"는 오늘 날짜 기준으로 판단(`current: true`).
- 백엔드 트리 컬럼 규약: `c_id` · `c_title` · `c_left` · `c_right` · `c_type`
  (nested set — `jsTreeBuild` 가 이 구조를 전제로 동작).

### 주요 필드
- **Version**: `versionId`, `versionName`, `quarter`, `tool`, `period`, `status`, `current`,
  `currentWeek`, `totalWeeks`, `totalIssues`, `planCount`, `completedCount`, `delayedCount`,
  `progressRate`, `achievementRate`
- **Requirement(일정 관점)**: `reqKey`, `reqTitle`, `productName`, `version`, `startDate`,
  `plannedEndDate`, `actualEndDate`, `plannedDurationDays`, `actualDurationDays`, `delayDays`,
  `started`, `completed`, `deadlineClass`

### ALM 필드 매핑
| 프론트 | ALM 원본 |
|--------|---------|
| `startDate` | `created` |
| `plannedEndDate` | `duedate` |
| `actualEndDate` | `resolutiondate` |

**공수(estimate) 데이터는 없다.** 모든 소요/지연 계산은 날짜 기반이다.

## 9. 파생값은 저장하지 말고 계산한다

| 값 | 계산식 |
|----|--------|
| 상태(status) | `progressRate` 구간 매핑 (100 Done / 80–99 Normal / 50–79 Warning / 1–49 Critical / 0 미시작) |
| 마감 분류 | 마감일 < 오늘 & 미완료 → 지연 / 오늘~D+7 & 미완료 → 임박 / 그 외 미시작 → 예정 / 완료 → 완료 |
| 계획 소요일 | `plannedEndDate − startDate` |
| 실제 소요일 | `actualEndDate − startDate` (미완료면 오늘까지) |
| 지연일 | `(actualEndDate 또는 오늘) − plannedEndDate` |
| 주차 라벨 | `"YYYY년 N주차"` |

## 10. 권한 등급

| 역할 | 화면 |
|------|------|
| `ROLE_USER` | 대시보드 · `detail_*` 실무자 화면 |
| `ROLE_MANAGER` | + 제품/ALM/요구사항 관리 |
| `ROLE_ADMIN` | + 분석 · 리포트 · 백오피스 |

`menu_setting()` 이 `permissions` 배열로 메뉴를 분기한다.
화면 안에서 권한별 요소를 감출 때도 같은 전역 배열을 쓴다.

## 11. 4단계 파이프라인 (화면 구성의 축)

| 단계 | 의미 | 대표 화면 |
|------|------|-----------|
| Connect | ALM 도구 연결 | `jiraServer`, `jiraConnection`, `mapping` |
| Deploy | 제품·버전·요구사항 트리 구성 | `pdService`, `pdServiceVersion`, `reqAdd` |
| Collect | 이슈·진척 수집/추적 | `reqStatus`, `reqStatusCalendar`, `reqGantt`, `reqKanban` |
| Statistics | 분석·리포트·대시보드 | `analysis*`, `report*`, `dashboard`, `detail_dashboard`, `detail_kpi` |
