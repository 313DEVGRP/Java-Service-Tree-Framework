# TreeFramework 상세

경로: `src/main/java/com/arms/egovframework/javaservice/treeframework/`

egovFramework 계열 이름을 쓰지만 **이 저장소 안의 자체 구현**이다. 외부 라이브러리가 아니므로
소스가 곧 스펙이다. 58개 컨트롤러 · 61개 서비스 · 78개 엔티티가 여기에 매달려 있다.

---

## 1. 클래스 지도

```
controller/
  TreeAbstractController<T extends TreeService, D extends TreeBaseDTO, V extends TreeSearchEntity>
  CommonResponse                      ApiResult<T>{success, response, error} / ApiError{message, errorCode, status}
service/
  TreeService                         인터페이스 (13개 메서드)
  TreeServiceImpl                     @Service("treeService") · 모든 도메인 ServiceImpl 의 부모
dao/
  TreeDao / TreeDaoImpl               @Repository("treeDao") · ThreadLocal<Class<T>> clazz
  TreeAbstractDao extends HibernateDaoSupport   (787줄, HibernateTemplate + DetachedCriteria)
model/
  TreeBaseEntity                      @MappedSuperclass · 트리 공통 컬럼 + 다수의 @Transient 계산 필드
  TreePaginatedEntity extends ...     페이징 파라미터 (pageIndex/pageUnit/pageSize/firstIndex/lastIndex)
  TreeSearchEntity extends ...        Criteria 빌더 (setWhere/setWhereLike/setWhereIn/setOrder...)
  TreeBaseDTO                         c_id · ref · c_position · c_title · c_type · copy · multiCounter
  TreeLogBaseEntity                   _LOG 테이블용 (c_method/c_state/c_date)
interceptor/
  RouteTableInterceptor               Hibernate EmptyInterceptor — SQL 테이블명 치환 (별도 문서 참조)
  SessionUtil                         RequestContextHolder 래퍼
errors/
  exception/  BaseException · EntityNotFoundException · IDNotFoundException ·
              DuplicateFoundException · InvalidParamException · ServiceProcessException · TreeDaoException
  response/   ErrorCode(enum) · ErrorControllerAdvice(@ControllerAdvice)
excel/        ExcelDown · ExcelStreamDown · ExcelRead(Wrapper) · ExcelPoiFactory · 애노테이션 3종
validation/
  group/      AddNode · UpdateNode · RemoveNode · AlterNode · AlterNodeType · MoveNode · GetChildNode · SearchNode
  custom/constraints/Contained
remote/       Chat · Global · User · ScriptSessionManager   (DWR 실시간 푸시)
util/         DateUtils · StringUtils · PaginationInfo · ParameterParser · EgovFileUploadUtil · …
TreeConstant  ROOT_CID=1 · First_Node_CID=2 · ROOT_TYPE="root" · First_Node_TYPE="drive"
              · Branch_TYPE="folder" · Leaf_Node_TYPE="default"
              · REQADD_PREFIX_TABLENAME="T_ARMS_REQADD_" · REQSTATUS_PREFIX_TABLENAME="T_ARMS_REQSTATUS_"
```

---

## 2. nested-set 모델

| 컬럼 | 의미 | 규칙 |
|------|------|------|
| `c_id` | PK | `GenerationType.IDENTITY` (엔티티가 `getC_id()` 오버라이드로 지정) |
| `c_parentid` | 부모 c_id | 루트는 0 |
| `c_position` | 형제 내 순서 | 0부터 |
| `c_left` / `c_right` | nested-set 경계 | **직접 쓰지 않는다** |
| `c_level` | 깊이 | 루트 0 |
| `c_title` | 노드명 | `Util_TitleChecker.StringReplace()` 로 정제 후 저장 |
| `c_type` | `root` / `drive` / `folder` / `default` | `TreeConstant.isCType()` 로 검증 |

모든 트리 테이블은 **고정 루트 2행**으로 시작한다(`DynamicDBMakerDao.xml` 의 `dmlOrgExecute1/2`):

```
c_id=1  parent=0  pos=0  left=1 right=4 level=0  'REQADD Table'  type='root'
c_id=2  parent=1  pos=0  left=2 right=3 level=1  '요구사항'       type='drive'
```

그래서 `ReqAddImpl` 의 `ROOT_REF = 2L` — 실제 요구사항은 c_id=2 밑에 붙는다.
목록 조회 시 `Restrictions.not(Restrictions.in("c_id", {ROOT_CID, First_Node_CID}))` 로 이 2행을 제외한다
(`getNodesWithoutRoot` 가 이미 해 준다).

`c_type` 규칙:
- `addNode` 는 부모(`ref`)의 타입이 `default`(리프)면 **`RuntimeException("nodeByRef is default Type")`**.
- `alterNodeType` 으로 `folder` → `default` 로 바꿀 때 자식이 있으면 예외.

---

## 3. `TreeServiceImpl` 메서드별 실제 동작

| 메서드 | 트랜잭션 | 핵심 동작 / 함정 |
|--------|---------|-----------------|
| `getNode(T)` | readOnly | `c_id` 로 unique 조회. **없으면 `TreeDaoException`** (null 아님) |
| `getChildNode(T)` | readOnly | `Order.desc("c_id")` 를 **내부에서 추가**한다. 호출부 정렬과 함께 누적됨 |
| `getChildNodeWithoutPaging(T)` | readOnly | 페이징 없이 전량. 대량 트리에 주의 |
| `getPaginatedChildNode(T)` | readOnly | `getCount` → `PaginationInfo` 세팅 → `getPaginatedList`. 기본 `pageUnit=1000` |
| `getNodesWithoutRoot(T)` | readOnly | c_id 1·2 제외 후 `getChildNode` |
| `getNodesWithoutRootMap(T,key,value)` | readOnly | 위 결과를 `Collectors.toMap`. **key 중복이면 예외** |
| `searchNode(T)` | — | `"#node_" + c_id` 문자열 리스트를 반환 (jsTree 용) |
| `addNode(T)` | `SERIALIZABLE`, rollbackFor=Exception | `ref` 로 부모 조회 → 자식 수로 `c_position` → `stretchLeft/Right` 로 전역 left/right 이동 → insert |
| `updateNode(T)` | (클래스 기본) | **비어있지 않은 필드만** 복사. `fieldsToAlwaysUpdate` 4개만 예외. `merge` + `update` |
| `updateField(T, "필드명")` | — | 그 필드 **하나만** 강제 복사. null 도 반영됨 → **값을 비워야 할 때 이걸 쓴다** |
| `overwriteNode(to, from)` | `SERIALIZABLE` | `from` 의 비어있지 않은 필드를 `to` 에 반영 |
| `removeNode(T)` | `SERIALIZABLE` | `c_left..c_right` 범위 노드를 **전부 삭제**(하위 포함) 후 오른쪽 노드들의 left/right 를 `spaceOfTargetNode` 만큼 감소 |
| `alterNode(T)` | — | `c_title` 만 변경 + `setFieldFromNewInstance()` 훅 호출 |
| `alterNodeType(T)` | — | `c_type` 변경. folder→default 시 자식 있으면 예외 |
| `moveNode(T, request)` | `SERIALIZABLE` | copy(1)/move(0) 분기. left/right/level 재계산. `multiCounter` 로 다중 선택 이동 |

> **`updateNode` 로는 값을 지울 수 없다.** 이 제약을 우회하는 정상 경로는
> ① `updateField(entity, "필드명")` 을 쓰거나, ② 도메인 ServiceImpl 에 전용 update 를 만드는 것이다.
> `TreeServiceImpl.fieldsToAlwaysUpdate` 에 필드를 추가하는 것은 **전역 영향**이므로 승인 대상이다.

### `setFieldFromNewInstance` 훅

`TreeSearchEntity` 의 **abstract** 메서드라 모든 엔티티가 구현해야 한다. `alterNode`·copy 경로에서 불린다.
대부분의 도메인은 복사 시 제목에 `copy_` 를 붙이는 정도만 한다:

```java
@Override
public <T extends TreeSearchEntity> void setFieldFromNewInstance(T paramInstance) {
    if (paramInstance instanceof TreeBaseEntity) {
        if (paramInstance.isCopied()) {
            this.setC_title("copy_" + this.getC_title());
        }
    }
}
```

---

## 4. DAO 계층

`TreeDaoImpl` 은 **싱글턴 빈 하나**이고, 대상 엔티티 타입을 `ThreadLocal<Class<T>>` 로 들고 있다.

```java
treeDao.setClazz(treeSearchEntity.getClass());   // 모든 작업 앞에 필수
treeDao.getCurrentSession().setCacheMode(CacheMode.IGNORE);
```

- `setClazz` 를 빼먹으면 **직전에 그 스레드가 쓰던 엔티티 타입**으로 쿼리가 나간다. 증상이 기괴하다.
  (과거 필드 공유 버그 → ThreadLocal 로 수정: commit `1cde27a5`)
- `@Async`·스레드풀 재사용 스레드에는 이전 값이 남는다. `ThreadLocal.remove()` 는 호출되지 않는다.
- `TreeAbstractDao` 는 `HibernateDaoSupport` + `HibernateTemplate` + `DetachedCriteria` 조합이다.
  `EntityManager`·`JpaRepository`·JPQL 은 여기서 쓰지 않는다.
- 주요 메서드: `getUnique(Long)` / `getUnique(Criterion)` / `getUnique(T)` / `getList` /
  `getListWithoutPaging` / `getPaginatedList` / `getCount` / `insert` / `update` / `merge` / `delete` / `refresh`.
- **조회 실패 = 예외**: `getUnique(Long)` 는 `TreeDaoException("...returnObj is null")`,
  `getUnique(Criterion)` 은 `TreeDaoException(...findByCriteria result is null)`.
  Optional 이 필요하면 `TreeServiceUtils.getNodeOptional(service, cId, Clazz.class)` 를 쓴다.

---

## 5. `TreeSearchEntity` 검색 API

```java
setWhere(String prop, Object value)      // value 가 String 이면 * 패턴 해석, 아니면 eq
setWhereLike(String prop, String str)    // 앞뒤에 * 를 붙여 setWhere 호출 → LIKE %str%
setWhere(Criterion)                      // 임의 Criterion 추가
setWhereOr(Criterion...)                 // Disjunction
setWhereBetween(prop, lo, hi)
setWhereIn(prop, Collection|Object[])
setWhere(Projection)                     // 집계 프로젝션
setOrder(Order)                          // ★ 내부적으로 list.add — 누적된다
getCriterions()                          // 직접 add 도 가능
```

`setWhere` 의 문자열 해석 규칙(주의):

| 입력 | 해석 |
|------|------|
| `"*abc*"` | `LIKE %abc%` |
| `"*abc"` | `LIKE %abc` (MatchMode.END) |
| `"abc*"` | `LIKE abc%` (MatchMode.START) |
| `"isNotNull..."` 로 시작 | `IS NOT NULL` |
| 그 외 | `= "abc"` |
| `""` (빈 문자열) | **조건이 추가되지 않는다** (조용히 무시) |
| `null` | **조건이 추가되지 않는다** |

→ 사용자 입력에 `*` 나 `isNotNull` 이 섞이면 의도치 않은 쿼리가 된다. 검증 후 넘긴다.

페이징 기본값(`TreePaginatedEntity`): `pageIndex=1`, `pageUnit=1000`, `pageSize=10`,
`firstIndex=0`, `lastIndex=9999`, `recordCountPerPage=10`.

---

## 6. `TreeAbstractController` 가 주는 것

`@PostConstruct initialize()` 에서 `setTreeService(...)` · `setTreeEntity(...)` 를 **반드시** 호출한다.
이 두 필드는 private 이고 생성자 주입이 아니다 — 빠뜨리면 상속 엔드포인트가 전부 NPE 다.

| 엔드포인트 | 메서드 | 검증 그룹 | 비고 |
|-----------|--------|----------|------|
| `/getNode.do` | GET | — | `c_id <= 0` 이면 예외 |
| `/getChildNode.do` | GET | — | `c_parentid = c_id` 로 조회, `Order.desc(c_position)` |
| `/getNodesWithoutRoot.do` | GET | — | `{paginationInfo, result}` 맵 반환 |
| `/getPaginatedChildNode.do` | GET | — | `{paginationInfo, result}` 맵 반환 |
| `/searchNode.do` | GET | — | ⚠️ `parser.get("parser")` 오타로 **검색어가 전달되지 않는다** |
| `/addNode.do` | POST | `AddNode` | `ref`, `c_position`, `c_title`, `c_type` |
| `/removeNode.do` | DELETE | `RemoveNode` | 하위 노드 포함 삭제 |
| `/updateNode.do` | PUT | `UpdateNode` | 부분 업데이트 |
| `/alterNode.do` | PUT | `AlterNode` | 제목 변경 |
| `/alterNodeType.do` | PUT | `AlterNodeType` | 타입 변경 |
| `/moveNode.do` | POST | `MoveNode` | `ref`, `c_position`, `copy`, `multiCounter` |
| `/analyzeNode.do` | GET | — | 스텁 (항상 `"true"`) |
| `/getMonitor.do` | GET | — | 전체 자식 목록 |
| `/send-message` | GET | — | DWR 브로드캐스트 |

DTO→Entity 변환은 `modelMapper.map(treeBaseDTO, treeEntity)` 로 이뤄진다.
**필드명이 다르면 조용히 매핑되지 않는다** — DTO와 Entity의 필드명을 동일하게 맞춘다.

> 동적 테이블 도메인(`reqAdd`/`reqStatus`/`wiki`)은 이 상속 엔드포인트를 **그대로 쓰면 안 된다.**
> 경로에 `{changeReqTableName}` 이 없어서 라우팅이 성립하지 않기 때문에, 각 컨트롤러가
> `/{changeReqTableName}/getNode.do` 같은 **오버라이드 엔드포인트를 따로 정의**한다.

---

## 7. 새 트리 도메인 추가 절차

1. 패키지 생성: `com/arms/api/<domain>/{controller,service,model}`
2. `assets/tree-domain-template/` 의 5개 파일을 복사해 이름 치환
3. `@Service("<domain>")` 이름 지정 빈으로 등록 — 컨트롤러는 `@Qualifier("<domain>")` 로 주입
4. Flyway `V<다음번호>__*.sql` 에 본 테이블 + `_LOG` 테이블 + 트리거 3종 + **루트 2행 seed**
5. 컨트롤러 `@RequestMapping` 은 `/arms/<domain>` (권한 prefix 금지, §SKILL.md 8)
6. `JAVA_HOME`=JDK11 로 `./gradlew compileJava`

별도 등록 파일은 없다 — `context-common.xml` 의 `<context:component-scan base-package="com.arms">`
(Service/Repository) + Boot 의 `@SpringBootApplication` 스캔(Controller)이 자동으로 잡는다.
