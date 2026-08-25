# Brief — frontend-expert / landing-function-license-flow

## Worker 행동 규약 (고정 — 모든 brief에 그대로 유지, 삭제 금지)

- 요청 범위만 최소로. 사변적 추상화·기능 추가 금지
- 외과수술식 수정: 기존 스타일 유지, 무관 코드 비접촉
- 사용자 대화 채널 없음: 가정은 명시하고, 불확실·불일치는 result의 Issues/Caveats에 표면화

## Execution Context

```yaml
target_repo: C:/DEV/sourcecode/Java-Service-Tree-Framework/Java-Service-Tree-Framework-Frontend-Web
write_scope: none     # 직접 쓰기 금지. 파일 전문을 텍스트로 반환 — 반영은 Orchestrator
```

## Objective

확정된 설계를 `landing_function/content-container.html` **전문**으로 구현한다.
기존 파일은 **전면 대체**한다(사용자 결정). 설계를 재해석하지 말고 그대로 옮긴다.

## Input

```
설계 정본(그대로 따를 것): workers/claude-main/result.md
  §1 화면 정보구조(S1~S7·7단계 표) · §2 스타일 매핑표 · §3 입출력 · §4 PRO·ENT 골격
참고 관례: <target_repo>/arms/html/landing_poc/content-container.html
공통 CSS(비접촉): <target_repo>/arms/css/common.css
대체 대상: <target_repo>/arms/html/landing_function/content-container.html
```

## Constraints

- 루트 래퍼 `.arms-fn-wrap`에 `--lf-*` 토큰 12개 선언. 모든 규칙을 이 래퍼로 프리픽스
- 신규 클래스는 `fnx-` 접두. 기존 `fn-*`는 전면 대체이므로 사용하지 않음
- `common.css` **수정 금지**. `.glass`·`.sunkenBack`·`.feature-row/col`·`.btn.btn-*` 등 재사용
- 설계 §2-1 밖의 **새 색상값 도입 금지**
- `.font10~18`은 `color:#f8f8f8`를 강제 동반 → 크기 목적 사용 시 래퍼 스코프에서 색 재지정
- 4관점 색상은 설계 §2-3 고정 매핑 준수 (Time=ok, Scope=warn, Resource=rose, Cost=violet)
- 입력 패널은 표현 전용 — `<form>`·`name` 속성·submit 금지
- Bootstrap 3 그리드 + jQuery 전제. 신규 라이브러리 의존 추가 금지
- 반응형 `@media (max-width:991px)` 1차 / `768px` 2차
- `content-header.html`은 **건드리지 않음**

## Output Format

`content-container.html` **전문**을 단일 코드블록으로 반환. 발췌·생략 금지.
이어서 아래 섹션:
- 구현 노트: 설계와 다르게 처리한 부분과 이유
- Issues/Caveats: 가정·불확실·설계 불일치

## Do NOT

- 파일 직접 쓰기·수정 (텍스트 반환만)
- 설계에 없는 섹션·기능 추가
- `common.css`·`content-header.html`·다른 `landing_*` 폴더 수정
- 백엔드 호출·JIRA 연동 실구현
