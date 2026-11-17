"""Submit every URL from the live sitemap to IndexNow (Bing, Yandex, Seznam, Naver share submissions).

Usage: python3 tools/indexnow.py            (after a deploy; the key file must already be live)
"""
import json
import re
import sys
import urllib.request

sys.path.insert(0, __import__('os').path.dirname(__file__))
from cloudflare_build import INDEXNOW_KEY, SITE

sm = urllib.request.urlopen(urllib.request.Request(SITE + '/sitemap.xml', headers={'User-Agent': 'Mozilla/5.0 (indexnow-submit)'}), timeout=60).read().decode('utf-8')
urls = re.findall(r'<loc>([^<]+)</loc>', sm)
for i in range(0, len(urls), 9000):
    body = json.dumps({'host': SITE.split('//')[1], 'key': INDEXNOW_KEY,
                       'keyLocation': '%s/%s.txt' % (SITE, INDEXNOW_KEY), 'urlList': urls[i:i + 9000]}).encode()
    req = urllib.request.Request('https://api.indexnow.org/indexnow', data=body,
                                 headers={'Content-Type': 'application/json; charset=utf-8'})
    try:
        r = urllib.request.urlopen(req, timeout=60)
        print('IndexNow', len(urls[i:i + 9000]), 'URLs ->', r.status)
    except urllib.error.HTTPError as e:
        print('IndexNow error', e.code, e.read()[:300])
