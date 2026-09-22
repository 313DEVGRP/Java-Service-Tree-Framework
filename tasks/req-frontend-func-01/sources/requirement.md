# 요구사항 원문 — REQ-FRONTEND-FUNC-01

<!-- 엑셀 시트 변경 감지 기준선. 손으로 고치지 말 것. -->
<!-- 출처: 요구사항정의서_엑셀양식_v3_1_3.xlsx / 시트 요구사항정의서 / 3행 -->

## 요구사항 ID
REQ-FRONTEND-FUNC-01
## 대분류
FRONTEND
## 중분류
FUNC
## 소분류
None
## 요구사항명
FrontEnd API 분석
## 상세 내용
[개요]
FrontEnd 의 엔드포인트 Rest API 목록을 찾아낸다.

[상세 기능 요구사항]
각 파일의 endpoint 를 찾아낸다.
함수로 조합해서 파싱하는 api들도 완성해서 나타내준다.
js에 해당하는 메뉴들을 찾아야한다.
ex) menuname,jsfilename,apiuril,etc…

[입력 / 출력]
- 출력 : CSV

[제약 조건 / 비기능 요구사항]
- 읽기 전용. 코드 수정·실행 금지.
- 레퍼런스 문서다. 구조 비평·결함 지적·개선 권고는 이 요구사항의 산출물이 아니다.
- 설명 문단을 늘리지 않는다. 표로 표현할 수 있으면 표로 한다.

[검증 기준]
- / 로 끝나는 api는 존재 하면 안된다.

[작업 대상]
Java-Service-Tree-Framework-Frontend-Web/arms/js/,
Java-Service-Tree-Framework-Frontend-Web/backoffice/js/

[Worker Settings]
- MainWorker : claude-main
- SubWorker : codex-critic
- MainWorker-SubAgent : frontend-expert
## 요청자
개발팀 이민규
## 수용 여부
수용
## 우선순위
High
## 담당자
개발팀 이민규
## 진행 현황
분석중
## 비고
None
