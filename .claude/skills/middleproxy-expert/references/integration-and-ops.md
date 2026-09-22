# 연동 · 빌드 · 배포 · 운영

---

## 1. Feign 클라이언트

`@EnableFeignClients({"com.arms.api.util.communicate"})` (`OpenFeignConfig`).
`FeignResponseDecoderConfig` 는 **Decoder 만** 등록한다 — Encoder 는 없다.

### 1.1 `백엔드코어통신기` (`backend-core`, `${arms.backend.url}`)

| 메서드 | 경로 | 용도 |
|--------|------|------|
| `각_제품서비스_별_요구사항이슈_조회_및_ES저장()` | `GET /arms/scheduler/pdservice/reqstatus/loadToES` | 스케줄 위임 |
| `각_제품서비스_별_요구사항_증분이슈_조회_및_ES저장()` | `GET .../increment/loadToES` | |
| `각_제품서비스_별_요구사항_Status_업데이트_From_ES()` | `GET .../updateFromES` | |
| `각_제품서비스_별_생성실패한_ALM_요구사항_이슈_재생성()` | `GET .../recreateFailedReqIssue` | |
| `sendMessage(message)` | `POST /arms/alarm/send-message/server` | 전역 알림 |
| `getReqAddByParentAndTitle(table, parentId, titleName)` | `GET /arms/reqAdd/{table}/getReqAddByParentAndTitle.do` | 분류(브랜치) 탐색 |
| `getReqAddByReqDefId(table, reqDefId)` | `GET /arms/reqAdd/{table}/getReqAddByReqDefId.do` | 리프 탐색 |
| `pruneEmptyFoldersFromUpload(table, folderIds)` | `POST /arms/reqAdd/{table}/pruneEmptyFoldersFromUpload.do` | 빈 분류 정리 |
| `ganttExcelUploadRefresh(requestId)` | `POST /arms/alarm/gantt-excel-upload-refresh` | 화면 갱신 |
| `excelUploadComplete(requestId)` | `POST /arms/alarm/excel-upload-complete` | 전 구간 완료 |
| `reqDefRowStatus(requestId, classLevelKey, state)` | `POST /arms/alarm/req-def-row-status` | 행 상태 |
| `wbsRowStatus(requestId, rowKey, state)` | `POST /arms/alarm/wbs-row-status` | 행 상태 |

### 1.2 `엔진통신기` (`engine-fire`, `${arms.engine.url}`)

`지라이슈_인덱스백업()` · `서버정보백업_스케줄러()` · `커넥션_상태_유지()`.

### 1.3 `내부통신기` (`loopback`, `http://127.0.0.1:13131` 하드코딩)

`/auth-sche/schedule/**` 경로를 자기 자신을 통해 호출한다 →
게이트웨이가 Global-Config(`global-config:33133`)로 라우팅한다.
포트가 바뀌면 이 상수도 바꿔야 한다.

### 1.4 규칙

- **`@RequestBody` 를 쓰지 않는다.** Encoder 가 없어 런타임에 깨진다.
  리스트도 `@RequestParam("folderIds") List<Long>` 처럼 쿼리 파라미터로 보낸다.
- 응답 래퍼는 `CommonResponse.ApiResult<T>` 로 그대로 받는다(`@JsonCreator` 가 있어 역직렬화됨).
- 기본 timeout 은 connect/read 각 180초(설정 주입 `feign.client.config.default.*`).
- Feign 호출은 블로킹이다. 리액티브 체인 안에서 부르면 `boundedElastic` 으로 감싸거나
  `@Async` 컨텍스트 안에서 부른다(엑셀 업로드 계열은 후자).
- 예외를 그대로 터뜨리지 않고 `try/catch` 로 감싸 로그만 남기는 것이 이 저장소 관례다
  (알림 실패가 본 작업을 막지 않도록).

---

## 2. Slack 알림

```java
SlackProperty  // @ConfigurationProperties("slack") : serviceName, token, profile, url
               // enum Channel { middleproxy, schedule }
SlackNotificationService.sendMessageToChannel(Channel, Exception|String)
```

- **`stg` 프로파일에서만 실제 전송**된다(`environment.getActiveProfiles().contains("stg")`).
- 예외 전송 시 스택트레이스를 `com.arms` 프레임만 남겨 압축한다.
- 전송 실패는 로그만 남기고 삼킨다.
- 자동 훅: `ErrorControllerAdvice.handleAllException` · `SessionParamAdvice` → `middleproxy` 채널,
  `@LogAndSlackNotify` → `schedule` 채널.

---

## 3. Swagger (Springfox 3.0.0)

```java
@Bean public static BeanPostProcessor springfoxHandlerProviderBeanPostProcessor()
```

`WebFluxRequestHandlerProvider` 의 `handlerMappings` 리스트에서
`RequestMappingHandlerMapping` 이 아닌 것(Actuator 매핑 등)을 리플렉션으로 제거한다.
**이것이 없으면 Spring Boot 2.6 + Springfox 3.0 조합에서 기동 중 `ClassCastException` 이 난다. 지우지 말 것.**

- Docket: `DocumentationType.SWAGGER_2`, `basePackage("com.arms")`, 전체 경로,
  `genericModelSubstitutes(Mono.class, Flux.class)`.
- 경로: `/middle-proxy-api` (UI `/middle-proxy-api/swagger-ui/`), `permitAll`.

---

## 4. 추적 · 모니터링

| 도구 | 설정 |
|------|------|
| Sleuth + Zipkin | `spring-cloud-starter-sleuth`, `spring-cloud-sleuth-zipkin`. live 에서는 `zipkin.enabled: false` (dev logback 이 zipkin 연결 WARN 을 ERROR 로 숨김) |
| Elastic APM | `elastic-apm-agent-1.47.1.jar` 동봉. `docker-entrypoint.sh` 에 `DEV/LIVE_MONITOR_ELK_OPTS` 가 정의돼 있으나 **기본 실행 커맨드에는 미포함** — 필요 시 `JAVA_OPTS` 로 주입 |
| Actuator | `refresh, env, health, beans, httptrace` 노출, `permitAll` |

---

## 5. 로깅 (logback)

- 프로파일별 `src/main/resources/logback/logback-{dev,stg,live}.xml` + 공용 `console-appender.xml`.
- 커스텀 컬러 컨버터 `highlightCustom` → `com.arms.api.util.HighlightingCompositeConverterCustom`
  (ERROR=굵은빨강, WARN=빨강, INFO=노랑).
- `ASYNC_CONSOLE` 어펜더(queue 512, neverBlock)가 준비돼 있다.

> ⚠️ `logback-dev.xml` 의 FILE 어펜더 경로가 **`/Users/leemingyu/dev/logs/arms-mp.log` 로 하드코딩**되어 있다
> (파일 안 주석도 "각자 pc 의 로컬 경로로 수정해서 사용하세요"라고 적혀 있다).
> Windows 에서 dev 프로파일로 띄우면 이 경로 때문에 문제가 될 수 있다. 커밋에 포함하지 않도록 주의.

---

## 6. 빌드

```bash
./gradlew compileJava      # 가장 빠른 검증
./gradlew printVersion     # 산정된 버전 출력
./gradlew bootJar
./gradlew publish          # Nexus(ple-releases) 배포 (+ spinnaker.properties 생성)
./gradlew docker           # 이미지 빌드 (palantir, noCache)
```

| 항목 | 값 |
|------|----|
| Gradle | 7.6.4 (wrapper) |
| Java | source/target **11** |
| group / artifact | `313devgrp` / `Java-Service-Tree-Framework-Middle-Proxy` |
| 버전 | `${majorVersion}.${minorVersion}.${patchVersion}` — major=26, minor=9, **patch 는 Nexus `metadata.xml` 의 latest patch + 1** |
| 테스트 | JUnit5 (`useJUnitPlatform()`, junit4 제외) |
| 정적분석 | `org.sonarqube` → `http://www.313.co.kr/sonar` |
| 라이선스 | `dependency-license-report` → `build/licenses` (`allowed-licenses.json` 을 참조하지만 **파일이 저장소에 없다**) |

버전 산정 규칙:
major 상승 → minor=0, patch=0 / minor 상승 → patch=0 / 그 외 → patch+1.
Linux 에서만 `wget` 으로 `metadata.xml` 을 받고, Windows·Mac 은 저장소에 커밋된 `metadata.xml` 을 쓴다.

> ⚠️ `build.gradle` 의 `sonarqube` 블록에 **Sonar 계정과 비밀번호가 평문으로 들어 있다.**
> 문서·로그·외부 채널에 복제하지 않는다.

---

## 7. Docker · 배포

```
Base   313.co.kr:5550/313devgrp/openjdk:11-jre
Image  313.co.kr:5550/313devgrp/java-service-tree-framework-middle-proxy:${version}
포함   javaServiceTreeFramework.jar · docker-entrypoint.sh · elastic-apm-agent.jar
인증서 313_co_kr.crt · a-rms_net.crt 를 cacerts 에 keytool import (SaaS TLS)
ENTRYPOINT sh /docker-entrypoint.sh   CMD start   포트 13131
```

`docker-entrypoint.sh`:

```sh
GC_OPTS  = -XX:+UseNUMA -XX:+UseG1GC
MEM_OPTS = -Xms1024m -Xmx1024m
NET_OPTS = DNS TTL 0, IPv4 우선, -XX:-UseContainerSupport
SPRING_PROFILES_ACTIVE 기본값 live
-Duser.timezone=Asia/Seoul
```

배포 흐름: `bootJar` → `publish`(Nexus + `spinnaker.properties`) → `docker` → Spinnaker 파이프라인.
CI 워크플로는 `.github/workflows/release-drafter.yml` 하나뿐이다(빌드 CI 아님).

> `Dockerfile` 이 받는 인증서 tar 이름(`cert_313-2025`, `cert_arms-2025`)과 alias 에 **연도가 박혀 있다.**
> 인증서 갱신 시 Dockerfile 을 함께 고쳐야 한다.

---

## 8. 로컬 개발

1. IntelliJ 에서 JDK 설정 — **README 는 17 이라고 하지만 `build.gradle` 은 11 이다.**
   JDK 17 로 실행해도 컴파일 타깃은 11 이므로 동작하지만, 문법은 11 까지만 쓴다.
2. Active Profile `dev` → Config 서버 `www.313.co.kr:33133` 에서 설정을 받아온다.
   **Config 서버에 닿지 못하면 포트·Redis·Keycloak 설정이 전부 비어 기동에 실패한다**
   (`import: optional:` 이라 import 자체는 실패하지 않지만 `@Value` 주입에서 터진다).
3. Redis: 저장소 동봉 `Redis-x64-3.2.100/redis-server.exe`.
4. Swagger 로 확인: `http://127.0.0.1:13131/middle-proxy-api/swagger-ui/`
5. JRebel 설정(`rebel.xml`)이 커밋되어 있다.
