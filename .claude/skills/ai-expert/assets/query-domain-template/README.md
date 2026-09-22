# 새 질의 도메인 템플릿

`{{Domain}}` (파스칼) · `{{domain}}` (소문자 경로/패키지) · `{{AUTHOR}}` · `{{YYYY-MM-DD}}` · `{{YY.MM.DD}}` 를 치환한다.

## 파일 배치

```
src/main/java/com/arms/api/{{domain}}/
├─ controller/{{Domain}}Controller.java
├─ model/dto/{{Domain}}DTO.java
└─ service/{{Domain}}ServiceImpl.java
```

## 코드 외에 해야 할 일

1. **Config Server(Global-Config)에 시스템 메시지 키 추가** — `prompt.{{domain}}.system-message`.
   템플릿은 기본값 없이 참조하므로 키가 없으면 기동이 실패한다(의도된 fail-fast).
   → 이 저장소가 아니라 Global-Config 변경이 필요하다는 점을 사용자에게 알린다.
2. **게이트웨이 노출 여부 판단** — 프론트가 직접 부르면 Middle-Proxy 라우트/권한 반영이 필요하다.
   `/anonymous/**` 는 MABC 대회용 임시 우회이므로 따라 붙이지 않는다.
3. `./gradlew compileJava` 로 검증.

## 파이프라인을 얼마나 쓸지

이 템플릿은 **직접 프롬프트를 조립하는** 형태다(`ChatServiceImpl` · `SupportServiceImpl` 계열).
다른 선택지:

| 원하는 것 | 바꿀 곳 |
|-----------|---------|
| RAG 만으로 답변 | `RagService.ragStream` / `ragGenerate` 위임 |
| aigenerate 7단계 전부 | `UserQueryServiceImpl.executeStream` / `execute` 위임 (`SampleQueryServiceImpl` 참고) |
| 도구·서브에이전트 | `references/agents-and-tools.md` |

## 빠뜨리기 쉬운 것

- DTO 의 `@SuperBuilder` + `@EqualsAndHashCode(callSuper = true)`
- 스트림의 `doFinally` (없으면 클라이언트 취소 시 `streamStatus` 누수)
- `generate` 의 `subscribeOn(Schedulers.boundedElastic())`
- 고객 데이터가 들어가는데 `routingModel()` 을 쓰는 실수
