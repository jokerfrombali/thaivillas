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
SKIP_DIRS = {'.git', '.github', 'tools', 'dist', 'node_modules', 'src'}
SKIP_FILES = {"README.md", "CNAME", ".nojekyll", ".gitignore", "wrangler.jsonc", "wrangler.toml", "wrangler.json"}
TEXT = ('.html', '.js', '.css', '.json', '.xml', '.txt', '.svg', '.webmanifest')
PREFIX = re.compile(r'/thaivillas(?=/|["\'`?#)\s,]|$)(?!-)')
SITE = 'https://luxuryphuket.net'
NOINDEX = re.compile(r'<meta name="robots" content="noindex[^"]*">\s*')
# pages that stay out of search: photo-tour duplicates, favourites, 404, the /villa/ redirect stub
HIDDEN = re.compile(r'(^|/)(gallery|saved)/index\.html$|^404\.html$|^villa/index\.html$')


def seo(rel, html):
    """luxuryphuket.net is the indexed copy: drop noindex, add canonical + og:url (GitHub Pages copy stays noindex)."""
    url = SITE + '/' + (rel[:-len('index.html')] if rel.endswith('index.html') else rel)
    html = NOINDEX.sub('', html)
    if HIDDEN.search(rel):
        canon = url.rsplit('gallery/', 1)[0] if '/gallery/' in rel else url
        add = '<meta name="robots" content="noindex, follow">\n<link rel="canonical" href="%s">\n' % canon
        return html.replace('</head>', add + '</head>', 1), None
    add = '<link rel="canonical" href="%s">\n' % url
    if 'property="og:url"' not in html:
        add += '<meta property="og:url" content="%s">\n' % url
    return html.replace('</head>', add + '</head>', 1), url


def main():
    shutil.rmtree(OUT, ignore_errors=True)
    n_files = n_text = 0
    urls = []
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
                if f.endswith('.html') and '</head>' in t:
                    rel = os.path.normpath(os.path.join(rel_d, f)).replace(os.sep, '/')
                    t, url = seo(rel, t)
                    if url:
                        urls.append(url)
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
    import datetime
    today = datetime.date.today().isoformat()
    urls.sort(key=lambda u: (u.count('/'), u))
    with open(os.path.join(OUT, 'sitemap.xml'), 'w', encoding='utf-8') as fh:
        fh.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        for u in urls:
            fh.write('<url><loc>%s</loc><lastmod>%s</lastmod></url>\n' % (u, today))
        fh.write('</urlset>\n')
    with open(os.path.join(OUT, 'robots.txt'), 'w') as fh:
        fh.write('User-agent: *\nAllow: /\nDisallow: /saved/\nDisallow: /api/\n\nSitemap: %s/sitemap.xml\n' % SITE)
    print('dist: %d files (%d rewritten), sitemap: %d URLs' % (n_files, n_text, len(urls)))


if __name__ == '__main__':
    sys.exit(main())
