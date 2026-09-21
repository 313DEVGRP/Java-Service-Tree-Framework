# -*- coding: utf-8 -*-
"""엔드포인트 → 컨트롤러 메서드 → 호출 메서드 → Feign 카탈로그 생성."""
import io, os, re, csv, json, collections

# ── 대상 저장소 · 출력 경로 (환경변수로 지정, 없으면 Backend-Core 기본값) ──
_REPO = os.environ.get('CATALOG_REPO', 'Java-Service-Tree-Framework-Backend-Core')
_TASK = os.environ.get('CATALOG_TASK', 'tasks/api-catalog')

ROOT = _REPO + '/src/main/java'
OUT = _TASK + '/artifacts'
read = lambda p: io.open(p, encoding='utf-8', errors='replace').read()

java = []
for dp, dn, fn in os.walk(ROOT):
    for f in fn:
        if f.endswith('.java'):
            java.append(os.path.join(dp, f).replace('\\', '/'))

MAP = re.compile(r'@(Get|Post|Put|Delete|Patch|Request)Mapping\s*(?:\(([^)]*)\))?', re.S)
STR = re.compile(r'"([^"]*)"')
RM = re.compile(r'RequestMethod\.(GET|POST|PUT|DELETE|PATCH)')
SIG = re.compile(r'(?:public\s+|protected\s+|default\s+)?(?:static\s+)?'
                 r'(?:final\s+)?([\w<>,\[\]\s\.\?]+?)\s+(\w+)\s*\(')
CLS = re.compile(r'(?:public\s+)?(?:abstract\s+)?class\s+(\w+)(?:\s*<[^>]*>)?\s*'
                 r'(?:extends\s+(\w+))?')
# 주입 필드: 타입 + 변수명
FIELD = re.compile(r'(?:@Autowired|@Resource[^;\n]*|private\s+final|private|protected)\s+'
                   r'((?:[A-Z]|[가-힣])\w*)(?:<[^>]*>)?\s+(\w+)\s*[;=]')

def body(src, start):
    """start = 파라미터 여는 '(' 직후.
    파라미터 괄호를 짝 맞춰 닫은 뒤에야 본문 '{' 를 찾는다.
    (파라미터 안의 @Validated({X.class}) 같은 중괄호를 본문으로 오인하지 않기 위함)"""
    d, j = 1, start
    while j < len(src) and d > 0:          # 파라미터 ')' 까지
        if src[j] == '(':
            d += 1
        elif src[j] == ')':
            d -= 1
        j += 1
    if d != 0:
        return ''
    k = src.find(';', j)                    # 추상/인터페이스 메서드면 본문 없음
    i = src.find('{', j)
    if i < 0 or (0 <= k < i):
        return ''
    d, j = 0, i
    while j < len(src):
        if src[j] == '{':
            d += 1
        elif src[j] == '}':
            d -= 1
            if d == 0:
                return src[i:j + 1]
        j += 1
    return src[i:]

# Feign 인터페이스 → 메서드명
feign = {}
for p in java:
    src = read(p)
    if '@FeignClient' not in src:
        continue
    nm = re.search(r'(?:interface|class)\s+(\w+)', src).group(1)
    a = re.search(r'@FeignClient\s*\(([^)]*)\)', src, re.S)
    a = a.group(1) if a else ''
    names = set()
    for m in MAP.finditer(src):
        sm = SIG.search(src, m.end())
        if sm:
            names.add(sm.group(2))
    feign[nm] = {
        'name': (re.search(r'name\s*=\s*"([^"]*)"', a).group(1)
                 if re.search(r'name\s*=\s*"([^"]*)"', a) else ''),
        'methods': names,
    }
FEIGN_TYPES = set(feign)

# 서비스 구현체 인덱스: 클래스명 → (파일, 소스)
impl_src = {}
for p in java:
    src = read(p)
    m = CLS.search(src)
    if m:
        impl_src.setdefault(m.group(1), (p.replace(ROOT + '/', ''), src))

# 인터페이스 → 구현체 후보
iface_impl = {}
for cls, (rel, src) in impl_src.items():
    im = re.search(r'class\s+\w+[^{]*?implements\s+([\w<>,\.\s]+?)\s*\{', src, re.S)
    if im:
        for i in re.findall(r'\b([A-Z]\w+)', im.group(1)):
            iface_impl.setdefault(i, []).append(cls)

def feign_in_method(cls, meth):
    """구현체의 특정 메서드 본문 안에서만 Feign 호출을 수집한다."""
    if cls not in impl_src:
        return set()
    rel, src = impl_src[cls]
    fields = {v: t for t, v in FIELD.findall(src)}
    out = set()
    for sm in re.finditer(r'\b%s\s*\(' % re.escape(meth), src):
        ln0 = src.rfind('\n', 0, sm.start())
        decl = src[ln0:sm.start()]
        if not re.search(r'[\w>\]]\s+$', decl):   # 선언부만 (앞이 반환형)
            continue
        b = body(src, sm.end())
        if not b:
            continue
        for var, typ in fields.items():
            if typ not in FEIGN_TYPES:
                continue
            for mm in re.finditer(r'\b%s\s*\.\s*(\w+)\s*\(' % re.escape(var), b):
                if mm.group(1) in feign[typ]['methods']:
                    out.add('%s.%s' % (typ, mm.group(1)))
    return out

# 클래스별 자체 필드 + 부모 상속 필드
own_fields, parent_of = {}, {}
for _cls, (_rel, _src) in impl_src.items():
    own_fields[_cls] = {v: t for t, v in FIELD.findall(_src)}
    _m = CLS.search(_src)
    parent_of[_cls] = (_m.group(2) or '') if _m else ''

def all_fields(cls, seen=None):
    seen = seen or set()
    if not cls or cls in seen or cls not in own_fields:
        return {}
    seen.add(cls)
    f = dict(all_fields(parent_of.get(cls, ''), seen))
    f.update(own_fields[cls])
    return f

rows = []
for p in java:
    src = read(p)
    head = src[:CLS.search(src).start()] if CLS.search(src) else src
    if '@RestController' not in head and '@Controller' not in head:
        continue
    cm = CLS.search(src)
    cls = cm.group(1)
    rel = p.replace(ROOT + '/', '')
    bm = re.search(r'@RequestMapping\s*\(([^)]*)\)', head, re.S)
    base = ''
    if bm:
        q = STR.findall(bm.group(1))
        base = q[0] if q else ''
    fields = all_fields(cls)

    for m in MAP.finditer(src):
        if m.start() < cm.start():
            continue
        verb = m.group(1).upper()
        a = m.group(2) or ''
        if verb == 'REQUEST':
            r = RM.search(a)
            verb = r.group(1) if r else 'ANY'
        q = [x for x in STR.findall(a) if x.startswith('/') or
             (x and 'application' not in x and 'charset' not in x)]
        path = q[0] if q else ''
        full = re.sub(r'/+', '/', base + ('' if path.startswith('/') or not path
                                          else '/') + path) or base or '/'
        sm = SIG.search(src, m.end())
        if not sm:
            continue
        jm = sm.group(2)
        b = body(src, sm.end())
        line = src[:m.start()].count('\n') + 1

        calls, fcalls, types = [], set(), set()
        for var, typ in fields.items():
            for mm in re.finditer(r'\b%s\s*\.\s*(\w+)\s*\(' % re.escape(var), b):
                calls.append('%s.%s' % (var, mm.group(1)))
                types.add(typ)
                if typ in FEIGN_TYPES and mm.group(1) in feign[typ]['methods']:
                    fcalls.add('%s.%s' % (typ, mm.group(1)))
        # 서비스 구현체를 1홉 더 들어가 Feign 확인
        downstream = set()
        for c in set(calls):
            var, _, meth = c.partition('.')
            t = fields.get(var)
            if not t or t in FEIGN_TYPES:
                continue
            for impl in iface_impl.get(t, []) + ([t] if t in impl_src else []):
                downstream |= feign_in_method(impl, meth)
        # 호출이 안 잡힌 경우 사유 분류
        note = ''
        if not calls:
            own = set(re.findall(r'(?:private|protected|public)\s+[\w<>,\[\]\.\?\s]+?\s+(\w+)\s*\(', src))
            local = sorted({mm.group(1) for mm in re.finditer(r'\b(\w+)\s*\(', b)
                            if mm.group(1) in own and mm.group(1) != jm})
            note = ('로컬 메서드 경유: ' + ' '.join(local[:4])) if local else '주입 빈 호출 없음(직접 응답)'

        rows.append({
            'http': verb, 'path': full, 'controller': cls, 'method': jm,
            'file': rel, 'line': line, 'note': note,
            'calls': sorted(set(calls)),
            'feign_direct': sorted(fcalls),
            'feign_via_service': sorted(downstream - fcalls),
        })

os.makedirs(OUT, exist_ok=True)
io.open(OUT + '/_catalog.json', 'w', encoding='utf-8', newline='\n').write(
    json.dumps(rows, ensure_ascii=False, indent=1))

print('자체 선언 엔드포인트 행: %d' % len(rows))
print('호출 메서드 추출된 행: %d' % len([r for r in rows if r['calls']]))
print('Feign 직접 호출 행: %d' % len([r for r in rows if r['feign_direct']]))
print('Feign 서비스경유 행: %d' % len([r for r in rows if r['feign_via_service']]))
