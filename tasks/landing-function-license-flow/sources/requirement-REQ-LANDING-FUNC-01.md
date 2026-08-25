# REQ-LANDING-FUNC-01 — 원문 발췌

출처: `요구사항정의서_엑셀양식_v3_1_3.xlsx` 시트 `요구사항정의서` 2행 (양식 v3.1.3)
발췌일: 2026-08-24 / 원본 셀 내용 그대로 (편집 금지)

| 컬럼 | 값 |
|---|---|
| 요구사항 ID | REQ-LANDING-FUNC-01 |
| 대분류 · 중분류 · 소분류 | LANDING · FUNC · (빈칸) |
| 요구사항명 | A-RMS 기능 페이지 개선 |
| 요청자 | 개발팀 이동민 |
| 수용 여부 | 수용 |
| 우선순위 | High |
| 담당자 | DEV: 이민규 / SE: 양형석 |
| 진행 현황 | 기획중 |
| 비고 | 본 요구사항은 지속적인 갱신이 전제되어 있음. |

## 상세 내용 (원문)

```text
[개요]
현재 A-RMS 기능 페이지는 단순 기능의 설명과 이미지로만 표시되어 사용자에게 내용을 전달하기가 어렵다.
따라서, 각 라이선스 타입에 따라 ( POC, PRO, ENT ) 실제 액션의 흐름을 표시하여,
A-RMS의 기능을 전달하고자 한다.

[상세 기능 요구사항]
1) POC 타입에 대해서, 화면을 구성하되, 맨 처음. 고객의 JIRA 와 A-RMS 를 연결한다.
2) 연결 후 Default 프로젝트의 Base Version 으로 고객사의 JIRA 프로젝트를 설정한다.
3) 설정 후 . 자동으로 Mapping 된 이슈의 타입 별. 우선순위와 유형을 확인한다.

4) 2) 연결 후. PM이나 팀장은 이슈 리스트에서, 요구사항 이슈에 준하는 ( ex: EPIC or 요구사항 label 같은 ) 이슈를 선정한다.
5) 선정된 이슈를 자동으로 A-RMS 가 수집한다.
6) 수집된 데이터를 기반으로 Time, Scope, Resource, Cost 관점으로 분석된 결과를 확인한다.
7) 개인의 성과지표를 확인하고, 주간 보고 리포트를 생성하여 확인 할 수 있다.

[입력 / 출력]
- 입력: 고객사의 JIRA 접속 정보 ( Admin 권한 필요 )
- 출력: Time, Scope, Resource, Cost 관점의 리포트, 개인 KPI 지표, 주간 보고 리포트

[제약 조건 / 비기능 요구사항]
- N/A

[검증 기준]
- common.css 와 기존에 구현된 html에서 사용된 css를 전부 확인하여, 통일성있는 디자인과 색감을 사용할 것.

[작업 대상]
Java-Service-Tree-Framework-Frontend-Web 모듈의 arms\html\landing_function에 작업해 줘
기존 작업은 무시하고 작업 해

[Worker Settings]
- MainWoker : claude-main
- SubWorker : ollama
- MainWoker-SubAgent : frontend-expert
```
