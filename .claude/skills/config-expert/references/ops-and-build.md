# 빌드 · 실행 · 배포 · 운영

`SKILL.md` §7 · §8 의 상세판. 정본은 `build.gradle` · `Dockerfile` · `docker-entrypoint.sh` ·
`src/main/resources/logback/*` · `com/arms/config/**` · `com/arms/api/util/{aspect,slack,errors,response}/**`.

---

## 1. 의존성 지도 (`build.gradle`)

| 축 | 값 |
|----|----|
| Java | 11 (`sourceCompatibility`/`targetCompatibility`) |
| Spring Boot | 2.6.15 |
| Spring Cloud BOM | 2021.0.9 |
| 그룹/아티팩트 | `313devgrp` / `Java-Service-Tree-Framework-Global-Config` |

주요 의존성:

```
spring-boot-starter-web        ← MVC(Tomcat). 웹 모델을 결정하는 것은 이것이다
spring-boot-starter-webflux    ← WebClient 전용. 앱은 서블릿으로 뜬다
spring-boot-starter-aop        ← LoggingAdvice · SlackSendAdvice
spring-boot-starter-actuator
spring-cloud-config-server     ← @EnableConfigServer. JGit 도 여기서 전이로 들어온다
spring-cloud-starter-config
spring-cloud-starter-openfeign
springfox-boot-starter 3.0.0 + springfox-swagger-ui 3.0.0
com.slack.api:slack-api-client 1.25.1
jakarta.json:jakarta.json-api 2.0.1
io.netty:netty-resolver-dns-native-macos (osx-aarch_64)
lombok
```

> `spring-boot-starter-web` 과 `-webflux` 가 **둘 다** 있으면 Spring Boot 는 **서블릿(MVC)** 으로 뜬다.
> 그래서 컨트롤러는 값을 직접 반환하고 `HttpServletRequest` 를 쓸 수 있다.
> `LoggingAdvice` 가 `org.apache.catalina.connector.RequestFacade` 를 import 하는 것도 그 때문이다.
> 이 조합을 건드리면(예: web 제거) 앱 전체가 리액티브로 바뀌며 AOP·Swagger 가 함께 깨진다.

### Middle-Proxy 와 다른 점 — Feign 인코더

`FeignResponseDecoderConfig` 는 Decoder 만 등록한다(Middle-Proxy 와 동일한 파일명).
하지만 여기는 **MVC 가 있어 `HttpMessageConverters` 가 자동 구성**되므로
기본 `SpringEncoder` 가 살아 있고 `@RequestBody` 가 동작한다
(`EngineCommunicator.getScheduleHistory(@RequestBody SearchDTO)` 가 실제로 그렇게 쓴다).
Middle-Proxy 의 "Feign 에 `@RequestBody` 금지" 규칙을 **이 저장소에 그대로 옮기지 말 것.**

### 미사용·미완 빌드 설정

- `licenseReport { allowedLicensesFile = new File("$projectDir/allowed-licenses.json") }`
  → **그 파일이 저장소에 없다.** `generateLicenseReport` 계열 태스크는 실패한다(`build` 에는 안 걸림).
- `org.openjfx.javafxplugin` 플러그인이 적용돼 있으나 JavaFX 를 쓰는 코드가 없다.
- `ThreadPoolConfig` 는 `@Configuration`/`@EnableScheduling` 이 주석 처리되어 비활성.
- Sonar 설정에 `sonar.login`/`sonar.password` 가 평문으로 들어 있다(복제 금지).

---

## 2. 버전 자동 계산

```groovy
majorVersion = 26
minorVersion = 9
// patchVersion = auto generation

// Windows/Mac: wget 생략 → 저장소에 커밋된 metadata.xml 사용
// Linux(CI):   wget 으로 Nexus maven-metadata.xml 다운로드 후 덮어씀
//   metadataUrl = http://www.313.co.kr/nexus/repository/ple-releases/313devgrp/
//                 Java-Service-Tree-Framework-Global-Config/maven-metadata.xml

// latest 와 비교해서
//   major 가 크면      → minor=0, patch=0
//   minor 만 크면      → patch=0
//   그 외              → patch = latestPatch + 1
version = "${majorVersion}.${minorVersion}.${patchVersion}"
```

저장소에 커밋된 `metadata.xml` 은 `latest = 0.0.1` 인 오래된 스텁이다.
→ **로컬(Windows/Mac) 빌드는 `26.0.0` 을 낸다**(major 26 > 0 이라 minor 가 0 으로 내려감).
`spinnaker.properties` 에 마지막으로 기록된 값도 `26.0.0` 이다.
CI 에서는 Nexus 실제 최신값을 기준으로 다르게 계산된다. **불일치는 정상이다.**

`publish` 는 `generatePublishInfo` 에 의존해 `spinnaker.properties` 를 다시 쓴다.
Nexus 자격증명은 `~/.m2/settings.xml` → 없으면 저장소의 `settings.xml` 에서 읽는다(평문, 복제 금지).

```bash
./gradlew printVersion      # 계산된 버전 확인
```

---

## 3. Docker · 배포

`Dockerfile`

```
FROM 313.co.kr:5550/313devgrp/openjdk:11-jre
  · elastic-apm-agent 1.47.1 를 Nexus 에서 받아 /elastic-apm-agent.jar 로 배치
  · 313.co.kr / a-rms.net 인증서를 cacerts 에 import (SaaS 용)
  · COPY <bootJar>  → javaServiceTreeFramework.jar
  · ENTRYPOINT ["sh","/docker-entrypoint.sh"] / CMD ["start"]
```

`docker`(palantir) 블록: 이미지 `313.co.kr:5550/313devgrp/java-service-tree-framework-global-config:<version>`.

`docker-entrypoint.sh`

- 기본 `SPRING_PROFILES_ACTIVE=live`.
- `GC_OPTS` = `-XX:+UseNUMA -XX:+UseG1GC`, `MEM_OPTS` = `-Xms1g -Xmx1g` + `-XX:-UseContainerSupport`.
- `DEV_MONITOR_ELK_OPTS` / `LIVE_MONITOR_ELK_OPTS`(APM javaagent)가 **정의만 되고 exec 줄에서 쓰이지 않는다.**
  APM 을 실제로 붙이려면 `JAVA_OPTS` 로 주입해야 한다.
- `if/else` 두 분기가 같은 값을 넣는다(사실상 분기 없음).
- **이 파일은 Backend-Core · Middle-Proxy · Engine-Fire 와 바이트 단위로 같은 org 공통 파일이다.**
  이 저장소에서만 단독 수정하지 말고, 바꿔야 하면 4개 모듈 동시 변경으로 제안한다.

배포는 Spinnaker 가 `spinnaker.properties`(groupId/artifactId/version)를 읽어 처리한다.

---

## 4. Swagger (`Swagger2Config`)

- Springfox 3.0.0 + Boot 2.6 조합은 기본 상태로 **기동 시 NPE** 가 난다.
  `springfoxHandlerProviderBeanPostProcessor` 가 `WebMvcRequestHandlerProvider` ·
  `WebFluxRequestHandlerProvider` 의 `handlerMappings` 에서 `patternParser != null` 인 항목을 제거해 우회한다.
  **`static` BeanPostProcessor 다. 지우거나 non-static 으로 바꾸면 기동이 깨진다.**
- `spring.mvc.pathmatch.matching-strategy: ant_path_matcher` 도 같은 우회의 일부다.
- `pathMapping("/global-config-api")`, 스캔 베이스 패키지 `com.arms`.
- UI: `http://<host>:33133/global-config-api/swagger-ui/`

---

## 5. 로깅

```
logging.config: classpath:logback/logback-${spring.profiles.active}.xml
```

| 프로파일 | 루트 appender |
|---------|--------------|
| dev | `CONSOLE`(동기) |
| stg · live | `ASYNC_CONSOLE`(queueSize 512, `neverBlock=true`) |

- 패턴은 `HighlightingCompositeConverterCustom` 을 `highlightCustom` 으로 등록해 레벨별 색을 입힌다
  (이 클래스는 Spring 빈이 아니라 logback 이 리플렉션으로 만든다 — 패키지·클래스명을 바꾸면 로깅이 깨진다).
- 파일 appender가 없다. **로그는 전부 stdout** 이고 수집은 컨테이너 런타임/Fluentd 몫이다.
- `neverBlock=true` 라 부하 시 stg/live 에서는 **로그가 유실될 수 있다.**

### 로그 관례

- 형식: `[ 클래스명 :: 메서드명 ] :: 메시지 => {}`
- `LoggingAdvice` 가 `com.arms..controller.*.*` · `com.arms..service.*.*` 전체에 자동으로
  `:: Start` / `:: End` 를 남긴다 → 같은 내용을 수동으로 또 찍지 않는다.
- `ArmsApplicationProperties` 는 이모지 접두(`✅`/`❗`)를 쓴다.

---

## 6. 에러 · 알림 파이프라인

```
컨트롤러/서비스 예외
   │
   ├─ LoggingAdvice.@Around → Slack 전송 + 상세 로그 → 예외 재던짐
   │
   └─ ErrorControllerAdvice
        · IllegalArgumentException → 400 + ErrorCode.COMMON_INVALID_PARAMETER
        · 그 외 Exception          → 500 + ErrorCode.COMMON_SYSTEM_ERROR + Slack 전송(두 번째)
```

- **같은 예외로 Slack 알림이 두 번 간다.** 세 번째 알림 지점을 추가하지 않는다.
- 응답 봉투 `ApiResult<T>` = `{ success, response, error{ message, errorCode, status } }`
  (`CommonResponse.success/error`). 에러는 이 형태로만 낸다.
- `@SlackSendAlarm(messageOnStart, messageOnEnd)` → `SlackSendAdvice` 가 before/afterReturning/afterThrowing 처리.
  현재 사용처는 `ConfigServerWebhookController.handlerConfigChanged`, `ScheduleWebhookController.refreshContext`.
- `@LogAndSlackNotify` + `LogAndSlackNotifyAspect` 는 구형이며 **현재 사용처가 없다.**
- `SlackNotificationService` 는 `stg`/`live` 프로파일에서만 전송한다.
  스택트레이스는 `com.arms` 프레임만 남겨 보낸다. 채널 enum 은 `globalconfig` 하나.
- Slack 토큰은 `slack.token: ${SLACK_TOKEN}` 환경변수다(dev 프로파일에는 `slack` 블록 자체가 없음).

---

## 7. 로컬 실행 체크리스트

```bash
./gradlew compileJava                 # 가장 빠른 검증 (Windows: gradlew.bat)
# IDE 실행: Active profile = dev
```

| 확인 | 기대 |
|------|------|
| 포트 | 33133 |
| Gitea 접근 | `www.313.co.kr` 도달 가능해야 함. 안 되면 `ScheduleInitializer` 가 기동 중 예외 |
| 기동 로그 | `✅ Loaded arms.urls properties:` + `Added task: ...` + `Registered [...] with cron [...]` |
| Config Server | `curl http://127.0.0.1:33133/javaServiceTreeFrameworkBackendCore/dev` |
| Swagger | `http://127.0.0.1:33133/global-config-api/swagger-ui/` |
| 액추에이터 | `/actuator/{health,env,beans,refresh}` — **`/actuator/shutdown` 도 열려 있으니 실수로 치지 말 것** |

dev 프로파일의 Feign 대상은 전부 `127.0.0.1` 이다 → 로컬에 Backend-Core/Engine-Fire 가 없으면
수동 실행 엔드포인트와 크론은 연결 거부로 실패한다. **정상이다.**

### 테스트

`src/test` 디렉터리가 **존재하지 않는다.** `test { useJUnitPlatform() }` 는 선언돼 있지만 실행할 것이 없다.
`./gradlew test` 통과는 아무 근거도 되지 않는다.
새 로직은 스프링 컨텍스트 없는 순수 단위 테스트(예: `LanguagePackFileReader` 의 flatten/unflatten,
`ConfigServerWebhookController` 의 정규식 매핑)를 직접 추가해 검증한다.
