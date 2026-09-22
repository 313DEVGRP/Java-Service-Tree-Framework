# 빌드 · 기동 · 배포

---

## 1. 빌드 (Windows 로컬, 검증 완료)

```bash
cd Java-Service-Tree-Framework-Backend-Core
JAVA_HOME="C:/Program Files/Microsoft/jdk-11.0.32.101-hotspot" ./gradlew compileJava
# → BUILD SUCCESSFUL (약 40초, warning 7건)
```

- **JDK 11 필수.** 이 PC 기본 JVM 은 JDK 25(`java -version` → `25.0.4.1`)이고,
  그대로 실행하면 Lombok 애노테이션 프로세서가 `java.lang.ExceptionInInitializerError` 로 죽는다.
- 설치돼 있는 JDK: `C:/Program Files/Microsoft/jdk-{11,17,21,25}.*-hotspot`,
  `C:/Program Files/Eclipse Adoptium/jdk-8.*`.
- Gradle Wrapper 6.9.1 (`gradle/wrapper/gradle-wrapper.properties`).
- `build.gradle` 은 Linux 에서 `wget` 으로 Nexus `maven-metadata.xml` 을 받아 patch 버전을 계산한다.
  **Windows/macOS 에서는 건너뛰고 커밋된 `metadata.xml`** 을 쓴다 →
  `*** Windows is not support build` 메시지는 정상이고 컴파일은 진행된다.
- 유용한 태스크: `compileJava`(가장 빠른 검증) · `bootJar` · `printVersion` ·
  `generateLicenseReport` · `sonarqube`.

## 2. 테스트

**`src/test` 디렉토리가 존재하지 않는다.** `test { useJUnitPlatform(); jvmArgs '-Xmx4096m' }` 설정만 있고
실행할 테스트가 없다.

→ 변경 검증 기준:
1. `compileJava` 성공
2. 변경 지점의 논리 검토 (특히 라우팅 키 등록 · 트랜잭션 경계 · 응답 형태)
3. 가능하면 기동 후 실제 엔드포인트 호출

**"테스트를 돌려서 통과했다"고 쓰지 않는다.**

## 3. 로컬 기동

```bash
JAVA_HOME=".../jdk-11..." ./gradlew bootRun --args='--spring.profiles.active=dev'
```

기동에는 **Config Server(Global-Config) 연결이 필수**다. `application.yml` 에는
앱 이름(`javaServiceTreeFrameworkBackendCore`)과 로깅 설정뿐이고, 아래가 전부 외부 주입이다:

`database.driver/url/username/password` · `hibernate.*` · `spring.datasource.hikari.*` ·
`spring.flyway.*` · `spring.kafka.*` · `arms.engine.url` · `arms.ai.url` ·
`arms.middle-proxy.url` · `arms.global-config.url` · `cors.allowed-origins` · `server.port`

| 프로파일 | bootstrap | Config Server |
|---|---|---|
| `dev` | `bootstrap-dev.yml` | `http://www.313.co.kr:33133` (watch 5초) |
| `stg` | `bootstrap-stg.yml` | — |
| `live` | `bootstrap-live.yml` | — |
| `mklee` | `bootstrap-mklee.yml` | 개인 개발용 |

로깅은 `logback/logback-${spring.profiles.active}.xml` 을 읽으므로 **프로파일을 반드시 지정**한다.

Actuator 노출: `refresh`, `env`, `health`, `beans`, `httptrace`.
설정을 바꾼 뒤 `POST /actuator/refresh` 로 `@RefreshScope` 빈을 갱신할 수 있다
(`WebConfig`, `KafkaConfig`).

Swagger UI: springfox 3.0.0 → `/swagger-ui/index.html`.

**loopback Feign 이 `http://127.0.0.1:31313` 을 하드코딩**하고 있으므로,
로컬에서 `server.port` 가 31313 이 아니면 Kafka 소비·일부 내부 호출이 실패한다.

## 4. 배포

```
Dockerfile
  FROM 313.co.kr:5550/313devgrp/openjdk:11-jre
  + elastic-apm-agent 1.47.1 (Nexus 에서 받음)
  ENTRYPOINT sh /docker-entrypoint.sh   CMD start

docker-entrypoint.sh
  GC_OPTS  = -XX:+UseNUMA -XX:+UseG1GC
  MEM_OPTS = -Xms2048m -Xmx2048m -XX:-UseContainerSupport -Xms2g -Xmx2g
  NET_OPTS = -Dsun.net.inetaddr.ttl=0 ... -Djava.net.preferIPv4Stack=true
  SPRING_PROFILES_ACTIVE 기본값 live
  TZ: -Duser.timezone=Asia/Seoul
```

- `-XX:-UseContainerSupport` 가 켜져 있어 **JVM 이 컨테이너 메모리 한도를 무시**한다.
  그래서 `-Xmx` 를 명시적으로 박아 둔 것이다(commit `bfc3fdf0` 참조). 이 조합을 함부로 풀지 않는다.
- 이미지 태그: `313.co.kr:5550/313devgrp/java-service-tree-framework-backend-core:<version>`
- 버전: `26.9.<auto>` — major 26 / minor 9 는 `build.gradle` 의 `ext` 에 하드코딩,
  patch 는 Nexus `maven-metadata.xml` 의 latest + 1.
- 아티팩트 배포: `publish` → `http://www.313.co.kr/nexus/repository/ple-releases/`
  (`settings.xml` 또는 `~/.m2/settings.xml` 의 계정 사용) + `spinnaker.properties` 자동 생성.
- GitHub Actions 는 `release-drafter.yml` 하나뿐 — **CI 빌드/테스트 파이프라인은 없다.**

## 5. 모니터링

- Elastic APM 에이전트가 컨테이너에 붙는다
  (`elastic.apm.service_name = dev_backend-core` / `live_backend-core`,
  `application_packages = com.arms`).
- SonarQube: `http://www.313.co.kr/sonar`, projectKey `Java-Service-Tree-Framework-Backend-Core`.
- Kafka lag: `KafkaLagMonitor` + `/kafka` (`KafkaMonitorController`).
- 오류 알림: `ErrorControllerAdvice` → Slack `backend` 채널.
