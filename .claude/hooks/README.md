Java-Service-Tree-Framework-Frontend-Web/docs/file의 모든 파일(프로젝트 산출물)을
최대한 자세히 읽고 분석한다. (이미 읽은 파일은 skip)



--> 여기에 요구사항 기록


대상 모듈의 기존 코드를 전부 분석해 기존 관례를 따르는 설계를 우선한다. (이미 읽은 코드는 skip)
이 요구로 작업을 만들어 진행한다.
승인·결정 사항은 묻지 말고 먼저 진행한 뒤, 임의로 결정한 내용은 로그에 남긴다.
모듈의 /docs/ai/ 하네스를 참고한다.
main worker는 claude-main 이 진행한다.
main worker의 서브 에이전트는 frontend-expert 가 진행한다.
review role worker 는 claude-reviewer 가 진행한다.
review role worker의 서브 에이전트는 plan-challenger, review-expert가 병렬 진행한다.



---

위 내용처럼. 요구사항 앞뒤로 컨텍스트를 붙이기가 어렵다 ( claude 의 기능으로는 )
따라서 훅을 제거하고 이 내용으로 갈음한다.