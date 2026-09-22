# 빌드 · 설정 · 운영

---

## 1. 빌드 (`build.gradle`)

| 항목 | 값 |
|------|----|
| Spring Boot 플러그인 | `3.5.6` |
| dependency-management | `1.1.7` |
| Java toolchain | **21** |
| Gradle wrapper | 8.13 |
| Spring Cloud BOM | `2025.0.1` |
| group / artifact | `313devgrp` / `Java-Service-Tree-Framework-Broker-Hub` |
| Docker 이미지 | `313devgrp/java-service-tree-framework-broker-hub` |

> `README.md` 의 "Java 17" 은 **틀렸다.** toolchain 과 Dockerfile 모두 21 이고,
> 코드가 실제로 Java 17+ 문법을 쓴다(text block · switch expression).

### 주요 의존성

| 묶음 | 내용 |
|------|------|
| Web | `spring-boot-starter-web`(MVC) · `-websocket` · `-aop` · `-cache` · `-actuator` · `-validation` · `-mail` |
| Redis | `spring-boot-starter-data-redis`(Lettuce) + `redis.clients:jedis:6.0.0`(**선언만 · 미사용**) |
| Cloud | `spring-cloud-starter-config` · `spring-cloud-starter-openfeign` · `feign-hc5` |
| 추적 | `micrometer-tracing-bridge-brave` · `zipkin-reporter-brave` |
| 기타 | Slack SDK 1.25.1 · springdoc-openapi 2.1.0 · Guava · Gson · commons-* · Lombok |
| 잔재 | `com.googlecode.lanterna:lanterna:3.1.2` — 제거된 mat TUI 의 흔적 |

> `springdoc-openapi-starter-webmvc-ui` 가 있으므로 `/swagger-ui.html`(기본 경로)이 뜬다.
> 전용 설정 클래스는 없다.

### 버전 산정 — 네트워크에 의존한다 ⚠️

`ext` 블록이 Nexus 에서 `metadata.xml` 을 받아 patch 를 자동 산정한다.

```groovy
majorVersion = 26
minorVersion = 9
// patchVersion = auto generation

if (Os.isFamily(Os.FAMILY_WINDOWS))  println "*** Windows is not support build "
else if (Os.isFamily(Os.FAMILY_MAC)) println "*** Mac "
else exec { executable "wget"; args "-O", "${projectDir}/metadata.xml", "${metadataUrl}" }
```

- **Windows·Mac**: `wget` 스킵 → 저장소 동봉 `metadata.xml`(latest `0.0.1`) 사용 →
  `majorVersion(26) > 0` 이므로 `minor=0, patch=0` → **버전 `26.0.0`**.
- **Linux**: Nexus(`http://www.313.co.kr/nexus/...`) 접근 필요. 없으면 **빌드 실패**.

검증 목적이면 항상 `compileJava` 만 돌린다.

```bash
gradlew.bat compileJava          # Windows
./gradlew compileJava            # Bash
```

### 부가 태스크

| 태스크 | 하는 일 |
|--------|---------|
| `printVersion` | 산정된 버전 출력 |
| `generatePublishInfo` | `spinnaker.properties` 생성 (`publish` 가 의존) |
| `publish` | Nexus `ple-releases` 업로드. 자격증명은 `~/.m2/settings.xml` → 없으면 저장소 `settings.xml` |
| `prepareDockerContext` → `buildDockerImage` → `pushDockerImage` | `313.co.kr:5550/...:{version}` 이미지 |
| `generateLicenseReport` | `build/licenses/report.html` |
| `sonarqube` | `http://www.313.co.kr/sonar` |

> ⚠️ `build.gradle` 의 `sonarqube` 블록과 저장소 `settings.xml` 에 **평문 자격증명**이 있다.
> 값을 다른 파일·로그·문서에 복제하지 않는다. 정리 제안은 가능하나 요청 없이 건드리지 않는다.

### 눈에 띄는 잔재

- `plugins { id 'org.openjfx.javafxplugin' }` — JavaFX 를 쓰는 코드가 없다.
- `configurations { compile.exclude ... }` — Gradle 8 에 `compile` 구성이 없다. 사실상 무의미.
- `class ClearDependencies implements ComponentMetadataRule` — 정의만 하고 적용하지 않는다.

---

## 2. 프로파일 · 설정 주입

| 파일 | 내용 |
|------|------|
| `application.yml` | `spring.application.name: javaServiceTreeFrameworkBrokerHub` |
| `application-dev.yml` | Config `www.313.co.kr:33133` · Redis `www.313.co.kr:36379` · actuator · `mat.*` |
| `application-stg.yml` | Config `global-config:33133` · actuator · `mat.mode: receiver` |
| `application-live.yml` | 〃 |

```yaml
spring:
  config:
    import: optional:configserver:http://...:33133
```

`optional:` 이라 Config 서버가 없어도 부팅을 시도하지만, 아래 값이 비면 그 다음 단계에서 실패한다.

### Config 서버가 반드시 주입해야 하는 것

| 키 | 비고 |
|----|------|
| `server.port` | Global-Config 의 `arms.broker-hub.url` 기준 **31113 으로 추정**. 로컬 yml 에 없음 |
| `spring.redis.host` / `spring.redis.port` | **live·stg 에는 로컬 값이 없다.** 없으면 기동 실패 |
| `arms.middle-proxy.url` | Feign 대상. dev `127.0.0.1:13131` / stg·live `middle-proxy:13131` |
| `slack.service-name` · `slack.token` · `slack.profile` · `slack.url` | stg·live 에서만 의미 있음 |

Config 서버는 gitea 저장소 `root/ARMS` 에서 `javaServiceTreeFrameworkBrokerHub.yml` 을 읽는다
(Global-Config `spring.cloud.config.server.git.uri`). **이 워크스페이스에는 없다.**

### Redis 키 이름 함정

`RedisConfig` 는 Boot 3 에서 제거된 `spring.redis.*` 를 `@Value` 로 읽는다.
그래서 dev yml 이 `spring.data.redis`(Boot 3 표준, 자동 구성용)와
`spring.redis`(이 코드용)를 **둘 다** 적어 놓았다. 한쪽만 지우면 기동이 안 된다.
`spring.redis.ssl.enable`(yml) vs `spring.redis.ssl.enabled`(코드)는 이름이 어긋난 죽은 설정이다.

### actuator

세 프로파일 모두:
```yaml
management.endpoints.web.exposure.include: refresh, env, health, beans, httptrace
```
`httptrace` 는 Boot 3 에서 `httpexchanges` 로 이름이 바뀌었다 — **죽은 항목**이다.
`refresh` 가 열려 있으므로 Config 서버 갱신을 런타임에 반영할 수 있다
(`SlackProperty` 가 `@RefreshScope` 다).

### `mat.*` — 죽은 설정

`mat`(MultiAgent Tracker) 소스는 커밋 `ffff1b0` 에서 제거됐다.
yml 의 `mat.mode` · `mat.ticket-id` · `mat.root` · `mat.remote.*` 와 `lanterna` 의존성은 잔재다.
관련 이력: `7763c89`(Go → Spring 컨버팅) → `9b5804a`(STOMP 양방향 보고) → `ffff1b0`(제거).

---

## 3. 실행

### 로컬

IntelliJ `Run/Debug Configurations` → Active profiles = **`dev`**.
Redis 는 `www.313.co.kr:36379` 를 본다(로컬 Redis 를 쓰려면 dev yml 의 host/port 를 바꾼다 —
`spring.data.redis` 와 `spring.redis` **양쪽 모두**).

확인:
```bash
curl http://127.0.0.1:31113/api/health/redis     # "Redis connection is OK"
curl http://127.0.0.1:31113/actuator/health
```

### 컨테이너

```dockerfile
FROM 313.co.kr:5550/313devgrp/openjdk:21-jdk
COPY ${ENTRY_FILE} docker-entrypoint.sh
COPY ${JAR_FILE}   javaServiceTreeFramework.jar
ENTRYPOINT ["sh","/docker-entrypoint.sh"]
CMD ["start"]
```

`docker-entrypoint.sh` 기본값:

| 변수 | 기본값 |
|------|--------|
| `GC_OPTS` | `-XX:+UseNUMA -XX:+UseG1GC` |
| `MEM_OPTS` | `-Xms1024m -Xmx1024m` |
| `NET_OPTS` | DNS TTL 0 · IPv4 우선 |
| `SPRING_PROFILES_ACTIVE` | **`live`** |
| timezone | `Asia/Seoul` |

> 스크립트에 `DEV_MONITOR_ELK_OPTS` · `LIVE_MONITOR_ELK_OPTS`(Elastic APM javaagent)가 정의돼 있지만
> **실제 `exec java` 에는 붙지 않는다.** 저장소에 `elastic-apm-agent-1.47.1.jar`(11MB)이 커밋돼 있으나
> Dockerfile 도 복사하지 않는다 — 현재 APM 은 비활성이다.
> 활성화하려면 스크립트에서 `$JVM_OPTS` 옆에 해당 변수를 추가하고 Dockerfile 에 jar 를 복사해야 한다.

`if/else` 분기가 live 와 그 외에 **같은 값**을 넣고 있다(사실상 무의미).

### 배포

`generatePublishInfo` → `spinnaker.properties`(groupId · artifactId · version) → Spinnaker 파이프라인.
이미지 태그는 `313.co.kr:5550/313devgrp/java-service-tree-framework-broker-hub:{version}`.

---

## 4. 로깅

프로파일별 `src/main/resources/logback/logback-{dev,stg,live}.xml` + `console-appender.xml`.

| 어펜더 | 대상 |
|--------|------|
| `CONSOLE` | 표준 출력 |
| `FILE` | `logs/app-info.log` (일별 롤링, 30일 보관) |
| `ERROR_FILE` | `logs/app-error.log` (`LevelFilter` ERROR 만) |

루트 레벨 INFO. 커스텀 컬러 컨버터 `com.arms.util.HighlightingCompositeConverterCustom`
(ERROR 굵은 빨강 · WARN 빨강 · INFO 노랑).

> ⚠️ **로깅 API 가 혼재한다.**
>
> | SLF4J(`org.slf4j.Logger`) | `java.util.logging.Logger` |
> |---|---|
> | `EditorController` · `LockController`(`@Slf4j`) · `ChatController` · `WebSocketEventListener` · `WikiLockService` · `RedisConfig` | `OtController` · `OtService` · `SessionController` · `SessionRegistryService` |
>
> JUL 로거는 logback 설정의 레벨·패턴을 그대로 따르지 않는다
> (`jul-to-slf4j` 브리지가 붙어야 하고, Boot 기본 구성에 포함되긴 하나 `FINE`/`FINEST` 는
> JUL 레벨 설정이 별도로 필요하다). **`logger.fine(...)` 으로 남긴 진단 로그는 기본적으로 안 보인다.**
>
> 파일을 고칠 때는 **그 파일의 기존 방식을 따르고**, 요청 없이 통일하려 들지 않는다.
> 새 파일이라면 SLF4J(`@Slf4j`)를 쓴다.

---

## 5. Slack 알림 (`api/util/slack`)

```
SlackConfig ─(@EnableConfigurationProperties)→ SlackProperty(@ConfigurationProperties("slack") @RefreshScope)
            └─(@Bean)→ SlackNotificationService
```

- 채널 enum 은 `Channel.engine` 하나뿐.
- 메시지 조립은 `SlackMessageDTO`(Lombok `@Builder` → `parseAttachment()` 로 Slack `Attachment` 생성),
  응답 래핑은 `SlackResponse<T>`(`createSlackResponse` · `SlackResponseData` 함수형 인터페이스).
  **`SlackResponse` 는 어디서도 쓰이지 않는다.**
- `isStageOrLiveProfile()` — **`stg`·`live` 프로파일에서만** 실제 발송한다. dev 는 no-op.
- 예외 전송 시 스택트레이스를 `com.arms` 프레임만 남겨 압축한다.
- 발송 실패는 다시 로그로만 남긴다(무한 루프 방지).

> ⚠️ **빈은 등록되지만 주입받아 호출하는 코드가 없다.** 현재 아무 알림도 나가지 않는다.
> 전역 예외 핸들러(`@ControllerAdvice`)가 없어서 연결 지점 자체가 없다.
> 알림이 필요하다는 요청이 오면 핸들러 신설이 함께 필요함을 명시한다.

---

## 6. 추적 · 모니터링

- `micrometer-tracing-bridge-brave` + `zipkin-reporter-brave` — 의존성만 있고 설정 클래스는 없다.
  Zipkin 엔드포인트는 Config 서버가 주입해야 동작한다.
- Elastic APM — §3 참조(현재 비활성).
- SonarQube — `http://www.313.co.kr/sonar`, projectKey `Java-Service-Tree-Framework-Broker-Hub`.

---

## 7. git

- 중첩 git 저장소. **브랜치 `dev`**(`origin/HEAD → origin/dev`).
- 커밋 컨벤션(YouTrack 연동):
  ```
  feat : [ARMS-1195] #comment✅문서 저장시 락 해제 안되는 문제 2026.09.10 #close #time 1h +review SR @sevoon0909
  feat: [ARMS-223] #comment 위키 편집락 기능 추가 2026.08.22 #close #time 1h +review SR @sevoon0909
  feat: [ARMSJIRASE-84] #comment broker-hub 8월 버전업 - 26.08.01 #close #time 1h +review SR @HsYang-hub
  ```
  `[ARMSJIRASE-84]` 는 정기 버전업(월 1회) 전용 티켓이다.
- **commit·push 는 하지 않는다.** 초안만 제시하고 사용자가 커밋한다.
- `.gitignore` 는 `build` · `.gradle` · `.idea` · `*.iml` · `out` 만 막는다 →
  `logs/*.log` · `certs/**`(개인키 `.key`/`.pfx` 포함) · `elastic-apm-agent-*.jar` 이
  **저장소에 커밋돼 있다.** 인증서·키 파일 내용을 읽거나 옮기지 말 것.
