# Brief — ollama / landing-function-license-flow

## Worker 행동 규약 (고정 — 모든 brief에 그대로 유지, 삭제 금지)

- 요청 범위만 최소로. 사변적 추상화·기능 추가 금지
- 외과수술식 수정: 기존 스타일 유지, 무관 코드 비접촉
- 사용자 대화 채널 없음: 가정은 명시하고, 불확실·불일치는 result의 Issues/Caveats에 표면화

## Objective

아래 설계안이 요구사항 7단계를 빠짐없이·올바른 순서로 담았는지 점검한다.

## Output Format

아래 8개 질문에 **정확히 이 형식으로만** 답하라. 다른 문장·설명·재작성 금지.

```
Q1: YES 또는 NO — (NO면 빠진 단계 번호)
Q2: YES 또는 NO — (NO면 잘못된 위치)
Q3: YES 또는 NO
Q4: YES 또는 NO
Q5: YES 또는 NO
Q6: YES 또는 NO — (NO면 해당 색상값)
Q7: 숫자
Q8: 한 문장
```

## 점검 질문

- Q1: 설계안에 아래 7단계가 **모두** 있는가?
  1)JIRA 연결 2)Base Version 프로젝트 설정 3)매핑 이슈 타입별 우선순위·유형 확인
  4)요구사항 이슈 선정 5)A-RMS 자동 수집 6)Time·Scope·Resource·Cost 분석 7)개인 성과지표·주간 보고
- Q2: 7단계가 위 번호 순서대로 배치되었는가?
- Q3: 입력(JIRA Admin 접속 정보)이 화면에 표현되는가?
- Q4: 출력 4종(4관점 리포트·개인 KPI·주간 보고)이 표현되는가?
- Q5: PRO·ENT 골격이 존재하는가?
- Q6: 스타일 매핑표의 모든 색상이 아래 허용 팔레트 안에 있는가?
  허용: #cbd5e1 #94a3b8 #f1f5f9 #64748b #60a5fa #34d399 #fbbf24 #f87171 #a78bfa #6ee7b7 #f8f8f8
- Q7: 스타일 매핑표에 정의된 `--lf-*` 토큰은 몇 개인가?
- Q8: 가장 큰 문제 하나를 한 문장으로.

## Do NOT

- 설계안을 재작성하지 말 것
- brief의 헤더 구조를 복제하지 말 것
- 위 8줄 형식 외의 출력 금지

## 점검 대상 설계안

# 화면 정보구조 · 스타일 매핑 설계 — `landing_function` (REQ-LANDING-FUNC-01)

전수 확인 근거 (직접 재확인분):
`arms/css/common.css` 856줄 전량 / `arms/html/landing_*` 30개 폴더 `content-container.html`·`content-header.html` 전량 토큰·클래스 스캔.
토큰 보유 페이지 실측 **17개** (recon 기재 19와 불일치 — §5 보고).

---

## 1. 화면 정보구조

### 1-0. 루트 스코프

기존 관례(전 페이지 예외 없음)는 **로컬 `<style>` + 단일 래퍼 클래스에 토큰 선언 + 모든 규칙을 래퍼로 프리픽스**다 (`.arms-poc-wrap`, `.rokg-guide`, `.cs-*`). 따라서:

```
루트 래퍼: .arms-fn-wrap        ← --lf-* 토큰 전량을 여기서 선언
전 규칙 프리픽스: .arms-fn-wrap .xxx
content-header.html: 변경 없음  ← landing_poc와 byte-identical한 공용 보일러플레이트
```

`common.css`는 CSS 변수 0개 · 전역 파일이므로 **비접촉**. 회귀 위험 0.

### 1-1. 섹션 순서 (상→하)

| # | 섹션 | 역할 | 핵심 컴포넌트 |
|---|---|---|---|
| S1 | 히어로 | 페이지 목적 1문장 + 라이선스 3타입 예고 | `.fnx-hero` (eyebrow/title/lead) |
| S2 | **라이선스 타입 셀렉터** | POC · PRO · ENT 전환 탭. 기본 선택 = POC | `.fnx-tier-tabs` |
| S3 | **입력 패널** | JIRA Admin 접속정보 (요구사항 `[입력]`) | `.fnx-io-panel.glass` |
| S4 | **POC 7단계 흐름** | 본론. 7 스텝 세로 타임라인 | `.fnx-flow` + `.fnx-step` ×7 |
| S5 | **출력 패널** | 4관점 리포트 · 개인 KPI · 주간보고 (요구사항 `[출력]`) | `.fnx-io-panel.glass` |
| S6 | PRO 골격 | 탭 전환 시 표시. 골격만 | `.fnx-tier-skeleton` |
| S7 | ENT 골격 | 동상 | `.fnx-tier-skeleton` |

S3·S5를 S4의 앞뒤로 감싸 **입력 → 처리(7단계) → 출력**이 화면 흐름 자체로 읽히게 한다. 검증기준 ③(입출력 명시)을 배치로 충족.

### 1-2. POC 7단계 — 제목 · 설명 · 시각 표현

각 스텝 공통 골격 (`.fnx-step`):

```
[num]  STEP n · <영문 eyebrow>
       <한글 heading>
       <설명 lead 1~2문장>
       <bullet .fnx-step-list>  ·  <시각 .fnx-step-visual>
```

`[num]`은 `landing_customerService`의 `.cs-step-num` 패턴(28×28 원형·monospace·700)을 그대로 차용하고 색만 `--lf-accent`로 교체.

| n | eyebrow | heading (한글) | 설명 | 시각 표현 |
|---|---|---|---|---|
| 1 | STEP 1 · Connect JIRA | 고객사 JIRA와 A-RMS를 연결합니다 | Admin 권한 계정으로 JIRA 인스턴스를 등록하면 A-RMS가 프로젝트 목록을 읽어옵니다. | **연결 카드 2개 + 중앙 커넥터**. 좌 `JIRA` / 우 `A-RMS`, 사이 점선 + `fa-exchange`. 연결 성공 pill `● Connected` (`--lf-ok`) |
| 2 | STEP 2 · Set Base Version | Default 프로젝트의 Base Version을 설정합니다 | 고객사 JIRA 프로젝트를 A-RMS Default 프로젝트의 Base Version으로 지정해 기준선을 만듭니다. | **매핑 행 2줄**: `JIRA Project ─▸ Base Version`. 선택된 값은 `--lf-accent` 태그 pill |
| 3 | STEP 3 · Review Mapping | 매핑된 이슈의 타입별 우선순위·유형을 확인합니다 | 설정 즉시 자동 매핑된 이슈를 이슈 타입별로 묶어 우선순위와 유형 분포를 확인합니다. | **타입별 미니 테이블**: 행=이슈타입(Epic/Story/Bug/Task), 열=우선순위 배지(High `--lf-danger` / Mid `--lf-warn` / Low `--lf-muted`) + 건수 |
| 4 | STEP 4 · Select Requirement | PM·팀장이 요구사항 이슈를 선정합니다 | 이슈 리스트에서 EPIC 또는 `요구사항` label 등 요구사항에 준하는 이슈를 선정합니다. | **선택 가능한 이슈 리스트**: 각 행 좌측 체크 아이콘, `EPIC` / `label:요구사항` 필터칩. 선택 행만 `--lf-accent` 좌측 3px 보더 |
| 5 | STEP 5 · Auto Collect | A-RMS가 선정 이슈를 자동으로 수집합니다 | 선정된 이슈와 하위 이슈·변경 이력을 A-RMS가 주기적으로 수집합니다. | **수집 진행 바** + 카운터 3개 (수집 이슈 / 하위 이슈 / 변경 이력). 바 색 `--lf-accent`→`--lf-accent-2` 그라디언트 |
| 6 | STEP 6 · 4-Perspective Analysis | Time · Scope · Resource · Cost 관점으로 분석합니다 | 수집 데이터를 네 관점으로 분석해 프로젝트 상태를 정량화합니다. | **2×2 관점 카드**. 관점별 색은 §2-3 기존 매핑 준수 |
| 7 | STEP 7 · KPI & Weekly Report | 개인 성과지표와 주간 보고 리포트를 확인합니다 | 개인별 KPI를 확인하고 주간 보고 리포트를 생성해 내려받습니다. | **좌: 개인 KPI 리스트**(담당자 · 지표 바) / **우: 주간보고 문서 카드**(`fa-file-text-o` + `생성` 버튼 `.btn.btn-primary`) |

**단계 4의 분기 표기**: 요구사항 원문 4)는 "2) 연결 후"로 시작해 3)과 병렬 분기다. 순차 7단계를 깨지 않되 사실을 보존하기 위해 STEP 4 카드에 `.fnx-step-branch` 각주 한 줄 — `STEP 2 완료 시점부터 수행 가능` — 을 단다. (§5 보고)

**연결선**: `.fnx-flow`에 `::before` 세로 1px 라인(`--lf-line`)을 두고 num 원이 그 위에 얹히는 타임라인. `landing_company`의 `.co-timeline` 선례와 동형.

---

## 2. 스타일 매핑표

### 2-1. `--lf-*` 토큰 정의 (`.arms-fn-wrap`에 선언)

신규 색상값 **0개** — 전부 정찰 팔레트 및 실측 확인값 재사용.

| 토큰 | 값 | 성격 | 출처 (실측) |
|---|---|---|---|
| `--lf-accent` | `#7cb5e0` | 주 액센트 | `landing_poc --poc-accent`, `pocThankyou`, `policy`, `privacy`, `provision` (5페이지 공유 최다값) |
| `--lf-accent-2` | `#93c5fd` | 보조 액센트 (그라디언트 끝) | `landing_poc --poc-accent-2`, `pocThankyou --ty-accent-2` |
| `--lf-text` | `#cbd5e1` | 본문 텍스트 | 12개 페이지 `--*-text` 전원 동일값. 빈도 157 |
| `--lf-text-mute` | `#94a3b8` | 보조 텍스트 | 12개 페이지 `--*-text-mute` 전원 동일값. 빈도 151 |
| `--lf-ink` | `#f1f5f9` | 제목 밝은 텍스트 | `landing_poc .poc-title color`. 빈도 103 |
| `--lf-warn` | `#fbbf24` | 경고·중간 우선순위 | `landing_poc --poc-warn`, `price --gold-3`, `company --co-accent-4`. 빈도 109 |
| `--lf-ok` | `#34d399` | 성공·완료·Time | `landing_price --green`, `index` SVG `Version-Time`. 빈도 97 |
| `--lf-danger` | `#f87171` | 오류·High 우선순위 | `landing_price --red`. 빈도 39 |
| `--lf-violet` | `#a78bfa` | 보조 액센트 (Cost) | `landing_company --co-accent`. 빈도 43 |
| `--lf-rose` | `#f472b6` | Resource 관점 | `landing_index` SVG `Assignee - Resource` |
| `--lf-muted` | `rgba(226,232,240,0.75)` | 반투명 본문 | `landing_index` blockquote 다수. 빈도 90 |
| `--lf-line` | `rgba(255,255,255,0.12)` | 구분선·보더 | `common.css .glass` border 값 그대로 |

파생 투명도(`rgba(124,181,224,.10/.15/.30)` 등)는 `--lf-accent`의 알파 변형으로, `landing_poc`가 이미 쓰는 동일 기법이다. 신규 색상 아님.

### 2-2. `common.css` 재사용 클래스 (전역 비접촉, 그대로 사용)

| 클래스 | 위치 | 용도 |
|---|---|---|
| `.glass` | common.css:772 | S3·S5 입출력 패널, 스텝 카드 컨테이너. `border-radius:24px` + blur + 그림자 완제품 |
| `.sunkenBack` | common.css:765 | 스텝 내부 시각 영역(테이블·진행바) 함몰 배경 |
| `.feature-row` / `.feature-col` | common.css:802 | 2×2 관점 카드, 좌우 분할 (양끝 마진 자동 제거) |
| `.font12` `.font13` `.font14` | common.css:132~142 | 캡션·본문·소제목 크기. `color:#f8f8f8` 동반 → 필요 시 `--lf-text`로 override |
| `.gradient_bottom_border` | common.css:383 | 섹션 구분선 |
| `.gradient_middle_border` | common.css:388 | 스텝 내부 약한 구분선 |
| `.flex` / `.flex-space-between` | common.css:650 | 헤더 행 정렬 |
| `.float` + `@keyframes float` | common.css:796 | 연결 커넥터 아이콘 미세 부유 |
| `.btn.btn-primary` | common.css:819 | 주요 액션(주간보고 생성). `rgba(59,130,246,.25)` |
| `.btn.btn-success` | common.css:824 | 연결 완료 상태 표시 |
| `.row` / `.col-lg-*` `.col-md-*` | Bootstrap 3 (전 페이지 공통) | 그리드. `landing_poc` `col-lg-5` + `col-lg-6 col-lg-offset-1` 관례 |
| `blockquote` | common.css:394 | 스텝 부연 설명 인용 (landing_index 관례) |

### 2-3. 4관점 색상 매핑 (기존 정본 준수)

`landing_index` SVG와 본문이 이미 확정한 매핑을 **그대로** 승계한다. 임의 재배정 금지.

| 관점 | 한글 라벨 | 색 토큰 | 근거 |
|---|---|---|---|
| Time | 일정 | `--lf-ok` `#34d399` | `landing_index`: `<tspan fill="#34d399">Version</tspan> - Time` |
| Scope | 진척도 | `--lf-warn` `#fbbf24` | `landing_index`: `<tspan fill="#fbbf24">Product (Service)</tspan> - Scope` |
| Resource | 성과 | `--lf-rose` `#f472b6` | `landing_index`: `<tspan fill="#f472b6">Assignee</tspan> - Resource` |
| Cost | ROI | `--lf-violet` `#a78bfa` | 나머지 1칸. `landing_index` 한글 라벨 `ROI (Cost)`, 색은 미지정 액센트 중 최다 `#a78bfa` |

한글 라벨은 `landing_index:308` 원문 `일정 (Time), 진척도 (Scope), 성과 (Resource), ROI (Cost)`를 그대로 쓴다.

### 2-4. 신규 로컬 클래스 (`.arms-fn-wrap` 스코프)

`fnx-` 프리픽스를 쓴다. 기존 `landing_function`의 `fn-*`와 **충돌 회피**가 목적 — 기존 구현을 무시하고 새로 짜지만 같은 파일 내 잔존/부분 이관 시 규칙이 섞이는 사고를 막는다. (§5 보고)

`.fnx-hero` `.fnx-tier-tabs` `.fnx-tier-tab` `.fnx-io-panel` `.fnx-io-title` `.fnx-field` `.fnx-flow` `.fnx-step` `.fnx-step-num` `.fnx-step-eyebrow` `.fnx-step-heading` `.fnx-step-lead` `.fnx-step-list` `.fnx-step-visual` `.fnx-step-branch` `.fnx-pill` `.fnx-badge` `.fnx-persp-card` `.fnx-kpi-row` `.fnx-tier-skeleton`

반응형 브레이크포인트는 실측 최다인 `@media (max-width: 991px)` (15회)를 1차, `768px` (7회)를 2차로 채택.

---

## 3. 입출력 표현

### 3-1. 입력 — JIRA Admin 접속정보 (S3)

`.fnx-io-panel.glass`, 헤더 `↓ INPUT · 고객사 JIRA 접속 정보`, 우측에 `Admin 권한 필요` 배지(`--lf-warn`).

| 필드 | 표기 예시 | 비고 |
|---|---|---|
| JIRA Base URL | `https://<고객사>.atlassian.net` | |
| Admin 계정 | `admin@company.com` | |
| API Token | `••••••••••••` | 마스킹 고정 |
| Default 프로젝트 | `ARMS` | STEP 2 연결 대상 |

**표현 전용**. `<form>`/`<input name>`/submit 없이 읽기 전용 `.fnx-field` 행으로 렌더 — 실제 연동 아님을 화면에서도 분명히 하고, 요구사항의 백엔드 금지 제약을 만족한다. 하단 각주: `※ 화면 예시입니다. 실제 연결은 관리자 콘솔에서 수행합니다.`

### 3-2. 출력 (S5) — 3블록 배치

`.fnx-io-panel.glass`, 헤더 `↑ OUTPUT · A-RMS 산출물`. 내부 `.feature-row` 3분할 (991px 이하 세로 스택).

**① 4관점 리포트** — `.feature-col` 안에 2×2 `.fnx-persp-card`. 카드당 [관점 아이콘 · 한글(영문) 라벨 · 대표 수치 1개 · 미니 바]. 색은 §2-3 고정.
- 일정 (Time) `--lf-ok` / 진척도 (Scope) `--lf-warn` / 성과 (Resource) `--lf-rose` / ROI (Cost) `--lf-violet`

**② 개인 KPI 지표** — `.fnx-kpi-row` 4~5행. [담당자명 · 지표 라벨 · 수평 바(`--lf-accent`) · 값]. 바 배경은 `.sunkenBack`.

**③ 주간 보고 리포트** — 문서 미리보기 카드. `fa-file-text-o` + `2026-W35 주간 보고` + 항목 3줄 요약 + `.btn.btn-primary` `리포트 생성`. 버튼은 표현용(`type="button"`, 핸들러 없음).

STEP 6·7의 시각 표현과 S5는 **동일 컴포넌트를 재사용**한다 (스텝 내부는 축소판, S5는 확대판). 중복 CSS 없이 `.fnx-persp-card--sm` 변형자 하나만 추가.

---

## 4. PRO · ENT 골격

두 타입은 S2 탭 전환 시 노출. 7단계 상세 없이 **골격만** (`.fnx-tier-skeleton`).

공통 골격 구조:

```
[타입 배지]  [한 줄 정의]
[POC 대비 확장점 3~4 bullet]
[단계 흐름 축약 칩 행 — 제목만, 설명·시각 없음]
[Coming Soon 안내 1줄]
```

**PRO** — 배지색 `--lf-accent-2`
- 정의: 단일 조직의 상시 운영 라이선스
- 확장점: 다중 프로젝트 동시 관리 / 상시 자동 수집 스케줄 / 조직 단위 KPI 집계 / 리포트 기간 커스터마이즈
- 축약 칩: `JIRA 연결` → `다중 프로젝트 Base Version` → `상시 수집` → `4관점 + 추세 분석` → `조직 KPI · 정기 리포트`

**ENT** — 배지색 `--lf-violet`
- 정의: 전사 다조직·거버넌스 라이선스
- 확장점: 다중 ALM 소스 연동 / 조직 계층별 롤업 / 권한·감사 정책 / 전용 배포(Single Tenant)
- 축약 칩: `다중 ALM 연결` → `조직 계층 매핑` → `전사 수집` → `4관점 롤업 분석` → `경영 대시보드 · 감사 리포트`

안내 문구: `PRO · ENT 상세 흐름은 후속 요구사항에서 정의됩니다.` (요구사항 원문이 POC만 기술 — 임의 창작 방지)

탭 전환은 CSS `:target` 또는 최소 jQuery `.toggleClass` 수준. 기존 페이지들이 이미 jQuery 전제이므로 신규 의존성 없음.

---

## 5. Issues / Caveats

1. **[정찰 불일치 — 토큰 보유 페이지 수]** `style-recon.md`는 19개 페이지가 로컬 토큰을 갖는다고 기재했으나, 실측 결과 **17개**다 (`ai, business, calendar, canyon, check, company, customerService, effect, index, poc, pocThankyou, policy, price, privacy, provision, rok, wai`). 설계 결론에는 영향 없음.

2. **[정찰 불일치 — 토큰 프리픽스 관례]** recon은 `--<page>-*` 접두를 관례로 제시했으나, `landing_price`는 실제로 **접두 없는 `--gold-1 / --blue / --ink / --muted`**를 쓴다. 또한 `landing_ai`·`landing_effect`는 페이지명과 무관한 `--hm-*`/`--roi-*`/`--hire-*` 도메인 접두를 쓰고 두 페이지가 토큰 세트를 공유한다(27개 동일). 즉 진짜 불변식은 "페이지명 접두"가 아니라 **"래퍼 클래스에 스코프된 로컬 선언"**이다. `--lf-*`는 관례에 부합하되, 근거는 recon이 적은 것과 다르다.

3. **[정찰 누락 — `common.css`가 토큰만 없는 게 아니라 컴포넌트를 갖고 있음]** recon은 "CSS 변수 0개 / 전역 토큰 체계 없음"까지만 기술했으나, `common.css`에는 **재사용 가능한 완성 컴포넌트**가 있다: `.glass`(772), `.sunkenBack`(765), `.feature-row/.feature-col`(802), `.float`+`@keyframes float`(796), `.gradient_*_border`(372~392), `.btn.btn-*` 색상 오버라이드(819~843), `.font10~18`(122~166). 스타일 통일성의 실질적 지렛대는 팔레트보다 이쪽이며, §2-2에서 전량 재사용했다. `landing_poc`도 `.poc-form-container glass`로 이미 `.glass`를 혼용한다.

4. **[`.font1x` 클래스의 색 강제]** `.font10~18`은 `font-size`와 함께 `color:#f8f8f8`를 항상 동반한다. 본문에 그대로 쓰면 `--lf-text`(`#cbd5e1`)와 어긋난다. 크기 목적으로 쓸 때는 `.arms-fn-wrap` 스코프에서 `color`를 재지정해야 한다. 구현 워커가 놓치기 쉬운 지점.

5. **[요구사항 4)의 순차성 위배]** 원문 4)는 `"2) 연결 후. PM이나 팀장은…"`으로 시작해 3)과 **병렬 분기**다. 화면은 7단계 순차로 읽혀야 한다는 완료조건과 충돌하므로, 순서는 유지하되 STEP 4에 `STEP 2 완료 시점부터 수행 가능` 각주(`.fnx-step-branch`)를 달아 사실을 보존했다. 요구사항 갱신 시 재검토 대상.

6. **[기존 `fn-*` 클래스 잔존 위험]** 대상 파일 `landing_function/content-container.html`(53,330 bytes)에는 이미 `fn-flow-step`·`fn-step-num`·`fn-step-eyebrow` 등 **부분 구현된 7단계 유사 흐름**이 있고(`:575`, `:610~619`에 "Base Version에 고객사 프로젝트를 연결합니다" 등 STEP 2 문구까지 존재), 이 페이지는 토큰 보유 17개 목록에 없다(= 로컬 토큰 0). 브리프상 이를 근거로 삼지 않았고, 충돌 회피를 위해 신규 프리픽스를 `fnx-`로 분리했다. **다만 이 파일을 전면 대체할지 부분 교체할지는 `context.md`의 미해결 이슈로 남아 있다.** 전면 대체를 권고한다 — 부분 교체 시 `fn-*`/`fnx-*` 두 체계가 한 파일에 공존해 유지보수가 나빠진다. Orchestrator 확인 필요.

7. **[Cost 관점 색상은 추론]** Time·Scope·Resource는 `landing_index` SVG에 색이 명시돼 있으나 **Cost만 명시가 없다**. `--lf-violet #a78bfa`는 남은 액센트 중 사용 빈도 최다값을 고른 결과로, 팔레트 내부이지만 기존 문서에 확정된 매핑은 아니다.

8. **[POC/PRO/ENT 명칭의 화면 선례 없음]** `landing_license`·`landing_price` 어디에도 `POC`/`PRO`/`ENT` 3분류 표기가 없다(`Enterprise`는 `landing_business`·`landing_customerService`에만 산문으로 등장). 즉 이번 페이지가 3타입 명칭의 **최초 화면 도입**이며, 향후 `landing_price`와 명칭이 어긋날 위험이 있다. 요구사항 원문 표기 `( POC, PRO, ENT )`를 그대로 따랐다.

9. **[표현 전용 범위]** S3 입력 패널은 `<form>`·`name` 속성·submit 없이 읽기 전용으로 설계했다. `landing_poc`는 실제 `<form id="poc_form">`을 쓰지만, 본 페이지는 백엔드·JIRA 연동 금지 제약이 있어 의도적으로 다르게 했다. 시각적으로는 동일 계열을 유지한다.

---
