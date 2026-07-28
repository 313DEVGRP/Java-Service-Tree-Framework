import json, re, os, sys, collections

REPO = 'C:/DEV/sourcecode/Java-Service-Tree-Framework/Java-Service-Tree-Framework-Frontend-Web'


def flatten(obj, parent=''):
    out = {}
    for k, v in obj.items():
        key = parent + '.' + k if parent else k
        if isinstance(v, dict):
            out.update(flatten(v, key))
        else:
            out[key] = v
    return out


packs = {}
for loc in ('ko', 'en', 'jp'):
    p = os.path.join(REPO, 'arms/locales', loc + '.json')
    raw = open(p, encoding='utf-8').read()
    if not raw.strip():
        packs[loc] = ('EMPTY', {})
        continue
    try:
        packs[loc] = ('OK', flatten(json.loads(raw)))
    except Exception as e:
        # repair trailing commas to see what it WOULD contain
        rep = re.sub(r',(\s*[}\]])', r'\1', raw)
        try:
            packs[loc] = ('INVALID:' + str(e), flatten(json.loads(rep)))
        except Exception as e2:
            packs[loc] = ('INVALID-UNREPAIRABLE:' + str(e2), {})

for loc, (st, d) in packs.items():
    print('%s.json status=%s keys=%d' % (loc, st, len(d)))
print()

# keys used in html
used = collections.defaultdict(list)
for dp, dn, fn in os.walk(os.path.join(REPO, 'arms/html')):
    for f in fn:
        if not f.endswith('.html'):
            continue
        p = os.path.join(dp, f)
        src = open(p, encoding='utf-8', errors='replace').read()
        rel = p.replace(os.sep, '/').split('Frontend-Web/')[-1]
        for i, line in enumerate(src.split('\n'), 1):
            for m in re.finditer(r'data-locale="([^"]*)"', line):
                used[m.group(1)].append((rel, i))

print('unique data-locale keys used: %d (sites: %d)' % (len(used), sum(len(v) for v in used.values())))
print()
print('| key | sites | ko | en | jp |')
print('|---|---|---|---|---|')
miss = collections.Counter()
for k in sorted(used):
    row = []
    for loc in ('ko', 'en', 'jp'):
        has = k in packs[loc][1]
        row.append('Y' if has else 'N')
        if not has:
            miss[loc] += 1
    print('| %s | %d | %s |' % (k, len(used[k]), ' | '.join(row)))
print()
print('missing per locale (of %d keys):' % len(used), dict(miss))
print()
print('=== keys defined in pack but NEVER used in html ===')
for loc in ('ko', 'en'):
    unused = sorted(set(packs[loc][1]) - set(used))
    print(loc, len(unused), unused)
