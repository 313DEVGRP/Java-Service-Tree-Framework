# -*- coding: utf-8 -*-
"""상속으로 늘어나는 엔드포인트 전개 + Feign 호출자 정밀 추출."""
import io, os, re, json, csv, collections

# ── 대상 저장소 · 출력 경로 (환경변수로 지정, 없으면 Backend-Core 기본값) ──
_REPO = os.environ.get('CATALOG_REPO', 'Java-Service-Tree-Framework-Backend-Core')
_TASK = os.environ.get('CATALOG_TASK', 'tasks/api-catalog')

ROOT = _REPO + '/src/main/java'
OUT = _TASK + '/sources'
read = lambda p: io.open(p, encoding='utf-8', errors='replace').read()

java = []
for dp, dn, fn in os.walk(ROOT):
    for f in fn:
        if f.endswith('.java'):
            java.append(os.path.join(dp, f).replace('\\', '/'))

MAP_RE = re.compile(r'@(Get|Post|Put|Delete|Patch|Request)Mapping\s*(?:\(([^)]*)\))?', re.S)
PATHS_RE = re.compile(r'"([^"]*)"')
METHOD_RE = re.compile(r'RequestMethod\.(GET|POST|PUT|DELETE|PATCH)')
SIG_RE = re.compile(r'(?:public\s+|default\s+)?(?:static\s+)?([\w<>,\[\]\s\.\?]+?)\s+(\w+)\s*\(')
CLS_RE = re.compile(r'(?:public\s+)?(?:abstract\s+)?class\s+(\w+)(?:\s*<[^>]*>)?\s*'
                    r'(?:extends\s+(\w+))?', re.S)

def mappings(src, skip_before=0):
    out = []
    for m in MAP_RE.finditer(src):
        if m.start() < skip_before:
            continue
        verb = m.group(1).upper()
        a = m.group(2) or ''
        if verb == 'REQUEST':
            mm = METHOD_RE.search(a)
            verb = mm.group(1) if mm else 'ANY'
        q = [x for x in PATHS_RE.findall(a)
             if x.startswith('/') or (x and '/' not in x and 'application' not in x)]
        sm = SIG_RE.search(src, m.end())
        out.append({'http': verb, 'path': q[0] if q else '',
                    'javaMethod': sm.group(2) if sm else '',
                    'line': src[:m.start()].count('\n') + 1})
    return out

# 전 클래스 인덱스
info = {}
for p in java:
    src = read(p)
    cm = CLS_RE.search(src)
    if not cm:
        continue
    cls = cm.group(1)
    head = src[:cm.start()]
    bm = re.search(r'@RequestMapping\s*\(([^)]*)\)', head, re.S)
    base = ''
    if bm:
        q = PATHS_RE.findall(bm.group(1))
        base = q[0] if q else ''
    info[cls] = {'file': p.replace(ROOT + '/', ''), 'parent': cm.group(2) or '',
                 'base': base, 'own': mappings(src, cm.start()),
                 'isCtl': ('@RestController' in head or '@Controller' in head)}

def chain(cls):
    out, cur, seen = [], cls, set()
    while cur and cur in info and cur not in seen:
        seen.add(cur)
        out.append(cur)
        cur = info[cur]['parent']
    return out

rows = []
per = {}
for cls, i in info.items():
    if not i['isCtl']:
        continue
    ch = chain(cls)
    base = next((info[c]['base'] for c in ch if info[c]['base']), '')
    own = inh = 0
    for c in ch:
        for e in info[c]['own']:
            pth = e['path']
            full = re.sub(r'/+', '/', (base + ('' if pth.startswith('/') or not pth else '/') + pth)) or base or '/'
            src_kind = '자체' if c == cls else '상속(%s)' % c
            if c == cls:
                own += 1
            else:
                inh += 1
            rows.append([e['http'], full, cls, e['javaMethod'], src_kind,
                         info[c]['file'], e['line']])
    per[cls] = {'base': base, 'own': own, 'inherited': inh,
                'parent': i['parent'], 'file': i['file']}

# ── Feign: 어떤 서비스/클래스가 어떤 Feign 메서드를 호출하나 ──
feign_ifaces = {}
for p in java:
    src = read(p)
    if '@FeignClient' not in src:
        continue
    nm = re.search(r'(?:interface|class)\s+(\w+)', src)
    iface = nm.group(1)
    fm = re.search(r'@FeignClient\s*\(([^)]*)\)', src, re.S)
    a = fm.group(1) if fm else ''
    feign_ifaces[iface] = {
        'file': p.replace(ROOT + '/', ''),
        'name': (re.search(r'name\s*=\s*"([^"]*)"', a) or [None, ''])[1] if re.search(r'name\s*=\s*"([^"]*)"', a) else '',
        'url': (re.search(r'url\s*=\s*"([^"]*)"', a).group(1) if re.search(r'url\s*=\s*"([^"]*)"', a) else ''),
        'methodNames': sorted(set(m['javaMethod'] for m in mappings(src) if m['javaMethod'])),
        'methodCount': len(mappings(src)),
    }

calls = collections.defaultdict(lambda: collections.defaultdict(set))
for p in java:
    src = read(p)
    rel = p.replace(ROOT + '/', '')
    for iface, fi in feign_ifaces.items():
        if iface not in src or rel == fi['file']:
            continue
        var = re.search(r'\b%s\s+(\w+)\s*[;=)]' % iface, src)
        vs = {var.group(1)} if var else set()
        vs |= {m.group(1) for m in re.finditer(r'\b%s\s+(\w+)' % iface, src)}
        for v in vs:
            for mm in re.finditer(r'\b%s\s*\.\s*(\w+)\s*\(' % re.escape(v), src):
                if mm.group(1) in fi['methodNames']:
                    calls[iface][rel].add(mm.group(1))

os.makedirs(OUT, exist_ok=True)
with io.open(OUT + '/endpoints_expanded.csv', 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.writer(f)
    w.writerow(['HTTP', 'path', 'controller', 'javaMethod', '출처', '선언파일', 'line'])
    for r in sorted(rows, key=lambda x: (x[2], x[1], x[0])):
        w.writerow(r)

with io.open(OUT + '/feign_calls.csv', 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.writer(f)
    w.writerow(['FeignClient', 'name', '호출자 파일', '호출 메서드 수', '호출 메서드'])
    for iface in sorted(calls):
        for rel in sorted(calls[iface]):
            ms = sorted(calls[iface][rel])
            w.writerow([iface, feign_ifaces[iface]['name'], rel, len(ms), ' '.join(ms)])

io.open(OUT + '/inventory.json', 'w', encoding='utf-8', newline='\n').write(json.dumps(
    {'perController': per, 'feign': feign_ifaces,
     'feignCallerCount': {k: len(v) for k, v in calls.items()},
     'totalEndpointInstances': len(rows)}, ensure_ascii=False, indent=1))

own = sum(v['own'] for v in per.values())
inh = sum(v['inherited'] for v in per.values())
print('컨트롤러 %d | 자체 선언 %d | 상속분 %d | 도달 가능 합계 %d' % (len(per), own, inh, len(rows)))
print('상속 있는 컨트롤러:', len([v for v in per.values() if v['inherited']]))
print('base path 없는 컨트롤러:', len([v for v in per.values() if not v['base']]))
for k, v in sorted(feign_ifaces.items()):
    print('  %-24s %-16s 메서드 %3d  호출자 %d' % (k, v['name'], v['methodCount'], len(calls.get(k, {}))))
