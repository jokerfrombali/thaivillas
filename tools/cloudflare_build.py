#!/usr/bin/env python3
"""Cloudflare Pages build step: copy the site to dist/ for a root domain (luxuryphuket.net).

The repository is built for GitHub Pages at /thaivillas/ (tools/thai/build_all.py --base /thaivillas).
On Cloudflare the site lives at the domain root, so the /thaivillas prefix is removed from every text file.
Photos stay on the thaivillas-media-NN GitHub Pages repos (their URLs contain "/thaivillas-media-", which
is not touched).

Cloudflare Pages settings:  Build command: python3 tools/cloudflare_build.py   Build output directory: dist
"""
import os
import re
import shutil
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
OUT = os.path.join(ROOT, 'dist')
SKIP_DIRS = {'.git', '.github', 'tools', 'dist', 'node_modules'}
SKIP_FILES = {"README.md", "CNAME", ".nojekyll", ".gitignore", "wrangler.jsonc", "wrangler.toml", "wrangler.json"}
TEXT = ('.html', '.js', '.css', '.json', '.xml', '.txt', '.svg', '.webmanifest')
PREFIX = re.compile(r'/thaivillas(?=/|["\'`?#)\s,]|$)(?!-)')


def main():
    shutil.rmtree(OUT, ignore_errors=True)
    n_files = n_text = 0
    for d, dirs, files in os.walk(ROOT):
        rel_d = os.path.relpath(d, ROOT)
        dirs[:] = [x for x in dirs if not (rel_d == '.' and x in SKIP_DIRS)]
        for f in files:
            if rel_d == '.' and f in SKIP_FILES:
                continue
            src = os.path.join(d, f)
            dst = os.path.join(OUT, rel_d, f)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            if f.endswith(TEXT):
                with open(src, encoding='utf-8', errors='surrogateescape') as fh:
                    s = fh.read()
                t = PREFIX.sub('', s)
                t = t.replace('href=""', 'href="/"').replace("href=''", "href='/'")
                with open(dst, 'w', encoding='utf-8', errors='surrogateescape') as fh:
                    fh.write(t)
                n_text += 1
            else:
                shutil.copy2(src, dst)
            n_files += 1
    # old links to /thaivillas/... keep working
    with open(os.path.join(OUT, '_redirects'), 'w') as fh:
        fh.write('/thaivillas/* /:splat 301\n/thaivillas / 301\n')
    with open(os.path.join(OUT, '_headers'), 'w') as fh:
        fh.write('/villa/ui/*\n  Cache-Control: public, max-age=604800\n/fonts/*\n  Cache-Control: public, max-age=31536000, immutable\n')
    print('dist: %d files (%d rewritten)' % (n_files, n_text))


if __name__ == '__main__':
    sys.exit(main())
