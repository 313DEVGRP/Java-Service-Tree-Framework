REQ-MAPPING-FUNC-01

목표: Frontend-Web 의 API 호출과 Backend-Core 의 엔드포인트를 게이트웨이 경로 규칙으로 대조해,
      **매핑되지 않는 것만** 메뉴별로 추린 목록을 만든다. 양방향(프론트→백엔드 미존재 / 백엔드→호출 없음) 모두.
완료 조건 :
① URL 을 게이트웨이 규칙으로 추론해 대조하고, 애매한 건은 note 에 사유를 남긴다.
② 매핑이 성립한 행은 싣지 않는다 (미매핑만).
③ menuname 에 추정 표현이 0건. js↔html 폴더 1:1 로 확정하고 출처를 menusource 에 남긴다.
④ 상속(TreeAbstractController·TreeMapAbstractController)으로 생긴 URL 이 provider 로 구분돼 있다.
성격: 분석·요약
target_repo: /Users/leemingyu/dev/Java-Service-Tree-Framework
write_scope: tasks-only
워커: 생산=claude-main(서브에이전트 frontend-expert), 리뷰=codex-critic
산출물: CSV 1본 + 엑셀 1본(한 시트, menuname 정렬)으로 artifacts/ 에
제약: 대상 저장소·엑셀 쓰기 금지, 코드 수정·실행 금지, 구조 비평·결함 지적·개선 권고 금지,
      설명 문단 늘리기 금지(표로 표현 가능하면 표로)
