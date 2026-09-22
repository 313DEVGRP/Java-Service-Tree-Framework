REQ-FRONTEND-FUNC-01

목표: Frontend-Web 의 js 파일들이 호출하는 REST API 엔드포인트를 전수 추출해
      메뉴·파일 단위로 플랫하게 나열한 목록을 만든다. 문자열·함수로 조합되는 URL 도 완성형으로 복원한다.
완료 조건 :
① `/` 로 끝나는 api 가 한 건도 없다 (미해결 조합 URL 이 남아 있지 않다).
② 각 행에 menuname · jsfilename · apiurl 이 채워져 있다.
③ arms/js/ · backoffice/js/ 두 경로의 js 가 모두 대상에 들어 있다.
성격: 분석·요약
target_repo: /Users/leemingyu/dev/Java-Service-Tree-Framework/Java-Service-Tree-Framework-Frontend-Web
write_scope: tasks-only
워커: 생산=claude-main(서브에이전트 frontend-expert), 리뷰=codex-critic
산출물: CSV 1본으로 artifacts/ 에
제약: 대상 저장소·엑셀 쓰기 금지, 코드 수정·실행 금지, 구조 비평·결함 지적·개선 권고 금지,
      설명 문단 늘리기 금지(표로 표현 가능하면 표로)
