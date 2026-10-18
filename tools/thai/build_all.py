#!/usr/bin/env python3
"""Build the whole site: run every page generator, recompile Tailwind, then (optionally) prefix
root-absolute links for a GitHub Pages project site.

    python3 -I tools/thai/build_all.py                 # local build, links stay root-absolute
    python3 -I tools/thai/build_all.py --base /thaivillas   # for https://<user>.github.io/thaivillas/

With a custom domain later, build without --base.
"""
import os, re, subprocess, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
HERE = pathlib.Path(__file__).resolve().parent
STEPS = ['build_home.py', 'build_areas.py', 'build_villas.py', 'build_monthly.py', 'build_vip.py', 'build_info.py']

TOP = ('images|villa|villas|property-rental|monthly-rental|vip|about|contacts|terms|privacy|saved|data|fonts|vendor|'
       'favicon\\.svg|404\\.html|thb-[\\w.-]+\\.(?:js|css)')

def prefix(base):
    base = '/' + base.strip('/')
    pat = re.compile(r'''(["'`(=,\s])/(?!/)(?=(%s)(?:[/"'`?#)\s,]|$))''' % TOP)
    home = re.compile(r'''((?:href|action|content)=["'](?:\d+;\s*url=)?)/(["'#?])''')
    n = 0
    for f in list(ROOT.rglob('*.html')) + list(ROOT.glob('data/*.json')) + list(ROOT.glob('thb-*.js')) + list(ROOT.rglob('*.css')):
        if {'.git', 'tools'} & set(f.relative_to(ROOT).parts):
            continue
        s = f.read_text(encoding='utf-8')
        t = pat.sub(lambda m: m.group(1) + base + '/', s)
        t = home.sub(lambda m: m.group(1) + base + '/' + m.group(2), t)
        t = t.replace(base + base + '/', base + '/')
        if t != s:
            f.write_text(t, encoding='utf-8'); n += 1
    print('prefixed', n, 'files with', base)

def main():
    base = sys.argv[sys.argv.index('--base') + 1] if '--base' in sys.argv else None
    for step in STEPS:
        print('==', step)
        subprocess.run([sys.executable, '-I', str(HERE / step)], cwd=ROOT, check=True)
    print('== tailwind')
    subprocess.run(['sh', 'tools/perf/build-tailwind.sh'], cwd=ROOT, check=True)
    if base:
        prefix(base)

if __name__ == '__main__':
    main()
