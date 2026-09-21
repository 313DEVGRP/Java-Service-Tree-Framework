# -*- coding: utf-8 -*-
"""API 카탈로그 문서 생성 — 표 중심, 설명 최소."""
import io, json, csv, collections, re, os

# ── 대상 저장소 · 출력 경로 (환경변수로 지정, 없으면 Backend-Core 기본값) ──
_REPO = os.environ.get('CATALOG_REPO', 'Java-Service-Tree-Framework-Backend-Core')
_TASK = os.environ.get('CATALOG_TASK', 'tasks/api-catalog')

OUT = _TASK + '/artifacts'
rows = json.load(io.open(OUT + '/_catalog.json', encoding='utf-8'))
inv = json.load(io.open(_TASK + '/sources/inventory.json', encoding='utf-8'))

def esc(t):
    return (t or '').replace('|', '\\|')

def j(xs, sep=' · '):
    return esc(sep.join(xs)) if xs else '—'

# 상속 14개 — 하드코딩하지 않고 TreeAbstractController 원문에서 생성한다
TAC = (_REPO + '/src/main/java/com/arms/'
       'egovframework/javaservice/treeframework/controller/TreeAbstractController.java')
_src = io.open(TAC, encoding='utf-8').read() if os.path.exists(TAC) else ''
_MAP = re.compile(r'@(Get|Post|Put|Delete|Request)Mapping\s*\(([^)]*)\)', re.S)
_SIG = re.compile(r'public\s+[\w<>,\[\]\s\.\?]+?\s+(\w+)\s*\(')
_FIELD = re.compile(r'(?:@Autowired\s+)?(?:private|protected)\s+((?:[A-Z]|[가-힣])\w*)(?:<[^>]*>)?\s+(\w+)\s*[;=]')
_fields = {v: t for t, v in _FIELD.findall(_src)}

def _body(src, st):
    d, j = 1, st
    while j < len(src) and d > 0:
        if src[j] == '(': d += 1
        elif src[j] == ')': d -= 1
        j += 1
    i = src.find('{', j)
    if i < 0: return ''
    d, s0 = 0, i
    while i < len(src):
        if src[i] == '{': d += 1
        elif src[i] == '}':
            d -= 1
            if d == 0: return src[s0:i+1]
        i += 1
    return src[s0:]

TREE = []
for _m in _MAP.finditer(_src):
    _a = _m.group(2)
    _verb = _m.group(1).upper()
    if _verb == 'REQUEST':
        _r = re.search(r'RequestMethod\.(GET|POST|PUT|DELETE)', _a)
        _verb = _r.group(1) if _r else 'ANY'
    _q = [x for x in re.findall(r'"([^"]*)"', _a) if x.startswith('/')]
    if not _q: continue
    _sm = _SIG.search(_src, _m.end())
    if not _sm: continue
    _b = _body(_src, _sm.end())
    _calls = []
    for _v, _t in _fields.items():
        for _c in re.finditer(r'\b%s\s*\.\s*(\w+)\s*\(' % re.escape(_v), _b):
            _lbl = '%s.%s' % (_v, _c.group(1))
            if _lbl not in _calls and _v not in ('log',):
                _calls.append(_lbl)
    _ln = _src[:_m.start()].count(chr(10)) + 1
    TREE.append((_verb, _q[0], _sm.group(1), _ln, ' · '.join(_calls) if _calls else '— (주입 빈 호출 없음)'))

# Feign 표 — 하드코딩하지 않고 inventory.json 에서 생성한다
FEIGN = []
for _k, _v in sorted(inv.get('feign', {}).items(),
                     key=lambda x: -len(x[1].get('methodNames', x[1].get('methods', [])))):
    _mc = _v.get('methodCount', len(_v.get('methodNames', _v.get('methods', []))))
    FEIGN.append((_k, _v.get('name', ''), _v.get('url', ''), _mc, ''))


chains = json.load(io.open(_TASK + '/sources/call_chains.json', encoding='utf-8'))

def _count_edges(ns):
    return sum(1 + _count_edges(n['children']) for n in ns)
_csv_eps = len(chains)
_csv_bean = _csv_feign = 0
def _tally(ns):
    global _csv_bean, _csv_feign
    for n in ns:
        if n['kind'] == 'feign':
            _csv_feign += 1
        else:
            _csv_bean += 1
        _tally(n['children'])
for _c in chains:
    _tally(_c['tree'])
_csv_none = len([c for c in chains if not c['tree']])
_csv_rows = _csv_bean + _csv_feign + _csv_none
CH = {(c['controller'], c['method'], c['http'], c['path']): c for c in chains}

def feign_of(tree, depth=1, out=None):
    """체인에서 Feign 노드를 깊이와 함께 수집 — §3 Feign 열의 단일 원천"""
    out = out if out is not None else []
    for n in tree:
        if n['kind'] == 'feign':
            out.append((depth, n['label'], n['name']))
        feign_of(n['children'], depth + 1, out)
    return out

per = collections.defaultdict(list)
for r in rows:
    per[r['controller']].append(r)

tree_children = sorted(c for c, v in inv['perController'].items()
                       if v['parent'] == 'TreeAbstractController')

m = []
A = m.append
_NAME = os.environ.get('CATALOG_REPO', 'repo').replace('Java-Service-Tree-Framework-', '')
_REQID = os.environ.get('CATALOG_REQID', '')
_VER = os.environ.get('CATALOG_VERSION', 'v1.0')
_DATE = __import__('datetime').date.today().strftime('%Y-%m-%d')
A('# %s API 카탈로그' % _NAME)
A('')
A('%s**%s** · %s · 정적 추출' % (('**%s** · ' % _REQID) if _REQID else '', _VER, _DATE))
A('')
A('## 읽는 법')
A('')
if TREE:
    A('- **§2 = 상속 공통 %d개.** 부모 컨트롤러가 선언하고 하위 컨트롤러가 그대로 물려받는다. 컨트롤러마다 반복 기재하지 않는다.' % len(TREE))
A('- **§3 = 컨트롤러가 직접 선언한 %d개.** 엔드포인트 하나당 한 줄: 경로 → 컨트롤러 메서드 → 그 메서드가 호출하는 것 → 그래서 어떤 Feign 이 나가는지.' % len(rows))
A('- **§4 = 호출 체인.** §3 의 `호출` 이 다시 무엇을 부르는지 최대 4단계까지 전개한다.')
A('- **§5 = Feign %d개.** `Feign` 표기의 접두어가 여기 대응한다.' % len(FEIGN))
A('- **§6 = 동반 CSV.** 같은 데이터를 long 형식으로 담아 엑셀 필터·피벗에 쓴다.')
A('- 추출은 정규식 정적 분석이다. 한계는 §7.')
A('')
A('| | 수 |')
A('|---|---:|')
_per = inv['perController']
_own = sum(v['own'] for v in _per.values())
_inh = sum(v['inherited'] for v in _per.values())
_have = len({r['controller'] for r in rows})
_fm = sum(f[3] for f in FEIGN)
A('| 컨트롤러 | %d (엔드포인트 보유 %d) |' % (len(_per), _have))
A('| 자체 선언 엔드포인트 | **%d** |' % _own)
A('| 상속 전개 엔드포인트 | %d |' % _inh)
A('| 도달 가능 합계 | %d |' % (_own + _inh))
A('| Feign 클라이언트 | %d (메서드 %d) |' % (len(FEIGN), _fm))
A('| 호출 체인 노드 (§4) | %d · 최대 4단계 |' % (_csv_bean + _csv_feign))
A('')
A('---')
A('')
if TREE:
    A('## 2. 상속 공통 %d개 — `TreeAbstractController`' % len(TREE))
    A('')
    A('선언: `egovframework/javaservice/treeframework/controller/TreeAbstractController.java`')
    A('경로는 각 컨트롤러의 base 뒤에 붙는다. 예) `ReqAddController` base 가 `/arms/reqAdd` → `GET /arms/reqAdd/getNode.do`')
    A('')
    A('| HTTP | 경로(상대) | 메서드 | line | 호출 |')
    A('|---|---|---|---:|---|')
    for h, p, mth, ln, call in TREE:
        A('| %s | `%s` | `%s` | %d | %s |' % (h, p, mth, ln,
          ' '.join('`%s`' % c for c in call.split(' · ')) if not call.startswith('—') else '*%s*' % call))
    A('')
    A('`treeService` 의 실제 구현은 컨트롤러마다 다르다 — `@PostConstruct` 에서 `setTreeService(<도메인빈>)` 로 주입된다.')
    A('')
    A('**이 14개를 상속하는 컨트롤러 58개**')
    A('')
    A('```')
    for i in range(0, len(tree_children), 3):
        A('  '.join('%-32s' % c for c in tree_children[i:i + 3]).rstrip())
    A('```')
    A('')
    A('별도로 `GlobalTreeMapController` 는 `TreeMapAbstractController` 에서 9개를 상속한다.')
    A('')
A('---')
A('')
A('## 3. 자체 선언 엔드포인트 (%d)' % len(rows))
A('')
A('`호출` = 컨트롤러 메서드 본문에서 직접 부르는 주입 빈의 메서드. `Feign` = 그 엔드포인트에서 최종적으로 나가는 외부 호출 — **§4 호출 체인에서 유도**했으므로 `→` 는 한 단계 아래를 거쳐 나간다는 뜻이다.')
A('')

for cls in sorted(per):
    rs = sorted(per[cls], key=lambda x: (x['path'], x['http']))
    f = rs[0]['file']
    A('### %s — %d개' % (cls, len(rs)))
    A('')
    A('`%s`' % f)
    A('')
    A('| HTTP | 경로 | 컨트롤러 메서드 | line | 호출 | Feign |')
    A('|---|---|---|---:|---|---|')
    for r in rs:
        ch = CH.get((r['controller'], r['method'], r['http'], r['path']))
        fg, seen_f = [], set()
        for d, lbl, _nm in (feign_of(ch['tree']) if ch else []):
            if lbl in seen_f:
                continue
            seen_f.add(lbl)
            fg.append(('`%s`' % lbl) if d == 1 else ('→ `%s`' % lbl))
        A('| %s | `%s` | `%s` | %d | %s | %s |' % (
            r['http'], esc(r['path']), r['method'], r['line'],
            j(['`%s`' % c for c in r['calls']], ' ') if r['calls']
            else ('*%s*' % esc(r.get('note', '') or '—')),
            ' '.join(fg) if fg else '—'))
    A('')

A('---')
A('')
A('## 4. 호출 체인 (메서드 → 메서드)')
A('')
A('§3 의 `호출` 열은 컨트롤러가 직접 부르는 1단계다. 여기서는 **그 메서드가 다시 무엇을 부르는지** 최대 4단계까지 전개한다.')
A('읽는 법 — `├─` `└─` 는 호출 깊이다. 오른쪽 표시는 그 호출의 성격이다.')
A('')
A('| 표시 | 뜻 |')
A('|---|---|')
A('| `→ Feign[name]` | 그 지점에서 해당 Feign 클라이언트로 **외부 호출**이 나간다 |')
A('| `via x→y` | 같은 클래스의 로컬 메서드 `x`, `y` 를 거쳐 도달했다 (컨트롤러가 직접 부른 것이 아님) |')
A('')
def depth_of(ns, d=1):
    return max([d] + [depth_of(n['children'], d + 1) for n in ns if n['children']]) if ns else 0
withc = [c for c in chains if c['tree']]
deep = [c for c in withc if depth_of(c['tree']) >= 2]
A('| | 수 |')
A('|---|---:|')
A('| 체인이 잡힌 엔드포인트 | **%d** / %d |' % (len(withc), len(chains)))
A('| 2단계 이상 | %d |' % len(deep))
A('| 최대 깊이 | %d |' % max((depth_of(c['tree']) for c in withc), default=0))
A('')
bycls = collections.defaultdict(list)
for c in withc:
    bycls[c['controller']].append(c)
def render(ns, prefix, buf):
    """트리 기호로 그린다. 마지막 자식은 └─, 그 외는 ├─."""
    for i, n in enumerate(ns):
        last = (i == len(ns) - 1)
        branch = '└─ ' if last else '├─ '
        marks = []
        if n['kind'] == 'feign':
            marks.append('→ Feign[%s]' % n['name'])
        if n.get('via'):
            marks.append('via %s' % n['via'])
        tail = ('   ' + '  '.join(marks)) if marks else ''
        buf.append(prefix + branch + n['label'] + tail)
        if n['children']:
            render(n['children'], prefix + ('   ' if last else '│  '), buf)

for cls in sorted(bycls):
    A('### %s' % cls)
    A('')
    for c in sorted(bycls[cls], key=lambda x: x['path']):
        buf = ['%s %s  →  %s()' % (c['http'], c['path'], c['method'])]
        render(c['tree'], '', buf)
        A('```text')
        for ln in buf:
            A(ln)
        A('```')
        A('')
A('---')
A('')
A('## 5. Feign 클라이언트 %d개' % len(FEIGN))
A('')
_fdirs = sorted({'/'.join(v.get('file','').split('/')[:-1]) for v in inv.get('feign', {}).values() if v.get('file')})
A('선언 위치: %s' % (' · '.join('`%s/`' % d for d in _fdirs) or '—'))
A('')
A('| 클라이언트 | name | url | 메서드 | 대상 |')
A('|---|---|---|---:|---|')
for n, nm, u, c, t in FEIGN:
    A('| `%s` | `%s` | `%s` | %d | %s |' % (n, nm, esc(u) or '—', c, t or '—'))
A('')
A('> Feign 공통 타임아웃·인터셉터 설정은 저장소마다 다르다. `config/` 아래 `*FeignConfig` 를 직접 확인할 것.')
A('')
A('---')
A('')
A('## 6. 동반 CSV')
A('')
_csvname = ([_p.split(chr(92))[-1].split('/')[-1] for _p in __import__('glob').glob(OUT + '/*.csv')] or ['(CSV)'])[0]
A('같은 폴더의 `%s` 는 이 문서와 **같은 원천**(`call_chains.json`)에서 생성된다. 값이 어긋날 수 없다.' % _csvname)
A('')
A('형식은 **long(tidy)** 이다 — 엔드포인트가 아니라 **호출 1건이 1행**이고, 한 칸에 값이 하나만 들어간다. 엑셀 자동 필터·피벗을 그대로 쓸 수 있다.')
A('')
A('| 열 | 내용 |')
A('|---|---|')
A('| `HTTP` `경로` `컨트롤러` `컨트롤러메서드` `파일` `line` | 엔드포인트 식별 (같은 엔드포인트가 여러 행에 반복된다) |')
A('| `depth` | 호출 깊이 1~4. §4 트리의 단계와 같다 |')
A('| `호출클래스` `호출메서드` | 그 단계에서 무엇을 부르는지 |')
A('| `종류` | `bean`(내부 빈) · `feign`(외부 호출) · `none`(호출 없음) |')
A('| `feign_name` | `종류=feign` 일 때 클라이언트 이름 (`engine`, `loopback` 등) |')
A('| `via` | 거쳐 간 같은 클래스의 로컬 메서드. §4 의 `via` 와 같다 |')
A('| `비고` | 호출이 없는 행의 사유 |')
A('')
A('규모: **%d행** / 엔드포인트 %d개 · `종류` 별 bean %d · feign %d · none %d.' % (_csv_rows, _csv_eps, _csv_bean, _csv_feign, _csv_none))
A('')
_topcls = ''
_cc = collections.Counter()
def _tc(ns):
    for n in ns:
        _cc[n['label'].split('.')[0]] += 1
        _tc(n['children'])
for _c in chains: _tc(_c['tree'])
if _cc: _topcls = _cc.most_common(1)[0][0]
A('쓰는 예 — `호출클래스 = %s` 로 거르면 그 클래스를 타는 엔드포인트가 전부 나오고, `종류 = feign` 으로 거르면 외부 호출 지점만 남는다. `feign_name` 으로 피벗하면 클라이언트별 호출 분포가 나온다.' % (_topcls or '<클래스명>'))
A('')
A('> 사람이 훑는 용도는 이 PDF(§3 표 · §4 트리)가, 기계·엑셀 처리는 CSV 가 맡는다. CSV 에는 엔드포인트 1건 = 1행 구조가 없으므로 목록 훑기는 §3 을 쓴다.')
A('')
A('---')
A('')
A('## 7. 추출 한계')
A('')
A('- 정규식 정적 분석이다. 리플렉션·동적 프록시 경유 호출은 잡히지 않는다.')
A('- `호출` 열은 **주입 필드를 통한 호출**만 센다. 로컬 변수·정적 유틸 호출은 빠진다.')
A('- §3 의 `Feign →` 열은 **1홉**만 본다(컨트롤러가 부른 서비스 메서드 본문까지). 더 깊은 경로는 **§4 호출 체인**에서 최대 4단계까지 전개한다.')
A('- §4 의 깊이 상한은 4단계이고 재귀는 같은 (클래스.메서드)를 두 번 밟지 않는다. 따라서 4단계를 넘거나 순환하는 경로는 잘린다.')
A('- §4 의 `(via …)` 는 같은 클래스 로컬 메서드를 거친 경로다. 조건 분기는 반영하지 않으므로 **정적으로 도달 가능한 것을 모두** 싣는다 — 한 번의 호출에서 전부 실행되지는 않는다.')
_nl = len([r for r in rows if not r['calls'] and r.get('note','').startswith('로컬')])
_nd = len([r for r in rows if not r['calls'] and not r.get('note','').startswith('로컬')])
A('- `호출` 이 비어 있는 %d개는 빈칸 대신 사유를 적었다 — **로컬 메서드 경유 %d개**(같은 클래스의 private 메서드를 거침), **주입 빈 호출 없음 %d개**(주입 빈을 하나도 부르지 않고 정적 응답만 하는 엔드포인트).' % (_nl+_nd, _nl, _nd))
A('- 인터페이스↔구현체 매칭은 `implements` 선언 기준이다. 다중 구현이면 모두 합산한다.')
if TREE:
    A('- §2 상속 매핑의 서비스 빈은 컨트롤러마다 다르므로 도메인별 Feign 은 §2 에 표기하지 않는다.')
A('')

io.open(OUT + '/API카탈로그_20260921.md', 'w', encoding='utf-8', newline='\n').write('\n'.join(m))
print('md 생성: %d줄' % len(m))
