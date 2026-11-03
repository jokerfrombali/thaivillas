#!/usr/bin/env python3
"""Turn Phuket Importer results into the site's data files.

    python3 -I tools/thai/import_listings.py --source gyp=<import dir> --source ind=<import dir> \
        --media-root <media dir> --media-map data/media-map.json

Writes data/villas.json (rent), data/sale.json (for sale), data/projects.json (new projects).
Photo URLs point at the media repos (thaivillas-media-NN, GitHub Pages) via data/media-map.json:
{"<source>/<slug>": "https://jokerfrombali.github.io/thaivillas-media-01"}.
Site-wide boilerplate (paragraphs/specs repeated on many listings of one source) is dropped.
"""
import argparse, collections, datetime, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
BASE = '/thaivillas'
AREAS = json.load(open(os.path.join(ROOT, 'data', 'areas.json'), encoding='utf-8'))['destinations']
PHUKET_SUBS = {a['slug']: a['name'] for a in next(d for d in AREAS if d['slug'] == 'phuket')['areas']}
EXTRA_SUBS = {  # Phuket areas without their own page: shown by name, listed under the closest beach page
    'nai-thon': ('Nai Thon', None), 'nai-yang': ('Nai Yang', 'mai-khao'), 'cherng-talay': ('Cherng Talay', 'bang-tao'),
    'kathu': ('Kathu', 'patong'), 'phuket-town': ('Phuket Town', None), 'cape-yamu': ('Cape Yamu', None),
    'koh-kaew': ('Koh Kaew', None), 'panwa': ('Cape Panwa', None), 'yanui': ('Yanui', 'nai-harn'), 'ao-po': ('Ao Po', None),
    'thalang': ('Thalang', None), 'kalim': ('Kalim', 'patong'), 'ao-yon': ('Ao Yon', None), 'pa-klok': ('Pa Klok', None),
    'kamala-beach': ('Kamala', 'kamala'),
}
DEST_RX = [('koh-samui', r'samui|самуи'), ('koh-phangan', r'phangan|пханган'), ('krabi', r'krabi|краби'),
           ('pattaya', r'pattaya|паттай'), ('bangkok', r'bangkok|бангкок'), ('hua-hin', r'hua\s*hin|хуахин'),
           ('chiang-mai', r'chiang\s*mai|чиангмай')]
DEST_NAME = {d['slug']: d['name'] for d in AREAS}
TYPE_NAME = {'villa': 'Villa', 'apartment': 'Apartment', 'condo': 'Condo', 'penthouse': 'Penthouse', 'townhouse': 'Townhouse',
             'house': 'House', 'land': 'Land', 'studio': 'Studio', 'complex': 'Residential complex', '': 'Property'}
AMEN_OK = re.compile(r'pool|wi-?fi|internet|air ?con|kitchen|parking|garden|gym|fitness|sauna|spa|jacuzzi|bbq|barbecue|'
                     r'security|gate|beach|sea view|view|terrace|balcony|washing|laundry|tv|netflix|workspace|desk|'
                     r'cleaning|maid|chef|playground|kids|elevator|lift|furnish|bathtub|shower|safe|generator|cctv|'
                     r'co-?working|restaurant|shop|shuttle|transfer|concierge|tennis|golf|club|lounge|rooftop|library', re.I)


def clean(s):
    return re.sub(r'\s+', ' ', (s or '').replace(' ', ' ')).strip()


def num(x):
    try:
        return float(str(x).replace(',', '').replace(' ', ''))
    except (TypeError, ValueError):
        return None


def boilerplate(props, key):
    """Lines/specs that repeat on >= 6% (min 4) of a source's listings are site chrome, not listing content."""
    c = collections.Counter()
    for p in props:
        c.update(set(key(p)))
    lim = max(4, int(len(props) * 0.06))
    return {k for k, n in c.items() if n >= lim}


def paragraphs(p):
    out = []
    for ln in (p.get('fullText') or '').split('\n'):
        ln = clean(ln)
        if len(ln) >= 60 and not ln.endswith('...'):
            out.append(ln)
    return out


def pick_prices(p, deal):
    pr = [x for x in p.get('prices') or [] if isinstance(x.get('amount'), (int, float))]
    thb = [x for x in pr if x.get('currency') == 'THB'] or pr
    low = lambda x: x['amountFrom'] if x.get('amountFrom') and x['amountFrom'] >= x['amount'] * 0.15 else x['amount']
    res = {'priceNight': None, 'priceMonth': None, 'priceSale': None, 'currency': (thb[0]['currency'] if thb else 'THB') or 'THB'}
    if deal == 'rent':
        n = [low(x) for x in thb if x.get('period') == 'night']
        m = [low(x) for x in thb if x.get('period') == 'month']
        if not n and not m:  # unlabeled rent price: small = per night, big = per month
            un = [low(x) for x in thb if x.get('period') is None]
            n = [v for v in un if v < 60000]
            m = [v for v in un if v >= 60000]
        res['priceNight'] = int(n[0]) if n else None   # first = the listing's own price block; later ones are extras
        res['priceMonth'] = int(m[0]) if m else None
    else:
        s = [low(x) for x in thb if x.get('period') == 'sale'] or [low(x) for x in thb if x.get('period') is None and x['amount'] >= 1_000_000]
        res['priceSale'] = int(s[0]) if s else None
    return res


def location(p):
    hay = ' '.join([p.get('url', ''), p.get('title', ''), ' '.join(p.get('breadcrumbs') or [])]).lower()
    dest = next((slug for slug, rx in DEST_RX if re.search(rx, hay)), 'phuket')
    sub, sub_name = None, None
    if dest == 'phuket':
        s = p.get('subArea') or ''
        if s in PHUKET_SUBS:
            sub, sub_name = s, PHUKET_SUBS[s]
        elif s in EXTRA_SUBS:
            sub_name, sub = EXTRA_SUBS[s]
            if sub is None:
                return dest, None, sub_name
            return dest, sub, sub_name
    return dest, sub, sub_name


def title_of(p):
    t = clean(p.get('title') or p.get('h1') or '')
    t = re.sub(r'\s*\|\s*', ' · ', t)
    return t[:110]


def convert(src, p, chrome_par, chrome_spec, media_url, media_index, today):
    deal = p.get('dealType') if p.get('dealType') in ('rent', 'sale', 'project') else 'rent'
    dest, sub, sub_name = location(p)
    ptype = p.get('propertyType') or ''
    beds = p.get('bedrooms')
    mt = re.search(r'(\d{1,2})(?:\s*\+\s*\d)?\s*(?:-\s*)?(?:bed(?:room)?s?\b|br\b|спал)', p.get('title') or '', re.I)
    if mt:
        beds = int(mt.group(1))
    beds = int(beds) if isinstance(beds, (int, float)) and 0 < beds < 30 else (1 if ptype in ('studio', 'apartment', 'condo') else None)
    baths = p.get('bathrooms')
    baths = float(baths) if isinstance(baths, (int, float)) and 0 < baths < 30 else None
    guests = p.get('guests')
    guests = int(guests) if isinstance(guests, (int, float)) and 0 < guests < 60 else None
    if beds and not guests:
        guests = beds * 2
    if beds and not baths:
        baths = float(beds)
    names = media_index.get(p['slug']) or []
    base = media_url.get(f"{src}/{p['slug']}")
    images = [f"{base}/{src}/{p['slug']}/{n}" for n in names] if base else []
    if not images:
        return None
    desc = [x for x in paragraphs(p) if x not in chrome_par]
    text = '\n\n'.join(desc)
    if len(text) > 6000:
        text = text[:6000].rsplit('\n\n', 1)[0]
    specs = [[clean(k), clean(v)] for k, v in (p.get('specs') or [])
             if (k, v) not in chrome_spec and 0 < len(clean(v)) <= 140 and len(clean(k)) <= 50
             and not re.search(r'whatsapp|telegram|отправить|book|запрос|request', k + v, re.I)]
    amen = [clean(a) for a in (p.get('amenities') or []) if 2 < len(clean(a)) <= 40 and not clean(a).endswith((':', '.'))]
    amen = list(dict.fromkeys(amen))[:24]
    if not amen:
        low = (text + ' ' + ' '.join(v for _, v in specs)).lower()
        amen = [a for a, rx in (('Private pool', r'private pool|pool'), ('Wi-Fi', r'wi-?fi|internet'), ('Air conditioning', r'air ?con'),
                                ('Fully equipped kitchen', r'kitchen'), ('Parking', r'parking'), ('Garden', r'garden'),
                                ('Sea view', r'sea view|ocean view'), ('Gym', r'gym|fitness'), ('Security', r'security|guard'))
                if re.search(rx, low)]
    prices = pick_prices(p, deal)
    title = title_of(p)
    place = sub_name or DEST_NAME[dest]
    name = '%s — %s' % (place, title) if place.lower() not in title.lower()[:len(place) + 12] else title
    slug = re.sub(r'[^a-z0-9]+', '-', p['slug'].lower()).strip('-')[:80]
    section = {'rent': 'villa', 'sale': 'sale', 'project': 'projects'}[deal]
    url = f'{BASE}/{section}/{dest}/{slug}/' if deal != 'project' else f'{BASE}/projects/{slug}/'
    daily = bool(prices['priceNight']) or deal == 'rent' and not prices['priceMonth']
    monthly = bool(prices['priceMonth']) or bool(re.search(r'long[- ]term|monthly|per month|/month', (p.get('url', '') + text).lower()))
    tags = []
    top = prices['priceNight'] or 0
    if top >= 30000 or (prices['priceSale'] or 0) >= 40_000_000 or (beds or 0) >= 5:
        tags.append('luxury')
    if (beds or 0) >= 3:
        tags.append('family')
    rec = {
        'id': slug, 'slug': slug, 'name': name, 'sample': False, 'dealType': deal,
        'propertyType': ptype or 'villa', 'propertyTypeName': TYPE_NAME.get(ptype, 'Property'),
        'area': DEST_NAME[dest], 'areaSlug': dest, 'subArea': sub_name, 'subAreaSlug': sub,
        'bedrooms': beds or 0, 'bathrooms': baths or 0, 'guests': guests or 0,
        'livingAreaSqm': p.get('livingAreaSqm'), 'landArea': p.get('landArea'), 'floors': p.get('floors'),
        **prices,
        'amenities': amen or ['Wi-Fi', 'Air conditioning'],
        'description': text, 'specs': specs[:40],
        'latitude': p.get('latitude'), 'longitude': p.get('longitude'),
        'videos': (p.get('videos') or [])[:4],
        'images': images, 'cardImage': images[0], 'topGallery': images[:5],
        'monthly': monthly if deal == 'rent' else False, 'daily': daily if deal == 'rent' else False,
        'categories': [c for c in ('property-rental' if deal == 'rent' else 'property-' + deal, dest, sub, 'monthly' if monthly and deal == 'rent' else None) if c],
        'filterTags': tags, 'url': url, 'source': src, 'sourceUrl': p.get('url'), 'updatedAt': today,
    }
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source', action='append', required=True, help='key=import_dir')
    ap.add_argument('--media-root', required=True)
    ap.add_argument('--media-map', default=os.path.join(ROOT, 'data', 'media-map.json'))
    a = ap.parse_args()
    media_url = json.load(open(a.media_map, encoding='utf-8'))
    today = datetime.date.today().isoformat()
    out = {'rent': [], 'sale': [], 'project': []}
    seen = set()
    for spec in a.source:
        src, d = spec.split('=', 1)
        props = json.load(open(os.path.join(d, 'catalog.json'), encoding='utf-8'))['properties']
        idx_file = os.path.join(a.media_root, src, 'index.json')
        media_index = json.load(open(idx_file, encoding='utf-8')) if os.path.exists(idx_file) else {}
        chrome_par = boilerplate(props, paragraphs)
        chrome_spec = boilerplate(props, lambda p: [tuple(x) for x in p.get('specs') or []])
        n = 0
        seen_urls = set()
        for p in props:
            key = (p.get('url') or '').lower().rstrip('/')
            if key in seen_urls:
                continue
            seen_urls.add(key)
            r = convert(src, p, chrome_par, chrome_spec, media_url, media_index, today)
            if not r:
                continue
            base_slug, i = r['slug'], 2
            while (r['dealType'], r['slug']) in seen:
                r['slug'] = r['id'] = '%s-%d' % (base_slug, i)
                r['url'] = re.sub(r'/[^/]+/$', '/%s/' % r['slug'], r['url'])
                i += 1
            seen.add((r['dealType'], r['slug']))
            out[r['dealType']].append(r)
            n += 1
        print('%s: %d of %d listings converted (boilerplate dropped: %d paragraphs, %d specs)'
              % (src, n, len(props), len(chrome_par), len(chrome_spec)))
    for deal, fn in (('rent', 'villas.json'), ('sale', 'sale.json'), ('project', 'projects.json')):
        with open(os.path.join(ROOT, 'data', fn), 'w', encoding='utf-8') as f:
            json.dump(out[deal], f, ensure_ascii=False, indent=1)
        print(fn, len(out[deal]))


if __name__ == '__main__':
    sys.exit(main())
