# Config Server — 설정 배포와 전파

`SKILL.md` §2 의 상세판. 정본은 `com/arms/api/configserver/**` 와 `src/main/resources/application-*.yml`.

---

## 1. 서버 구성

`com.arms.Application` 에 `@EnableConfigServer` 가 붙어 있다. 그 외 설정은 전부 yml 이다.

```yaml
# application.yml (공통)
spring.application.name: javaServiceTreeFrameworkGlobalConfig
spring.mvc.async.request-timeout: 7200
spring.mvc.pathmatch.matching-strategy: ant_path_matcher   # Config Server·Springfox 호환용
server.port: 33133
logging.config: classpath:logback/logback-${spring.profiles.active}.xml
```

```yaml
# application-<profile>.yml — Git 백엔드
spring.cloud.config.server.git:
  uri: <Gitea root/ARMS 주소>       # dev: http://www.313.co.kr/gitea/root/ARMS, stg/live: http://gitea:3000/root/ARMS
  default-label: main               # ← 브랜치는 main 이다. 이 저장소의 작업 브랜치(dev)와 다르다
  clone-on-start: true
  force-pull: true
  timeout: 30
  username / password / token       # 평문. 복제 금지
```

`force-pull: true` 때문에 서버 로컬 클론에 손으로 낸 변경은 다음 pull 에서 날아간다.
`default-label: main` 이므로 Gitea 에서 **`main` 브랜치에 push 해야** 설정이 반영된다.

### 노출되는 Config Server 엔드포인트 (의존성이 만드는 것)

```
GET /{application}/{profile}
GET /{application}/{profile}/{label}
GET /{application}-{profile}.yml        (.json / .properties 도 동일)
GET /{label}/{application}-{profile}.yml
```

수동 확인 예:

```bash
curl http://127.0.0.1:33133/javaServiceTreeFrameworkBackendCore/dev
curl http://127.0.0.1:33133/javaServiceTreeFrameworkMiddleProxy-live.yml
```

이 패턴이 최상위 경로를 점유하므로 **새 컨트롤러는 반드시 리터럴 접두로 시작**한다(`SKILL.md` §5.3).

---

## 2. 프로파일 지도

| 프로파일 | Git uri | 모듈 주소 | Slack |
|---------|---------|----------|-------|
| `dev` | `http://www.313.co.kr/gitea/root/ARMS` | 전부 `127.0.0.1:<port>` | 설정 없음(= 미발송) |
| `stg` | `http://gitea:3000/root/ARMS` | 컨테이너명(`backend-core:31313` 등) | `${SLACK_TOKEN}` |
| `live` | `http://gitea:3000/root/ARMS` | 컨테이너명 | `${SLACK_TOKEN}` |

`docker-entrypoint.sh` 기본값은 `SPRING_PROFILES_ACTIVE=live` 다.

### 모듈 포트 (`arms.*.url` · `clients.urls.*.url` 양쪽에 같은 값이 중복 정의됨)

| 키 | 포트 |
|----|------|
| `backend-core` | 31313 |
| `engine-fire` | 33333 |
| `middle-proxy` | 13131 |
| `ai` | 31311 |
| `broker-hub` | 31113 |

- `arms.*` 는 **Feign 클라이언트 URL**(`@FeignClient(url = "${arms.backend-core.url}")`).
- `clients.urls.*` 는 **웹훅 refresh 대상**(`ArmsApplicationProperties`, prefix `clients`).
- **둘은 별개다.** 새 모듈을 붙일 때 한쪽만 넣으면 조용히 반쪽만 동작한다.

`ArmsApplicationProperties` 는 `@PostConstruct` 에서 로드된 URL 을 전부 로그로 찍는다
(`✅ Loaded arms.urls properties:` / 비었으면 `❗ ArmsApplicationProperties.urls is EMPTY`).
기동 로그에서 이 줄을 먼저 확인하면 §3 디버깅의 절반이 끝난다.

---

## 3. 웹훅 전파 (`ConfigServerWebhookController`)

```
POST /api/config-server/config-changed
Body: GitHub 형식 push payload  { "commits": [ { "added": [], "modified": [], "removed": [] } ] }
응답: 200 "Processed"  (항상. 전파 성공 여부와 무관)
```

`@SlackSendAlarm(messageOnEnd = "A-RMS MSA 환경 파일 리플레시 및 적용 완료")` 가 붙어 있어
stg/live 에서는 완료 시 Slack 알림이 간다.

### 파일명 → 키 변환 규칙

```java
Pattern.compile("javaServiceTreeFramework(\\w+?)(Core|Fire|Proxy|Hub|AI)?(?:-(\\w+))?\\.yml");
// key = group(1).toLowerCase() + (group(2) != null ? "-" + group(2).toLowerCase() : "")
```

| 변경 파일 | group(1) | group(2) | group(3) | key | 결과 |
|----------|----------|----------|----------|-----|------|
| `javaServiceTreeFrameworkBackendCore.yml` | Backend | Core | - | `backend-core` | refresh |
| `javaServiceTreeFrameworkBackendCore-dev.yml` | Backend | Core | dev | `backend-core` | refresh |
| `javaServiceTreeFrameworkBackendCore-mklee.yml` | - | - | mklee | - | **IGNORED_PROFILES 로 스킵** |
| `javaServiceTreeFrameworkEngineFire-live.yml` | Engine | Fire | live | `engine-fire` | refresh |
| `javaServiceTreeFrameworkMiddleProxy.yml` | Middle | Proxy | - | `middle-proxy` | refresh |
| `javaServiceTreeFrameworkAI.yml` | AI | - | - | `ai` | refresh |
| `javaServiceTreeFrameworkBrokerHub.yml` | Broker | Hub | - | `broker-hub` | refresh |
| `javaServiceTreeFrameworkGlobalConfig.yml` | GlobalConfig | - | - | `globalconfig` | **clients.urls 에 없어 무시** |
| `application.yml` 등 접두 불일치 | - | - | - | - | `대상 아님(패턴 불일치)` 로그 |

```java
private static final Set<String> IGNORED_PROFILES = Set.of("local", "mklee");
```

주석이 못박아 둔 규칙: **`spring.profiles.group` 으로 상시 활성화되는 프로파일은 여기에 넣으면 안 된다**
(예: AI 서비스의 `prompt` — dev/stg/live 모두에서 함께 로드되는 정식 설정).

### 전파 방식

```java
webClientBuilder.build().post().uri(url + "/actuator/refresh")
    .retrieve().bodyToMono(String.class)
    .doOnSuccess(...).doOnError(...)
    .subscribe();            // ← fire-and-forget
```

- 실패해도 컨트롤러는 200 을 반환한다. 성공 여부는 **로그로만** 확인 가능하다
  (성공 `Refreshed: <url>` / 실패 `Error refreshing <url>: <msg>` — `System.out`/`System.err` 로 나간다).
- 대상 모듈은 `/actuator/refresh` 를 노출하고 있어야 한다. 실제로 세 모듈 모두
  `management.endpoints.web.exposure.include: refresh, env, health, beans, httptrace` 를 켜 두었다.
- refresh 는 `@RefreshScope` 빈과 `@ConfigurationProperties` 재바인딩만 한다.
  **Kafka 리스너 컨테이너, 커넥션 풀, 게이트웨이 라우트처럼 기동 시 고정되는 것은 갱신되지 않을 수 있다.**
  값이 바뀌었는데 동작이 그대로면 해당 모듈 재기동이 필요한 값인지 먼저 판단한다.

---

## 4. 새 MSA 모듈을 설정 서버에 태우는 절차

1. 새 모듈의 `spring.application.name` 을 `javaServiceTreeFramework<Module>` 형태로 정한다.
2. Gitea `root/ARMS` 에 `javaServiceTreeFramework<Module>[-<profile>].yml` 을 만든다(브랜치 `main`).
3. **이 저장소**의 `application-{dev,stg,live}.yml` 에 `clients.urls.<key>.url` 을 추가한다.
   Feign 으로도 부를 거면 `arms.<key>.url` 도 함께 추가한다.
4. 키가 정규식으로 안 나오는 이름이면 `ConfigServerWebhookController` 의 접미사 그룹
   `(Core|Fire|Proxy|Hub|AI)` 에 새 접미사를 추가한다.
5. 클라이언트 쪽 접속 방식을 고른다.
   - 신규는 **ConfigData 방식** 권장: `spring.config.import: optional:configserver:http://<host>:33133`
   - 레거시 bootstrap 방식(`spring.cloud.config.uri`)은 `spring-cloud-starter-bootstrap` 의존성이 추가로 필요하다.
6. 클라이언트가 `management.endpoints.web.exposure.include` 에 `refresh` 를 포함하는지 확인한다.
7. 기동 후 `✅ Loaded arms.urls properties:` 로그에 새 키가 보이는지 확인한다.

---

## 5. "설정이 반영 안 된다" 3단 분해

| 단계 | 확인 방법 |
|------|----------|
| ① Gitea 에 반영됐나 | `main` 브랜치인지, 파일명이 `spring.application.name` 과 정확히 같은지 |
| ② Config Server 가 읽나 | `curl http://<host>:33133/<appName>/<profile>` 로 값이 나오는지 |
| ③ 클라이언트에 도달했나 | 대상 모듈 `/actuator/env` 에서 값 확인. 없으면 `/actuator/refresh` 수동 POST |

②에서 옛 값이 나오면 Git 백엔드 pull 문제(`force-pull`·자격증명·`default-label`).
③에서만 옛 값이면 웹훅 전파 문제(§3) 또는 refresh 로 갱신되지 않는 종류의 값이다.

`optional:` 접두 때문에 **설정 서버가 아예 죽어 있어도 클라이언트는 조용히 기동한다.**
"설정이 통째로 기본값이다" 싶으면 설정 서버 생존부터 확인한다.
