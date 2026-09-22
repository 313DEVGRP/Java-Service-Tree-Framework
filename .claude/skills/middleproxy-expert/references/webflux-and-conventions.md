# WebFlux 패턴과 코딩 관례

정본: `src/main/java/com/arms/**` 실제 코드.

---

## 1. 애플리케이션 진입점

```java
@EnableSwagger2
@EnableAsync
@SpringBootApplication(exclude = {
        KafkaAutoConfiguration.class,                 // Kafka 빈은 config/KafkaConfig 에서 수동 정의
        UserDetailsServiceAutoConfiguration.class     // Servlet Security 자동 구성 비활성화 (WebFlux 사용)
})
public class Application { ... }
```

두 개의 `exclude` 는 **의도된 것**이다. 되살리면 빈 충돌과 인메모리 기본 유저가 살아난다.

---

## 2. 컨트롤러 작성 표준

### 2.1 뼈대

```java
@RestController                       // (KeycloakUserController 만 @Controller + @ResponseBody 조합)
@RequestMapping("/<도메인 경로>")
@RequiredArgsConstructor              // 또는 @AllArgsConstructor
@Slf4j
public class XxxController {
    private final XxxService xxxService;
}
```

### 2.2 반환 타입 선택

| 상황 | 반환 |
|------|------|
| 단건/목록 + HTTP 상태 제어 | `Mono<ResponseEntity<T>>` (aichat 관례) |
| 공통 래퍼 사용 | `Mono<CommonResponse.ApiResult<T>>` (mapping · poc · wbs · reqdef 관례) |
| 스트림 | `Flux<T>` |
| `@Async` 로 넘겨 즉시 응답 | `CommonResponse.ApiResult<String>` 동기 반환도 실제로 쓰임 (`WbsController.saveAllThenGetWbsRowVOS`, `ReqDefUploadController.saveReqDefUpload`) |

> 마지막 행처럼 **동기 반환을 쓰는 곳이 실제로 있다.** 내부에서 즉시 `@Async` 로 넘기고 아무것도
> 블로킹하지 않기 때문이다. 흉내 낼 때는 "핸들러 스레드에서 블로킹이 0인가"를 반드시 확인한다.

### 2.3 인증 주체 얻기

```java
@GetMapping("/rooms")
public Mono<...> getRoom(@AuthenticationPrincipal OidcUser oidcUser) {
    String userId = oidcUser.getPreferredUsername();   // 표준 사용자 식별자
}
```

세션/exchange 가 필요하면 `ServerWebExchange exchange` 를 파라미터로 받는다
(`SessionParamAdvice` AOP 가 이 파라미터를 찾아 에러 로그에 세션 ID 를 붙인다).

### 2.4 요청 본문 추출

```java
@PostMapping("/{changeReqTableName}/addNode.do")
public Mono<Map<String, Object>> addNode(@PathVariable String changeReqTableName,
                                         ServerHttpRequest request) {
    return requestBodyExtractor.extract(request)
            .flatMap(payload -> service.publishToKafka("ADD_NODE", "POST", changeReqTableName, payload));
}
```

`RequestBodyExtractor` 가 하는 일:
- `DataBuffer` 스트림을 UTF-8 문자열로 합친다.
- `Content-Type: application/x-www-form-urlencoded` 면 URL 디코딩 후 JSON 객체 문자열로 변환.
- 그 외(`application/json`)는 원문 그대로.
- 변환 실패 시 `{}` 를 돌려주고 에러 로그만 남긴다(예외를 던지지 않는다).

---

## 3. 블로킹 격리 패턴

```java
// 값을 반환하는 블로킹
return Mono.fromCallable(() -> service.doBlocking(...))
        .subscribeOn(Schedulers.boundedElastic())
        .map(ResponseEntity::ok);

// 반환 없는 블로킹
return Mono.fromRunnable(() -> service.doBlocking(...))
        .subscribeOn(Schedulers.boundedElastic())
        .then(Mono.just(ResponseEntity.ok().<Void>build()));

// 콜백 기반(진짜 논블로킹) — ReqAddProxyServiceImplAsync
return Mono.create(sink -> {
    future.addCallback(new ListenableFutureCallback<>() {
        public void onSuccess(SendResult<...> r) { sink.success(response); }
        public void onFailure(Throwable ex)      { sink.success(errorResponse); }
    });
});
```

`@Async` 스레드 풀은 `ThreadPoolConfig.executor()` — core 10 / max 20 / queue 10 /
`CallerRunsPolicy`. 큐가 차면 **호출 스레드가 직접 실행**하므로, `@Async` 안에서 다시
오래 걸리는 작업을 쌓으면 이벤트 루프가 잠길 수 있다.

> `ThreadPoolConfig` 의 `@EnableScheduling` 은 주석 처리되어 있다. 이 저장소에는 활성 `@Scheduled` 가 없다.
> 스케줄은 Global-Config 모듈(`/auth-sche/**`)이 돌리고, 이 저장소는 `내부통신기`로 호출만 받는다.

---

## 4. 응답 · 에러 계약

### 4.1 CommonResponse

```java
CommonResponse.success(data)                      // {success:true,  response:data, error:null}
CommonResponse.error(message, errorCode, status)  // {success:false, response:null, error:{...}}
```

`ApiResult<T>` 는 `@JsonCreator` 가 붙어 있어 **Feign 응답 역직렬화에도 그대로 쓰인다**
(`백엔드코어통신기.getReqAddByReqDefId` 가 `ApiResult<ReqAddDTO>` 를 받는다).

### 4.2 예외 계층

```
BaseException (RuntimeException, ErrorCode + HttpStatus=400 기본)
 ├─ PasswordPolicyNotMetException  → COMMON_PASSWORD_POLICY_NOT_MET
 └─ UserAlreadyExistsException     → COMMON_DUPLICATE_FOUND / 409
```

`ErrorCode` enum: `COMMON_SYSTEM_ERROR` · `COMMON_INVALID_PARAMETER` · `COMMON_ENTITY_NOT_FOUND` ·
`COMMON_ILLEGAL_STATUS` · `COMMON_ID_NOT_FOUND` · `COMMON_DUPLICATE_FOUND` · `COMMON_TREE_DAO_ERROR` ·
`COMMON_PASSWORD_POLICY_NOT_MET`.

### 4.3 두 개의 에러 핸들러

| 핸들러 | 잡는 것 |
|--------|--------|
| `ErrorControllerAdvice` (`@ControllerAdvice`) | 컨트롤러에서 올라온 예외. `WebExchangeBindException`(검증) · `IllegalArgumentException` · `BaseException` · 그 외 `Exception`(→ **Slack 알림**) · `ClientAuthorizationException`(→ 401) |
| `GlobalErrorWebExceptionHandler` (`@Order(-2)`) | 라우팅/게이트웨이 레벨. Accept 가 JSON 이면 `{status,error,message,path}`, 아니면 빈 본문 + 상태코드 |

새 예외 타입을 추가하면 `ErrorControllerAdvice` 에 핸들러를 추가하거나 `BaseException` 을 상속한다.

---

## 5. AOP

| Aspect | 포인트컷 | 하는 일 |
|--------|---------|--------|
| `SessionParamAdvice` | `execution(* com.arms..controller.*.*(..))` | 모든 컨트롤러 예외를 잡아 Slack 알림 + 세션ID/파라미터/스택 로그 후 **재throw** |
| `LogAndSlackNotifyAspect` | `@annotation(LogAndSlackNotify)` | 메서드 시작/종료를 `schedule` 채널로 알림 |

Slack 은 **`stg` 프로파일에서만 실제로 전송**된다(`SlackNotificationService.isStage()`).
dev·live 에서는 조용히 스킵되므로, "Slack 이 안 온다"는 대부분 버그가 아니다.

---

## 6. 네이밍 · 언어 관례

- **한글 식별자가 실존한다:** `엔진통신기`, `백엔드코어통신기`, `내부통신기`, `서버정보_엔티티`,
  `각_제품서비스_별_요구사항이슈_조회_및_ES저장()`. 검색할 때 한글 그대로 grep 한다.
  기존 것을 영문으로 바꾸지 않는다.
- 로그는 한국어 + 대괄호 태그 관례: `[PERF]`, `[ReqDef]`, `[WBS]`, `[Lock]`, `[{feature} 락]`.
  Kafka 발행 로그는 이모지 접두(`📤`, `❌`)를 쓴다.
- DTO/VO/Entity 구분이 도메인마다 느슨하다(`model/dto`, `model/vo`, `domain`, `dto`, `vo` 혼재).
  **신규 코드는 인접 도메인의 배치를 그대로 따른다.**
- Lombok: `@RequiredArgsConstructor`(final) 또는 `@AllArgsConstructor` 생성자 주입. `@Slf4j`.
  `@Builder` + `@NoArgsConstructor` + `@AllArgsConstructor` 조합이 VO 의 기본형.
- 값 객체로 키를 감싸는 관례가 있다: `ChangeReqTableName`, `ClassLevelKey`, `WbsRowId`,
  `ReqDefRowId`, `ExcelUploadKey`, `KeyName`. 문자열 조합을 흩뿌리지 말고 이 패턴을 따른다.

---

## 7. 직렬화 유틸

- 도메인 코드는 **주입받은 `ObjectMapper`** 를 쓴다(Boot 자동구성 빈. `AppConfig` 에는 없다).
- `com.arms.util.DataSerializer` 는 static 유틸로 `JavaTimeModule` + `FAIL_ON_UNKNOWN_PROPERTIES=false`
  설정의 별도 ObjectMapper 를 갖는다. 실패 시 예외 대신 `null` 을 반환하므로 주의해서 쓴다.

---

## 8. 검증

- `spring-boot-starter-validation` 사용. 실패는 `WebExchangeBindException` → `ErrorControllerAdvice`.
- 커스텀 검증: `@CronCheck` (필드용). `MadCronExpression.isLessThan600seconds()` 로
  **10분 미만 주기 cron 을 거부**한다. `@Valid` 그룹으로 `ApplyNode` 가 정의되어 있다.
