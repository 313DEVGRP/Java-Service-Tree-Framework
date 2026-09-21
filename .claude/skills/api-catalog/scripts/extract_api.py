# -*- coding: utf-8 -*-
"""Backend-Core 엔드포인트 → 컨트롤러 → 서비스 → Feign 정적 추출.
정규식 기반이므로 결과는 '기계 추출본'이며 표본 검증이 필요하다."""
import io, os, re, json, csv, collections

# ── 대상 저장소 · 출력 경로 (환경변수로 지정, 없으면 Backend-Core 기본값) ──
_REPO = os.environ.get('CATALOG_REPO', 'Java-Service-Tree-Framework-Backend-Core')
_TASK = os.environ.get('CATALOG_TASK', 'tasks/api-catalog')

ROOT = _REPO + '/src/main/java'
OUT = _TASK + '/sources'

def read(p):
    return io.open(p, encoding='utf-8', errors='replace').read()

java = []
for dp, dn, fn in os.walk(ROOT):
    for f in fn:
        if f.endswith('.java'):
            java.append(os.path.join(dp, f).replace('\\', '/'))

MAP_RE = re.compile(
    r'@(Get|Post|Put|Delete|Patch|Request)Mapping\s*(?:\(([^)]*)\))?', re.S)
PATHS_RE = re.compile(r'"([^"]*)"')
METHOD_RE = re.compile(r'RequestMethod\.(GET|POST|PUT|DELETE|PATCH)')
SIG_RE = re.compile(
    r'public\s+(?:static\s+)?([\w<>,\[\]\s\.\?]+?)\s+(\w+)\s*\(')
CLASS_RE = re.compile(r'(?:public\s+)?(?:abstract\s+)?class\s+(\w+)'
                      r'(?:\s*<[^>]*>)?\s*(?:extends\s+([\w<>,\.\s]+?))?'
                      r'(?:\s+implements\s+([\w<>,\.\s]+?))?\s*\{')

endpoints = []
controllers = {}

for p in java:
    src = read(p)
    if '@RestController' not in src and '@Controller' not in src:
        continue
    lines = src.split('\n')
    cm = CLASS_RE.search(src)
    cls = cm.group(1) if cm else os.path.basename(p)[:-5]
    parent = (cm.group(2) or '').strip() if cm else ''
    # 클래스 레벨 @RequestMapping
    base = ''
    head = src[:cm.start()] if cm else src
    bm = re.search(r'@RequestMapping\s*\(([^)]*)\)', head, re.S)
    if bm:
        q = PATHS_RE.findall(bm.group(1))
        if q:
            base = q[0]
    rel = p.replace(ROOT + '/', '')
    controllers[cls] = {'file': rel, 'parent': parent, 'base': base, 'n': 0}

    for m in MAP_RE.finditer(src):
        args = m.group(2) or ''
        # 클래스 레벨 애노테이션은 건너뜀
        if cm and m.start() < cm.start():
            continue
        verb = m.group(1).upper()
        if verb == 'REQUEST':
            mm = METHOD_RE.search(args)
            verb = mm.group(1) if mm else 'ANY'
        paths = [x for x in PATHS_RE.findall(args) if not x.startswith('application/')
                 and 'charset' not in x and x != '']
        path = paths[0] if paths else ''
        full = (base + path) if path.startswith('/') or not path else base + '/' + path
        full = re.sub(r'/+', '/', full) or base or '/'
        line = src[:m.start()].count('\n') + 1
        # 애노테이션 뒤 첫 public 메서드 시그니처
        sm = SIG_RE.search(src, m.end())
        jm = sm.group(2) if sm else ''
        endpoints.append({'controller': cls, 'file': rel, 'line': line,
                          'http': verb, 'path': full, 'javaMethod': jm})
        controllers[cls]['n'] += 1

# ── 컨트롤러가 주입받는 서비스 타입 ──
INJ_RE = re.compile(r'(?:@Autowired|@Resource|private\s+final)[^;]*?\b(\w+(?:Service|Repository|Client|Dao|Mapper))\s+(\w+)\s*;', re.S)
for cls, info in controllers.items():
    src = read(ROOT + '/' + info['file'])
    info['deps'] = sorted(set(m.group(1) for m in INJ_RE.finditer(src)))

# ── Feign 클라이언트 ──
feigns = {}
for p in java:
    src = read(p)
    if '@FeignClient' not in src:
        continue
    cm = CLASS_RE.search(src)
    name = re.search(r'(?:interface|class)\s+(\w+)', src)
    iface = name.group(1) if name else os.path.basename(p)[:-5]
    fm = re.search(r'@FeignClient\s*\(([^)]*)\)', src, re.S)
    args = fm.group(1) if fm else ''
    nm = re.search(r'name\s*=\s*"([^"]*)"', args)
    url = re.search(r'url\s*=\s*"([^"]*)"', args)
    methods = []
    for m in MAP_RE.finditer(src):
        verb = m.group(1).upper()
        a = m.group(2) or ''
        if verb == 'REQUEST':
            mm = METHOD_RE.search(a)
            verb = mm.group(1) if mm else 'ANY'
        q = [x for x in PATHS_RE.findall(a) if x.startswith('/')]
        sm = SIG_RE.search(src, m.end())
        methods.append({'http': verb, 'path': q[0] if q else '',
                        'javaMethod': sm.group(2) if sm else '',
                        'line': src[:m.start()].count('\n') + 1})
    feigns[iface] = {'file': p.replace(ROOT + '/', ''),
                     'name': nm.group(1) if nm else '',
                     'url': url.group(1) if url else '',
                     'methods': methods}

# ── 서비스 구현체가 호출하는 Feign ──
callers = collections.defaultdict(set)   # feignIface -> {ServiceImpl}
for p in java:
    src = read(p)
    base = os.path.basename(p)[:-5]
    for iface in feigns:
        if re.search(r'\b%s\b' % iface, src) and base != iface:
            callers[iface].add(p.replace(ROOT + '/', ''))

os.makedirs(OUT, exist_ok=True)
with io.open(OUT + '/endpoints.csv', 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.writer(f)
    w.writerow(['HTTP', 'path', 'controller', 'javaMethod', 'file', 'line'])
    for e in sorted(endpoints, key=lambda x: (x['controller'], x['path'])):
        w.writerow([e['http'], e['path'], e['controller'], e['javaMethod'], e['file'], e['line']])

io.open(OUT + '/inventory.json', 'w', encoding='utf-8', newline='\n').write(
    json.dumps({'controllers': controllers, 'feigns': feigns,
                'feignCallers': {k: sorted(v) for k, v in callers.items()},
                'endpointCount': len(endpoints)},
               ensure_ascii=False, indent=1))

vc = collections.Counter(e['http'] for e in endpoints)
tree = [c for c, i in controllers.items() if 'TreeAbstract' in (i['parent'] or '')]
print('컨트롤러 %d개 · 엔드포인트 %d개' % (len(controllers), len(endpoints)))
print('HTTP:', dict(vc))
print('TreeAbstractController 상속:', len(tree))
print('Feign 인터페이스:', {k: len(v['methods']) for k, v in feigns.items()})
