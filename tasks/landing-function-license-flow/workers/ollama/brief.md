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

(Orchestrator가 claude-main result 전문을 여기 붙여 넣는다)
