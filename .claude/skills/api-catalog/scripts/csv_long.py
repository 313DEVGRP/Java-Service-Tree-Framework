# -*- coding: utf-8 -*-
"""엔드포인트 카탈로그 CSV — long(tidy) 형식. 호출 1건 = 1행.
   원천은 call_chains.json 하나이므로 PDF §3·§4 와 값이 어긋날 수 없다."""
import io, os, json, csv

# ── 대상 저장소 · 출력 경로 (환경변수로 지정, 없으면 Backend-Core 기본값) ──
_REPO = os.environ.get('CATALOG_REPO', 'Java-Service-Tree-Framework-Backend-Core')
_TASK = os.environ.get('CATALOG_TASK', 'tasks/api-catalog')

T = _TASK
_SHORT = os.environ.get('CATALOG_REPO', 'repo').replace('Java-Service-Tree-Framework-', '')
OUT = T + '/artifacts/API카탈로그_%s_%s.csv' % (_SHORT, __import__('datetime').date.today().strftime('%Y%m%d'))

cat = json.load(io.open(T + '/artifacts/_catalog.json', encoding='utf-8'))
chains = json.load(io.open(T + '/sources/call_chains.json', encoding='utf-8'))

meta = {(c['controller'], c['method'], c['http'], c['path']): c for c in cat}

def walk(ns, depth, acc):
    for n in ns:
        cls, _, mth = n['label'].partition('.')
        _JDK = {'Logger','String','Map','Integer','Long','Boolean','Object','List','Set',
                'HashMap','HashSet','ArrayList','Optional','File','Files','Collections',
                'Arrays','Math','System','Thread','Stream','Pattern','Matcher','Date',
                'LocalDate','LocalDateTime','StringBuilder','Double','Float','Byte','Character'}
        _kind = 'feign' if n['kind'] == 'feign' else ('lib' if cls in _JDK else 'bean')
        acc.append({
            'depth': depth,
            'cls': cls,
            'mth': mth,
            'kind': _kind,
            'feign': n.get('name', ''),
            'via': n.get('via', ''),
        })
        walk(n['children'], depth + 1, acc)
    return acc

rows = []
for c in sorted(chains, key=lambda x: (x['controller'], x['path'], x['http'])):
    k = (c['controller'], c['method'], c['http'], c['path'])
    m = meta.get(k, {})
    base = [c['http'], c['path'], c['controller'], c['method'],
            m.get('file', ''), m.get('line', '')]
    edges = walk(c['tree'], 1, [])
    if edges:
        for e in edges:
            rows.append(base + [e['depth'], e['cls'], e['mth'], e['kind'],
                                e['feign'], e['via'], ''])
    else:
        rows.append(base + ['', '', '', 'none', '', '', m.get('note', '')])

with io.open(OUT, 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.writer(f)
    w.writerow(['HTTP', '경로', '컨트롤러', '컨트롤러메서드', '파일', 'line',
                'depth', '호출클래스', '호출메서드', '종류', 'feign_name', 'via', '비고'])
    w.writerows(rows)

ep = len(set((r[0], r[1], r[2], r[3]) for r in rows))
print('%d행 / 엔드포인트 %d개' % (len(rows), ep))
print('  종류별:', {k: sum(1 for r in rows if r[9] == k) for k in ('bean', 'feign', 'none')})
print('  depth별:', {d: sum(1 for r in rows if r[6] == d) for d in (1, 2, 3, 4)})
fe = sorted({r[10] for r in rows if r[9] == 'feign'})
print('  feign_name:', fe)
