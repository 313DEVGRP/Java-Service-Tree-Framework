# 알려진 함정 · 안티패턴

저장소 자체 기록: `docs/ai/12_known_issues/frontend-web-known-issues.md`
(새 함정을 발견하면 그 문서에 `- [영역] 증상 — 원인 / 우회법` 형식으로 추가한다.)

---

## 1. 런타임에 조용히 깨지는 것들

### DataTable 콜백 미선언 → `ReferenceError`
`common.js` 의 `dataTable_extendBuild()` 는 `initComplete` / `drawCallback` / 행 클릭에서
페이지 전역 함수 `dataTableCallBack` · `dataTableDrawCallback` · `dataTableClick` 을 호출한다.
`$.isFunction(...)` 으로 감싸긴 하지만, **선언 자체가 없는 식별자**는 인자 평가 시점에
`Uncaught ReferenceError: dataTableDrawCallback is not defined` 를 던진다.
→ DataTable 을 쓰는 페이지는 세 함수를 **빈 본문이라도 선언**한다.

### `execDocReady()` 미정의 → 아무 일도 안 일어남
`$.getScript("js/{page}.js")` 성공 콜백이 `execDocReady()` 를 부른다.
이름이 다르거나 없으면 에러 없이 화면만 비어 있다. 새 페이지에서 가장 흔한 실수다.

### 페이지 쌍 누락
`html/{page}/content-container.html` 과 `js/{page}.js` 중 하나만 있으면 라우팅이 성립하지 않는다.
(`landing_canyon` · `landing_check` 등 html 만 있는 예외가 남아 있지만 신규 작성 시엔 쌍을 지킨다.)

### 로딩 스피너 문구 잔류
`loadPlugin()` 은 로드 직전 `.spinner` 에 "OO.js 다운로드 중…" 을 쓰고 **완료 후 비우지 않는다.**
그룹 병렬 로딩이라 가장 무거운 파일(예: `echarts.min.js` ≈ 1MB) 문구가 마지막에 남아
그 파일만 계속 로딩되는 것처럼 보인다.
`setSideMenu()` 를 호출하는 페이지는 1초 뒤 문구가 교체돼 가려지지만, 호출하지 않는 페이지
(KPI 대시보드류)는 영구 잔류한다.
→ **우회법:** `loadPluginGroupsParallelAndSequential(...).then()` 안에서 `$(".spinner").empty();`
공통 함수 자체를 고치는 건 전 페이지 영향이 있어 신중히 한다.

### 테이블 재빌드 시 낡은 핸들러 누적 (해결됨 — 패턴만 유지)
같은 테이블을 `destroy: true` 로 재빌드해도 tbody DOM 이 재사용되므로, `off` 없이 매번
클릭 핸들러를 bind 하면 이전 인스턴스를 잡은 핸들러가 쌓여 `row().data()` 가 TypeError 를 냈다.
현재 `common.js` 는 `click.dtBuild` · `page.dt.dtBuild` · `length.dt.dtBuild` 네임스페이스로
bind/off 한다. **페이지에서 직접 거는 핸들러는 다른 네임스페이스를 쓴다.**

### 중첩(child row) 테이블의 이벤트 버블링
child row 안 테이블의 `tr` 은 DOM 상 부모 tbody 안에 있어 행 인덱스가 부모 기준으로 해석된다.
자식 테이블 행 클릭에는 `stopPropagation()` 을 건다.

### DataTables 헤더 수동 작성
`<thead>` 를 손으로 쓰면 `columnList` 와 개수가 어긋나 라벨이 한 칸씩 밀린다.
`<thead></thead>` 로 비우고 `columnList` 의 `title` 로 생성하게 둔다.

## 2. i18n

- **일본어 폴백 부재:** `setLocale()` 은 Global-Config 실패 시 `/arms/locales/{locale}.json` 을
  부르고 허용 로케일은 `["ko","ja","en"]` 이다. 저장소 파일은 `ko.json` · `en.json` ·
  **`jp.json`(0바이트)** 라 `ja` 선택 시 `ja.json` 404 → 라벨 전부 빈 값.
  `jp.json` 은 **어느 코드도 읽지 않는 사(死)파일**이므로 키를 넣지 않는다.
  0바이트 파일에 키 하나만 넣으면 JSON 파싱이 성공해버려 `bindLocaleText()` 가
  **나머지 모든 라벨을 빈 값으로 덮는다** — 안 건드리는 쪽이 안전하다.
  일본어 지원이 필요하면 `ja.json` 신설/Global-Config 등록을 별도 과제로 제안한다.
  (도움말 JSON 폴더는 `arms/help/*/ja/` 로 `ja` 를 쓴다 — 두 규칙이 다르다.)
- `data-locale` 키를 `ko.json` 에만 넣고 `en.json` 을 빠뜨리면 영어에서 **빈 라벨**이 노출된다.
- `setLocale()` 은 i18next 가 아니라 자체 구현이다. i18next API 를 부르지 않는다.
- 값에 넣은 HTML 은 `sanitizeHTML()` 의 허용 태그(`span,small,strong,p,b,ul,li,br`)만 남는다.

## 3. 라이브러리 · 경로

- **버전 폴더명 하드코딩:** `echarts-5.5.0`, `select2-4.0.2` 처럼 경로에 버전이 박혀 있다.
  업그레이드 시 `<script src>` 가 전부 깨진다.
- **버전 공존:** echarts 5.4.3 / 5.5.0, d3 5.16 / 6.7 이 함께 있다.
  기존 화면 수정 시엔 **그 화면이 이미 로드한 버전**을 따른다. 한 페이지에 두 버전을 올리지 않는다.
- **CKEditor4 신규 사용 지양** — 성능 이슈로 일부 비활성화돼 있다(`CKEDITOR.md` 참고).
- **대형 정적 도구 직접 편집 금지:** `drawio` · `drawio-wiki` · `drawdb` · `three.js-r165` 는
  임베드만 하고 통째 교체로 업그레이드한다.
- **Three.js r165 호환:** 일부 모듈(`CapsuleGeometry` 등) 포함 여부를 `build/` · `examples/jsm/` 에서
  먼저 확인한다.
- **CDN 새로 박지 않기:** 사내망/오프라인 전제라 외부 CDN 의존은 배포 후 깨질 수 있다.

## 4. 없는 것을 있다고 착각하기 쉬운 것들

- **`$.ApiGenerator` 는 구현이 없다.** `backoffice/js/scheduleConfig/api/scheduleConfigApi.js` 가
  호출하지만 저장소 어디에도 정의가 없어 해당 모듈은 TypeError 가 난다.
  문서 3곳이 "커스텀 `$.ApiGenerator`"라고 적고 있으니 문서만 보고 따라 쓰지 않는다.
- **React/Vue/TypeScript 는 이 저장소에 없다.** backoffice 의 React 선언은 미도입 스캐폴딩이고,
  루트 Vue 는 2026-06-23 제거됐다. `.ts`/`.tsx` 를 추가하지 않는다.
- **자동화 테스트 인프라가 없다.** Vitest/RTL 은 전략 문서상의 계획이며 설정이 없다.
  검증은 브라우저 육안 확인 + 콘솔 에러 0건이다.
- **루트 `개발규칙.txt` 는 존재하지 않는다**(여러 문서가 원본으로 인용한다).
  실질 정본은 `docs/ai/04_coding_standards/frontend-web-coding-standards.md`.
- **`.travis.yml` 과 루트 `file/` 디렉토리도 없다.** CI 는 `.github/workflows/release-drafter.yml`
  하나(트리거 브랜치 `master`)뿐이고, 문서 자산은 `docs/file/` 에 있다. 실제 작업 브랜치는 `dev`.
- `06_page_playbooks/guide.md` 가 링크하는 `landing_test.md` 와 `landing_test` 페이지는 삭제됐다.
- `03_directory_structure/frontend-web-directory.md` §3 은 backoffice 를 React(`src/`)로 서술한다.
  같은 폴더의 `02_tech_stack` §3 · `12_known_issues` §1 이 맞다.

## 5. 공통 자산 변경의 폭발 반경

| 파일 | 영향 |
|------|------|
| `arms/js/common.js` | **arms + backoffice 전 페이지** (백오피스도 이 파일을 로드한다) |
| `arms/template.html` | 레이아웃 조립이 깨지면 전 페이지 진입 불가 |
| `arms/locales/*.json` | 키 누락 시 전역 빈 라벨 |
| `arms/css/override.css` · `common.css` | 전 화면 스타일 |
| `arms/html/template/page-sidebar.html` | 전 화면 내비게이션 |

고치기 전에 **영향 범위를 먼저 말하고**, 페이지 단위로 해결 가능하면 그쪽을 택한다.
불가피하게 고쳤다면 인증·메뉴·트리·테이블을 쓰는 대표 페이지 몇 개를 직접 확인한다.

## 6. 데이터·도메인에서 자주 나오는 오류

- **진척률 ↔ 상태 불일치** (42% 를 Warning 으로 표기하는 식). 구간 매핑을 정확히 지킨다.
- **semver 버전명 생성.** 버전은 `"YYYY년 N분기 ( 도구 )"` 분기형이다.
- **목업 필드명 임의 변경** → 실데이터 연동 시 매핑이 끊긴다. 실제 API 형태를 유지한다.
- **가짜 ID 생성.** `versionId` 는 백엔드 `c_id` 를 그대로 쓴다.
- **요청 범위 초과 가공(YAGNI 위반).** 실무자 화면에 매니저용 롤업/집계를 임의로 얹지 않는다.

## 7. 편집 사고

- 대량 수정 후 **태그 불균형**(`div`/`section`/`table`/`tr`) 확인.
- 목업 수정 후 **JSON 유효성** 확인.
- 스플라이스용 **임시 파일 즉시 삭제.**
- `console.log` · `alert` 잔존 금지.
