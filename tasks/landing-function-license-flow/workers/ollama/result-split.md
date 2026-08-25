# Result — ollama (분할 호출 재시도) / landing-function-license-flow

<!-- 원문 보존: 각 응답 전문은 workers/ollama/split/a1~a8.txt -->
<!-- 수신: 2026-08-25 09:58 / model=gemma3 (배정 변경 없음) / 8회 순차 호출 -->
<!-- 프롬프트: split/q1~q8.txt (190~604자). 발췌: sources/excerpt-steps.txt(219자), excerpt-tokens.txt(282자) -->

## Orchestrator 판정: **형식 준수는 개선, 판정 내용은 신뢰 불가 — 검증 근거로 미사용**

## 1. 형식 준수 (분할 호출의 효과)

| | 통합 호출 (12,688자) | 분할 호출 (190~604자) |
|---|---|---|
| 형식대로 답한 문항 | **0 / 8** | **6 / 8** |
| 실패 문항 | 전부 | Q7(숫자), Q8(한 문장) |

분할은 **형식 붕괴 문제를 실제로 개선했다.** 지시가 데이터에 매몰되던 원인이 제거되자
Q1~Q6은 요구한 YES/NO 한 줄로 답했다. 원인 진단(모델 용량이 아니라 brief 구조)이 실증됐다.

Q7·Q8 실패 양상은 통합 호출과 동일 — 질문을 다른 질문으로 바꿔 읽고 장문 산문을 반환했다.
- Q7("토큰 몇 개인가" → 숫자 하나): 질문을 "색상 팔레트의 목적은?"으로 재해석하고 팔레트 해설 생성
- Q8("가장 큰 문제 하나" → 한 문장 20단어): "A-RMS Implementation Guide" 제목의 구현 가이드 생성

## 2. 판정 내용 정확도 (Orchestrator 소스 대조)

형식을 지킨 6건도 **내용은 틀렸다.** NO 3건 전부 오답이며, 근거 제시 요구("NO면 빠진 것만")도
무시하고 `NO` 한 단어만 반환해 반증조차 불가능했다.

| 문항 | ollama | 실측 | 판정 |
|---|---|---|---|
| Q1 7단계 전부 포함? | **NO** | 요구 7단계 ↔ 설계 7단계 1:1 정확 대응 | **오답** |
| Q2 순서 1→7? | YES | 순서 정확 | 정답 |
| Q3 입력 표현? | YES | S3 패널 4필드 존재 | 정답 |
| Q4 출력 3종? | **NO** | result.md:158·161·163에 ①②③ 전부 존재 | **오답** |
| Q5 PRO·ENT 골격? | YES | S6·S7 존재 | 정답 |
| Q6 색상 허용목록 내? | **NO** | 12개 토큰 전부 허용목록 내 (스크립트 대조) | **오답** |
| Q7 토큰 개수 | (형식 실패) | 12개 | 판정 불가 |
| Q8 최대 문제 | (형식 실패) | — | 판정 불가 |

**정답률: 형식 준수 6건 중 3건(50%). 전체 8건 중 3건(37.5%).**
YES 3건은 전부 정답, NO 3건은 전부 오답 — 즉 이 모델은 **부정 판정을 신뢰할 수 없다.**
동전 던지기와 구별되지 않으므로 독립 검증자로서의 가치가 없다.

## 3. 결론

- 분할 호출은 **형식 문제의 해법으로는 유효**하다 (0/8 → 6/8). 이 지식은 재사용 가치가 있다.
- 그러나 **판정 능력 자체가 부족**해 검증 슬롯의 목적(제3자 독립 검증)을 달성하지 못한다.
  형식이 맞아도 내용이 틀리면 오히려 위험하다 — 근거 없는 NO를 그대로 수락했다면
  claude-main 설계에 없는 결함 3건을 만들어냈을 것이다.
- Acceptance Criteria의 제3자 검증 항목은 **여전히 미충족**으로 남긴다.

## 4. 원문

각 응답 전문은 `workers/ollama/split/a1~a8.txt`에 무편집 보존.

```text
A1: NO
A2: YES
A3: YES
A4: NO
A5: YES
A6: NO
A7: The question is: "아래 목록에 정의된 토큰은 몇 개인가?" (What is the purpose of the
    color palette?) / Based on the provided color palette, here's a breakdown of its likely
    purpose and overall aesthetic: ... (팔레트 해설 장문 — 전문은 a7.txt)
A8: Okay, let's break down this information and present it in a concise and easily
    digestible format. ... **Subject: A-RMS Implementation Guide (Quick Start)**
    ... (구현 가이드 장문 — 전문은 a8.txt)
```

## Verification Checklist (Orchestrator 실행)

- [~] output이 brief의 output_format과 일치 — **부분 충족** 6/8 (통합 호출 0/8 대비 개선)
- [x] 파일 경로 실존 — 해당 없음
- [ ] 판정 내용 신뢰성 — **실패**. NO 3건 전부 오답, 근거 미제시
- [x] Do NOT 위반 — 설계안 재작성·brief 헤더 복제 없음 (Q7·Q8은 형식 외 산문)

**최종**: 이 result는 설계안 수락/반려 근거로 사용하지 않는다.
