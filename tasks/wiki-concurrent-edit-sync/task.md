# wiki 동시 편집 동기화 불일치 — 원인 분석 · 개선안 · SRS

## 메타

```yaml
status: done
created: 2026-08-07
updated: 2026-08-07
priority: medium
phases:
  - id: 1
    name: 원인 분석 및 개선안 (PDF)
    status: done
  - id: 2
    name: 개선 설계 SRS (md)
    status: done
```

## Goal

### 1단계 — 원인 분석 및 개선안

wiki 동시 편집 시 편집 내용이 서로 동기화되지 않아 ① 의도치 않은 내용이 문서에 남거나 ② 같은 문자열이 복붙처럼 중복 삽입되는 현상의 **원인**과 **개선안**을 규명해, PDF 산출물 1건으로 정리한다.

완료 조건 =
① 중복 삽입·내용 유실 각각에 대해 재현 시나리오(누가 언제 무엇을 보냈을 때 깨지는지) 수준의 원인 가설이 제시됨
② 각 원인에 대응하는 개선안이 적용 난이도·영향 범위와 함께 제시됨
③ 위 내용이 PDF 파일로 `artifacts/`에 산출됨

### 2단계 — 개선 설계 SRS

1단계 분석 결과를 입력으로, 동기화 불일치를 해소하는 **개선 설계 SRS**를 Markdown 1건으로 작성한다.

완료 조건 =
① 원인 A-1~A-4 · B-1~B-7이 빠짐없이 요구사항으로 추적됨 (추적표 존재)
② 각 요구사항이 검증 가능한 수용 기준을 가짐
③ 적용 순서·마이그레이션 경로 제시
④ SRS Markdown 파일이 `artifacts/`에 산출됨

## Constraints

- 대상 시스템의 운영 데이터·문서 내용을 수정하지 않는다 (분석 전용, read-only)
- 코드 수정·커밋을 직접 수행하지 않는다. 개선안은 문서로만 제시
- 근거 없는 단정 금지 — 코드·로그로 확인된 사실과 가설을 구분해 표기

## Acceptance Criteria

### 1단계 — 원인 분석 (5/5)

- [x] 중복 삽입 현상의 원인 가설이 재현 조건과 함께 문서화 — 원인 A-1~A-4, 7단계 이벤트 표
- [x] 내용 유실·의도치 않은 내용 반영 현상의 원인 가설이 재현 조건과 함께 문서화 — 원인 B-1~B-7
- [x] 원인별 개선안 제시 (단기 완화책 / 근본 해결책 구분) — 단기 S1~S7 / 근본 R1~R5, 영향범위·난이도 표기
- [x] 사실 / 가설 구분 표기 — 항목마다 `사실|가설` 명시
- [x] PDF 파일이 `artifacts/`에 존재하고 열림 — `wiki-sync-analysis.pdf` 9p/449KB, 맑은고딕 임베딩 검증

### 2단계 — SRS (7/7)

- [x] 원인 11건(A-1~A-4, B-1~B-7) 전건이 추적표에서 요구사항으로 매핑 — §9 추적표, 누락 0
- [x] 각 기능 요구사항에 수용 기준(검증 방법) 명시 — FR-01~16 전건 AC 부여
- [x] 비기능 요구사항 포함 (성능·호환성·관측성) — NFR-01~09
- [x] 메시지 프로토콜 변경이 스키마 수준으로 기술됨 — §6 AS-IS/TO-BE + 호환 전략
- [x] 단계별 적용(마이그레이션) 순서 제시 — §7 단계 0~6 + 의존 관계도
- [x] 분석서의 미검증 가설이 전제/선행조사 항목으로 분리 표기 — §10-1~10-5
- [x] 산출물 md 파일 존재 — `artifacts/SRS-wiki-sync-improvement.md`

## Worker Plan

```yaml
# 모든 worker는 사용 전 승인 필요. 비어있으면 호출 금지.
workers_approved:
  - worker: codex-main
    approved_at: 2026-08-07
    purpose: 대상 wiki 코드베이스의 동시편집·동기화 경로 read-only 분석, 이후 본문 → PDF 렌더링
    write_scope: tasks-only     # 외부 repo 쓰기 미승인 (분석 read-only)
    approved_by: user
  - worker: claude-main
    approved_at: 2026-08-07
    purpose: 원인 가설 수립 · 개선안 설계 · 본문 작성 (strategist / 디버깅 원인 분석)
    approved_by: user
  - worker: claude-main   # 2차 호출 (2단계 SRS)
    approved_at: 2026-08-07
    purpose: 개선 설계 SRS 작성 (strategist)
    write_scope: none
    approved_by: user     # "해당 목표를 가지고 진행해"
  - worker: ollama
    approved_at: 2026-08-07
    purpose: 1단계 코드 분석 대체 시도 — 사용자 지시("ollama 로 처리해봐")
    result: REJECTED (슬롯 밖 용도·파일 접근 부재로 실패. workers/ollama/result.md 참조)
    approved_by: user

planned_workers:
  - role: codex-main
    purpose: "[1단계] target_repo 코드 분석 + PDF 렌더링"
    status: 미실행 — codex CLI·MCP 부재로 호출 불가 (log [ERROR] 참조)
    write_scope: tasks-only
  - role: claude-main
    purpose: "[1단계] 코드 분석 + 원인 가설 + 개선안 본문 → workers/claude-main/result.md"
  - role: claude-main
    purpose: "[2단계] 분석서 → 개선 설계 SRS → workers/claude-main/result-srs.md"
    write_scope: none
# codex-critic: 미승인 (사용자 선택으로 제외)
# PDF 렌더링은 codex-main 불가로 Orchestrator가 직접 수행 (로컬 Chrome headless)
```

## 산출물

| 파일 | 단계 | 내용 |
|---|---|---|
| `artifacts/wiki-sync-analysis.pdf` | 1 | 원인 분석·개선안 (9p) |
| `artifacts/wiki-sync-analysis.md` / `.html` | 1 | PDF 소스 |
| `artifacts/SRS-wiki-sync-improvement.md` | 2 | 개선 설계 SRS |
| `workers/claude-main/result.md` | 1 | 분석 원문 (정본) |
| `workers/claude-main/result-srs.md` | 2 | SRS 검증 기록 |
| `workers/ollama/result.md` | — | 실패 기록 (사용 금지) |

## Context Snapshot

이 레포(Java-Service-Tree-Framework)에는 wiki 관련 코드가 없다 (`wiki` grep 결과: 문서·설정 파일만 히트). 분석 대상 wiki는 외부 시스템으로 추정되며, `target_repo` 확정 전까지 코드 기반 분석은 불가.

## Notes

- **미확정 1 — 분석 대상**: 실제 wiki 코드베이스 경로(target_repo)가 있는지, 없다면 일반 원리(동시편집 알고리즘·충돌 해결) 기반 분석으로 진행할지 사용자 확인 필요
- **미확정 2 — 입력 자료**: 재현 스크린샷·로그·문서 diff가 있으면 `sources/`에 배치 (있을 경우 gemini 멀티모달 검토 후보)
- PDF는 codex-main이 로컬 렌더링(Markdown → PDF)으로 `artifacts/`에 생성
