---
description: Auto-Code(Telosys) 생성 규약대로 Backend-Core 에 트리 도메인 한 벌(Entity·DTO·Service·Impl·Controller·Flyway)을 생성한다
argument-hint: "[EntityName] [--domain <pkg>] [--table <T_ARMS_X>] [--fields \"c_a:string:설명, c_b:text:비고\"] [--with-dao] [--non-tree] [--dry-run]"
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(git config:*), Bash(ls:*), Bash(find:*), Bash(cat:*), Bash(sed:*), Bash(./gradlew compileJava), Bash(gradlew.bat compileJava), AskUserQuestion
---

# ARMS Auto-Code — Backend-Core 도메인 생성

`Java-Service-Tree-Framework-Auto-Code` 의 Telosys 템플릿 계약을 **현재 Backend-Core 규약으로 옮겨서**
트리 도메인 한 벌을 생성한다. 사용자 입력: `$ARGUMENTS`

---

## 0. 먼저 알아야 할 것 — 왜 Telosys 를 직접 돌리지 않는가

`Auto-Code/TelosysTools/templates/JSTF-template/*.vm` 는 **2024-01 기준**이고,
현재 `Java-Service-Tree-Framework-Backend-Core` 와 아래가 어긋난다. 그대로 생성하면 **컴파일되지 않는다.**

| 항목 | Auto-Code 템플릿 | Backend-Core 현재 | 이 command 의 처리 |
|------|-----------------|------------------|-------------------|
| 패키지 | `com.arms.<entity>.{controller,dao,model,service}` | `com.arms.api.<domain>.{controller,model,service}` | `api` 세그먼트를 넣는다 |
| TreeFramework import | `com.egovframework.javaservice.treeframework.*` | **`com.arms.`** `egovframework.javaservice.treeframework.*` | `com.arms.` 접두를 붙인다 |
| DDL 산출물 | `${RES}/com/arms/db/<Name>_Database.sql` | Flyway `V<n>__*.sql` (같은 폴더) | 다음 버전 번호를 자동 계산 |
| DDL 스키마 | `` `aRMS`. `` 하드코딩 · `DELIMITER $$` | 스키마 접두 없음 · `DROP TRIGGER IF EXISTS` | 스키마 접두 제거, 멱등 트리거 |
| Controller | `@Controller` + `@RestController` 동시 + `@AllArgsConstructor` + `@Autowired`+`@Qualifier` 중복 | `@Controller` + `@RequiredArgsConstructor` + 메서드별 `@ResponseBody` | 현재 규약을 따른다 |
| INSERT 트리거 | `c_method='update'`(오기) | — | `'insert'` 로 바로잡는다 |
| 루트 seed | 2행 중 하나가 `'제품(서비스)'` 로 하드코딩 | 도메인마다 다름 | 파라미터로 받는다 |
| 도메인 컬럼 | **템플릿이 `.entity` 필드를 무시한다** (빈 스켈레톤만 생성) | 컬럼이 있어야 쓸모가 있음 | `--fields` 로 받아 실제 생성 |
| 빈 이름·URL | `$entity0toLowerCase` = **마지막 non-key 필드명** (엔티티명이 아님 — 잠재 버그) | camelCase(엔티티명) | 엔티티명에서 유도 |
| dao 계층 | 항상 생성(`JpaRepository` + `Repository`) | 19개 도메인 중 `globaltreemap` **하나만** 사용 | 기본 미생성, `--with-dao` 로 선택 |
| 작성자 | `Dongmin.lee` 하드코딩 | — | `git config user.name` 기본 |

> 이 표는 생성 결과를 사용자에게 보고할 때 근거로 쓴다. Auto-Code 저장소는 **읽기 전용 참조**다 — 절대 수정하지 않는다.

상세 규약은 `arms-backend-core` 스킬이 정본이다. **생성 전에 그 스킬을 먼저 읽는다.**

---

## 1. 파라미터

### 1.1 필수

| 파라미터 | 형식 | 설명 | Auto-Code 대응 |
|----------|------|------|----------------|
| `EntityName` | PascalCase | 도메인 엔티티 이름. 모든 클래스명의 어근 | `.entity` 파일의 엔티티명 (`${BEANNAME}`) |

### 1.2 선택 (미지정 시 아래 기본값을 쓰고, 무엇을 썼는지 보고한다)

| 파라미터 | 기본값 | 설명 | Auto-Code 대응 |
|----------|--------|------|----------------|
| `--domain <pkg>` | `lowercase(EntityName)` | `com.arms.api.<pkg>` 패키지 세그먼트. `_` 허용(`product_service` 처럼 중첩도 가능) | `${BEANNAME_LC}` |
| `--bean <name>` | `camelCase(EntityName)` | `@Service("...")` 빈 이름 · `@Qualifier` · URL 세그먼트 | `$entity0toLowerCase` |
| `--table <name>` | `T_ARMS_` + `UPPER_SNAKE(EntityName)` | 테이블명. `_LOG` 짝 테이블은 여기에 `_LOG` | `T_ARMS_${BEANNAME_UC}` |
| `--fields "..."` | 없음 (컬럼 없는 순수 트리) | `이름:타입:주석` 을 `,` 로 구분. 타입은 `string`(varchar 255) · `text` · `long` · `int` · `date` · `datetime` · `boolean` | `.entity` 의 필드 선언 |
| `--url <path>` | `/arms/<bean>` | `@RequestMapping` 값 | `/arms/$entity0toLowerCase` |
| `--seed "<root>,<first>"` | `"<table> Table,<EntityName>"` | 루트 2행(`c_id=1` root / `c_id=2` drive)의 `c_title` | DDL 템플릿 하드코딩 |
| `--flyway <n>` | 자동 계산 | Flyway 버전 번호 | (Auto-Code 에 없음) |
| `--author <name>` | `git config user.name` | 헤더 주석 `@author` | `java_header.vm` 하드코딩 |
| `--with-dao` | off | `<Name>JpaRepository` + `<Name>Repository` 를 `dao/` 에 추가 | `Dao_java.vm` · `DaoImpl_java.vm` |
| `--non-tree` | off (트리) | 트리가 아닌 일반 도메인. 네이밍이 `<Name>Service`/`<Name>ServiceImpl` 로 바뀌고 Entity·Flyway 규약이 달라진다 | (Auto-Code 에 없음 — 트리 전용) |
| `--dry-run` | off | 파일을 쓰지 않고 생성 계획만 출력 | (Auto-Code 에 없음) |

### 1.3 필드 타입 매핑

| `--fields` 타입 | Java | JPA 어노테이션 | DDL |
|----------------|------|---------------|-----|
| `string` | `String` | `@Column(name="...")` | `varchar(255)` |
| `text` | `String` | `@Column(name="...")` + `@Type(type="text")` | `text` |
| `long` | `Long` | `@Column(name="...")` | `bigint(20)` |
| `int` | `Integer` | `@Column(name="...")` | `int(11)` |
| `date` | `String` | `@Column(name="...")` | `date` |
| `datetime` | `String` | `@Column(name="...")` | `datetime` |
| `boolean` | `String` | `@Column(name="...")` | `varchar(1)` (`'Y'`/`'N'` 관례) |

컬럼명은 **`c_` 접두**가 이 저장소의 규약이다. `--fields` 에 `c_` 없이 주면 붙여서 쓰고 그 사실을 보고한다.

---

## 2. 파라미터 수집 절차

1. `$ARGUMENTS` 를 파싱한다. **`EntityName` 이 없으면** `AskUserQuestion` 으로 묻지 말고,
   무엇이 필요한지 한 줄로 안내하고 종료한다(이름 없이는 아무것도 못 만든다).
2. `EntityName` 만 있고 나머지가 비면 **기본값으로 진행하되**, 아래 2가지는
   기본값이 결과를 크게 바꾸므로 `AskUserQuestion` 으로 한 번에 확인한다.
   - **도메인 컬럼**: `--fields` 가 없을 때 — "컬럼 없는 순수 트리로 생성" vs "컬럼을 입력하겠다"
   - **dao 계층**: `--with-dao` 가 없을 때는 묻지 않는다(기본 미생성이 압도적 관례).
     단 사용자가 "JPA" · "Repository" 를 언급했으면 켠다.
3. 나머지는 묻지 않는다. 기본값을 쓰고 **§6 보고에 전부 명시**한다.

---

## 3. 착수 전 검증 게이트 (하나라도 실패하면 생성하지 않고 보고한다)

```
① 스킬 로드        : arms-backend-core 스킬을 읽었는가
② 이름 충돌        : src/main/java/com/arms/api/<domain>/ 가 이미 있는가
                     → 있으면 중단. 덮어쓰기는 사용자가 명시적으로 요청할 때만
③ 클래스 충돌      : <Name>Entity / <Name>DTO / <Name>Controller 가 저장소 어디에든 있는가
                     → Glob 으로 확인. 있으면 패키지가 달라도 경고한다
④ 테이블 충돌      : src/main/resources/com/arms/db/*.sql 에 해당 테이블 CREATE 가 있는가
⑤ Flyway 번호      : ls src/main/resources/com/arms/db/ | grep -oE '^V[0-9]+' 의 최댓값 + 1
                     → 결번(V33~V36, V41)은 채우지 않는다. 항상 최댓값 다음을 쓴다
⑥ 예약어           : 컬럼명이 트리 공통 컬럼(c_id, c_parentid, c_position, c_left,
                     c_right, c_level, c_title, c_type, c_method, c_state, c_date)과 겹치는가
                     → 겹치면 중단. TreeBaseEntity 가 이미 갖고 있다
⑦ 작성자           : git config user.name 이 비었으면 --author 를 요구한다
```

---

## 4. 생성 아티팩트

`--dry-run` 이면 아래 경로·내용 요약만 출력하고 파일을 쓰지 않는다.

| # | 산출물 | 경로 | Auto-Code 템플릿 |
|---|--------|------|-----------------|
| 1 | `<Name>Entity.java` | `src/main/java/com/arms/api/<domain>/model/` | `Entity_java.vm` |
| 2 | `<Name>DTO.java` | `src/main/java/com/arms/api/<domain>/model/` | `DTO_java.vm` |
| 3 | `<Name>.java` (비트리: `<Name>Service.java`) | `src/main/java/com/arms/api/<domain>/service/` | `Service_java.vm` |
| 4 | `<Name>Impl.java` (비트리: `<Name>ServiceImpl.java`) | `src/main/java/com/arms/api/<domain>/service/` | `ServiceImpl_java.vm` |
| 5 | `<Name>Controller.java` | `src/main/java/com/arms/api/<domain>/controller/` | `Controller_java.vm` |
| 6 | `V<n>__add_<snake>_table.sql` | `src/main/resources/com/arms/db/` | `DDL_DML_sql.vm` |
| 7 | `<Name>JpaRepository.java` *(--with-dao)* | `src/main/java/com/arms/api/<domain>/dao/` | `Dao_java.vm` |
| 8 | `<Name>Repository.java` *(--with-dao)* | `src/main/java/com/arms/api/<domain>/dao/` | `DaoImpl_java.vm` |

기준 형태는 `arms-backend-core` 스킬의 `assets/tree-domain-template/` 이다.
**그 템플릿을 베끼고 이름·컬럼만 치환한다.** 새 구조를 발명하지 않는다.

### 4.1 반드시 지킬 것

- 모든 `.java` 파일 맨 위에 313 DEV GRP 헤더 주석(`@author` · `@since` · `@version`).
  `@since` 는 오늘 날짜(`YYYY-MM-DD`), `@version` 은 `YY.MM.DD`.
- Entity 는 **접근 타입이 PROPERTY** 다 — `@Id` 가 `getC_id()` getter 에 붙는다.
  필드명과 컬럼명을 반드시 동일하게 짓는다(ModelMapper·Criteria 가 이름으로 매핑한다).
- Entity 는 `TreeSearchEntity` 의 abstract 훅 `setFieldFromNewInstance` 를 **반드시 구현**한다.
- DTO 는 `TreeBaseDTO` 를 상속하고, Entity 와 **필드명을 1:1로** 맞춘다.
- `@Service("<bean>")` 에 **빈 이름을 반드시 준다.** `TreeServiceImpl` 자신이 빈이라 타입 주입이 모호해진다.
- Controller 의 `@PostConstruct initialize()` 에서 `setTreeService(...)` + `setTreeEntity(...)`.
  **이게 없으면 상속받은 엔드포인트가 전부 NPE 다.**
- Controller 는 `@Controller` + `@RequiredArgsConstructor`, 신규 엔드포인트는 메서드에 `@ResponseBody`
  + `ResponseEntity.ok(CommonResponse.success(...))`. `/auth-user` 같은 권한 접두는 **쓰지 않는다**(게이트웨이가 붙인다).
- Flyway SQL 은 본 테이블 + `_LOG` 짝 테이블 + **루트 2행 seed** + 트리거 3종이 한 세트다.
  seed 가 없으면 `addNode` 가 동작하지 않는다.
- 트리거는 **트리 공통 컬럼만** `_LOG` 에 복사한다(도메인 컬럼은 남기지 않는 것이 이 저장소 관례).
  `DROP TRIGGER IF EXISTS` 를 앞에 붙여 재실행 가능하게 한다.
- Java 11 / Spring Boot 2.6 / `javax.*` 로 작성한다. **`jakarta.*` · Java 17+ 문법 금지.**

### 4.2 하지 않을 것

- Auto-Code 저장소 파일 수정
- `commit` · `push`
- 요청하지 않은 도메인 고유 메서드 발명 — 스킬 템플릿의 예시 메서드는 **주석으로만 남기거나 제거**한다
- 기존 파일 수정(이 command 는 **신규 생성 전용**이다). 기존 도메인 변경은 `backend-expert` 에게 보낸다
- `DynamicDBMakerDao.xml` 수정 — 제품별 동적 테이블(`T_ARMS_X_<pdServiceId>`)은 이 command 범위 밖이다.
  사용자가 동적 테이블을 원하면 **생성하지 말고** `database-expert` · `backend-expert` 로 안내한다

---

## 5. 생성 후 검증

1. `./gradlew compileJava` (Windows: `gradlew.bat compileJava`) — Backend-Core 디렉토리에서 실행.
   오프라인·Nexus 미접속으로 실패하면 **실패 사실과 원인을 그대로 보고**한다. 성공한 척하지 않는다.
2. 생성한 파일 경로가 실제 존재하는지 확인한다.
3. 아래를 눈으로 대조한다.
   - Entity 필드명 == DTO 필드명 == DDL 컬럼명
   - `@Service("<bean>")` == Controller 의 주입 필드명
   - `@Table(name=...)` == DDL 의 `CREATE TABLE` 이름
   - Flyway 번호가 기존 최댓값 + 1 이고 중복이 없는지

---

## 6. 보고 (한국어)

```
## 생성 결과
- 엔티티: <Name>   도메인: com.arms.api.<domain>   빈: <bean>   테이블: <table>
- 생성 파일 N개 (경로 목록)
- Flyway: V<n>__add_<snake>_table.sql  (직전 최댓값 V<n-1>)

## 적용한 기본값
(사용자가 주지 않아 추론한 값만. 근거 함께)

## 검증
- compileJava: 성공 / 실패(사유)
- 이름 정합성 대조 결과

## 남은 일 (사용자 몫)
- Flyway 마이그레이션 실행 시점
- 프론트 화면·게이트웨이 라우트가 필요하면 별도 작업
- 커밋 메시지 초안:
  feat : [ARMS-????] #comment <Name> 도메인 신규 생성 YYYY.MM.DD #close
```

작업 브랜치는 `dev` 다. **커밋·푸시는 하지 않는다.**

---

## 7. 사용 예

```
/arms-autocode Notice
/arms-autocode Notice --fields "c_notice_desc:text:공지 내용, c_use_yn:boolean:사용 여부"
/arms-autocode ReleaseNote --domain release_note --table T_ARMS_RELEASE_NOTE \
               --fields "c_release_ver:string:릴리즈 버전, c_release_date:date:배포일" \
               --seed "RELEASE_NOTE Table,릴리즈" --dry-run
/arms-autocode GlobalMap --with-dao
```
