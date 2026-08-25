# 스타일 사전 정찰 (Orchestrator 내부 추론 — worker 호출 아님)

조사일 2026-08-25. 대상: `Java-Service-Tree-Framework-Frontend-Web/arms`

> **상한 아님.** 워커는 이 결론 위에서 직접 재확인하고, 더 깊은 사실을 발견하면 result에 보고할 것.

## 1. common.css

- 856줄, **CSS 변수(`--*`) 정의 0개**. 전역 디자인 토큰 체계가 없다.

## 2. 페이지별 로컬 토큰이 실제 관례

> **[정정 2026-08-25]** 아래 원 기재에 오류 2건. claude-main이 검출하고 Orchestrator가 재실측해 확인.
> (1) 토큰 보유 페이지 **19개 → 실측 17개** (ai, business, calendar, canyon, check, company,
>     customerService, effect, index, poc, pocThankyou, policy, price, privacy, provision, rok, wai)
> (2) `--<page>-*` **접두는 관례가 아니다** — `landing_price`는 접두 없는 `--gold-1`/`--blue`/`--ink`,
>     `landing_ai`·`landing_effect`는 페이지명과 무관한 `--hm-*`/`--roi-*` 접두를 27개 공유한다.
>     진짜 불변식은 **"래퍼 클래스에 스코프된 로컬 선언"**이며, 접두명은 자유다.
>     `--lf-*` 채택 결론 자체는 유효(관례에 부합)하나 근거가 아래 기재와 다르다.

`landing_*` 30개 폴더는 각각 `content-container.html` + `content-header.html` 2파일 구성.
**17개 페이지가 로컬 `<style>` 블록에 토큰을 정의**한다 (원 기재 "19개 / `--<page>-*` 접두"는 위 정정 참조).

```
landing_poc   : --poc-accent #7cb5e0 / --poc-accent-2 #93c5fd / --poc-warn #fbbf24
                --poc-text #cbd5e1 / --poc-text-mute #94a3b8
landing_price : --gold-1 #fcd34d / --gold-2 #f59e0b / --gold-3 #fbbf24
                --blue #a4c6ff / --green #34d399 / --red #f87171
                --ink #f8f8f8 / --muted rgba(226,232,240,0.7)
```

→ 신규 페이지는 `--lf-*` 접두로 자체 토큰을 정의하는 것이 관례에 맞다.
   전역 파일을 건드리지 않으므로 회귀 위험도 없다.

## 3. 공통 팔레트 (landing_* 전체 출현 빈도 상위)

| 값 | 빈도 | 성격 |
|---|---|---|
| `#cbd5e1` | 157 | 본문 텍스트 (slate-300) |
| `#94a3b8` | 151 | 보조 텍스트 (slate-400) |
| `#fbbf24` | 109 | 경고·강조 (amber-400) |
| `#f1f5f9` | 103 | 밝은 텍스트 (slate-100) |
| `#60a5fa` | 99 | 주 액센트 (blue-400) |
| `#34d399` | 97 | 성공·완료 (emerald-400) |
| `#64748b` | 90 | 흐린 텍스트 (slate-500) |
| `rgba(226,232,240,0.75)` | 90 | 반투명 텍스트 |
| `#6ee7b7` | 55 | 보조 성공 (emerald-300) |
| `#a78bfa` | 43 | 보조 액센트 (violet-400) |
| `#f87171` | 39 | 오류 (red-400) |

Tailwind slate/amber/blue/emerald 계열. 다크 배경 전제.

## 3-b. [추가 2026-08-25] common.css는 토큰이 없을 뿐 컴포넌트는 있다

claude-main 지적(Issue #3). 원 기재가 "CSS 변수 0개"까지만 다뤄 오해 소지가 있었다.
실제로는 재사용 가능한 완성 컴포넌트가 있고, 스타일 통일의 실질적 지렛대는 팔레트보다 이쪽이다:
`.glass`(772) `.sunkenBack`(765) `.feature-row/.feature-col`(802) `.float`+`@keyframes`(796)
`.gradient_*_border`(372~392) `.btn.btn-*`(819~843) `.font10~18`(122~166).
주의: `.font10~18`은 `color:#f8f8f8`를 강제 동반하므로 크기 목적 사용 시 색 재지정 필요.

## 4. 대상 폴더 현황

`landing_function/` — `content-container.html` 53,330 bytes, `content-header.html` 515 bytes.
요구사항 `[작업 대상]`이 "기존 작업은 무시하고 작업 해"라고 지시.
