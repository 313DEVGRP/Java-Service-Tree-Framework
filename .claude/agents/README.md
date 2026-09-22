# `.claude/agents/` — 두 계층의 서브에이전트

이 폴더에는 **목적이 다른 두 계층**의 에이전트 정의가 공존한다. 등록·수정 시 계층을 반드시 구분할 것.

## 1. 오케스트레이션 Worker Pool

파일 기반 멀티에이전트 시스템의 정식 워커. **능력 슬롯에 배정**되며 슬롯 정의는 불변이다.
배정 정본은 `_shared/capability-profile.md`(가변층), 슬롯 정의는 `_shared/routing.md`(안정층).

| 파일 | name | 슬롯 |
|------|------|------|
| `claude-main.md` | `claude-main` | strategist |

> codex-main · codex-critic · gemini 는 `.claude/agents/` 파일이 아니라 MCP/CLI 로 호출된다
> (호출 스펙 정본: `_shared/backends.json`). Worker Pool 전체 목록은 `CLAUDE.md` Architecture 참조.

**이 계층에 워커를 추가하려면** `_shared/capability-profile.md` §갱신 절차를 따른다 —
새 능력 슬롯 판정 + 정본 5개(capability-profile · routing · CLAUDE.md · README · backends.json) 동기화.
도메인 전문성은 슬롯이 아니므로 이 계층에 넣지 않는다.

## 2. 도메인 서브에이전트 (Worker Pool과 별개 계층)

이 저장소(Java Service Tree Framework)를 **실제 개발할 때** 쓰는 도메인 특화 에이전트.
일반 Claude Code 서브에이전트로 동작한다 — 직접 파일을 쓰고, 필요 시 가정을 명시하거나 질문한다.
오케스트레이션 워커 규약(무통신·file-as-memory·헤드리스)을 따르지 않으며, `workers_approved`
승인 게이트 대상도 아니다. `backends.json` 에도 등록하지 않는다.

| 파일 | name | 도메인 |
|------|------|--------|
| `frontend-expert.md` | `frontend-expert` | vanilla JS · jQuery · Bootstrap 기반 서버렌더링 프론트엔드 |
| `backend-expert.md` | `backend-expert` | Backend-Core(A-RMS API 서버: Java 11 · Spring Boot 2.6 · TreeFramework nested-set · 제품별 동적 테이블 라우팅 · Feign(Engine-Fire) · Kafka · POI) — 상세 규약은 `arms-backend-core` 스킬 |
| `database-expert.md` | `database-expert` | A-RMS(MySQL 8) 스키마 — Flyway 마이그레이션 · nested-set 루트 seed · `_LOG` 짝 테이블/트리거 · 제품별 동적 테이블 · 엔티티↔DDL 정합성 |
| `middleproxy-expert.md` | `middleproxy-expert` | Middle-Proxy(A-RMS API 게이트웨이: Spring Cloud Gateway/WebFlux · Keycloak OIDC · Redis 세션·도메인 저장 · Kafka REQADD 프로듀서 · Feign) |
| `broker-expert.md` | `broker-expert` | Broker-Hub(A-RMS 실시간 협업 브로커: Boot 3.5/Java 21 · STOMP/SockJS · OT 동시편집 엔진 · Redis 문서·참가자 상태 · 위키 편집락 방송(Middle-Proxy 위임)) — 상세 규약은 `broker-expert` 스킬 |
| `engine-expert.md` | `engine-expert` | Engine-Fire(A-RMS 수집·집계 엔진: Java 21 · Spring Boot 3.5.6 · OpenSearch esframework · ALM 이슈 수집 · 요구사항 기준 집계 · 인덱스 운영) — 상세 규약은 `engine-expert` 스킬 |
| `config-expert.md` | `config-expert` | Global-Config(A-RMS 중앙 설정·스케줄 허브: Spring Cloud Config Server/Gitea 백엔드 · 설정 변경 웹훅 전파 · 동적 크론 스케줄러 · 언어팩 · system-info) — 상세 규약은 `config-expert` 스킬 |
| `ai-expert.md` | `ai-expert` | AI(A-RMS 생성·검색 모듈: Java 21 · Spring Boot 3.5.6 · Spring AI M8 · WebFlux · RAG/OpenSearch VectorStore · 역할별 LLM 분리 · 도구 호출·멀티에이전트 · 문서 벡터화 · 프롬프트 외부화) — 상세 규약은 `ai-expert` 스킬 |

**이 계층에 에이전트를 추가하려면** 이 표에 한 줄 추가하고 `.claude/agents/<name>.md` 를 둔다.
정본 5개(Worker Pool 문서)는 건드리지 않는다.

