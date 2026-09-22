# esframework — 쿼리·집계 API 전량

패키지: `com.arms.egovframework.javaservice.esframework`
이 계층을 거치지 않고 OpenSearch에 접근하는 코드는 이 저장소에 쓰지 않는다.

```
esframework/
├── annotation/      @ElasticSearchIndex @RollingIndexName @Recent @RecentId
│                    @ElasticSearchCreatedDate @ElasticSearchUpdateDate @ElasticSearchTemplateConfig
├── config/          EsRepositoryWrapperConfig · RepositoryConfiguration · EsIndexTemplateConfig
├── custom/client/   CustomOpenSearchRestTemplate 등 (직접 건드리지 않는다)
├── esquery/         SimpleQuery + bool/filter/must/mustnot/should/sort/highlight/subaggregation
├── factory/         SearchDocQueryFactory · AggregationQueryFactory · CompositeAggregationQueryFactory
├── model/           dto(esquery·request) · entity(BaseEntity) · vo(결과 래퍼)
├── repository/      EsCommonRepository(Impl) · EsCommonRepositoryWrapper · RecentFieldConvertor
└── util/            ReflectionUtil
```

---

## 1. 진입점 — `EsCommonRepositoryWrapper<E extends BaseEntity>`

`config/EntityClassConfig` 가 엔티티별 `@Bean` 으로 노출한다. 서비스는 이것만 주입받는다.

### 1.1 조회 (find)

| 메서드 | recent | 반환 | 용도 |
|--------|:---:|------|------|
| `findHits(SimpleQuery<SearchDocDTO>)` | | `DocumentResultWrapper<E>` | 조건에 맞는 문서(이력 포함) |
| `findRecentHits(SimpleQuery<SearchDocDTO>)` | ✅ | `DocumentResultWrapper<E>` | 조건 + 최신본만 |
| `findAllHits()` | | `DocumentResultWrapper<E>` | 조건 없이 인덱스 전체 |
| `findRecentAllHits()` | ✅ | `DocumentResultWrapper<E>` | 조건 없이 최신본 전체 |
| `findDocById(id)` | | `E` | `_id` 단건 |
| `findRecentDocById(id)` | | `DocumentResultWrapper<E>` | `_id` ids 쿼리 |
| `findRecentDocByRecentId(recentId)` | ✅ | `E` | 논리 키 + `recent=true` 단건 |
| `findAllDocsBySearchAfter(SimpleQuery<SearchDocDTO>)` | | `List<E>` | search_after 로 전량 순회 |
| `findAllRecentDocsBySearchAfter(SimpleQuery<SearchDocDTO>)` | ✅ | `List<E>` | 최신본 전량 순회 |

> `findAllHits()` 는 조건 없는 전체 조회이고 기본 상한이 있다(`SearchDocDTO.size` 기본 10000).
> **대량 전량 수집은 `findAll*BySearchAfter` 또는 composite 를 쓴다.**

### 1.2 집계 (aggregate) — `MainGroupDTO`

| 메서드 | recent | 형태 |
|--------|:---:|------|
| `aggregate` / `aggregateRecent` | / ✅ | `terms` group by |
| `aggregateCount` / `aggregateRecentCount` | / ✅ | count 계열 |
| `aggregateSum` / `aggregateRecentSum` | / ✅ | sum 계열 |
| `aggregateByDay` / `aggregateRecentByDay` | / ✅ | `date_histogram` 1일 |
| `aggregateByWeek` / `aggregateRecentByWeek` | / ✅ | `date_histogram` 1주 |
| `aggregateByMonth` / `aggregateRecentByMonth` | / ✅ | `date_histogram` 1개월 |

`date_histogram` 계열은 `minDocCount(0)` 이라 **문서가 없는 구간도 0으로 채워 나온다**(차트용).

### 1.3 카디널리티 집계 — `SingleValueGroupDTO`

| 메서드 | recent | 형태 |
|--------|:---:|------|
| `aggregateCardinalityByDay` / `aggregateRecentCardinalityByDay` | / ✅ | `date_histogram(mainField)` + `cardinality(subField)` |

요청 DTO는 `AggregationCardinalityRequestDTO`(단일 `SubGroupFieldDTO`)를 쓰고, 프레임워크가
내부적으로 `CardinalityLeaves` 를 세팅한다.

### 1.4 Composite 집계 — `CompositeGroupDTO`

| 메서드 | recent | 반환 | 용도 |
|--------|:---:|------|------|
| `compositeHits` / `compositeRecentHits` | / ✅ | `CompositeAggregationResultWrapper<E>` | 단일 페이지 |
| `compositeAllHits` / `compositeRecentAllHits` | / ✅ | `CompositeAggregationResultWrapper<E>` | `after_key` 가 null 될 때까지 전체 순회 |
| `compositeAggregation` / `compositeAggregationRecent` | / ✅ | `DocumentAggregations` | 버킷만 필요할 때 |

**terms 와 composite 선택 기준**

| | terms | composite |
|---|---|---|
| 목적 | Top N | 전체 버킷 순회 |
| 정렬 | doc_count | key |
| 페이지네이션 | 불가 | `after_key` 로 가능 |
| 정확성 | 일부 누락 가능 | 전량 |
| 다중 필드 group by | 제한적 | 강력 |

→ **전체 통계·배치성 집계는 composite.** terms 로 전량을 뽑으려고 `size` 를 키우면 OpenSearch 메모리를 때린다.

### 1.5 쓰기·인덱스 운영

| 메서드 | 설명 |
|--------|------|
| `save(E)` / `saveAll(Iterable<E>)` | `@ElasticSearchIndex` 가 있으면 recent 전환 포함 저장, 없으면 단순 저장 |
| `saveEmpty(E)` | recent 처리 없이 롤링 인덱스에 그대로 저장 |
| `modifyWithIndexName(E, indexName)` | 인덱스를 지정해 저장(수정) |
| `deleteById` / `deleteRecentDocById` / `deleteAll` / `deleteAllById` | 삭제 |
| `indexAliasName()` | 엔티티의 인덱스(별칭) 이름 |
| `deleteIndex(int days)` / `deleteIndex(Map)` / `merge(int day)` / `reindex(Map)` | 인덱스 운영 |
| `catIndexVOList()` / `indexAllCount()` | `_cat/indices` 조회 · 전체 건수 |

---

## 2. `SimpleQuery` 조립 — 쿼리를 만드는 유일한 방법

### 2.1 시작 (정적 팩토리)

용도별로 시작점이 다르다. 반환 제네릭이 그대로 Wrapper 메서드의 입력 타입을 결정한다.

```java
SimpleQuery.search(SearchRequestDTO)                       // → SimpleQuery<SearchDocDTO>      find* 용
SimpleQuery.aggregation(AggregationRequestDTO)             // → SimpleQuery<MainGroupDTO>      aggregate* 용
SimpleQuery.aggregation(AggregationCardinalityRequestDTO)  // → SimpleQuery<SingleValueGroupDTO>
SimpleQuery.composite(CompositeRequestDTO)                 // → SimpleQuery<CompositeGroupDTO> composite* 용
```

조건만으로 시작하는 단축 팩토리(모두 `SimpleQuery<SearchDocDTO>`):

```java
SimpleQuery.matchAllQueryMust()
SimpleQuery.termQueryFilter(key, value)      SimpleQuery.termsQueryFilter(key, List)
SimpleQuery.termQueryMust(key, value)        SimpleQuery.termQueryMustNot(key, value)
SimpleQuery.termsQueryMustNot(key, List)
SimpleQuery.matchQueryFilter(key, value|List)
SimpleQuery.existsQueryFilter(key)           SimpleQuery.existsQueryMustNot(key)
SimpleQuery.rangeQueryFilter(RangeQueryFilter)
SimpleQuery.wildQueryQueryFilter(key, value[, caseInsensitive])
SimpleQuery.queryStringFilter(key)           SimpleQuery.queryStringMust(QueryStringMust)
SimpleQuery.moreLikeThisMust(String[] texts, String[] fields)
```

### 2.2 조건 추가 (`and*` 체이닝)

```java
.andTermQueryFilter(k, v)      .andTermsQueryFilter(k, List)
.andTermQueryMust(k, v)        .andTermQueryMustNot(k, v)     .andTermsQueryMustNot(k, List)
.andMatchQueryFilter(k, v|List)
.andExistsQueryFilter(k)       .andExistQueryMustNot(k)
.andRangeQueryFilter(RangeQueryFilter.of("@timestamp").betweenDate("now-3M/d", "now/d+1d"))
.andWildCardQueryFilter(k, v[, caseInsensitive])
.andQueryStringFilter(k)       .andQueryStringMust(QueryStringMust)
.andMoreLikeThisMust(texts, fields)
```

`should`(OR) · 정렬 · 하이라이트:

```java
.withMultiMatchQueryShould(MultiMatchQueryShould::defaultFuzzy, "키워드1", "키워드2")
.withMultiMatchQueryShouldAtLeastOne(MultiMatchQueryShould::defaultFuzzy, keywords)   // + minimum_should_match(1)
.minimumShouldMatch(1)
.orderBy(SortDTO.builder().field("@timestamp").sortType("desc").build())
.highlight(esHighlightQuery)
```

`MultiMatchQueryShould.defaultFuzzy(keyword)` = 전체 필드(`*`) + `fuzziness AUTO` + `lenient true` + `BEST_FIELDS`.

### 2.3 `RangeQueryFilter` 의 null 관용 동작 — 알아둘 것

`lt/lte/gt/gte/from/to/betweenDate` 에 **null 이나 빈 문자열을 넣으면 필터 자체가 무효화(null)** 된다.
즉 "값이 없으면 범위 조건을 걸지 않는다" 가 기본 동작이다. 조건을 반드시 걸어야 하는 자리에서는
호출 전에 값을 검증한다. `betweenDate(from, to)` 는 한쪽만 주면 `gte` 또는 `lte` 단방향으로 동작한다.

### 2.4 기본값 주의

| DTO | 필드 | 기본값 |
|-----|------|--------|
| `SearchRequestDTO` | `size` | **10** |
| `SearchDocDTO` (내부) | `size` | **10000** |
| `AggregationRequestDTO` | `size` | 10000 |
| `SubGroupFieldDTO` | `size` | 10000 |
| `CompositeRequestDTO` | `size` / `hitSize` | 10000 / 1 |

`SimpleQuery.search(SearchRequestDTO)` 경로는 **size 기본이 10** 이다. 많이 받아야 하면 명시적으로 설정한다.

---

## 3. 서브 집계 4종 — 타입이 모양을 결정한다

`AggregationRequestDTO.builder().subAgg(...)` 에 넣는다. 기본값은 `NestedPath.empty()`.

| 타입 | 모양 | 예 |
|------|------|-----|
| `NestedPath.of(a, b, c)` | **순서 있는 중첩 체인** a→b→c (드릴다운) | 심각도별 → 우선순위별 → 담당자별 |
| `Dimensions.of(a, b, c)` | **순서 없는 병렬 sibling** (독립 분포) | 담당자 분포, 우선순위 분포를 한 번에 |
| `MetricLeaves.of(a, b)` | 각 필드에 avg/max/min/sum 부착(리프) | `avg_by_*`, `max_by_*`, `min_by_*`, `sum_by_*` |
| `CardinalityLeaves.of(field)` | 단일 필드 cardinality(리프) | 고유값 수 |

```java
AggregationRequestDTO.builder()
    .mainField("assignee.assignee_displayName.keyword")
    .mainFieldAlias("assignee")
    .subAgg(NestedPath.of(
        SubGroupFieldDTO.builder().subField("status.status_name.keyword").subFieldAlias("status").build()
    ))
    .build();
```

- 별칭 생략 시 자동 별칭은 `group_by_<subField>` (Metric 은 `avg_by_<alias>` 등).
- **리프(`MetricLeaves`/`CardinalityLeaves`) 아래에는 더 붙지 않는다.**

---

## 4. 집계 결과 읽기 — `DocumentAggregations` / `DocumentBucket`

```java
DocumentAggregations aggs = wrapper.aggregateRecent(query);

aggs.getTotalHits();     // 전체 매칭 문서 수 (버킷 기반 생성자면 -1)
aggs.getDocSumCount();   // 최상위 버킷 doc_count 합
aggs.docBuckets();       // 최상위 버킷 목록 (계층 유지)
aggs.deepestList();      // 최하위 버킷만 평평하게 — 대부분 이것을 쓴다
aggs.allSearchHits();    // top_hits 가 섞인 경우의 원시 hit
aggs.toEntities(converter, Clazz.class);   // hit → 엔티티 변환
```

`deepestList()` 로 얻은 버킷에서 값을 꺼낼 때:

```java
String v = bucket.valueByName("aliasName");     // 자기 또는 조상 버킷의 키 문자열
Object o = bucket.objectByName("aliasName");    // 원시 키 객체 (날짜 히스토그램 등)
Long   c = bucket.countByName("aliasName");     // 해당 레벨의 doc_count
Float  f = bucket.floatCountByName("aliasName");// sum/avg 등 소수 메트릭
```

**동작 원리:** `deepestList()` 가 순회하면서 각 버킷에 부모 포인터를 심는다. `valueByName(alias)` 는
자기 `groupKey` 가 alias 와 같으면 자기 값을, 아니면 부모로 거슬러 올라가 찾는다.
→ **alias 는 `mainFieldAlias`/`subFieldAlias` 로 지정한 이름과 정확히 일치해야 한다.** 오타는 빈 문자열/0 을 낸다.

> `valueByName`/`countByName` 을 쓰지 않을 거면 alias 를 아예 지정하지 않는다(코딩 표준).

---

## 5. 검색 결과 읽기 — `DocumentResultWrapper<E>`

```java
DocumentResultWrapper<WikiEntity> hits = wrapper.findRecentHits(query);
List<SearchHit<WikiEntity>> raw = hits.toHitDocs();   // _id · _index · score 가 필요할 때
// hit.getContent() 로 엔티티, hit.getId()/getIndex()/getScore() 로 메타
```

점수·인덱스명·하이라이트가 필요하면 `toHitDocs()` 로 `SearchHit` 을 직접 다룬다
(`api/ai/search/WikiSearchServiceImpl` 이 표준 예시).

---

## 6. recent 저장 로직 (`RecentFieldConvertor`) — 왜 이렇게 동작하는지

`@ElasticSearchIndex` 가 붙은 엔티티를 `save`/`saveAll` 할 때:

1. 저장 대상들의 `@RecentId` 값으로 기존 `recent=true` 문서를 한 번에 조회한다.
2. **기존 최신본과 새 엔티티가 `equals` 로 동일하면 저장하지 않는다**(no-op).
   → `AlmIssueEntity` 는 `@EqualsAndHashCode(exclude = {"recent","rawData"})` 라서
   `recent`·`rawData` 를 제외한 내용이 같으면 중복 색인되지 않는다.
3. 다르면 새 문서에 `recent=true` 를 세팅하고, 기존 문서들은 `recent=false` 로 내려쓴다.
4. 저장 위치는 `@RollingIndexName` 메서드가 만든 접미사가 붙은 인덱스(`jiraissue-2026-03-25`).

**함의**
- 엔티티에 필드를 추가하면 `equals` 비교 대상이 바뀌어 중복 판정이 달라진다. 변경 이력에 영향 없는
  필드(캐시·임시값)는 `@EqualsAndHashCode(exclude=...)` 에 넣을지 판단한다.
- `saveEmpty` 는 recent 전환을 건너뛴다. 이력 보존이 필요 없는 적재에만 쓴다.
