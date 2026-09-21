# -*- coding: utf-8 -*-
"""작업 루트에서 Spring 프로젝트를 찾아 카탈로그 대상 목록을 만든다.

판정 기준 (전부 충족):
  1. `src/main/java` 가 있다
  2. 빌드 파일(build.gradle / build.gradle.kts / pom.xml)이 있고 spring 의존성이 보인다
     — 또는 소스에 `@SpringBootApplication` 이 있다
  3. `@RestController` 또는 `@Controller` 가 1개 이상 있다 (API 표면이 없으면 카탈로그가 무의미)

사용:
  python discover.py            # 사람이 읽는 표
  python discover.py --names    # 저장소 폴더명만 (쉘 반복용)
"""
import io, os, re, sys, json

try:
    # Windows 기본 CRLF 방지 — 쉘 for 루프가 경로 끝에 CR 을 달고 들어간다
    sys.stdout.reconfigure(newline=chr(10))
except Exception:
    pass

ROOT = os.environ.get('CATALOG_WORKSPACE', '.')
BUILD = ('build.gradle', 'build.gradle.kts', 'pom.xml')
read = lambda p: io.open(p, encoding='utf-8', errors='replace').read()

def java_files(src):
    out = []
    for dp, dn, fn in os.walk(src):
        dn[:] = [d for d in dn if d not in ('build', 'target', '.git', 'node_modules')]
        out += [os.path.join(dp, f) for f in fn if f.endswith('.java')]
    return out

found = []
for name in sorted(os.listdir(ROOT)):
    d = os.path.join(ROOT, name)
    if not os.path.isdir(d) or name.startswith('.') or name.startswith('_'):
        continue
    src = os.path.join(d, 'src', 'main', 'java')
    if not os.path.isdir(src):
        continue

    build_txt = ''
    for b in BUILD:
        p = os.path.join(d, b)
        if os.path.isfile(p):
            build_txt += read(p)
    jf = java_files(src)
    if not jf:
        continue

    blob = ''
    ctl = feign = boot = 0
    for p in jf:
        s = read(p)
        if '@RestController' in s or '@Controller' in s:
            ctl += 1
        if '@FeignClient' in s:
            feign += 1
        if '@SpringBootApplication' in s:
            boot += 1

    is_spring = ('springframework' in build_txt or 'spring-boot' in build_txt or boot > 0)
    if not is_spring or ctl == 0:
        continue

    lines = sum(read(p).count('\n') + 1 for p in jf)
    mappings = 0
    for p in jf:
        mappings += len(re.findall(r'@(?:Get|Post|Put|Delete|Patch|Request)Mapping', read(p)))

    found.append({'repo': name, 'files': len(jf), 'lines': lines,
                  'controllers': ctl, 'feign': feign, 'mappings': mappings,
                  'build': 'gradle' if 'gradle' in ''.join(
                      b for b in BUILD if os.path.isfile(os.path.join(d, b))) else 'maven'})

if '--names' in sys.argv:
    for f in found:
        print(f['repo'])
elif '--json' in sys.argv:
    print(json.dumps(found, ensure_ascii=False, indent=1))
else:
    print('Spring 프로젝트 %d개 발견 (기준: src/main/java + spring 빌드/부트 + 컨트롤러 ≥1)\n' % len(found))
    print('%-40s %7s %9s %7s %6s %8s' % ('저장소', 'java', '줄수', '컨트롤러', 'Feign', '매핑'))
    for f in found:
        print('%-40s %7d %9d %7d %6d %8d' % (
            f['repo'], f['files'], f['lines'], f['controllers'], f['feign'], f['mappings']))
    print('\n제외된 디렉터리는 src/main/java 가 없거나 컨트롤러가 0개다.')
