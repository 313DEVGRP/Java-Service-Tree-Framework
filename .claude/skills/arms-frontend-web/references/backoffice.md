# `backoffice/` 영역 작업 가이드

## 1. 현재 실구현은 jQuery다 (React 아님)

`backoffice/package.json` 에 React 17 · Redux Toolkit 2 · react-router 6 · TanStack Table 8 ·
react-hook-form · i18next · Vite 5 가 **선언되어 있다.** 그런데:

- `backoffice/src/` 디렉토리가 **없다.** `.jsx` 파일도 0개다.
- `backoffice/README.md`: *"React 선행 과제 … 아직 React 는 자동 빌드를 지원하지 않습니다."*
- 실제 화면은 `backoffice/html/{feature}/` + `backoffice/js/{feature}.js` 로,
  **arms 와 완전히 같은 구조**다.
- `backoffice/template.html` 이 `../arms/js/common.js` 를 로드한다 → 공통 함수가 그대로 쓰인다.

따라서 **신규 백오피스 화면도 jQuery 로 작성한다.** JSX 를 만들면 진입점이 없어 빌드조차 되지 않는다.
React 전환을 실제로 착수한다면 그건 별도 과제이며, 지시 없이 시작하지 않는다.

## 2. 구조

```
backoffice/
├── template.html                  # SPA 셸 (arms/template.html 과 동일 패턴)
├── html/
│   ├── template/                  # page-logo · page-sidebar · page-header · content-* 조각
│   └── {feature}/
│       ├── content-container.html
│       └── content-header.html
├── js/
│   ├── {feature}.js               # execDocReady() 정의
│   ├── common/                    # table_new.js · colorPalette.js · dwrChat.js · jspreadsheet · tourGuide
│   └── scheduleConfig/            # 기능이 커지면 하위 폴더로 분리 (api/ · table/ · 모달)
├── css/ · img/ · help/ · mock/
├── vite.config.js · .env · package.json · .eslintrc.cjs   # React 전환용 스캐폴딩 (현재 미사용)
└── README.md
```

기능 폴더(현재): `accessControl` · `appearance` · `auditLogging` · `backupRestore` ·
`dynamicConfig` · `esIndexConfig` · `esMonitoring` · `invoiceBilling` · `kafkaAdmin` ·
`languageConfig` · `mailReportConfig` · `scheduleConfig` · `securityGroup` · `securityRole` ·
`securityUser` · `smtp` · `systemInfo` · `timeoff` · `vectorIndexing`

## 3. 새 백오피스 화면 추가

1. `backoffice/html/{feature}/content-container.html` + `content-header.html`
2. `backoffice/js/{feature}.js` — `function execDocReady() { ... }`
3. `backoffice/html/template/page-sidebar.html` 에 링크 등록
   ```html
   <li id="sidebar_menu_config_schedule">
   	<a href="/backoffice/template.html?page=scheduleConfig">Schedule Config</a>
   </li>
   ```
4. 스크립트에서 `setSideMenu("sidebar_menu_config", "sidebar_menu_config_schedule")`
5. 확인 URL: `http://localhost/backoffice/template.html?page={feature}`

## 4. arms 와 다른 점

| 항목 | arms | backoffice |
|------|------|-----------|
| 테이블 | `dataTable_build()` 가 다수 | **`$.fn.table`(`table_new.js`) 가 주력** — 플러그인 그룹에 `"../arms/js/common/table_new.js"` 추가 필요 |
| 폼 검증 | 페이지별 | `parsleyjs`(lightblue4 번들) 사용 빈도 높음 |
| API prefix | `/auth-user/api/arms/...` 중심 | `/auth-admin/...`(Keycloak · 언어설정) 비중 높음 |
| 기능 분할 | 단일 `{page}.js` | 큰 기능은 `js/{feature}/` 하위로 `api/` · `table/` · 모달 분리 |

`$.fn.table` 사용 예:
```javascript
var table = $("#user_table").table({ columns: [...] }).table;   // 내부 DataTables 인스턴스
table.ajax.reload(function () { /* ... */ });
$("#user_table").table().getSelectedData();
```

## 5. 주의할 실제 문제

- **`$.ApiGenerator` 는 정의가 없다.** `backoffice/js/scheduleConfig/api/scheduleConfigApi.js` 가
  `$.ApiGenerator(BASE_URL)` 을 호출하지만 저장소 어디에도 이 jQuery 확장의 구현이 없다
  (문서 3곳이 "커스텀 `$.ApiGenerator`"라고 서술하지만 실체가 없다).
  → 그 모듈은 로드 시 TypeError 가 난다. **이 패턴을 새 코드에 복사하지 말고**
  `$.ajax` 를 직접 쓴다. 고쳐야 한다면 별도 과제로 제안한다.
- **`.env` 와 `vite.config.js` 가 어긋나 있다.** config 는 `env.VITE_MIDDLE_PROXY` 를 프록시
  target 으로 읽는데, `.env` 에는 `VITE_BACKEND_ADDR=localhost` 만 있다.
  어차피 현재는 Vite 를 쓰지 않으므로 영향이 없지만, React 전환 시 먼저 정리해야 한다.
- 쿠키 path 가 `["/arms","/backoffice"]` 라 **arms 와 세션을 공유**한다.
  인증 관련 코드를 고칠 때 두 영역을 함께 생각한다.

## 6. React 전환 스택 (착수 전까지는 참고용)

착수 지시가 있을 때만 유효하다. 선언된 규약:
- JSX 전용(`.ts`/`.tsx` 금지), 함수형 컴포넌트 + Hooks
- 전역 상태 Redux Toolkit slice(`store/`), 로컬은 `useState`/`useReducer`
- 폼은 react-hook-form (HTML `<form>` 기본 제출 금지)
- import 는 `@/...` alias, 스타일은 SCSS(`variables`/`mixins` 자동 주입 — 개별 import 금지)
- 라우팅 react-router-dom 6, 테이블 TanStack Table 8, 셀렉트 react-select 5, i18n i18next
- 빌드 Vite 5 (`base: "/backoffice/dist/"`, dev 포트 3000), 린트 ESLint 9 flat + react-hooks
