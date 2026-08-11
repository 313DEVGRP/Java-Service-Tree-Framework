# Context — wiki 동시 편집 동기화 불일치

## 현재 상태

**1·2단계 모두 완료(done).** 원인 분석 PDF + 개선 설계 SRS 산출.
2단계는 별도 폴더(`wiki-sync-srs`)로 분리했다가 규약 위반(orchestrator-rules §3)으로 이 작업에 통합함.

## 핵심 정보

- 스택: CKEditor4 + STOMP/SockJS + **자체 블록 LCS diff**. OT/CRDT 아님 (서버에 `OtService`는 있으나 위키 클라이언트가 안 씀)
- **중복 삽입 주원인**: 원격 diff 적용 후 로컬 `lastBlocks` 미갱신 (adms.js:235 vs 164). echo 없이도 결정론적 재현
- **유실 주원인**: 블록 통째 replace + base 어긋나면 delete/replace만 무시되고 insert는 항상 성공 (collab-diff.js:123,139 vs 131)
- 최우선 조치 **S1 / FR-01**: `applyBlockDiff` 직후 `lastBlocks` 재동기화 — adms.js 1줄
- 선행가설 "자기 diff 재적용"은 **반증** (session-manager.js:165에서 이미 필터)
- SRS 구성: FR-01~16 / NFR-01~09 / T-01~15 / 단계 0~6 / §9 추적표(원인 11건 누락 0) / §10 선행조사

## 미해결 이슈

- **§10 선행 조사 5건 미수행** — 브라우저·부하 실측 필요. 정적 분석으로 불가
- **§10-5(다중 인스턴스 여부)가 최우선** — `enableSimpleBroker`(인메모리)라 2대 이상이면 편집이 안 오감. 다중이면 SRS 단계 3 이후 계획 전체 재검토
- SRS 내 미결 3건: FR-05 (a)병합/(b)우선순위 택일, FR-04 식별자 저장 정책, `OtService` 재활용 여부

## 참조 자료

- artifacts/SRS-wiki-sync-improvement.md (2단계 산출물)
- artifacts/wiki-sync-analysis.pdf (1단계 산출물)
- workers/claude-main/result.md (분석 정본) · result-srs.md (SRS 검증)
- workers/ollama/result.md (실패 기록, 사용 금지)
- sources/analysis-scope.md
