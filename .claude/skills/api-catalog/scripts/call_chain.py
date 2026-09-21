# -*- coding: utf-8 -*-
"""컨트롤러 메서드에서 시작해 메서드→메서드 호출 체인을 깊이 N 까지 전개한다."""
import io, os, re, json, collections

# ── 대상 저장소 · 출력 경로 (환경변수로 지정, 없으면 Backend-Core 기본값) ──
_REPO = os.environ.get('CATALOG_REPO', 'Java-Service-Tree-Framework-Backend-Core')
_TASK = os.environ.get('CATALOG_TASK', 'tasks/api-catalog')

ROOT = _REPO + '/src/main/java'
OUT = _TASK
MAXD = 4
read = lambda p: io.open(p, encoding='utf-8', errors='replace').read()

java = []
for dp, dn, fn in os.walk(ROOT):
    for f in fn:
        if f.endswith('.java'):
            java.append(os.path.join(dp, f).replace('\\', '/'))

MAP = re.compile(r'@(Get|Post|Put|Delete|Patch|Request)Mapping\s*(?:\(([^)]*)\))?', re.S)
STR = re.compile(r'"([^"]*)"')
RM = re.compile(r'RequestMethod\.(GET|POST|PUT|DELETE|PATCH)')
SIG = re.compile(r'(?:public\s+|protected\s+|private\s+|default\s+)?(?:static\s+)?'
                 r'(?:final\s+)?([\w<>,\[\]\s\.\?]+?)\s+(\w+)\s*\(')
CLS = re.compile(r'(?:public\s+)?(?:abstract\s+)?(?:class|interface)\s+(\w+)'
                 r'(?:\s*<[^>]*>)?\s*(?:extends\s+(\w+))?')
FIELD = re.compile(r'(?:@Autowired|@Resource[^;\n]*|private\s+final|private|protected)\s+'
                   r'((?:[A-Z]|[가-힣])\w*)(?:<[^>]*>)?\s+(\w+)\s*[;=]')

def body(src, start):
    d, j = 1, start
    while j < len(src) and d > 0:
        if src[j] == '(':
            d += 1
        elif src[j] == ')':
            d -= 1
        j += 1
    if d != 0:
        return ''
    k, i = src.find(';', j), src.find('{', j)
    if i < 0 or (0 <= k < i):
        return ''
    d, s0 = 0, i
    while i < len(src):
        if src[i] == '{':
            d += 1
        elif src[i] == '}':
            d -= 1
            if d == 0:
                return src[s0:i + 1]
        i += 1
    return src[s0:]

# 클래스 인덱스
info, feign = {}, {}
for p in java:
    src = read(p)
    cm = CLS.search(src)
    if not cm:
        continue
    cls = cm.group(1)
    rel = p.replace(ROOT + '/', '')
    is_feign = '@FeignClient' in src[:cm.start()]
    if is_feign:
        a = re.search(r'@FeignClient\s*\(([^)]*)\)', src, re.S)
        a = a.group(1) if a else ''
        nm = re.search(r'name\s*=\s*"([^"]*)"', a)
        feign[cls] = nm.group(1) if nm else ''
    info.setdefault(cls, {'file': rel, 'src': src, 'fields': {v: t for t, v in FIELD.findall(src)},
                          'feign': is_feign, 'parent': cm.group(2) or ''})

# 부모 클래스에서 상속한 주입 필드를 병합한다 (protected 필드 등)
def inherited_fields(cls, seen=None):
    seen = seen or set()
    if cls not in info or cls in seen:
        return {}
    seen.add(cls)
    f = dict(inherited_fields(info[cls]['parent'], seen))
    f.update(info[cls]['fields'])
    return f
for _c in list(info):
    info[_c]['fields'] = inherited_fields(_c)

iface_impl = collections.defaultdict(list)
for cls, i in info.items():
    im = re.search(r'class\s+\w+[^{]*?implements\s+([\w<>,\.\s]+?)\s*\{', i['src'], re.S)
    if im:
        for x in re.findall(r'\b([A-Z]\w+)', im.group(1)):
            iface_impl[x].append(cls)

def find_body(cls, meth):
    """cls(또는 구현체)에서 meth 선언부 본문을 찾는다."""
    for c in ([cls] + iface_impl.get(cls, [])):
        if c not in info:
            continue
        src = info[c]['src']
        for sm in re.finditer(r'\b%s\s*\(' % re.escape(meth), src):
            ln0 = src.rfind('\n', 0, sm.start())
            if not re.search(r'[\w>\]]\s+$', src[ln0:sm.start()]):
                continue
            b = body(src, sm.end())
            if b:
                return c, b
    return None, ''

LOCAL_DECL = re.compile(r'(?:private|protected|public)\s+[\w<>,\[\]\.\?\s]+?\s+(\w+)\s*\(')

def collect(owner, b, depth, seen, dedup, out, via=''):
    """본문 b 안의 주입 빈 호출을 모으고, 같은 클래스 로컬 메서드는 투과해 따라간다."""
    fields = info.get(owner, {}).get('fields', {})
    for var, typ in fields.items():
        for mm in re.finditer(r'\b%s\s*\.\s*(\w+)\s*\(' % re.escape(var), b):
            m2 = mm.group(1)
            k2 = '%s.%s' % (typ, m2)
            if k2 in dedup:
                continue
            dedup.add(k2)
            node = {'label': k2, 'kind': 'feign' if typ in feign else 'bean',
                    'via': via, 'children': []}
            if typ in feign:
                node['name'] = feign[typ]
            else:
                node['children'] = expand(typ, m2, depth + 1, seen)
            out.append(node)
    # 같은 클래스의 로컬 메서드 호출은 노드로 만들지 않고 투과해 들어간다
    locals_ = set(LOCAL_DECL.findall(info.get(owner, {}).get('src', '')))
    for mm in re.finditer(r'(?<![.\w])(\w+)\s*\(', b):
        lm = mm.group(1)
        if lm not in locals_:
            continue
        lk = '%s#%s' % (owner, lm)
        if lk in seen or depth > MAXD:
            continue
        seen.add(lk)
        _, lb = find_body(owner, lm)
        if lb:
            collect(owner, lb, depth, seen, dedup, out, via=(via + '→' if via else '') + lm)

def expand(cls, meth, depth, seen):
    key = '%s.%s' % (cls, meth)
    if depth > MAXD or key in seen:
        return []
    seen = set(seen) | {key}
    owner, b = find_body(cls, meth)
    if not b:
        return []
    out, dedup = [], set()
    collect(owner, b, depth, seen, dedup, out)
    return out

rows = []
for p in java:
    src = read(p)
    cm = CLS.search(src)
    if not cm:
        continue
    head = src[:cm.start()]
    if '@RestController' not in head and '@Controller' not in head:
        continue
    cls = cm.group(1)
    bm = re.search(r'@RequestMapping\s*\(([^)]*)\)', head, re.S)
    base = ''
    if bm:
        q = STR.findall(bm.group(1))
        base = q[0] if q else ''
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
        full = re.sub(r'/+', '/', base + ('' if path.startswith('/') or not path else '/') + path) or base or '/'
        sm = SIG.search(src, m.end())
        if not sm:
            continue
        tree = expand(cls, sm.group(2), 1, set())
        rows.append({'http': verb, 'path': full, 'controller': cls,
                     'method': sm.group(2), 'tree': tree})

def depth_of(ns, d=1):
    return max([d] + [depth_of(n['children'], d + 1) for n in ns if n['children']]) if ns else 0

def count(ns):
    return sum(1 + count(n['children']) for n in ns)

io.open(OUT + '/sources/call_chains.json', 'w', encoding='utf-8', newline='\n').write(
    json.dumps(rows, ensure_ascii=False, indent=1))

deep = [r for r in rows if depth_of(r['tree']) >= 2]
print('엔드포인트 %d' % len(rows))
print('체인 있음 %d / 2단계 이상 %d' % (len([r for r in rows if r['tree']]), len(deep)))
print('최대 깊이 %d / 총 노드 %d' % (max((depth_of(r['tree']) for r in rows), default=0),
                                sum(count(r['tree']) for r in rows)))
