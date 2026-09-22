REQ-BACKEND-FUNC-01

목표: Backend-Core 의 REST 엔드포인트 전수를 컨트롤러별로 플랫하게 나열한 목록을 만든다.
완료 조건 :
① 자체 선언 엔드포인트가 표에 빠짐없이 있다.
② 상속 엔드포인트가 1회 기재되고 상속 컨트롤러가 열거돼 있다.
③ 각 행에 controller class name · rest end point · package name 이 채워져 있다.
성격: 분석·요약
target_repo: /Users/leemingyu/dev/Java-Service-Tree-Framework/Java-Service-Tree-Framework-Backend-Core
write_scope: tasks-only
워커: 생산=claude-main(서브에이전트 backend-expert), 리뷰=codex-critic
산출물: CSV 1본으로 artifacts/ 에
제약: 대상 저장소·엑셀 쓰기 금지, 코드 수정·실행 금지, 구조 비평·결함 지적·개선 권고 금지,
      설명 문단 늘리기 금지(표로 표현 가능하면 표로)
