# wiki 동기화 SRS — §10 선행 조사

## 메타

```yaml
status: in_progress
created: 2026-08-07
updated: 2026-08-07
priority: high        # SRS 단계 3 착수의 선행 게이트
parent: tasks/wiki-concurrent-edit-sync
```

## 부모 작업 연결 (orchestrator-rules §3 연결고리)

이 작업은 `tasks/wiki-concurrent-edit-sync`의 **후속 단계**다. SRS(2단계 산출물) §10이 요구한 선행 조사 5건을 수행한다.

**필독 입력** (경로만 — inline 금지):
```
tasks/wiki-concurrent-edit-sync/artifacts/SRS-wiki-sync-improvement.md   # §10 조사 항목 정의 (정본)
tasks/wiki-concurrent-edit-sync/workers/claude-main/result.md            # 원인 분석 정본 (가설의 출처)
tasks/wiki-concurrent-edit-sync/sources/analysis-scope.md                # 대상 코드 위치
tasks/wiki-concurrent-edit-sync/log.md                                   # 1·2단계 이력
```

## Goal

SRS §10-1 ~ §10-5 각 항목에 **"확인됨 / 반증됨 / 영향 없음 / 판정 불가(사유)"** 판정을 부여하고, 그 결과로 SRS의 FR 우선순위 조정안을 산출한다.

완료 조건 =
① 5개 항목 전건에 판정과 근거가 기록됨
② 정적 분석으로 판정 불가한 항목은 **필요한 수단(런타임 실측·담당자 확인)을 명시**하고 미판정으로 남김 — 추측으로 채우지 않음
③ 판정 결과에 따른 SRS FR 우선순위 조정안 제시

## Constraints

- **추측으로 판정하지 않는다.** 근거 없이 "확인됨"으로 적지 않는다
- 코드·설정 수정 금지 (조사 전용, read-only)
- 런타임 실측이 필요한 항목을 정적 추론으로 대체하지 않는다

## Acceptance Criteria

- [ ] §10-1 (STOMP 순서 역전) 판정
- [ ] §10-2 (위젯이 정화 대상 요소 생성) 판정
- [ ] §10-3 (커서 span의 저장본 혼입) 판정
- [ ] §10-4 (재연결 시 구독 복구 중단) 판정
- [ ] §10-5 (다중 인스턴스 배포 여부) 판정
- [ ] 판정 불가 항목에 필요한 수단 명시
- [ ] SRS FR 우선순위 조정안 제시

## Worker Plan

```yaml
workers_approved: []   # 정찰 결과에 따라 결정. Orchestrator 내부 추론 우선 (routing 복합작업 우선순위 2)

planned_workers: []
```

## Context Snapshot

사전 정찰(Orchestrator 내부 추론)에서 확인: 배포 설정이 config server(`global-config:33133`)로 외부화되어 있고 이 repo에 k8s 매니페스트·replica 설정이 없다 → **§10-5는 코드로 판정 불가**, 인프라 담당자 확인 필요.

## Notes

- 5개 항목의 판정 가능성이 균일하지 않다. 런타임 실측이 필요한 항목과 코드로 결론 가능한 항목을 먼저 분류하고, 후자부터 처리한다
- §10-5가 최우선 — 다중 인스턴스면 SRS 단계 3 이후 계획 전체가 재검토 대상
