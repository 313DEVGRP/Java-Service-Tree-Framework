# -*- coding: utf-8 -*-
"""게이트웨이 라우트 규칙을 읽어 '외부 경로 → 내부 경로 → 저장소' 로 정규화한다.

라우트는 Config Server 가 외부 저장소에서 받아 주입하므로 이 워크스페이스에는 없다.
사람이 그 내용을 파일로 떨궈 두면 이 스크립트가 읽는다.

**둘 중 아무 데나 두면 된다** (앞에서부터 찾는다):
  1. 환경변수 `CATALOG_ROUTES` 가 가리키는 파일
  2. `_local/gateway-routes.yml`  (또는 .yaml / .json)

내용은 config 의 `spring.cloud.gateway.routes` 부분을 **그대로 붙여넣으면 된다.**
형식 예시는 SKILL.md 의 「게이트웨이 라우트」 절에 있다.
상위 `spring:` 키가 있어도 없어도 되고, 들여쓰기도 그대로 둬도 된다.

사용:  python routes.py            # 사람이 읽는 표
       python routes.py --json     # 정규화 결과 (다른 스크립트 입력용)
"""
import io, os, re, sys, json

CAND = [os.environ.get('CATALOG_ROUTES', ''),
        '_local/gateway-routes.yml', '_local/gateway-routes.yaml',
        '_local/gateway-routes.json']


def find():
    for p in CAND:
        if p and os.path.isfile(p):
            return p
    return None


def parse_yaml_routes(text):
    """`routes:` 아래 리스트만 뽑는 최소 파서 (PyYAML 없이 동작)."""
    lines = [l.rstrip() for l in text.split('\n')]
    ri = next((i for i, l in enumerate(lines) if re.match(r'^\s*routes:\s*$', l)), None)
    if ri is None:
        return []
    base = len(lines[ri]) - len(lines[ri].lstrip())
    out, cur, key = [], None, None
    for l in lines[ri + 1:]:
        if not l.strip() or l.strip().startswith('#'):
            continue
        ind = len(l) - len(l.lstrip())
        if ind <= base:
            break
        s = l.strip()
        if s.startswith('- '):
            body = s[2:].strip()
            if re.match(r'^id\s*:', body):
                cur = {'id': body.split(':', 1)[1].strip(),
                       'uri': '', 'predicates': [], 'filters': []}
                out.append(cur)
                key = None
            elif cur is not None and key:
                cur[key].append(body)
        elif ':' in s and cur is not None:
            k, _, v = s.partition(':')
            k, v = k.strip(), v.strip()
            if k in ('predicates', 'filters') and not v:
                key = k
            elif k in ('uri', 'id', 'order'):
                cur[k] = v
                key = None
    return out


def rewrite_target(filters):
    """RewritePath=<정규식>, <치환> 에서 내부 경로 접두어를 뽑는다.
    예) /auth-admin/api/(?<path>.*), /admin/${path}  →  ('/auth-admin/api/', '/admin/')"""
    for f in filters:
        if not f.startswith('RewritePath='):
            continue
        body = f[len('RewritePath='):]
        # 쉼표로 나누되 정규식 안의 쉼표는 드물다는 전제
        src, _, dst = body.partition(',')
        src, dst = src.strip(), dst.strip()
        ext = re.sub(r'\(\?<\w+>.*$', '', src)          # 캡처 그룹 앞까지
        inn = re.sub(r'\$\\?\{\w+\}.*$', '', dst)        # ${path} 앞까지
        return ext, inn
    return '', ''


def load():
    p = find()
    if not p:
        return None, []
    txt = io.open(p, encoding='utf-8').read()
    if p.endswith('.json'):
        d = json.loads(txt)
        if isinstance(d, dict):
            d = (d.get('spring', {}).get('cloud', {})
                  .get('gateway', {}).get('routes', d.get('routes', [])))
        raw = d
    else:
        raw = parse_yaml_routes(txt)
    out = []
    for r in raw:
        paths = []
        for x in r.get('predicates', []):
            if x.startswith('Path='):
                paths += [q.strip() for q in x[5:].split(',')]
        ext, inn = rewrite_target(r.get('filters', []))
        out.append({'id': r.get('id', ''), 'uri': r.get('uri', ''),
                    'paths': paths, 'filters': r.get('filters', []),
                    'ext_prefix': ext, 'inner_prefix': inn})
    return p, out


def repos_present(root='.'):
    try:
        return [n for n in sorted(os.listdir(root))
                if os.path.isdir(os.path.join(root, n, 'src', 'main', 'java'))]
    except Exception:
        return []


NOISE = ('swagger', 'authanon', 'authuser', 'manageruser', 'adminuser',
         'dwr', 'jstf', 'javaservicetreeframework', 'api')


def guess_repo(route, repos, port_map=None):
    """① 라우트 id 에 박힌 저장소 이름 ② uri 의 서비스명 ③ 포트 매핑 순으로 맞춘다."""
    def flat(x):
        return re.sub(r'[^a-z]', '', x.lower())

    tokens = [t for t in re.split(r'[-_]', route['id']) if t]
    cand = ''.join(t for t in tokens if flat(t) not in NOISE)
    for src in (cand, re.sub(r'^\w+://', '', route['uri']).split(':')[0]):
        f = flat(src)
        if not f:
            continue
        best, score = '', 0
        for r in repos:
            rf = flat(r.replace('Java-Service-Tree-Framework-', ''))
            if rf and (rf in f or f in rf) and len(rf) > score:
                best, score = r, len(rf)
        if best:
            return best
    if port_map:
        m = re.search(r':(\d+)', route['uri'])
        if m and m.group(1) in port_map:
            return port_map[m.group(1)]
    return ''


def build_port_map(routes, repos):
    """같은 포트를 쓰는 라우트들의 id 로부터 포트→저장소를 역산한다."""
    pm = {}
    for r in routes:
        m = re.search(r':(\d+)', r['uri'])
        if not m:
            continue
        g = guess_repo(r, repos)
        if g and m.group(1) not in pm:
            pm[m.group(1)] = g
    return pm


if __name__ == '__main__':
    p, routes = load()
    if not p:
        print('라우트 파일 없음. 아래 중 한 곳에 두면 읽는다:')
        for c in CAND[1:]:
            print('  -', c)
        print('  - 또는 CATALOG_ROUTES 환경변수로 경로 지정')
        print('형식 예시는 SKILL.md 의 「게이트웨이 라우트」 절 참조')
        sys.exit(0)

    repos = repos_present()
    pm = build_port_map(routes, repos)
    for r in routes:
        r['repo'] = guess_repo(r, repos, pm)

    if '--json' in sys.argv:
        print(json.dumps({'source': p, 'port_map': pm, 'routes': routes},
                         ensure_ascii=False, indent=1))
    else:
        print('라우트 %d건  ·  원본 %s\n' % (len(routes), p))
        print('%-30s %-22s %-14s %s' % ('외부 경로', '내부 경로', '수신', 'route id'))
        print('-' * 104)
        for r in sorted(routes, key=lambda x: (x.get('repo', ''), x['paths'])):
            ext = ' '.join(r['paths']) or '—'
            inn = (r['inner_prefix'] + '**') if r['inner_prefix'] else '(변환 없음)'
            print('%-30s %-22s %-14s %s' % (
                ext[:30], inn[:22],
                (r.get('repo') or '?').replace('Java-Service-Tree-Framework-', '')[:14],
                r['id']))
        print('\n포트 매핑(라우트에서 역산): %s' % ', '.join(
            '%s→%s' % (k, v.replace('Java-Service-Tree-Framework-', '')) for k, v in sorted(pm.items())))
        nore = [r['id'] for r in routes if not r.get('repo')]
        if nore:
            print('수신 저장소 미확정: %s' % ', '.join(nore))
