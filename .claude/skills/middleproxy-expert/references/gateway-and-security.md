# 게이트웨이 · 인증 · 세션

정본: `config/security/SecurityConfiguration`, `config/handler/**`, `config/filter/**`,
`config/interceptor/LoginErrorFilter`, `config/KeycloakConfig`, `api/keycloak/**`.

---

## 1. 설정이 어디서 오는가

저장소의 `src/main/resources/application*.yml` 은 **뼈대만** 있다.

```yaml
# application.yml (전부다)
spring:
  application:
    name: javaServiceTreeFrameworkMiddleProxy
server:
  forward-headers-strategy: framework
```

```yaml
# application-dev.yml   (stg/live 는 global-config:33133)
spring:
  config:
    import: optional:configserver:http://www.313.co.kr:33133
management:
  endpoints:
    web:
      exposure:
        include: refresh, env, health, beans, httptrace
```

즉 **포트·라우트·Redis·Kafka·Keycloak·Feign URL·시크릿이 전부 Config 서버에서 온다.**

| 설정 키 | 쓰이는 곳 |
|---------|----------|
| `spring.cloud.gateway.routes` | 게이트웨이 라우팅 (이 저장소에 코드 없음) |
| `spring.security.oauth2.client.registration.middle-proxy.{realm,server-url,client-id,client-secret}` | `KeycloakConfig`, `KeycloakLogoutHandler` |
| `spring.security.auth.success.redirect-url` | `SecurityConfiguration`, `LoginErrorFilter` |
| `spring.kafka.bootstrap-servers`, `spring.kafka.topic.reqadd` | `KafkaConfig`, 발행 서비스 |
| `arms.backend.url`, `arms.engine.url` | Feign 클라이언트 |
| `permit.urls` | `PermitUrl` → `BlockRequestGatewayFilter` |
| `aes.token` | `AESProperty` → `AES256` |
| `slack.{serviceName,token,profile,url}` | `SlackProperty` |

`@RefreshScope` 가 붙은 빈(`SecurityConfiguration` · `KeycloakConfig` · `KafkaConfig` ·
`LoginErrorFilter`)은 `POST /actuator/refresh` 로 재생성된다.

> **라우트를 바꿔야 하는 작업이면 이 저장소를 고칠 게 아니라 Global-Config 를 고쳐야 한다.**
> 그 사실을 사용자에게 명확히 보고한다.

---

## 2. SecurityConfiguration 전문 요약

```java
@Configuration @EnableWebFluxSecurity
@EnableGlobalMethodSecurity(jsr250Enabled = true)   // @RolesAllowed 사용 가능
@RefreshScope
public class SecurityConfiguration {

  @Bean SecurityWebFilterChain securityWebFilterChain(ServerHttpSecurity http) {
    return http
      .cors(CorsSpec::disable)            // CORS 비활성 — 프론트는 같은 도메인으로 들어온다
      .csrf(CsrfSpec::disable)
      .authorizeExchange(authorize -> authorize
        .pathMatchers("/login").permitAll()
        .pathMatchers("/middle-proxy-api", "/middle-proxy-api/**").permitAll()
        .pathMatchers("/backend-core-api", "/backend-core-api/**").permitAll()
        .pathMatchers("/engine-fire-api", "/engine-fire-api/**").permitAll()
        .pathMatchers("/actuator/**").permitAll()          // TODO: IP 제한 예정 (코드 주석)
        .pathMatchers("/mapping/**").permitAll()
        .pathMatchers("/poc/**","/wbs/**","/req-def/**","/wiki/lock/**","/atlassian/**").permitAll()
        .pathMatchers("/dwr/**").hasAnyRole("USER","MANAGER","ADMIN")
        .pathMatchers("/auth-anon/**").permitAll()
        .pathMatchers("/auth-user/**").hasAnyRole("USER","MANAGER","ADMIN")
        .pathMatchers("/auth-manager/**").hasAnyRole("MANAGER","ADMIN")
        .pathMatchers("/auth-admin/**").hasRole("ADMIN")
        .anyExchange().authenticated())
      .exceptionHandling().authenticationEntryPoint(/* referer → session["rd-page"], 401 */)
      .and().oauth2Login().authenticationSuccessHandler(new AuthSuccessHandler(...))
      .and().logout(logout -> logout.logoutUrl("/logout")
                                    .logoutHandler(WebSession + Keycloak 위임)
                                    .logoutSuccessHandler(200 OK));
  }
}
```

주의점:

- `pathMatchers` 는 **선언 순서대로** 평가된다. 더 구체적인 규칙을 먼저 둔다.
- `hasRole("ADMIN")` 은 권한 문자열 `ROLE_ADMIN` 을 요구한다. Keycloak realm role 이
  `ROLE_` 로 시작해야 매핑된다(§3).
- `/kafka/**` 는 어떤 permitAll 에도 없다 → `anyExchange().authenticated()` 로 **인증 필요**.
- `@EnableGlobalMethodSecurity(jsr250Enabled = true)` 덕분에 컨트롤러 메서드에
  `@RolesAllowed("ADMIN")` 을 쓸 수 있다(`KeycloakAdminController` 가 사용).

---

## 3. 권한 추출 (OIDC claim → GrantedAuthority)

```java
@Bean ReactiveOAuth2UserService<OidcUserRequest, OidcUser> oidcUserService() { ... }

// claims["realm_access"]["roles"] 중 "ROLE_" 로 시작하는 것만 SimpleGrantedAuthority 로 매핑
// realm_access 가 없거나 roles 가 없으면 → List.of("ROLE_USER")
```

즉 Keycloak realm 에 `ROLE_ADMIN` · `ROLE_MANAGER` · `ROLE_USER` 형태의 realm role 이
정의되어 있어야 한다. `admin` 같은 접두 없는 롤은 **조용히 무시**된다.

---

## 4. 로그인 · 로그아웃 흐름

```
미인증 요청
  └ authenticationEntryPoint
      ├ exchange.session["rd-page"] = request.header("referer")
      └ 401 (ResponseStatusException "Session is null")
  → 프론트가 /oauth2/authorization/... 으로 로그인 유도 → Keycloak

로그인 성공
  └ AuthSuccessHandler (extends RedirectServerAuthenticationSuccessHandler)
      ├ session["rd-page"] 가 있으면 그 URL 로, 없으면 ${spring.security.auth.success.redirect-url} 로 리다이렉트
      └ (중복 로그인 제거는 현재 주석 처리됨 — AuthSuccessAfterDuplicateUserRemove.removeSession)

로그아웃  POST/GET /logout
  └ DelegatingServerLogoutHandler
      ├ WebSessionServerLogoutHandler   (Redis 세션 무효화)
      └ KeycloakLogoutHandler           (Keycloak end_session_endpoint 호출)
  └ logoutSuccessHandler → 200 OK (본문 없음)
```

- `KeycloakLogoutHandler` 의 end-session URL 이 **`http://keycloak:8080/auth` 로 하드코딩**되어 있다
  (`serverUrl` 을 주입받지만 실제로 쓰지 않는다). 컨테이너 밖에서는 이 호출이 실패하지만,
  실패해도 `onErrorResume` 으로 삼켜져 **로컬 세션 정리는 정상 진행**된다.
- `AuthSuccessAfterDuplicateUserRemove` 는 `spring:session:sessions:*` 를 스캔해
  같은 `preferredUsername` 의 다른 세션을 찾아 Keycloak 로그아웃 + 세션 삭제하고
  `백엔드코어통신기.sendMessage(...)` 로 알린다. **현재는 호출부가 주석 처리되어 비활성**이다.
  되살릴 때는 세션 전량 스캔 비용을 감안한다.
- `LoginErrorFilter` (`WebFilter`): 브라우저 뒤로가기로 `/login?error` 에 도달하면
  302 로 `redirect-url` 로 되돌린다.

---

## 5. 세션

```java
@EnableRedisWebSession(maxInactiveIntervalInSeconds = 60 * 60 * 2)   // 2시간
```

- 저장 위치: Redis `spring:session:sessions:{id}`, 속성 키 `sessionAttr:SPRING_SECURITY_CONTEXT`.
- 게이트웨이 인스턴스 간 공유되므로 수평 확장이 가능하다.
- `UserController` 가 제공하는 것:
  `GET /auth-user/me`(사용자 정보) · `GET /auth-user/session-id` · `GET /auth-user/logout`.
  프론트(`common.js`)가 `/auth-user/me` 로 인증 확인을 한다.

---

## 6. 게이트웨이 필터

### `BlockRequestGatewayFilter` (`AbstractGatewayFilterFactory`)

라우트 설정에서 `BlockRequestGatewayFilter` 이름으로 붙여 쓰는 커스텀 필터.
요청 경로가 `permit.urls` 목록 중 **어느 하나라도 substring 으로 포함**하지 않으면
`exchange.getResponse().setComplete()` 로 **본문 없이 즉시 종료**한다(상태코드 미지정 → 200).

```yaml
# Global-Config 쪽 설정 예시
permit:
  urls:
    - /some/allowed/path
```

> ⚠️ `path.contains(permitUrl)` 방식이라 부분 문자열 우회가 가능하다. 새로 쓸 때는
> 접두 매칭으로 좁히는 것을 검토하되, 기존 라우트 동작을 깨지 않도록 사용자와 합의한다.

### `WebConfig`

- 코덱 `maxInMemorySize = 16MB` (그보다 큰 본문은 게이트웨이 프록시 경로로만 통과).
- `WebClient` 빈 등록(로그아웃 핸들러가 사용).
- `LoginErrorFilter` 를 `WebFilter` 빈으로 등록.

---

## 7. Keycloak Admin 연동

```java
@Bean Keycloak keycloak()            // CLIENT_CREDENTIALS 그랜트, client-id/secret 주입
@Bean RealmResource realmResource(Keycloak keycloak)
```

`api/keycloak/admin` 이 realm·client·group·role·user 를 Admin REST 로 조작한다
(`KeycloakAdminController`, `@RolesAllowed` 로 보호). 비밀번호 정책은
`KeycloakPasswordPolicyService.getPasswordPolicy(realm)` 으로 조회해
정책 위반 시 `PasswordPolicyNotMetException` 을 던진다
(Keycloak 응답 본문의 `"Password policy not met"` 문자열이 판정 근거).

`api/keycloak/user` 는 일반 사용자용 조회(`/auth-user/search-user/{userName}`,
`/auth-user/users`, `/auth-user/user/{id}/check-permission/{page}`).

---

## 8. 새 보호 경로 추가 절차 (요약)

1. 이 저장소가 직접 처리 → 컨트롤러 추가. 다운스트림 → Global-Config 라우트 추가.
2. `SecurityConfiguration.pathMatchers` 에 규칙 추가 (구체적인 것을 위로).
3. 다운스트림이면 `RewritePath` 로 접두를 벗긴다.
   관례: `/auth-anon/api/(path)` → `/anonymous/${path}` (+ `RemoveRequestHeader=Cookie`),
   `/auth-user/api/(path)` → `/${path}`,
   `/auth-manager/api/(path)` → `/manager/${path}`,
   `/auth-admin/api/(path)` → `/admin/${path}`.
4. 인증이 필요 없는 내부 전용 API 라면 permitAll 에 추가하되 **외부 노출 여부를 반드시 확인**한다.
5. Swagger 에 노출할지 확인(`Swagger2Config` 는 `com.arms` 전체 패키지를 스캔한다).
