# 연동 · 설정 · 빌드 · 배포 · 운영

---

## 1. 모듈 경계 — 먼저 판단할 것

| 하는 일 | 어느 모듈 |
|---------|----------|
| 임베딩 · LLM 호출 · RAG · 프롬프트 조합 · 도구/에이전트 | **AI (이 저장소)** |
| ALM(Jira/Redmine) 수집 · OpenSearch 색인 · 집계 · 키워드 검색 제공 | Engine-Fire |
| 요구사항/제품/버전 CRUD · 트리 · MySQL | Backend-Core |
| 게이트웨이 라우트 · 인증 · 세션 · Kafka 발행 | Middle-Proxy |
| 설정·프롬프트 값 · 스케줄 · 언어팩 | Global-Config |

**ALM 집계나 인덱스 적재 로직을 이 저장소에 만들지 않는다.** `EngineClient` 로 받아 쓴다.
반대로 임베딩·LLM 을 Engine-Fire 에 만들지 않는다. 경계를 넘으면 같은 로직이 두 모듈로 갈라지고
조용히 어긋난다(`docs/ai/12_known_issues` 의 "모듈 경계" 항목과 같은 판단이다).

---

## 2. Feign

```java
@Configuration
@EnableFeignClients({"com.arms.api.util.msa_communicator"})   // ★ 이 패키지만 스캔한다
public class OpenFeignConfig {
    @Bean Request.Options requestOptions() {
        return new Request.Options(30, SECONDS, 60, MINUTES, true);   // connect 30s / read 60m
    }
    @Bean HttpMessageConverters httpMessageConverters() {              // ★ WebFlux 라 수동 등록 필수
        return new HttpMessageConverters(new MappingJackson2HttpMessageConverter());
    }
}
```

| 인터페이스 | URL 키 | 비고 |
|-----------|--------|------|
| `BackendCoreClient` | `${arms.backend.url}` | 요구사항·제품·버전·위키·담당자·리포트 원천. 경로에 `T_ARMS_REQADD_{pdServiceId}` 같은 **제품별 동적 테이블명**이 들어간다 |
| `EngineClient` | `${arms.engine.url}` | `/ai-search/keyword` · `/report/rolling3m` · `/report/rolling3m/assignee` · `/engine/kpi/dashboard/*` 5종 |
| `DwrClient` | `${arms.backend.url}` | `/arms/alarm/send-message` — 진행 상황 푸시 |
| `TtsClient` | `${spring.ai.tts.base-url,...}` | 현재 더미(`TtsClientDummyImpl`) |

주의:
- **read 타임아웃 60분**은 LLM·PPT 생성 때문이다. 줄이려면 어떤 호출이 그렇게 오래 걸리는지 먼저 확인한다.
- `HttpMessageConverters` 빈을 지우면 `@RequestBody` 를 쓰는 Feign 호출이 **런타임에** 깨진다(컴파일은 통과).
- 응답 VO 를 상대 모듈과 1:1로 유지한다. 필드가 빠지면 역직렬화가 조용히 비고 **지표가 0 으로 나온다** —
  에러가 안 나므로 발견이 늦다.
- Feign 인터페이스를 `com.arms.api.util.msa_communicator` 밖에 두면 빈이 안 생긴다.

---

## 3. 설정 — Config Server 가 거의 전부다

저장소 안의 yml 은 뼈대뿐이다.

```yaml
# application.yml
spring.application.name: javaServiceTreeFrameworkAI
springdoc.api-docs.path: /v3/api-docs
springdoc.swagger-ui: { path: /swagger-ui.html, use-root-path: true }

# application-dev.yml
spring.config.import: optional:configserver:http://www.313.co.kr:33133
management.endpoints.web.exposure.include: refresh, env, health, beans, httptrace
```

- 프로파일: `dev` · `stg` · `live`. `SPRING_PROFILES_ACTIVE` 기본값은 컨테이너에서 `live`.
- `optional:` 접두라 Config Server 가 없어도 **기동은 시도한다.** 하지만
  `prompt.*` · `spring.ai.vectorstore.opensearch.uris`·`index-name` 은 기본값이 없어
  **빈 생성 단계에서 실패한다.** 이건 의도된 fail-fast 다.
- 설정 변경 반영: Global-Config 웹훅 → 각 클라이언트 `POST /actuator/refresh`.
  `LlmModelConfig` 는 `@RefreshScope` 이라 `external-chat` 전환이 무중단으로 먹는다.
- **프롬프트 값을 바꿔야 하면 이 저장소가 아니라 Global-Config(Gitea) 를 고쳐야 한다.**
  그 저장소 작업은 `config-expert` 스킬 쪽이다.

키 전체 목록은 `references/llm-and-models.md` §7.1.

---

## 4. 빌드

```bash
./gradlew compileJava        # 가장 빠른 검증. Windows: gradlew.bat
./gradlew bootJar
./gradlew buildDockerImage   # prepareDockerContext → DockerBuildImage
./gradlew pushDockerImage    # 313.co.kr:5550 로 push
```

- Java toolchain **21**, Spring Boot 플러그인 **3.5.6**, dependency BOM 은
  `spring-cloud-dependencies:2025.0.1` + `spring-ai-bom:1.0.0-M8`.
- **버전이 구성 단계에서 계산된다.** `majorVersion=26` · `minorVersion=9` 고정,
  patch 는 Nexus `maven-metadata.xml` 의 latest + 1.
  - Linux 는 `wget` 으로 메타데이터를 내려받는다. **Windows/Mac 은 저장소 동봉 `metadata.xml` 을 쓴다.**
  - 그래서 오프라인 Windows 에서도 구성은 통과하지만, 계산된 버전은 실제 Nexus 와 다를 수 있다.
- `sonarqube` 블록과 `settings.xml` 에 **자격증명이 평문으로 들어 있다.**
  값을 복제·인용·로그 출력하지 않는다. 키 경로만 참조한다.
- `metadata.xml` · `spinnaker.properties` 는 빌드가 갱신하는 산출물이다. 손으로 고치지 않는다.

### 의존성 추가 시 확인할 것

- Spring AI 는 **BOM 이 버전을 정한다.** 개별 스타터에 버전을 적지 않는다.
- 새 모델 스타터를 넣으면 `ChatModel`/`EmbeddingModel` 빈이 늘어난다 →
  `@Primary` 충돌과 임베딩 오염을 먼저 검토한다(`references/llm-and-models.md` §1).
- PDFBox 는 `spring-ai-pdf-document-reader` 와 맞춘 **3.0.3** 이다. 올리면 리더가 깨질 수 있다.

---

## 5. Docker · 배포

```
FROM 313.co.kr:5550/313devgrp/openjdk:21-jdk
ENTRYPOINT sh /docker-entrypoint.sh   CMD start
이미지: 313.co.kr:5550/313devgrp/java-service-tree-framework-ai:26.9.x
```

`docker-entrypoint.sh` 기본값: `-XX:+UseNUMA -XX:+UseG1GC` · `-Xms1024m -Xmx1024m` ·
`-Duser.timezone=Asia/Seoul` · `SPRING_PROFILES_ACTIVE=live`.

> ⚠️ 스크립트의 Elastic APM 옵션 변수명이 `*_global-config` 로 되어 있다(다른 모듈에서 복사된 흔적).
> 현재 실제로 적용되지는 않지만(`JVM_OPTS` 에 안 들어감), APM 을 켤 때 `service_name` 부터 고쳐야 한다.

배포는 Nexus publish → Spinnaker(`spinnaker.properties`) 경로다.

---

## 6. 관찰

| 수단 | |
|------|---|
| Swagger | `/swagger-ui.html` (root path), 그룹 `arms` (`com.arms` 전체 스캔) |
| Actuator (dev) | `/actuator/{refresh,env,health,beans,httptrace}` |
| 예열 상태 | `GET /chat/status` |
| 외부 서비스 | `GET /status` |
| 트레이싱 | `micrometer-tracing-bridge-brave` + `zipkin-reporter-brave` (의존성만 있음) |
| Slack | `slack-api-client` (의존성만 있음 — 현재 소스에서 쓰는 곳 없음) |

### 로그에서 찾을 것

이 저장소의 로그는 `클래스명 :: 메서드명 | key=value` 관례를 따른다. 새 로그도 이 모양으로 쓴다.

| 증상 | 볼 로그 |
|------|--------|
| 첫 토큰이 느리다 | `[OllamaWarmupRunner :: warmup]` · `첫 토큰 도착 \| streamId=..., 소요=...ms` |
| 답변이 이상하다 | `FallbackChatModel :: 주 모델 실패` (Anthropic 이 답한 것) |
| 도구가 안 불린다 | `SupportRouter :: 라우팅 응답 \| screens=[]` · `알 수 없는 도구` |
| 지표가 0 이다 | `<X>MetricCollector :: ... 조회 실패` · `SupportToolsService :: collector 없음` |
| 파이프라인이 느리다 | `PromptContextServiceImpl :: build 완료 [느린 요청 감지 {}ms]` |
| AI 가 멈춘 것 같다 | `[KeywordHtml] hit` (LLM 우회 게이트가 걸린 것 — 정상 동작) |

---

## 7. 코드 관례

- 클래스 헤더 주석은 `@author` · `@since` · `@version` + 313 DEV GRP 저작권 블록.
  기존 파일 형식을 따른다.
- Lombok: `@Slf4j` · `@RequiredArgsConstructor` · `@Getter` · `@Builder`(VO) ·
  `@SuperBuilder` + `@EqualsAndHashCode(callSuper = true)`(`UserQueryDTO` 하위).
- 모델 네이밍: 요청은 `*DTO`, 응답·값 객체는 `*VO`. 섞지 않는다.
- 응답 봉투: 관리 API 는 `CommonResponse.success(...)` → `ApiResult<T>`(`{success, response, error}`).
  질의 파이프라인은 봉투 없이 `Flux<String>` / `Mono<String>` 을 그대로 흘린다. **둘을 섞지 않는다.**
- 에러 코드는 `ErrorCode` enum(한국어 메시지). 새 코드를 추가할 때 메시지도 한국어로.
- 주석과 로그는 한국어. 사용자 대상 문자열도 한국어.
