# Result (노트 부분) — frontend-expert / landing-function-license-flow

<!-- 워커 응답 중 구현 노트·Issues·Checklist 부분. HTML 전문은 같은 폴더 result-content-container.html -->
<!-- 수신: 2026-08-25 10:46 / 63721 tokens / 5 tool_uses / 306s -->
<!-- Orchestrator 주: 전달 과정에서 꺾쇠가 HTML 이스케이프(&lt;)되어 도착 → 원복. 그 외 무편집. -->

## 구현 노트

- **탭 전환 방식**: 설계 §4는 "CSS `:target` 또는 최소 jQuery `.toggleClass` 수준"을 허용했다. `:target`은 URL 해시를 바꿔 페이지 스크롤이 튀고 `template.html?page=` 라우팅 관례와 충돌 소지가 있어 jQuery 이벤트 위임(`$wrap.on("click", ".fnx-tier-tab", ...)`)을 택했다. 인라인 핸들러 없음, 신규 라이브러리 없음.
- **`.feature-row` / `.feature-col` 활용 범위**: 설계 §2-2는 이 클래스를 "2×2 관점 카드, 좌우 분할"에 지정했다. 2×2 격자는 `.feature-row`가 `flex` 1행 고정이라 부적합해, 2×2에는 별도 `.fnx-persp-grid`(wrap)를 쓰고 `.feature-row`는 **좌우/3분할**(스텝 내부 설명↔시각, S5 3블록)에만 사용했다. 설계 §3-2의 "내부 `.feature-row` 3분할"은 그대로 적용.
- **`.font12~14` 미사용**: 설계 §2-2 목록에 있으나 실제 마크업에서 크기는 `rem` 단위 로컬 규칙으로 통일했다(`landing_poc` 관례와 동형). 다만 향후 부분 편집 시 `.font1x`가 섞여도 색이 깨지지 않도록 래퍼 스코프의 `color` 재지정 규칙은 선제적으로 넣어 두었다(제약 §5 대응).
- **`.glass` 패딩 오버라이드**: `common.css`의 `.glass`는 `padding: 20px 24px 24px`. 입출력 패널 헤더 정렬을 위해 `.fnx-io-panel.glass`에서 `padding`만 `!important`로 재지정했다(`landing_poc`의 `.poc-form-container.glass`가 쓰는 동일 기법). `common.css` 자체는 비접촉.
- **`.sunkenBack` 이중 용도**: 스텝 시각 영역 컨테이너와, KPI 바 트랙(`.fnx-kpi-bar`)에 모두 적용했다. 설계 §3-2 ②의 "바 배경은 `.sunkenBack`"을 문자 그대로 반영한 것이다.
- **`.float`**: STEP 1 커넥터 아이콘(`fa-exchange`)에만 적용해 설계 §2-2의 용도와 일치시켰다.
- **`blockquote` 규칙**: 설계 §2-2에 "스텝 부연 설명 인용" 용도로 올라와 있으나, 7개 스텝 어디에도 인용이 필요한 문안이 없어 실제 마크업에서는 쓰지 않았다. 래퍼 스코프 스타일 정의만 남겨 두었다(향후 사용 시 톤 일치 보장, 미사용 시 렌더 영향 0).
- **STEP 4 `<code>`**: 설계 표의 "`요구사항` label" 백틱 표기를 `<code>` 요소로 옮겼다. 별도 스타일은 주지 않아 Bootstrap 기본값을 따른다.
- **아이콘 셋**: Font Awesome 4 문법(`fa fa-*`)으로 통일했다. `landing_poc`는 `fas fa-check-circle`(FA5) 표기가 일부 섞여 있으나, 설계가 지정한 아이콘(`fa-exchange`, `fa-file-text-o`)이 모두 FA4 계열이므로 FA4로 맞췄다.
- **더미 수치**: 설계는 시각 표현의 종류만 규정하고 값은 지정하지 않았다. 표현 전용 화면이므로 일관된 시나리오(요구사항 24건 / 진척도 64% / 담당자 8명)를 한 벌 만들어 STEP 5·6·7과 S5 전체에서 동일 값을 재사용했다. KPI 담당자명은 `김＊＊` 형태로 마스킹했다.

## Issues / Caveats

1. **[설계 §2-2 일부 미사용]** `.font12/13/14`와 `blockquote`는 CSS 규칙만 두고 마크업에서 쓰지 않았다(위 구현 노트 참조). 재사용 클래스 목록을 "반드시 전부 사용"으로 읽어야 한다면 재작업 대상이다.

2. **[`.feature-row`의 2×2 한계]** `common.css:802`의 `.feature-row`는 `flex-wrap` 없는 단일 행이라 2×2 격자를 만들 수 없다. 설계 §2-2가 이 클래스를 2×2 관점 카드 용도로 지정한 것은 `common.css` 구현과 불일치한다. `.fnx-persp-grid`를 새로 정의해 우회했고, `common.css`는 건드리지 않았다.

3. **[더미 데이터 창작]** 이슈 키(`CUS-101` 등), 요구사항 제목, KPI 수치, 주간보고 문구는 설계·요구사항에 없는 예시값이다. 화면이 표현 전용임을 밝히는 각주(`※ 화면 예시입니다`)를 입출력 패널 양쪽에 달았으나, 실제 고객 데모용으로는 값 검수가 필요하다.

4. **[주간 보고 주차 표기 `2026-W35`]** 설계 §3-2 ③의 예시값을 그대로 썼다. 고정 문자열이므로 시간이 지나면 낡은 값이 된다. 동적 표기가 필요하면 별도 요청이 필요하다.

5. **[`is-selected` 등 상태 클래스는 정적]** STEP 4 이슈 리스트의 선택 상태, STEP 5 진행률 72%는 하드코딩된 표현이다. 클릭 토글 등 상호작용은 설계에 없어 넣지 않았다(탭 전환만 유일한 스크립트).

6. **[`$` 전역 의존]** 탭 스크립트는 `content-container.html`이 로드되는 시점에 jQuery가 이미 있다고 가정한다. `landing_poc`가 별도 `landing_poc.js`에서 동일 전제를 쓰고 있어 관례에 부합하나, 이 페이지는 별도 JS 파일 없이 인라인 `<script>`를 썼다. 페이지 JS 파일 분리가 프로젝트 규약이라면 `arms/js/landing_function.js` 등으로 옮겨야 한다 — 규약을 확인하지 못해 인라인으로 두었다.

7. **[설계 §5-7 승계 — Cost 색상]** `--lf-violet #a78bfa`를 Cost에 배정한 것은 설계 단계의 추론이며 기존 문서에 확정된 매핑이 아니다. 그대로 구현했다.

8. **[기존 `fn-*` 전면 대체]** 기존 파일(53,330 bytes)의 내용은 근거로 삼지 않았고 전면 대체본을 작성했다. 기존 파일에 있던 문안·섹션 중 요구사항에 없던 것은 모두 사라진다. 되살릴 내용이 있다면 별도 확인이 필요하다.

## Verification Checklist (워커 자가 체크 — Orchestrator 재검증 결과는 log.md 참조)

- [x] output이 brief의 output_format과 일치 — `content-container.html` 전문 단일 코드블록 + 구현 노트 + Issues/Caveats
- [x] 파일 경로 실존 확인 — `arms/html/landing_poc/content-container.html`, `arms/css/common.css`, `arms/html/landing_function/content-header.html` 전부 직접 읽음
- [x] constraints 충족 — 루트 래퍼 `.arms-fn-wrap`에 `--lf-*` 12개 선언 / 전 규칙 래퍼 프리픽스 / 신규 클래스 전부 `fnx-` 접두, `fn-*` 0건 / `common.css` 미수정 / 설계 §2-1 밖 새 색상값 0개(파생 알파 변형만) / `.font1x` 색 재지정 규칙 포함 / 4관점 색상 Time=ok·Scope=warn·Resource=rose·Cost=violet 준수 / `<form>`·`name` 속성·submit 0건 / Bootstrap 3 그리드 + jQuery만 사용 / `@media (max-width:991px)` + `768px` 2단 / `content-header.html` 미접촉
- [x] Do NOT 위반 없음 — 파일 쓰기·수정 0건(read-only 명령만 실행, `write_scope: none` 준수) / 설계에 없는 섹션·기능 추가 없음(탭 전환 스크립트는 설계 §4 명시) / 다른 `landing_*` 폴더 미수정 / 백엔드·JIRA 호출 코드 0건
