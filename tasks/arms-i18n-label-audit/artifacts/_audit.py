import os, re, json, collections, sys

ROOT = sys.argv[1] if len(sys.argv) > 1 else 'arms/html'
files = []
for dp, dn, fn in os.walk(ROOT):
    for f in fn:
        if f.endswith('.html'):
            files.append(os.path.join(dp, f).replace(os.sep, '/'))
files.sort()

def strip(s):
    s = re.sub(r'<!--.*?-->', '', s, flags=re.S)
    s = re.sub(r'<script\b.*?</script>', '', s, flags=re.S | re.I)
    s = re.sub(r'<style\b.*?</style>', '', s, flags=re.S | re.I)
    return s

KO = re.compile(r'[가-힣]')
LAT = re.compile(r'[A-Za-z]{2,}')

def line_of(s, pos):
    return s.count('\n', 0, pos) + 1

folder = collections.defaultdict(lambda: dict(files=0, labels=0, tagged_labels=0, ko=0, en=0, tagged_files=0))
tot = dict(files=0, labels=0, tagged=0, ko=0, en=0)
detail = {}

for p in files:
    src = open(p, encoding='utf-8', errors='replace').read()
    s = strip(src)
    rel = p[len(ROOT) + 1:] if p.startswith(ROOT) else p
    fol = rel.split('/')[0] if '/' in rel else '(root)'
    folder[fol]['files'] += 1
    tot['files'] += 1

    labels = []
    for m in re.finditer(r'>([^<>]+)<', s):
        t = m.group(1).strip()
        if not t:
            continue
        if re.fullmatch(r'(?:&[a-z]+;|&#\d+;|[\s\W\d])+', t):
            continue
        if KO.search(t) or LAT.search(t):
            labels.append(('text', t, line_of(s, m.start(1))))
    for attr in ('placeholder', 'title', 'alt'):
        for m in re.finditer(attr + r'\s*=\s*"([^"]*)"', s, re.I):
            t = m.group(1).strip()
            if t and (KO.search(t) or LAT.search(t)):
                labels.append((attr, t, line_of(s, m.start(1))))
    for m in re.finditer(r'<input[^>]*?type\s*=\s*"(?:button|submit|reset)"[^>]*?>', s, re.I):
        v = re.search(r'value\s*=\s*"([^"]*)"', m.group(0), re.I)
        if v and v.group(1).strip():
            labels.append(('value', v.group(1).strip(), line_of(s, m.start())))
    for m in re.finditer(r'<option\b[^>]*>([^<]*)<', s, re.I):
        t = m.group(1).strip()
        if t and (KO.search(t) or LAT.search(t)):
            labels.append(('option', t, line_of(s, m.start(1))))

    dl = len(re.findall(r'data-locale', s))
    kon = sum(1 for k, t, l in labels if KO.search(t))
    enn = len(labels) - kon
    folder[fol]['labels'] += len(labels)
    folder[fol]['tagged_labels'] += dl
    folder[fol]['ko'] += kon
    folder[fol]['en'] += enn
    if dl:
        folder[fol]['tagged_files'] += 1
    tot['labels'] += len(labels)
    tot['tagged'] += dl
    tot['ko'] += kon
    tot['en'] += enn
    detail[p] = dict(labels=len(labels), dl=dl, ko=kon, items=labels)

print('TOTAL html=%d labels=%d data-locale=%d korean=%d latin=%d'
      % (tot['files'], tot['labels'], tot['tagged'], tot['ko'], tot['en']))
print()
print('| folder | html | tagged html | labels | data-locale | untagged | cov%% |')
print('|---|---|---|---|---|---|---|')
for k, v in sorted(folder.items(), key=lambda x: -x[1]['labels']):
    un = v['labels'] - v['tagged_labels']
    cov = 100.0 * v['tagged_labels'] / v['labels'] if v['labels'] else 0.0
    print('| %s | %d | %d | %d | %d | %d | %.1f |'
          % (k, v['files'], v['tagged_files'], v['labels'], v['tagged_labels'], un, cov))

print()
print('=== TOP 20 files by untagged label count ===')
rows = sorted(detail.items(), key=lambda x: -(x[1]['labels'] - x[1]['dl']))
for p, d in rows[:20]:
    print('%-62s labels=%-4d dl=%-3d untagged=%d' % (p, d['labels'], d['dl'], d['labels'] - d['dl']))

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_audit_detail.json'), 'w', encoding='utf-8') as fh:
    json.dump(detail, fh, ensure_ascii=False, indent=1)
