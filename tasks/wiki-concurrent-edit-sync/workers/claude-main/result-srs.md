# Result — claude-main / wiki 동기화 개선 SRS

## 실행 메타

```yaml
worker: claude-main
call_type: native (Task sub-agent, subagent_type=claude-main)
tool_uses: 12
duration_s: 366
status: 수락 (ACCEPTED)
```

## 산출물 (worker 응답 원문)

worker 응답 본문(SRS 전문)은 **무편집 그대로** 아래 경로에 저장되어 있다. 중복 보관하지 않고 경로로 참조한다 (요약본 대체 아님 — telephone game 방지).

```
tasks/wiki-concurrent-edit-sync/artifacts/SRS-wiki-sync-improvement.md
```

Orchestrator가 가한 변경: 없음. 단, worker 응답 말미의 "Orchestrator 조치 필요" 안내문과 Verification Checklist는 문서 본문이 아니므로 산출 파일에 포함하지 않고 이 result.md에 남겼다. 부록 B(참조 문서)는 Orchestrator가 추가했다.

## 산출물 개요

- 섹션 11개 (`1.개요` ~ `11.Issues/Caveats`) + 부록 A(근거 코드 위치) · B(참조 문서)
- 기능 요구사항 **FR-01 ~ FR-16** (16건), 각각 설명·근거원인·수용기준(AC)·우선순위(P0/P1/P2)
- 비기능 요구사항 **NFR-01 ~ NFR-09** (9건)
- 검증 시나리오 **T-01 ~ T-15** (15건) + 단계별 배포 게이트
- 적용 계획 **단계 0 ~ 6** + 의존 관계도
- 선행 조사 항목 **§10-1 ~ §10-5** (미검증 가설 분리)

## Verification Checklist (worker 자체 신고)

- [x] output이 brief의 output_format과 일치
- [x] 참조한 파일 경로가 실제 존재
- [x] task.md의 constraints 충족
- [x] Do NOT 항목 위반 없음

## Orchestrator 검증 결과

### 통과

- **원인 11건 전건 추적** — §9 추적표에 A-1~A-4·B-1~B-7 모두 매핑, 누락 0. 역방향(원인에 직접 대응하지 않는 FR 4건)도 근거 명시
- **가설 분리 준수** — B-3·B-4·B-5·Caveat 7을 §10 선행 조사로 분리하고, 해당 FR의 우선순위를 조사 결과에 종속시킴 (brief Constraints 핵심 요구)
- **A-3 반증 유지** — 분석서의 반증 결론을 뒤집지 않고, FR-03을 "증상 해소가 아닌 회귀 방지·코드 명확화" 목적으로 P2 배치
- **수용 기준의 검증 가능성** — 전 FR에 AC 부여, 대부분 관측 가능한 수치·상태로 기술
- **스택 교체 요구 없음** — CKEditor4/STOMP/Spring 전제 유지 (brief Constraints)
- **구현 지시가 아닌 성질로 기술** — FR-13을 "서버 권위 수용·거부"라는 성질로만 규정해 신규 구현/기존 OT 이관 양쪽으로 충족 가능하게 열어둠

### 신규 사실 주장 재검증 (분석서에 없던 것 — Orchestrator 직접 확인)

| 주장 | 위치 | 확인 결과 |
|---|---|---|
| 콘텐츠 diff가 사용자 selection 상태로 Redis 영속화 | §2.3, `EditorController.java:179` | **확인** — `sessionRegistryService.updateUserState(sessionId, documentId, senderClientId, cursorPositionMap, selectionInfo)`. diff가 실린 `SelectionInfo`가 그대로 사용자 상태로 저장됨 |
| `OtService` 실존 (revision·transform 자산) | §2.2, Caveat 5 | **확인** — `Broker-Hub/src/main/java/com/arms/api/wiki/service/OtService.java` 존재 |
| 인용 DTO 실존 | 부록 A | **확인** — `dto/`에 `CursorMessage`·`UserInfo`·`SelectionInfo`·`DocumentState` 모두 존재 |

### 미결로 남긴 사항 (은폐 없이 명시)

worker가 스스로 미결로 표기한 3건은 **설계 판단이 아니라 이해관계자 결정이 필요한 사항**이므로 SRS 단계에서 확정하지 않는 것이 타당하다고 판단해 그대로 수락:

1. FR-05 (a)블록 내부 병합 / (b)우선순위+고지 중 택일 — 단계 3 완료 후 실사용 근거로 결정 권고
2. FR-04 AC-04-4 블록 식별자를 저장 본문에 남길지 — 위키 검색·버전비교 담당자 합의 필요
3. `OtService` 재활용 여부 — 단계 3 설계 시 비교 판단

### 후속 조치 제안 (이 작업 범위 밖)

§10 단계 0 선행 조사 5건은 **브라우저·부하 실측**이 필요해 정적 분석으로 해소 불가. 별도 task 분리 권장. 특히 **§10-5(다중 인스턴스 여부)**는 단계 3 착수 전 필수이며, 다중 인스턴스로 판명되면 SRS의 단계 3 이후 계획 전체가 재검토 대상이 된다.
