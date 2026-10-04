# 리팩토링 가이드북

이 가이드북은 우리 코드를 더 읽기 쉽고 고치기 쉽게 만들기 위한 기준을 13개 카테고리로 정리한 것입니다. 카테고리마다 어떤 상황에서 손을 대야 하는지, 우리 코드(Engine-Fire)에서 실제로 찾은 예, 그 코드를 어떻게 바꾸면 되는지, 그리고 앞으로 코드를 쓸 때 지켜야 할 방향을 차례로 설명합니다. 앞부분은 자바(Engine-Fire) 코드를, 뒷부분의 **자바스크립트 편**은 화면 코드(Frontend-Web)를 다룹니다.

리팩토링은 **프로그램이 하는 일은 그대로 두고 코드의 구조만 바꾸는 작업**입니다. 기능을 추가하거나 버그를 고치는 일과는 다릅니다. 이 차이를 지키는 것이 리팩토링을 안전하게 하는 가장 중요한 조건입니다.

## 시작하기 전에 지켜야 할 네 가지

**첫째, 테스트를 먼저 준비합니다.** 리팩토링을 하고 나서 동작이 그대로인지 확인하려면, 바꾸기 전의 동작을 기록해 둔 테스트가 있어야 합니다. 테스트 없이 구조를 바꾸면 무언가 깨졌을 때 알아차릴 방법이 없습니다.

**둘째, 기능 변경과 섞지 않습니다.** 리팩토링 커밋에는 동작이 바뀌는 코드가 하나도 없어야 합니다. 구조를 바꾸다가 버그를 발견했다면 그 자리에서 고치지 말고 메모해 두었다가, 리팩토링 커밋이 끝난 뒤 별도 커밋으로 고칩니다. 그래야 문제가 생겼을 때 어느 변경 때문인지 바로 알 수 있습니다.

**셋째, 작게 바꾸고 매번 테스트합니다.** 한 번에 여러 곳을 크게 고치지 않습니다. 메소드 하나를 빼내고 테스트, 이름 하나를 바꾸고 테스트하는 식으로 작은 단계를 반복합니다. 단계가 작을수록 실수했을 때 되돌리기 쉽습니다.

**넷째, 리팩토링은 따로 시간을 잡기보다 일하는 중에 합니다.** 같은 코드를 세 번째로 복사하려 할 때, 새 기능을 넣기 직전에 코드가 너무 엉켜 있을 때, 버그를 찾느라 코드를 읽다가 이해가 잘 안 될 때, 코드 리뷰 중에 읽기 어려운 부분을 발견했을 때가 리팩토링하기 좋은 시점입니다.

## 어떤 카테고리부터 보면 될까

코드를 읽다가 아래 증상이 보이면 오른쪽 카테고리를 찾아가면 됩니다. 코드 리뷰 때는 바로 다음의 「객체지향 생활 체조 — 코드 리뷰 때 점검할 아홉 가지」를 함께 훑어보면 좋습니다.

| 코드에서 이런 모습이 보이면 | 볼 카테고리 |
|---|---|
| 고치려는 코드에 테스트가 없다 | RF-00 안전망 |
| 주석 처리된 코드나 쓸모없는 주석, 아무도 쓰지 않는 메소드가 남아 있다 | RF-01 정리 |
| 이름만 봐서는 무엇을 담는지, 무엇을 하는지 알 수 없다 | RF-02 이름 |
| 메소드가 너무 길고 주석으로 구역을 나눠 놓았다 | RF-03 함수 분해 |
| 메소드 인수가 너무 많거나 `true`/`false` 인수로 동작이 갈린다 | RF-04 함수 인수 |
| 같은 코드 블록이 여러 곳에 복사되어 있다 | RF-05 중복 |
| 같은 switch 문이 여러 곳에 있거나 if 문이 깊게 겹쳐 있다 | RF-06 조건 로직 |
| 상태를 `"CRITICAL"` 같은 문자열이나 의미 없는 숫자로 다룬다 | RF-07 데이터 |
| 한 클래스가 너무 많은 일을 하거나, 다른 객체의 데이터만 꺼내 쓰는 메소드가 있다 | RF-08 클래스 책임 |
| 예외를 잡고 아무것도 하지 않거나 실패를 `null`로 돌려준다 | RF-09 오류 처리 |
| 형제 클래스들에 똑같은 메소드가 복사되어 있다 | RF-10 상속 |
| 컨트롤러가 업무 흐름을 직접 처리하거나 설정 값이 코드에 박혀 있다 | RF-11 구조 |
| 여러 요청이 동시에 건드리는 공유 변수가 있다 | RF-12 동시성 |
| 응답 VO에 토큰 같은 값이 섞여 있거나, 응답 VO가 서비스 곳곳에서 인자로 쓰인다 | VO와 도메인 객체 |

---

## 객체지향 생활 체조 — 코드 리뷰 때 점검할 아홉 가지

### 어떻게 쓰는가

객체지향 생활 체조는 객체지향 설계 감각을 기르기 위한 아홉 가지 규칙입니다. 원래는 "작은 프로그램 하나를 이 규칙에 100% 맞춰 짜 보는 훈련"으로 만들어졌기 때문에, 실제 업무 코드에 모든 규칙을 그대로 강제하면 오히려 코드가 어색해지는 경우가 있습니다.

그래서 우리는 이 규칙들을 **코드 리뷰 때 훑어보는 점검 질문**으로 씁니다. 규칙에 걸린다고 바로 고쳐야 하는 것은 아니고, "여기를 한번 들여다보자"는 신호로 받아들입니다. 들여다본 결과 실제로 문제가 있으면, 각 규칙에 적어 둔 카테고리의 방법으로 고칩니다. 아래에는 규칙마다 무슨 뜻인지, 왜 필요한지, 우리 팀은 어디까지 적용하는지를 적었습니다.

### 규칙 1. 메소드 안의 들여쓰기는 한 단계만

**무슨 뜻인가.** 메소드 안에 if 안의 for, for 안의 if처럼 제어문이 겹쳐 들어가지 않게 하라는 규칙입니다.

**왜 필요한가.** 들여쓰기가 두 단계 이상이면 그 메소드는 대개 두 가지 이상의 일을 하고 있습니다. 바깥 반복문이 하는 일과 안쪽 조건문이 하는 일이 섞여 있는 것입니다.

**우리 코드에서는.** `AnalysisScopeImpl.treeBarData()`는 들여쓰기가 9단까지 들어갑니다.

**우리 팀 적용.** 들여쓰기 깊이는 들여다볼 신호로만 씁니다. 안쪽 블록이 하는 일을 이름 하나로 설명할 수 있다면 메소드로 빼서(RF-03) 들여쓰기를 줄입니다.

### 규칙 2. else 를 쓰지 않는다

**무슨 뜻인가.** if 다음에 else를 붙이지 말고, 예외적인 경우를 먼저 확인해서 바로 return 하거나 다형성으로 분기를 없애라는 규칙입니다.

**왜 필요한가.** else가 쌓이면 중첩이 깊어지고, 같은 상태 분기가 여러 곳에 복사되기 쉽습니다.

**우리 코드에서는.** `EsMonitoringServiceImpl`은 상태 문자열로 if / else if를 이어 가며 같은 판단을 반복합니다.

```java
if ("RED".equals(clusterHealth.getStatus())) { ... }
else if ("YELLOW".equals(clusterHealth.getStatus())) { ... }
```

**우리 팀 적용.** else를 무조건 금지하지는 않습니다. 한쪽이 예외적인 경우(값이 없음, 이미 처리됨)라면 먼저 확인하고 빠져나가게 바꿉니다. 하지만 두 경우가 모두 정상적인 흐름이라면 if/else로 나란히 두는 것이 의도를 더 잘 보여 줍니다. 같은 값으로 갈라지는 분기가 여러 곳에 있다면 RF-06의 방법으로 다형성으로 옮깁니다.

### 규칙 3. 원시값과 문자열을 포장한다

**무슨 뜻인가.** `int`나 `String`을 그대로 쓰지 말고, 그 값의 의미를 나타내는 작은 클래스로 감싸라는 규칙입니다.

**왜 필요한가.** `String status`는 어떤 문자열이든 들어갈 수 있어서 오타를 컴파일러가 잡지 못하고, 그 값에 붙은 규칙이 여기저기 흩어집니다. 시간을 받는 메소드에 연도를 넘기는 실수도 타입이 다르면 막을 수 있습니다.

**우리 코드에서는.** 위의 `EsMonitoringServiceImpl`이 `"HEALTHY"`, `"WARNING"`, `"CRITICAL"`을 문자열로 다룹니다.

**우리 팀 적용.** 모든 값을 감싸지는 않습니다. 상태, 금액, 기간처럼 **의미와 규칙이 따라다니는 값**, 또는 같은 타입끼리 순서를 바꿔 넣기 쉬운 값을 enum이나 전용 타입으로 만듭니다(RF-07).

### 규칙 4. 한 줄에 점은 하나만

**무슨 뜻인가.** `a.getB().getC()`처럼 한 줄에서 다른 객체의 속을 여러 단계 파고들지 말라는 규칙입니다.

**왜 필요한가.** 점이 이어진 코드는 중간 객체들의 구조를 모두 알고 있어야 동작합니다. 중간 구조가 바뀌면 이렇게 쓴 곳이 모두 함께 깨집니다.

**우리 코드에서는.** 담당자 정보를 꺼내는 코드가 이슈 객체의 속을 직접 파고들고, 같은 모양이 Engine-Fire 전체에 30곳 넘게 있습니다. 요청 DTO에서 제품 ID를 꺼내는 체인도 37곳입니다.

```java
String accountId = issue.getAssignee().getAccountId();
Long pdServiceId = scopeDTO.getPdServiceAndIsReq().getPdServiceId();
```

**우리 팀 적용.** 같은 체인이 여러 곳에 반복되면 바깥 객체에 필요한 값을 바로 주는 메소드를 둡니다(`issue.assigneeAccountId()`, `scopeDTO.pdServiceId()`). 다만 모든 체인을 이렇게 감싸면 전달만 하는 메소드가 가득한 클래스가 되므로, 반복되거나 구조 변경이 예상되는 곳부터 합니다. `stream().filter().map()`이나 빌더처럼 같은 객체에 이어서 호출하는 체인은 대상이 아닙니다(RF-08).

### 규칙 5. 줄여 쓰지 않는다

**무슨 뜻인가.** 클래스, 메소드, 변수 이름을 줄이지 말고, 이름은 한두 단어로 짧게 유지하라는 규칙입니다. 클래스 이름이 이미 말해 주는 단어는 메소드 이름에 되풀이하지 않습니다(`order.shipOrder()` 대신 `order.ship()`).

**왜 필요한가.** 줄인 이름은 쓴 사람만 압니다. 그리고 이름이 너무 길어서 줄이고 싶어진다면, 그 메소드가 너무 많은 일을 하고 있다는 신호인 경우가 많습니다.

**우리 코드에서는.** 반복 변수에 `tp`(스레드 풀 상태), 람다 변수에 `schHits`(검색 결과) 같은 줄인 이름이 쓰이고 있습니다.

```java
for (ThreadPoolStatsVO tp : threadPoolStats) { ... }
.map(schHits -> schHits.getSearchHits().stream() ...)
```

**우리 팀 적용.** 그대로 적용합니다. `tp` 대신 `threadPool`, `schHits` 대신 `searchHits`처럼 줄이지 않고 씁니다(RF-02).

### 규칙 6. 모든 클래스를 작게 유지한다

**무슨 뜻인가.** 클래스는 50줄, 패키지는 파일 10개를 넘기지 말라는 규칙입니다.

**왜 필요한가.** 큰 클래스는 대개 한 가지보다 많은 일을 하고 있어서, 이해하기도 재사용하기도 어렵습니다.

**우리 코드에서는.** `AnalysisResourceImpl`은 2,346줄로 차트 9종을 모두 처리합니다.

**우리 팀 적용.** 50줄, 10파일이라는 숫자는 기준이 아니라 참고치입니다. 판단은 "이 클래스가 바뀌는 이유를 한 문장으로 말할 수 있는가"로 합니다. 말할 수 없으면 이유별로 나눕니다(RF-08).

### 규칙 7. 인스턴스 변수는 두 개 이하로

**무슨 뜻인가.** 한 클래스가 가진 필드를 두 개 이하로 유지하라는 규칙입니다.

**왜 필요한가.** 필드가 늘어날수록 클래스가 하는 일이 흐려집니다. 대부분의 클래스는 상태 하나를 책임지는 클래스이거나, 두 객체를 조율하는 클래스 중 하나여야 합니다. 이 둘을 한 클래스에 섞으면 응집도가 떨어집니다.

**우리 팀 적용.** 두 개라는 숫자는 지키지 않습니다. Entity나 응답 VO처럼 데이터를 담는 것이 목적인 클래스는 필드가 많을 수밖에 없습니다. 대신 업무 로직을 가진 클래스에서 필드가 많아지면, 항상 같이 쓰이는 필드 묶음을 찾아 별도 클래스로 묶을 수 있는지 봅니다. 예를 들어 이름 관련 필드 세 개를 `Name` 클래스 하나로 묶는 식입니다(RF-07, RF-08).

### 규칙 8. 일급 컬렉션을 쓴다

**무슨 뜻인가.** 컬렉션을 가진 클래스는 그 컬렉션 하나만 필드로 갖게 하라는 규칙입니다. 목록과 그 목록에 대한 규칙을 하나의 클래스로 만드는 것입니다.

**왜 필요한가.** `List`를 그대로 들고 다니면, 그 목록을 거르고 세는 코드가 서비스 곳곳에 복사됩니다.

**우리 팀 적용.** 목록에 대한 같은 처리(필터, 집계, 검사)가 여러 곳에 반복된다면 일급 컬렉션으로 만듭니다.

```java
// 서비스마다 같은 필터를 반복하는 대신
class ReqIssues {
    private final List<AlmIssueEntity> issues;

    long openCount() { return issues.stream().filter(i -> !i.isResolved()).count(); }
    ReqIssues ofProduct(Long pdServiceId) { ... }
}
```

### 규칙 9. getter/setter 를 쓰지 않는다

**무슨 뜻인가.** 객체에서 값을 꺼내 밖에서 계산하지 말고, 그 계산을 객체에게 시키라는 규칙입니다. "묻지 말고 시켜라"라고도 합니다.

**왜 필요한가.** 값을 꺼내(get) 밖에서 계산하고 다시 넣는(set) 코드가 많으면, 그 객체에 대한 규칙이 객체 밖 여러 곳에 흩어집니다.

**우리 팀 적용.** 이 규칙은 **업무 로직을 가진 객체(도메인 객체)에만** 적용합니다. 요청 DTO와 응답 VO는 대상이 아닙니다. DTO와 VO는 데이터를 실어 나르는 것 자체가 목적이라 감출 동작이 없고, 데이터를 드러내는 것이 정상입니다. Spring이 요청 JSON을 DTO로 바꿀 때, 응답 VO를 JSON으로 만들 때도 getter/setter가 필요합니다.

도메인 객체와 Entity에서는 getter/setter를 없애는 것이 목표가 아닙니다. **값을 꺼내 밖에서 계산하는 코드가 보이면, 그 계산을 데이터가 있는 객체 안으로 옮깁니다.** 그리고 바뀌면 안 되는 값에는 setter를 두지 않습니다(RF-07, RF-08).

---

## RF-00 안전망 — 테스트부터 갖춘다

### 언제 필요한가

모든 리팩토링의 출발점입니다. 코드 구조를 바꾼 뒤 "예전과 똑같이 동작하는가"를 확인할 수 있어야 하는데, 그 확인 수단이 테스트입니다. 고치려는 코드에 테스트가 없다면 리팩토링보다 테스트 작성이 먼저입니다.

### 우리 코드의 예

Engine-Fire에서 가장 큰 서비스 클래스들에 테스트가 하나도 없습니다. 현재 테스트는 이슈 수집 쪽에만 있고, 아래 클래스들은 지금 상태로는 안전하게 고칠 방법이 없습니다.

```
AnalysisResourceImpl       2,346줄   테스트 없음
AnalysisScopeImpl          1,596줄   테스트 없음
WeeklyServiceImpl          1,457줄   테스트 없음
EsMonitoringServiceImpl              테스트 없음
```

### 이렇게 바꾼다

리팩토링 전에 만드는 테스트는 "올바른 값"을 검증하는 테스트가 아니라 **"지금 이 코드가 내놓는 값"을 그대로 기록하는 테스트**입니다. 실제 입력 몇 가지를 넣어 보고, 나온 결과를 기대값으로 적습니다.

```java
@Test
void calcProgress_현재동작_고정() {
    assertEquals(40,  service.calcProgress(2, 5));
    assertEquals(0,   service.calcProgress(0, 0));   // 이상해 보여도 지금 나오는 값을 그대로 적는다
    assertEquals(100, service.calcProgress(5, 5));
}
```

이렇게 해 두면 리팩토링 후에 테스트가 하나라도 실패할 때 "동작이 바뀌었다"는 것을 바로 알 수 있습니다.

### 가이드 방향

결과가 이상해 보여도 테스트에서는 일단 지금 값을 그대로 고정합니다. 그 값이 버그라면 리팩토링을 마친 뒤에 따로 고치고, 그때 테스트의 기대값도 함께 바꿉니다.

처음 테스트를 붙일 곳은 OpenSearch 같은 외부 시스템 없이 입력만으로 결과가 나오는 계산 메소드가 좋습니다. 준비할 것이 적어서 빨리 만들 수 있습니다.

빌드와 테스트는 명령 하나로 끝까지 돌 수 있어야 합니다. 여러 단계를 손으로 거쳐야 한다면 사람들이 테스트를 건너뛰게 됩니다.

---

## RF-01 정리 — 읽기를 방해하는 것을 걷어낸다

### 언제 필요한가

주석 처리된 코드, 코드가 하는 일을 그대로 되풀이하는 주석, 더 이상 호출되지 않는 메소드처럼 동작에는 아무 영향이 없지만 읽는 사람의 주의를 빼앗는 것들이 남아 있을 때입니다. 이런 것들은 "혹시 필요한 건가?" 하고 매번 멈추게 만듭니다. 가장 위험이 낮은 리팩토링이라 처음 시작하기에 좋습니다.

### 우리 코드의 예

`AnalysisCostImpl`의 이 메소드에는 예전 판정 로직이 주석으로 남아 있습니다. 읽는 사람은 이 코드가 왜 꺼져 있는지, 다시 켜야 하는 건지 알 수 없습니다.

```java
private ResolvedInfo resolveResolutionDates(AlmIssueEntity issue) {
    Date resolutionDate = issue.getResolutiondate();
    if (resolutionDate == null) {
        return new ResolvedInfo(new Date(), false);
    }
//    Date updated = issue.getUpdated();
//    if (updated != null && resolutionDate.before(updated)) {
//        return new ResolvedInfo(new Date(), false);
//    }
    return new ResolvedInfo(resolutionDate, true);
}
```

### 이렇게 바꾼다

주석 처리된 부분을 지웁니다. 지운 코드는 git 이력에 남아 있으니 필요하면 언제든 되살릴 수 있습니다.

```java
private ResolvedInfo resolveResolutionDates(AlmIssueEntity issue) {
    Date resolutionDate = issue.getResolutiondate();
    if (resolutionDate == null) {
        return new ResolvedInfo(new Date(), false);
    }
    return new ResolvedInfo(resolutionDate, true);
}
```

"재오픈된 이슈를 어떻게 판정할지" 같은 고민이 남아 있다면, 그 내용은 코드가 아니라 이슈 관리 도구에 기록합니다.

### 가이드 방향

주석으로 남길 것은 코드만 봐서는 알 수 없는 내용, 즉 **왜 이렇게 했는지**, 주의할 점은 무엇인지, 외부 제약이 무엇인지입니다. 코드가 **무엇을 하는지** 설명하는 주석이 필요하다고 느껴진다면, 주석을 다는 대신 메소드나 변수 이름을 그 설명처럼 바꾸는 편이 낫습니다.

TODO 주석은 누가 언제까지 할지 정하지 않으면 그대로 몇 년씩 남습니다. 할 일이라면 이슈로 등록하고 코드에는 남기지 않습니다.

---

## RF-02 이름 — 이름만 봐도 알 수 있게 한다

### 언제 필요한가

변수나 메소드 이름을 보고 그것이 무엇을 담고 있는지, 무엇을 하는지 알 수 없을 때입니다. 코드는 쓰는 시간보다 읽는 시간이 훨씬 길기 때문에, 이름을 바꾸는 것만으로도 효과가 큽니다. IDE가 호출하는 곳까지 자동으로 바꿔 주므로 위험도 낮습니다.

### 우리 코드의 예

`AnalysisScopeImpl.treeBarData()`에는 `reqIssue1`과 `reqIssue`가 함께 나옵니다. 둘이 어떻게 다른지는 앞뒤 코드를 한참 읽어야 알 수 있습니다.

```java
for (AlmIssueEntity reqIssue1 : reqIssues) { ... }
for (AlmIssueEntity notReqIssue1 : notReqIssues) { ... }
for (AlmIssueEntity reqIssue : rightReqIssueMap.values()) { ... }
```

`StateMappingCacheService`는 클래스 이름에 "Cache"가 붙어 있어서 저장된 값을 돌려줄 것 같지만, 실제로는 호출할 때마다 원격 서버를 부릅니다. 이름을 믿고 반복문 안에서 호출하면 의도치 않게 원격 호출이 반복됩니다.

```java
public StateMappingInfo getStateMappingInfo() {
    StateMappingInfo latest = fetchStateMappingInfo();   // 매번 원격 호출
    ...
}
```

### 이렇게 바꾼다

번호 대신 둘의 차이를 이름에 담습니다. 앞의 것은 아직 분류 전인 후보이고, 뒤의 것은 이 제품에 속한다고 판정된 이슈입니다.

```java
for (AlmIssueEntity candidateReq : reqIssues) { ... }
for (AlmIssueEntity ownReq : rightReqIssueMap.values()) { ... }
```

메소드 이름은 실제로 하는 일을 말하도록 바꿉니다. "가져오되, 실패하면 마지막으로 받은 값을 준다"는 동작이 이름에 드러납니다.

```java
public StateMappingInfo fetchOrLastKnown() { ... }
```

### 가이드 방향

변수에 `1`, `2` 같은 번호를 붙이거나 `cnt`, `tmp`처럼 줄여 쓰지 않습니다. 번호가 필요하다고 느껴지면 그 둘이 무엇이 다른지 생각해서 그 차이를 이름에 넣습니다.

이름과 실제 동작이 다르면 둘 중 하나를 고칩니다. 특히 "조회"처럼 보이는 이름이 데이터를 바꾸거나 원격 호출을 한다면 반드시 고쳐야 합니다.

같은 개념에는 같은 단어를 씁니다. 어떤 곳은 `get`, 어떤 곳은 `fetch`, 어떤 곳은 `retrieve`라고 쓰면 읽는 사람은 셋이 다른 동작이라고 오해합니다.

복잡한 조건식에 이름을 붙이고 싶을 때는 지역 변수보다 메소드로 빼는 것을 먼저 고려합니다. `req.isOverdue()`처럼 만들어 두면 다른 곳에서도 같은 판단을 재사용할 수 있습니다.

IntelliJ에서 이름 위에 커서를 두고 `⇧F6`을 누르면 그 이름을 쓰는 모든 곳이 함께 바뀝니다.

---

## RF-03 함수 분해 — 긴 메소드를 이름 있는 단계로 나눈다

### 언제 필요한가

메소드가 길어서 한눈에 들어오지 않고, 중간중간 주석으로 "1단계", "2단계"처럼 구역을 나눠 놓았거나, if와 for가 여러 겹으로 들여쓰기 되어 있을 때입니다. 이런 메소드는 한 번에 여러 가지 일을 하고 있어서, 일부만 고치려 해도 전체를 다 이해해야 합니다.

### 우리 코드의 예

`AnalysisScopeImpl.treeBarData()`는 222줄이고 들여쓰기가 9단까지 들어갑니다. 작성자도 길다는 것을 알아서 주석 번호로 단계를 표시해 두었습니다.

```java
// 1.1 (이슈 분리) 요구사항 이슈 / 다른 제품의 요구사항이슈
for (...) { ... }
// 1.2 (이슈 분리) 하위이슈 / 연결이슈, 다른 제품의 하위이슈
for (...) { ... }
// 2.1 요구사항 이슈
for (...) { ... //처리 여부 체크 ... }
// 2.2 subtask
for (...) { ... //처리 여부 체크 ... }
// 연결이슈들
for (...) { if (...) { if (...) { for (...) { ... } } } }
```

### 이렇게 바꾼다

주석으로 적어 둔 단계 하나하나를 메소드로 빼고, 주석 내용을 메소드 이름으로 삼습니다. 그러면 원래 메소드는 단계들을 순서대로 부르는 짧은 목차가 됩니다.

```java
IssueBuckets buckets = splitByOwnership(reqIssues, notReqIssues, pdServiceId);
countRequirementIssues(buckets.ownReqs(), existingSet, result);
countSubtasks(buckets.ownSubtasks(), existingSet, result);
countLinkedIssues(buckets.linked(), result);
```

이제 "하위 이슈 집계 방식만 바꾸고 싶다"면 `countSubtasks` 하나만 열어 보면 됩니다. 2.1과 2.2에 똑같이 들어 있던 "처리 여부 체크" 부분도 따로 빼면 중복이 함께 사라집니다.

### 가이드 방향

메소드를 나눌지 판단하는 기준은 줄 수가 아닙니다. **그 코드 덩어리가 하는 일을 이름 하나로 설명할 수 있는가**가 기준입니다. 설명할 수 있다면 한두 줄짜리라도 메소드로 빼는 것이 읽기 쉽습니다.

나눈 메소드들은 위에서 아래로 읽었을 때 이야기처럼 이어지도록 배치합니다. 큰 흐름을 먼저 보여 주는 메소드가 위에, 세부 단계가 아래에 오게 합니다.

지역 변수가 너무 많이 얽혀 있어서 메소드로 빼기 어렵다면, 그 메소드 전체를 별도 클래스로 옮기는 방법이 있습니다. 지역 변수들이 그 클래스의 필드가 되므로 단계별 메소드로 나누기가 쉬워집니다.

IntelliJ에서 빼낼 코드를 선택하고 `⌥⌘M`을 누르면 메소드 추출이 자동으로 됩니다.

---

## RF-04 함수 인수 — 인수를 줄이고 뜻이 드러나게 한다

### 언제 필요한가

메소드 인수가 너무 많아서 호출하는 쪽에서 순서를 헷갈리기 쉬울 때, 또는 `true`/`false` 값 하나로 메소드 안에서 전혀 다른 동작을 고를 때입니다. 호출하는 코드만 봐서는 `true`가 무슨 뜻인지 알 수 없습니다.

### 우리 코드의 예

`WeeklyServiceImpl.buildAlmIssueStatusKey()`는 문자열 다섯 개를 받습니다. 세 곳에서 같은 다섯 값을 풀어서 넘기는데, 모두 `String`이라 순서를 바꿔 넣어도 컴파일러가 잡아 주지 못합니다.

```java
private String buildAlmIssueStatusKey(String serverType, String serverId, String project,
                                      String issuetypeId, String statusId) { ... }
```

`DocumentResultWrapper`의 `getT()`는 `boolean` 값에 따라 경고 로그를 남길지 말지를 정합니다. `getT(true)`만 봐서는 무엇이 참이라는 건지 알 수 없습니다.

```java
public T findFirst()    { return getT(false); }
public T fetchOnlyOne() { return getT(true); }
private T getT(boolean warningVisible) { ... }
```

### 이렇게 바꾼다

항상 같이 다니는 다섯 값은 하나의 객체로 묶습니다. 키를 만드는 규칙도 그 객체 안으로 들어가므로, 규칙이 바뀌어도 한 곳만 고치면 됩니다.

```java
String key = AlmStatusKey.of(issue).asString();
```

`boolean` 인수로 동작을 고르는 대신, 각 동작을 이름이 다른 메소드로 나눕니다.

```java
private T firstOrEmpty() { ... }
private void warnIfMultiple() { ... }
```

### 가이드 방향

인수는 적을수록 이해하기 쉽습니다. 항상 같이 넘어가는 값 묶음이 보이면 객체로 묶습니다. 묶은 객체에는 그 값들로 하는 계산도 함께 옮길 수 있어서 코드가 자연스럽게 정리됩니다.

`true`/`false` 인수로 메소드 안에서 분기하고 있다면 메소드를 둘로 나누는 것이 거의 항상 낫습니다. 호출하는 쪽에서 무엇을 원하는지가 메소드 이름으로 드러납니다.

값을 돌려주면서 내부 상태도 바꾸는 메소드는 "조회"와 "변경" 두 메소드로 나눕니다. 조회하려고 불렀다가 상태가 바뀌는 일을 막을 수 있습니다.

---

## RF-05 중복 제거 — 같은 코드는 한 곳에만 둔다

### 언제 필요한가

같은 코드 블록이 여러 곳에 복사되어 있을 때입니다. 복사된 코드는 규칙이 바뀔 때 모든 곳을 찾아 똑같이 고쳐야 하고, 한 곳이라도 빠뜨리면 그곳만 다르게 동작하는 버그가 생깁니다.

### 우리 코드의 예

아래 정렬 설정 블록이 `AnalysisTimeImpl`에 4곳, `ReportServiceImpl`에 3곳, 모두 7곳에 똑같이 들어 있습니다.

```java
timeDTO.setSources(
    List.of(
        CompositeSourceDTO.builder().fieldAlias("update_date").field("updated").isAscending(false).build(),
        CompositeSourceDTO.builder().fieldAlias("recent_id").field("recent_id").isAscending(false).build()
    ));
```

### 이렇게 바꾼다

블록을 이름 있는 메소드 하나로 만들고, 7곳에서는 그 메소드를 부릅니다. 메소드 이름이 "최신 수정순 정렬"이라는 의도까지 알려 줍니다.

```java
timeDTO.setSources(CompositeSources.latestUpdateFirst());
```

이제 정렬 기준이 바뀌면 `latestUpdateFirst()` 한 곳만 고치면 됩니다.

### 가이드 방향

비슷한 코드를 처음 쓸 때는 그냥 씁니다. 두 번째에는 중복이 생긴다는 것을 인식만 하고 넘어갑니다. **세 번째로 같은 코드를 쓰게 되면 그때 한 곳으로 모읍니다.** 처음부터 공통화하면 아직 드러나지 않은 차이 때문에 잘못 묶을 수 있기 때문입니다.

같은 클래스 안의 중복은 메소드로 빼고, 형제 클래스들 사이의 중복은 공통 부모 클래스로 올립니다.

Gradle 빌드 스크립트도 마찬가지입니다. 모듈마다 같은 설정이 복사되어 있다면 공통 설정 한 곳으로 모읍니다.

---

## RF-06 조건 로직 — 분기를 읽기 쉽게, 반복되는 분기는 한 곳으로

### 언제 필요한가

같은 값(예를 들어 이슈 종류)으로 갈라지는 switch 문이 여러 메소드에 반복되어 있을 때, 또는 if 안에 if가 여러 겹으로 들어가 있어서 어떤 경우에 어디로 가는지 따라가기 어려울 때입니다.

### 우리 코드의 예

`AnalysisResourceImpl`에는 이슈 종류(`IssueTypeV3`)로 갈라지는 switch 문이 4곳에 있습니다. 이슈 종류가 하나 새로 생기면 4곳을 모두 찾아서 고쳐야 하고, 하나라도 빠뜨리면 그 화면에서만 새 종류가 누락됩니다.

```java
switch (type) {
    case RIGHT_REQ:       context.getRightReqIssues().put(recentId, issue); break;
    case RIGHT_SUBTASK:   context.getRightSubtask().put(recentId, issue); break;
    case NOT_REQ_WITH_PD: context.getNotReqIssuesHasPd().put(recentId, issue); break;
    case LINKED_ONLY:
    case LINKED_SUBTASK:  context.getJustLinkedKeyIssues().put(recentId, issue); break;
}
```

### 이렇게 바꾼다

종류마다 해야 할 일을 enum 자신이 알도록 옮깁니다. 그러면 호출하는 곳에서는 switch 없이 한 줄로 끝납니다.

```java
enum IssueTypeV3 {
    RIGHT_REQ { void store(IssueBuckets b, AlmIssueEntity i) { b.rightReqs().put(i.getRecentId(), i); } },
    ...;
    abstract void store(IssueBuckets b, AlmIssueEntity i);
}

type.store(buckets, issue);
```

새 종류를 추가할 때는 enum에 항목을 하나 넣으면, 그 종류가 해야 할 일을 구현하지 않으면 컴파일이 되지 않습니다. 빠뜨릴 수가 없게 됩니다.

### 가이드 방향

같은 값으로 갈라지는 분기가 두 곳 이상에 있다면, 분기마다 할 일을 그 값의 타입(enum이나 클래스) 안으로 옮기는 것을 고려합니다.

if가 깊게 겹쳐 있다면, 예외적인 경우(값이 없음, 이미 처리됨 등)를 메소드 앞부분에서 먼저 확인하고 바로 return 합니다. 그러면 남은 코드는 정상적인 흐름만 다루게 되어 들여쓰기가 얕아집니다. 다만 두 경우가 모두 정상적인 흐름이라면 if/else로 나란히 두는 것이 의도를 더 잘 보여 줍니다.

조건식이 길면 그 조건이 뜻하는 바를 이름으로 가진 메소드로 뺍니다. `endDate != null && endDate.isBefore(now) && !done` 대신 `isOverdue()`라고 쓰면 읽는 순간 의미가 들어옵니다.

`!isNotEmpty()`처럼 부정을 두 번 하는 조건은 `isEmpty()`처럼 긍정형으로 바꿉니다.

---

## RF-07 데이터 — 의미 있는 값은 타입으로 만든다

### 언제 필요한가

상태를 `"CRITICAL"` 같은 문자열이나 `"03"` 같은 코드로 들고 다닐 때, 코드 곳곳에 `60000` 같은 숫자가 설명 없이 박혀 있을 때입니다. 문자열 상태는 오타를 내도 컴파일러가 잡지 못하고, 그 상태에 붙은 규칙이 여러 곳에 흩어집니다.

### 우리 코드의 예

`EsMonitoringServiceImpl.getMonitoringSummary()`는 전체 상태를 문자열로 관리합니다. "이미 CRITICAL이면 WARNING으로 낮추지 않는다"는 규칙을 지키려고 같은 비교를 4번 반복합니다.

```java
String overallStatus = "HEALTHY";
if ("RED".equals(clusterHealth.getStatus())) { overallStatus = "CRITICAL"; }
else if ("YELLOW".equals(clusterHealth.getStatus())) { overallStatus = "WARNING"; }
...
if (!"CRITICAL".equals(overallStatus)) { overallStatus = "WARNING"; }   // 같은 비교를 4번 반복
...
boolean isHealthy = "HEALTHY".equals(overallStatus);
```

### 이렇게 바꾼다

상태를 enum으로 만들고, "더 심각한 쪽으로만 올라간다"는 규칙을 enum 안에 한 번만 적습니다.

```java
enum Health {
    HEALTHY, WARNING, CRITICAL;
    Health escalate(Health other) { return other.ordinal() > ordinal() ? other : this; }
}

Health overall = Health.HEALTHY;
if (heapWarn) overall = overall.escalate(Health.WARNING);
```

이제 "CRITICAL이 아닐 때만"이라는 조건을 매번 쓸 필요가 없고, `"CRTICAL"` 같은 오타는 컴파일 단계에서 걸립니다.

### 가이드 방향

상태, 금액, 기간처럼 의미와 규칙이 붙어 있는 값은 enum이나 작은 전용 타입(예: `Money`, `Period`)으로 만듭니다. 여기서 말하는 전용 타입은 응답용 VO와는 다른, 업무 값을 표현하는 클래스입니다. 다만 모든 숫자와 문자열을 감쌀 필요는 없습니다. 규칙이 따라다니거나 잘못 넣기 쉬운 값이 대상입니다.

`60000`처럼 설명 없는 숫자는 `SCROLL_KEEP_ALIVE_MS` 같은 이름 있는 상수로 바꿉니다. 같은 숫자가 여러 곳에 있다면 상수 하나를 공유하게 해서 한 곳만 고치면 되게 합니다.

필드와 getter/setter만 있는 클래스를 보면, 다른 클래스에서 그 값을 꺼내 계산하는 코드를 찾아서 그 계산을 이 클래스 안으로 옮겨 옵니다. 데이터와 그 데이터를 다루는 로직이 한곳에 있어야 고칠 곳을 찾기 쉽습니다.

목록을 돌려줄 때는 바깥에서 함부로 추가·삭제할 수 없도록 수정 불가능한 목록으로 돌려줍니다. 한 번 정해지면 바뀌면 안 되는 값에는 setter를 두지 않습니다.

---

## RF-08 클래스 책임 — 한 클래스는 한 가지 이유로만 바뀌게 한다

### 언제 필요한가

클래스가 너무 커서 "이 클래스가 무엇을 하는가"를 한 문장으로 말할 수 없을 때, 또는 어떤 메소드가 자기 클래스의 데이터는 거의 쓰지 않고 다른 객체의 데이터만 꺼내 계산할 때입니다. 큰 클래스는 서로 관계없는 기능들이 한 파일에 섞여 있어서, 하나를 고치다가 다른 기능을 깨뜨리기 쉽습니다.

### 우리 코드의 예

`AnalysisResourceImpl`은 2,346줄에 차트 9종을 모두 처리합니다. 그중 트리맵과 생키 차트는 각자 전용 데이터 묶음과 처리 메소드들을 따로 가지고 있어서, 사실상 이미 별개의 기능입니다.

```
AnalysisResourceImpl
 ├ 담당자별 상태, 워드클라우드, 누적 막대, 파이 2종, 가로 막대 2종, 담당자 정보
 ├ 트리맵 V3  (전용 데이터 묶음 + 분류·저장·처리 메소드)
 └ 생키 V3    (전용 데이터 묶음 + 분류·저장·처리 메소드)
```

### 이렇게 바꾼다

이미 드러나 있는 경계를 따라 클래스를 나눕니다. 기존 클래스는 외부에서 부르는 입구 역할만 남겨서, 이 서비스를 쓰는 다른 코드는 바꾸지 않아도 되게 합니다.

```
AnalysisResourceImpl      ← 입구만 남김 (기존 인터페이스 그대로)
 ├ ResourceTreeMapBuilder  ← 트리맵 전담
 ├ ResourceSankeyBuilder   ← 생키 전담
 ├ ResourceChartQueries    ← 나머지 차트 집계
 └ IssueTypeClassifier     ← 두 빌더가 함께 쓰는 이슈 분류 규칙
```

이제 생키 차트를 고칠 때는 `ResourceSankeyBuilder`만 열면 되고, 트리맵 쪽을 깨뜨릴 걱정이 없습니다.

### 가이드 방향

"이 클래스가 바뀌는 이유"를 한 문장으로 말해 봅니다. 이유가 여러 개라면, 이유마다 클래스를 나눌 때입니다.

어떤 메소드가 다른 객체의 값만 계속 꺼내서 계산하고 있다면, 그 메소드는 데이터가 있는 쪽 클래스로 옮기는 것이 자연스럽습니다.

`a.getB().getC().doSomething()`처럼 다른 객체의 속을 여러 단계 파고드는 코드는, 중간 구조가 바뀌면 함께 깨집니다. 이럴 때는 `a`에 필요한 일을 해 주는 메소드를 하나 만들어서 호출하는 쪽이 내부 구조를 몰라도 되게 합니다. 다만 모든 호출을 이런 식으로 감싸서 남에게 넘기기만 하는 메소드만 가득한 클래스를 만들지는 않습니다. 하는 일 없이 전달만 하는 클래스는 오히려 없애는 편이 낫습니다.

---

## RF-09 오류 처리 — 실패를 숨기지 않는다

### 언제 필요한가

예외를 잡고 아무것도 하지 않거나, 로그 한 줄만 남기고 계속 진행하거나, 실패를 `null`이나 `-1`로 돌려줄 때입니다. 이렇게 하면 호출하는 쪽은 실패가 있었는지조차 모른 채 다음 단계로 넘어갑니다.

### 우리 코드의 예

`RecentFieldConvertor.search()`는 성격이 전혀 다른 세 가지 상황을 모두 `null` 하나로 돌려줍니다. 인덱스가 아직 없는 것은 정상적인 상황이지만, 조회 장애는 심각한 상황입니다. 그런데 호출하는 쪽은 `null`을 받으면 무조건 "기존 문서가 없다"고 판단하고 진행합니다. 조회에 실패했을 때도 문서가 없는 것으로 보고 새로 저장하게 되어 중복 데이터가 생길 수 있습니다.

```java
try {
    return openSearchOperations.search(query, clazz);
} catch (NoSuchIndexException e) {
    if (... "no such index" ...) { return null; }   // 인덱스가 없음 — 정상적인 상황
    log.warn(...);                                   // 예상하지 못한 상황
} catch (Exception e) {
    log.error(...);                                  // 조회 장애
}
return null;   // 세 경우가 모두 같은 null 로 돌아간다
```

### 이렇게 바꾼다

정상적인 "없음"은 빈 결과로 돌려주고, 실패는 예외로 알립니다. 호출하는 쪽은 빈 결과와 실패를 구분해서 처리할 수 있게 됩니다.

```java
} catch (NoSuchIndexException e) {
    return SearchHitsImpl.empty();                   // 인덱스가 없으면 결과가 비어 있는 것
} catch (Exception e) {
    throw new RecentLookupException("recent 문서 조회 실패: " + clazz.getSimpleName(), e);
}
```

### 가이드 방향

예외를 잡았다면 반드시 무언가를 해야 합니다. 복구하든지, 의미 있는 예외로 바꿔서 다시 던지든지 해야 하고, 그냥 삼켜서는 안 됩니다.

"값이 없음"과 "가져오다 실패함"은 다른 상황입니다. 없음은 `Optional`이나 빈 목록으로, 실패는 예외로 표현해서 호출하는 쪽이 둘을 구분할 수 있게 합니다.

예외를 던질 때는 무엇을 하다가 실패했는지 메시지에 적습니다. 어떤 문서를, 어떤 서버에서, 무슨 작업 중에 실패했는지가 있어야 나중에 원인을 찾을 수 있습니다.

검사 예외(checked)와 비검사 예외(unchecked) 중 무엇을 쓸지는 호출하는 쪽의 상황으로 정합니다. 호출 전에 미리 확인해서 피할 수 있는 실패라면 비검사 예외로, 외부 시스템 장애처럼 호출하는 쪽이 미리 막을 수 없는 실패라면 검사 예외로 해서 대비를 강제합니다.

---

## RF-10 상속 — 공통 코드는 부모에 한 번만 둔다

### 언제 필요한가

같은 인터페이스를 구현하는 형제 클래스들에 똑같은 메소드가 복사되어 있을 때입니다. 공통 동작을 고치려면 모든 형제 클래스를 찾아서 똑같이 고쳐야 합니다.

### 우리 코드의 예

이슈 수집 전략 클래스 세 개(`CloudJiraIssueStrategy`, `OnPremiseJiraIssueStrategy`, `OnPremiseRedmineIssueStrategy`)에 `isExistIssue()`가 글자 하나 다르지 않게 복사되어 있습니다. 게다가 어떤 예외든 잡아서 `false`를 돌려주기 때문에, 네트워크 오류나 인증 만료로 확인을 못 한 경우에도 "이슈가 없다"고 판단됩니다.

```java
public boolean isExistIssue(AlmIssueDTO almIssueDTO) {
    try {
        AlmIssueVO issue = this.getIssueVO(almIssueDTO, false);
        return issue != null && issue.getKey().equals(almIssueDTO.getIssueKeyOrId());
    } catch (Exception e) {
        return false;
    }
}
```

### 이렇게 바꾼다

공통 부모 클래스를 만들어 이 메소드를 한 번만 두고, 각 전략 클래스는 서로 다른 부분(이슈를 가져오는 방법)만 구현하게 합니다.

```java
abstract class AbstractIssueStrategy implements IssueStrategy {
    @Override
    public boolean isExistIssue(AlmIssueDTO dto) { ... }        // 한 곳에만 있다
    protected abstract AlmIssueVO getIssueVO(AlmIssueDTO dto, boolean convert);
}
```

이렇게 모아 두면 "확인을 못 한 것과 없는 것을 구분해야 한다"는 문제도 한 곳에서 고칠 수 있습니다.

### 가이드 방향

형제 클래스들에 같은 코드가 있으면 공통 부모 클래스로 올립니다. 공통 부모를 두기 어렵다면 인터페이스의 default 메소드로 둘 수도 있습니다.

부모 클래스를 상속했는데 부모의 메소드 일부를 쓰지 않으려고 빈 메소드로 덮어쓰고 있다면, 상속 관계가 맞지 않는 것입니다. 이럴 때는 상속하지 말고 부모 클래스를 필드로 가지고 필요한 기능만 호출하는 방식(위임)으로 바꿉니다.

"나중에 필요할지도 몰라서" 만든, 구현체가 하나뿐인 추상 클래스나 인터페이스는 오히려 코드를 읽기 어렵게 만듭니다. 실제로 두 번째 구현이 필요해질 때까지는 합쳐 둡니다.

---

## RF-11 구조 — 역할에 맞는 계층에 코드를 둔다

### 언제 필요한가

컨트롤러가 요청을 받는 것을 넘어 업무 흐름까지 직접 처리할 때, 또는 타임아웃이나 주소 같은 설정 값이 코드에 박혀 있을 때입니다. 컨트롤러에 들어간 업무 로직은 다른 곳에서 재사용하거나 테스트하기 어렵고, 코드에 박힌 설정은 값을 바꿀 때마다 다시 빌드하고 배포해야 합니다.

### 우리 코드의 예

`IssueDiscoveryController`는 서버와 프로젝트를 돌며 이슈를 모으고, 다른 서비스에 동기화를 요청하고, 그 실패까지 직접 처리합니다. 이 흐름은 웹 요청이 아닌 스케줄러 같은 곳에서 부르고 싶어도 컨트롤러에 묶여 있어 재사용할 수 없습니다.

```java
@PostMapping("/issue/loadToES/bulk/increment")
public void discoverIncrementalIssues(@RequestBody DiscoveryRequestDTO requestDTO) {
    for (ServerProjectInfo info : requestDTO.getServerProjectInfos()) { ... }   // 수집
    try {
        dwrBackendCoreClient.transferAlmDataToBackend(allCollectedIssues);       // 다른 서비스로 동기화
    } catch (Exception e) {
        log.error("Backend-Core 동기화 요청 실패", e);
    }
}
```

`OpensearchClientConfig`에서는 버퍼 크기는 설정 파일에서 읽는데, 바로 옆의 타임아웃은 코드에 숫자로 박혀 있습니다.

```java
@Value("${opensearch.buffer-limit-mb:300}") private int bufferLimitMb;   // 설정에서 읽음
.withConnectTimeout(60000)                                               // 코드에 고정
```

### 이렇게 바꾼다

업무 흐름은 서비스로 옮기고 컨트롤러는 요청을 서비스에 넘기기만 합니다.

```java
@PostMapping("/issue/loadToES/bulk/increment")
public void discoverIncrementalIssues(@RequestBody DiscoveryRequestDTO requestDTO) {
    issueDiscoveryService.discoverIncrementalAndSync(requestDTO);
}
```

타임아웃도 버퍼 크기처럼 설정에서 읽도록 바꿉니다. 이제 운영 중에 값을 조정할 때 다시 배포하지 않아도 됩니다.

```java
@Value("${opensearch.connect-timeout-ms:60000}") private int connectTimeoutMs;
```

### 가이드 방향

컨트롤러는 요청을 받아 검증하고 서비스에 넘기는 일만 합니다. 반복, 다른 서비스 호출, 실패 처리 같은 흐름은 서비스에 둡니다.

외부 라이브러리의 클래스가 우리 업무 코드 곳곳에 퍼지지 않게 합니다. 외부 라이브러리를 직접 다루는 코드는 한 곳(어댑터)에 모으고, 나머지 코드는 우리가 정의한 타입만 쓰게 하면 라이브러리를 바꿀 때 그 한 곳만 고치면 됩니다.

운영 중에 바뀔 수 있는 값(주소, 타임아웃, 버전)은 코드에 쓰지 않고 설정으로 뺍니다.

이 카테고리는 여러 파일에 걸친 큰 변경이 되기 쉽습니다. 어떻게 나눌지 먼저 팀과 공유하고, 여러 번의 작은 커밋으로 나눠서 진행합니다.

---

## RF-12 동시성 — 여러 요청이 함께 쓰는 변수를 없앤다

### 언제 필요한가

여러 요청이 동시에 읽고 쓰는 변수가 있을 때입니다. 스프링 서비스 빈은 애플리케이션 전체에 하나만 만들어져서 모든 요청이 함께 쓰므로, 빈의 필드에 값을 저장하면 요청끼리 그 값을 덮어쓸 수 있습니다. 이런 문제는 평소에는 드러나지 않다가 요청이 몰릴 때 가끔씩만 나타나서 원인을 찾기가 아주 어렵습니다.

### 우리 코드의 예

`StateMappingCacheService`는 `static` 필드에 값을 저장하고, 요청이 올 때마다 그 값을 덮어씁니다. 여러 스레드가 동시에 쓰는 것에 대한 보호 장치가 없어서, 한 스레드가 쓴 값이 다른 스레드에 제때 보이지 않을 수도 있습니다.

```java
@Service
public class StateMappingCacheService {
    private static StateMappingInfo cachedStateMappingInfo;

    public StateMappingInfo getStateMappingInfo() {
        StateMappingInfo latest = fetchStateMappingInfo();
        if (latest != null) cachedStateMappingInfo = latest;     // 요청마다 덮어쓴다
        return cachedStateMappingInfo;
    }
}
```

### 이렇게 바꾼다

빈은 이미 하나뿐이므로 `static`을 쓸 이유가 없습니다. 여러 스레드가 안전하게 읽고 쓸 수 있는 `AtomicReference`로 바꾸고, 메소드 이름도 실제 동작에 맞춥니다.

```java
@Service
public class StateMappingCacheService {
    private final AtomicReference<StateMappingInfo> lastKnown = new AtomicReference<>();

    public StateMappingInfo fetchOrLastKnown() {
        StateMappingInfo latest = fetchStateMappingInfo();
        if (latest != null) lastKnown.set(latest);
        return lastKnown.get();
    }
}
```

### 가이드 방향

요청마다 달라지는 값은 빈의 필드에 두지 않고 메소드 안의 지역 변수로 다룹니다. 지역 변수는 요청마다 따로 만들어지므로 서로 섞일 일이 없습니다.

여러 요청이 정말로 값을 공유해야 한다면 `AtomicReference`나 `ConcurrentHashMap`처럼 동시 접근을 안전하게 처리해 주는 타입을 씁니다.

스레드를 만들거나 작업을 예약하는 코드는 업무 로직과 다른 클래스로 분리합니다. 그래야 업무 로직은 동시성을 신경 쓰지 않고 테스트할 수 있습니다.

가끔씩만 실패하는 테스트가 있다면 운이 나빴다고 넘기지 말고 동시성 문제를 의심해 봅니다.

---

## VO와 도메인 객체 — 언제 나눠야 하나

### 먼저 용어

우리 팀에서 **DTO는 요청을 받는 객체**, **VO는 응답으로 내보내는 객체**입니다. **도메인 객체**는 "서버 접속 정보", "요구사항"처럼 업무 개념을 표현하고 그 개념에 대한 규칙을 가진 객체입니다. Entity나 서비스 안에서 업무를 처리할 때 쓰는 객체가 여기에 해당합니다.

둘의 차이는 **누가 모양을 정하느냐**입니다. 도메인 객체의 모양은 업무가 정하고, VO의 모양은 그 응답을 받는 화면이나 호출자가 정합니다. 그래서 도메인 객체는 업무 규칙이 바뀔 때 바뀌고, VO는 화면이나 API 요구가 바뀔 때 바뀝니다.

### 언제 필요한가

처음에는 화면에 보여 주는 값과 업무에서 쓰는 값이 거의 같아서, VO 하나를 응답에도 쓰고 서비스 안에서도 인자로 넘기며 쓰게 됩니다. **이렇게 한 클래스를 함께 쓰는 것 자체는 문제가 아닙니다.** 둘을 미리 나눠 두면 필드를 옮겨 담는 코드만 늘어나고, 그 코드도 관리해야 하기 때문입니다.

문제는 시간이 지나면서 업무에 필요한 값과 밖에 보여 줄 값이 달라질 때 생깁니다. 한 클래스가 두 역할을 하고 있으면, 업무에 필요한 값이 응답으로 새어 나가거나, 화면을 고치다가 업무 처리가 깨집니다. 아래 "가이드 방향"의 네 가지 중 하나라도 해당하면 그때 나눕니다.

### 우리 코드의 예

`ServerInfoVO`는 응답 객체로 만들어졌지만, 실제로는 서비스·변환기·전략 클래스 71곳에서 메소드 인자로 쓰이는 **서버 접속 정보 도메인 객체** 역할을 하고 있습니다. 업무에는 ALM 서버에 접속할 비밀번호나 토큰이 필요하므로 그 값도 들고 있습니다.

```java
@Getter @Builder
public class ServerInfoVO {
    private String connectId;
    private String userId;
    private String passwordOrToken;      // 업무(서버 접속)에 필요한 값
    private String type;
    private String uri;
    ...
}

// 같은 클래스가 응답으로도 그대로 나간다
public List<ServerInfoVO> serverInfoListByConnectIds(@RequestParam List<String> connectIds) { ... }
```

`passwordOrToken`에는 응답에서 빼는 장치가 없어서, 이 목록을 조회하면 **토큰이 응답 JSON에 그대로 담깁니다.** 업무에 필요한 값과 밖에 보여 줄 값이 달라졌는데 한 클래스를 계속 함께 쓰고 있어서 생긴 문제입니다.

### 이렇게 바꾼다

**급한 불은 필드 단위로 막습니다.** 문제가 되는 필드가 한두 개라면 클래스를 나누지 않고도 응답에서만 빼낼 수 있습니다.

```java
@JsonIgnore
private String passwordOrToken;          // 서비스 안에서는 그대로 쓰고, 응답 JSON 에서만 빠진다
```

**업무용과 응답용의 모양이 계속 갈라진다면 클래스를 나눕니다.** 업무 개념과 그 규칙은 도메인 객체에 두고, 응답 VO는 도메인 객체에서 밖에 보여 줄 값만 골라 만듭니다.

```java
// 도메인 객체 — 서비스 안에서 인자로 주고받는 쪽
public class ServerInfo {
    private final String connectId;
    private final String passwordOrToken;
    private final ServerType type;
    private final String uri;

    public boolean isCloud() { return type == ServerType.CLOUD; }    // 업무 규칙은 여기에
}

// 응답 VO — 밖에 보여 줄 값만
@Getter @Builder
public class ServerInfoVO {
    private String connectId;
    private String typeLabel;            // 화면용으로 다듬은 값
    private String uri;

    public static ServerInfoVO from(ServerInfo server) {
        return ServerInfoVO.builder()
                .connectId(server.getConnectId())
                .typeLabel(server.isCloud() ? "Jira Cloud" : "Jira On-Premise")
                .uri(server.getUri())
                .build();                // 토큰은 처음부터 담지 않는다
    }
}
```

이렇게 나누면 서비스 코드는 `ServerInfo`만 보고 일하고, 화면에 무엇을 보여 줄지는 `ServerInfoVO`만 고치면 됩니다.

### 가이드 방향

기본은 **함께 써도 됩니다.** 단순한 조회·등록처럼 보여 주는 값과 업무에서 쓰는 값이 거의 같고, 우리 팀 안에서만 쓰는 API라면 VO 하나로 충분합니다.

다음 네 가지 중 하나라도 해당하면 **나눕니다.**

**첫째, 밖에 보여 주면 안 되는 값이 생겼을 때.** 토큰, 비밀번호, 내부 관리용 상태처럼 업무에는 필요하지만 응답에 나가면 안 되는 필드가 있는 경우입니다. 이것은 발견하는 즉시 막아야 합니다. 필드가 한두 개라면 `@JsonIgnore`로 응답에서만 빼고, 여러 개라면 클래스를 나눕니다.

**둘째, 받는 쪽마다 원하는 모양이 다를 때.** 같은 데이터를 어떤 화면은 요약으로, 어떤 화면은 상세로 원해서 한 클래스에 이쪽저쪽 필드가 계속 붙는 경우입니다. 한 화면을 고쳤더니 다른 화면이 깨지기 시작하면 나눌 때입니다. 이때는 화면마다 VO를 따로 두고, 모두 같은 도메인 객체에서 만듭니다.

**셋째, 외부에 공개된 API일 때.** 다른 팀이나 다른 시스템, 고객사가 받아 가는 응답이라면, 내부 구조를 고칠 때마다 응답 모양이 바뀌어서는 안 됩니다. 응답 VO를 따로 두면 내부를 자유롭게 고쳐도 응답은 그대로 유지됩니다.

**넷째, 업무 규칙이 쌓이기 시작할 때.** 응답 VO 안에 판단 로직이 늘어나거나, 같은 판단이 여러 VO에 복사되기 시작하는 경우입니다. 그 규칙을 도메인 객체로 옮기면서 나눕니다.

나누든 나누지 않든, **응답 VO 안에 두어도 되는 것과 두지 말아야 할 것**은 같습니다. 도메인 객체나 Entity에서 자신을 만드는 변환 로직(`from()`, `fromEntity()`)은 길어도 VO 안에 둡니다. 자기 필드만으로 계산되는 표시용 값(완료 수와 전체 수로 계산한 진행률 등)도 괜찮습니다. 하지만 저장소를 조회하거나 다른 서비스를 불러야 하는 판단, 응답이 아닌 다른 흐름에서도 써야 하는 업무 규칙은 VO에 두지 않고 도메인 객체에 둡니다.

---

## 어떤 순서로 진행할까

위험이 낮고 효과가 빨리 보이는 것부터, 범위가 작은 것에서 큰 것 순으로 진행합니다.

1. **RF-00 안전망.** 손댈 코드에 테스트부터 붙입니다. 이것 없이는 다음 단계로 가지 않습니다.
2. **RF-01 정리와 RF-02 이름.** 동작을 거의 건드리지 않아 가장 안전하고, 이후 작업의 변경 범위를 작게 만들어 줍니다.
3. **RF-03부터 RF-07까지.** 메소드 분해, 인수 정리, 중복 제거, 조건 정리, 데이터 타입 정리처럼 메소드와 값 단위의 작업입니다.
4. **RF-08부터 RF-10까지.** 클래스를 나누고, 오류 처리를 바로잡고, 상속 구조를 정리하는 클래스 단위의 작업입니다. 앞 단계에서 메소드가 정리되어 있어야 쉽게 나눌 수 있습니다.
5. **RF-11과 RF-12.** 여러 파일과 모듈에 걸친 구조 변경입니다. 계획을 먼저 공유하고 나눠서 진행합니다.
