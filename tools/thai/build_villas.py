#!/usr/bin/env python3
"""Villa pages for Thai Villas: /villa/{area}/{slug}/ and /villa/{area}/{slug}/gallery/.

Clones the canonical villa page design of the reference site (the same template that
tools/villa-page/make_villa_page.py / make_gallery_page.py use) and substitutes data from
data/villas.json. Layout and classes are kept; everything API-, review-, Bali- and
management-specific is removed or rewritten. All villas are SAMPLE listings, prices "On request".

    python3 -I tools/thai/build_villas.py
"""
import sys, os, re, json, shutil, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from thv import *                                   # noqa: F401,F403
from thv import _balanced

TPL_V = 'villa/sanur/modern-2br-pool-townhouse-sanur/index.html'
TPL_G = 'villa/sanur/modern-2br-pool-townhouse-sanur/gallery/index.html'
T_URL = '/villa/sanur/modern-2br-pool-townhouse-sanur/'
T_NAME = 'Modern 2BR Pool Townhouse in Sanur'
T_SHORT = 'Modern 2BR Pool Townhouse'
T_BASE = '/public-objects/images/sanur-modern-2br-townhouse-'
UI = '/villa/ui/'                                   # local copies of the villa page CSS + icon sprites
MONTHLY_HUBS = {'phuket', 'koh-samui', 'pattaya', 'bangkok', 'chiang-mai'}
SEASONS = ('High season runs from November to April; May to October is the green season, '
           'with short tropical showers and softer rates.')


# ---------------------------------------------------------------- helpers
def sub1(s, old, new, what, count=1):
    n = s.count(old)
    assert n == count if count else n >= 1, '%s: found %d times' % (what, n)
    return s.replace(old, new)

def resub(s, pat, new, what, flags=re.S):
    s2, n = re.subn(pat, new, s, flags=flags)
    assert n >= 1, 'pattern not found: ' + what
    return s2

def close_div(s, i):
    """i = index right after an opening <div ...>; returns the index of its </div>."""
    depth = 1
    for m in re.finditer(r'<div\b[^>]*>|</div>', s[i:]):
        depth += 1 if m.group(0) != '</div>' else -1
        if depth == 0:
            return i + m.start()
    raise AssertionError('unclosed div')

def jpeg_size(rel):
    """(w, h) of a JPEG read from its SOF marker — no PIL needed."""
    with open(os.path.join(ROOT, rel.lstrip('/')), 'rb') as f:
        data = f.read()
    i = 2
    while i < len(data):
        if data[i] != 0xFF:
            i += 1; continue
        m = data[i + 1]
        if m in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
            h, w = struct.unpack('>HH', data[i + 5:i + 9])
            return w, h
        i += 2 + struct.unpack('>H', data[i + 2:i + 4])[0]
    return 1600, 1067

def short(v):
    return v['name'].split(' — ', 1)[1] if ' — ' in v['name'] else v['name']

def dest(v):
    return next(d for d in AREAS if d['slug'] == v['areaSlug'])

def subarea(v):
    return next((a for a in dest(v).get('areas', []) if a['slug'] == v.get('subAreaSlug')), None)

def back_url(v):
    return area_url(v['areaSlug'], v.get('subAreaSlug'))

def place(v):
    return v.get('subArea') or v['area']

def periods(v):
    return [p for p, ok in (('Daily', v.get('daily')), ('Monthly', v.get('monthly'))) if ok]

def group_of(img):
    b = os.path.basename(img)
    return 'Exterior & pool' if b.startswith('ext-') else 'Living' if b.startswith('living-') else 'Bedrooms' if b.startswith('bed-') else 'More photos'

def groups(v):
    order = ['Exterior & pool', 'Living', 'Bedrooms', 'More photos']
    g = {}
    for img in v['images']:
        g.setdefault(group_of(img), []).append(img)
    return [(k, g[k]) for k in order if k in g]

def amen_list(v):
    a = [x.lower().replace('wi-fi', 'Wi-Fi') for x in v['amenities']]
    return ', '.join(a[:-1]) + ' and ' + a[-1] if len(a) > 1 else a[0]

def stay_text(v):
    p = periods(v)
    return ('short holiday stays and monthly / long stays' if len(p) == 2 else
            'short holiday stays (daily rental)' if p == ['Daily'] else 'monthly and long stays')

def description(v):
    sa, d = subarea(v), dest(v)
    loc = (sa or d)['short']
    return ('Sample listing. A %d-bedroom, %g-bathroom villa in %s for up to %d guests, with %s. %s '
            'Offered for %s. This page shows how our villa listings will look — real villas with verified '
            'photos, details and prices are coming soon. Message us on WhatsApp with your dates and we will '
            'suggest villas that fit.'
            % (v['bedrooms'], v['bathrooms'], where(v), v['guests'], amen_list(v), loc, stay_text(v)))

def meta_desc(v):
    return ('Sample listing: %d-bedroom villa in %s, Thailand — %s. Sleeps %d. %s rental, price on request via WhatsApp.'
            % (v['bedrooms'], where(v), ', '.join(x.lower().replace('wi-fi', 'Wi-Fi') for x in v['amenities'][:3]),
               v['guests'], ' & '.join(periods(v))))

def related(v, n=4):
    others = [x for x in VILLAS if x['id'] != v['id']]
    rank = lambda x: (0 if x['areaSlug'] == v['areaSlug'] and x.get('subAreaSlug') == v.get('subAreaSlug') and x.get('subAreaSlug')
                      else 1 if x['areaSlug'] == v['areaSlug'] else 2)
    return sorted(others, key=rank)[:n]   # sorted() is stable: keeps villas.json order inside each rank


# ---------------------------------------------------------------- amenity icons (same sprite as the reference)
ICONS = [('pool', 'am-pool'), ('wi-fi', 'am-wifi'), ('wifi', 'am-wifi'), ('air conditioning', 'am-ac'),
         ('kitchen', 'am-kitchen'), ('chef', 'am-dining'), ('workspace', 'am-workspace'), ('motorbike', 'am-motorbike'),
         ('parking', 'am-parking'), ('beach', 'am-beach'), ('garden', 'am-garden'), ('sea view', 'am-view'),
         ('view', 'am-view'), ('washing', 'am-washer'), ('laundry', 'am-washer'), ('tv', 'am-tv'), ('safe', 'am-safe')]
def icon_for(t):
    t = t.lower()
    return next((ic for k, ic in ICONS if k in t), 'am-check')

AM_ITEM = ('<div class="flex items-center gap-2.5 self-stretch"><svg class="shrink-0 size-5 text-primary" aria-hidden="true">'
           '<use href="' + UI + 'amenities.svg#{ic}"></use></svg>'
           '<p class="text-body-lg-long text-primary font-normal" data-slot="text">{txt}</p></div>')

SLIDE = ('<div class="relative shrink-0 w-[89vw] h-[112vw] max-h-55vh my-4 snap-start">'
         '<button type="button" class="w-full h-full p-0 bg-transparent border-none"><picture>'
         '<img alt="{alt}" loading="{load}"{prio} decoding="async" data-nimg="fill" '
         'class="animate-fade-in duration-300 w-full h-full object-cover rounded-xl shadow-[0_4px_8px_0px_rgba(0,0,0,0.16)]" '
         'style="position:absolute;height:100%;width:100%;left:0;top:0;right:0;bottom:0;color:transparent" '
         'src="{src}" width="1200" height="800"></picture></button></div>')
CAROUSEL_HEAD = ('class="overflow-x-auto scrollbar-hide snap-x snap-mandatory scroll-smooth overscroll-x-contain '
                 'w-screen lg:mx-0 -m-5 relative scroll-px-5"><div class="flex items-start self-stretch px-5 gap-2 w-fit">')

BED_ITEM = ('<div class="flex flex-col items-start gap-1.5"><picture>'
            '<img class="w-full rounded-xl object-cover aspect-136/93" src="{src}" alt="{alt}" '
            'width="1200" height="900" loading="lazy" decoding="async"></picture>'
            '<p class="text-body-lg font-medium text-primary mt-2" data-slot="text">{label}</p>'
            '<p class="text-body text-secondary font-normal" data-slot="text">{sub}</p></div>')

PILL = ('<span style="display:inline-flex;align-items:center;gap:6px;border:1px solid #e6e3dc;background:#fff;color:#0a0a0a;'
        'border-radius:999px;padding:5px 12px;font-size:13px;font-weight:600;line-height:1.3">{t}</span>')
SAMPLE_PILL = ('<span style="display:inline-flex;align-items:center;background:rgba(10,10,10,.82);color:#fff;border-radius:999px;'
               'padding:5px 12px;font-size:11.5px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;line-height:1.3">Sample listing</span>')

EXTRA_CSS = '''<style id="thv-villa-css">
details.thb-area{border:1px solid #e6e3dc;border-radius:16px;background:#fff;padding:0}
details.thb-area summary{cursor:pointer;padding:16px 20px;font-weight:600;font-size:15px;list-style:none;display:flex;justify-content:space-between;align-items:center}
details.thb-area summary::-webkit-details-marker{display:none}
details.thb-area summary::after{content:"+";font-size:20px;font-weight:400;color:#6b6b66}
details.thb-area[open] summary::after{content:"\\2013"}
details.thb-area .in{padding:0 20px 18px;font-size:15px;line-height:1.6;color:#3c3c39}
details.thb-area .in p{margin:0 0 12px}
details.thb-area .lk{display:flex;flex-wrap:wrap;gap:8px;margin-top:6px}
details.thb-area .lk a{border:1px solid #e6e3dc;border-radius:999px;padding:7px 14px;font-size:13.5px;font-weight:600;color:#0a0a0a;text-decoration:none}
details.thb-area .lk a:hover{border-color:#0a0a0a}
header span:has(>a[data-hostpill]){white-space:nowrap}
@media(min-width:768px){header div:has(>span>a[data-hostpill]){flex:none}}
@media(max-width:767.98px){.thb-navlink{display:none}}
.thv-rel{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}
@media(min-width:768px){.thv-rel{grid-template-columns:repeat(4,minmax(0,1fr))}}
.thv-rel a{display:flex;flex-direction:column;gap:4px;color:inherit;text-decoration:none;min-width:0}
.thv-rel a:hover img{opacity:.9}
.thv-rel p{overflow:hidden;text-overflow:ellipsis}
.thv-rel .t{display:-webkit-box;-webkit-box-orient:vertical;-webkit-line-clamp:2;white-space:normal}
</style>'''


# ---------------------------------------------------------------- shared rewrites
def strip_common(s):
    s = re.sub(r'<meta name="(robots|googlebot)"[^>]*>\s*', '', s)
    s = re.sub(r'<base href="[^"]*">\s*', '', s)
    s = re.sub(r'<script[^>]*src="/thb-(bot|consent|ru|it|lang|sale|sale-map)\.js[^"]*"[^>]*></script>\s*', '', s)
    s = re.sub(r'<link rel="stylesheet" href="https://cdn\.jsdelivr\.net/npm/glightbox[^>]*>(<noscript>.*?</noscript>)?', '', s, flags=re.S)
    s = re.sub(r'<meta name="theme-color"[^>]*>\s*', '', s)
    s = re.sub(r'<!-- seo-rent-ld -->', '', s)
    s = re.sub(r'<source srcset="[^"]*" type="image/avif">', '', s)
    s = s.replace('wa.me/6285746499697', 'wa.me/' + WA_NUM).replace('+62 857 4649 9697', PHONE)
    s = s.replace('hello@thehostbali.com', EMAIL).replace('tel:+6285746499697', 'tel:+' + WA_NUM)
    s = s.replace('/villa/assets/css/main.css', UI + 'main.css')
    s = re.sub(r'/villa/assets/(icon|wos)\.svg\?v=[0-9a-f]+#', lambda m: UI + m.group(1) + '.svg#', s)
    s = s.replace('/brand/amenities.svg#', UI + 'amenities.svg#')
    # footer: Thai shell (5 columns: brand + 4 lists)
    s = replace_el(s, r'<footer class="thb-ft"', footer(), 'footer')
    s = s.replace('.thb-ft-grid{display:grid;grid-template-columns:1.6fr 1fr 1fr 1.3fr;gap:40px}',
                  '.thb-ft-grid{display:grid;grid-template-columns:1.5fr 1fr 1fr 1fr 1.3fr;gap:36px}')
    return s

def bookbar(s, v):
    text = "Hi Thai Villas! I'd like to book %s (%s). Is it available?" % (v['name'], v['url'])
    s = resub(s, r'<div id="thbBookBar"><div class="tbb-i"><strong>Prices on request</strong><span>[^<]*</span></div><a href="[^"]*"',
              '<div id="thbBookBar"><div class="tbb-i"><strong>On request</strong><span>Sample listing · fast reply on WhatsApp</span></div>'
              '<a href="%s"' % esc(wa(text)), 'book bar')
    return s

def ld_villa(v):
    return {'@context': 'https://schema.org', '@type': 'VacationRental', 'name': v['name'],
            'description': description(v), 'url': v['url'],
            'image': list(dict.fromkeys(v['topGallery'] + v['images']))[:8],
            'address': {'@type': 'PostalAddress', 'addressLocality': place(v), 'addressRegion': v['area'], 'addressCountry': 'TH'},
            'containsPlace': {'@type': 'Accommodation', 'additionalType': 'Villa',
                              'occupancy': {'@type': 'QuantitativeValue', 'maxValue': v['guests']},
                              'numberOfBedrooms': v['bedrooms'], 'numberOfBathroomsTotal': v['bathrooms']},
            'amenityFeature': [{'@type': 'LocationFeatureSpecification', 'name': a, 'value': True} for a in v['amenities']],
            'brand': {'@type': 'Brand', 'name': BRAND}}

def crumbs_list(v, gallery=False):
    c = [('Thailand', '/villas/'), (v['area'], area_url(v['areaSlug']))]
    if v.get('subAreaSlug'):
        c.append((v['subArea'], back_url(v)))
    c.append((short(v), v['url']))
    if gallery:
        c.append(('Photo tour', v['url'] + 'gallery/'))
    return c

def ld_crumbs(v, gallery=False):
    items = [('Home', '/')] + crumbs_list(v, gallery)
    return {'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': i + 1, 'name': n, 'item': u} for i, (n, u) in enumerate(items)]}


# ---------------------------------------------------------------- villa page
def build_villa(v, tpl):
    name, sh, url = v['name'], short(v), v['url']
    tg = list(v['topGallery']) + [v['cardImage']] * 5
    s = strip_common(tpl)
    s = clean_head(s, title='%s | %s' % (name, BRAND), desc=meta_desc(v), jsonld=[ld_villa(v), ld_crumbs(v)],
                   image=v['cardImage'])
    s = s.replace('</head>', EXTRA_CSS + '\n</head>', 1)

    # header: logo + nav links
    s = sub1(s, '<span style="font-style:italic;font-weight:400">The</span>&nbsp;<span style="font-weight:700;letter-spacing:0.09em">HOST</span>',
             '<span style="font-style:italic;font-weight:400">Thai</span>&nbsp;<span style="font-weight:700;letter-spacing:0.09em">VILLAS</span>',
             'logo', 2)
    s = sub1(s, '>Villas&nbsp;for&nbsp;rent</a>', '>Villas</a>', 'nav villas', 2)
    s = sub1(s, '<a href="/villas-for-sale/" class="thb-navlink"', '<a href="/monthly-rental/" class="thb-navlink"', 'nav sale', 2)
    s = sub1(s, '>For&nbsp;sale</a>', '>Monthly</a>', 'nav sale text', 2)
    s, n = re.subn(r'<a href="/blog/" class="thb-navlink"([^>]*)>Guides</a>', r'<a href="/vip/" class="thb-navlink"\1>VIP</a>', s)
    assert n == 2, 'nav guides'

    # mobile menu
    links = [('/property-rental/', 'All villas <span>%d</span>' % len(VILLAS)),
             ('/villas/phuket/', 'Phuket <span>%d</span>' % count('phuket'))]
    links += [(area_url('phuket', a['slug']), a['name'] + ' <span>%d</span>' % count('phuket', a['slug']))
              for a in PHUKET['areas'] if count('phuket', a['slug'])][:4]
    links += [('/property-rental/?period=daily', 'Daily rentals'), ('/monthly-rental/', 'Monthly &amp; long stay'),
              ('/vip/', 'VIP services'), ('/villas/', 'All destinations'), ('/about/', 'About'), ('/contacts/', 'Contacts')]
    menu = ('<div id="thbMobileMenu" hidden>\n  <a href="/saved/" class="thb-saved-item" style="color:#e11d48">Saved villas '
            '<span data-fav-count style="display:none"></span></a>\n'
            + ''.join('  <a href="%s">%s</a>\n' % l for l in links)
            + '  <a href="%s" rel="noopener" style="color:#0a7d43">WhatsApp</a>\n</div>' % WA)
    s = replace_el(s, r'<div id="thbMobileMenu" hidden>', menu)

    # breadcrumbs (visible, same markup as the template)
    cl = crumbs_list(v)
    lis = ''.join('<li itemprop="itemListElement" itemscope itemtype="https://schema.org/ListItem">'
                  '<a itemprop="item" href="%s"><span itemprop="name">%s</span></a><meta itemprop="position" content="%d"></li>'
                  % (u, esc(n), i + 1) for i, (n, u) in enumerate(cl[:-1]))
    lis += ('<li itemprop="itemListElement" itemscope itemtype="https://schema.org/ListItem"><span aria-current="page" '
            'itemprop="name">%s</span><meta itemprop="position" content="%d"></li>' % (esc(sh), len(cl)))
    s = replace_el(s, r'<nav aria-label="breadcrumb" class="thb-crumbs">',
                   '<nav aria-label="breadcrumb" class="thb-crumbs"><ol itemscope itemtype="https://schema.org/BreadcrumbList">%s</ol></nav>' % lis, 'nav')

    # mobile carousel: one slide per photo
    a = s.find(CAROUSEL_HEAD); assert a >= 0, 'carousel'
    a += len(CAROUSEL_HEAD)
    b = s.find('</div></div></div><div class="absolute bottom-8', a); assert b > a, 'carousel end'
    b += len('</div>')
    slides = ''.join(SLIDE.format(alt='%s — %s photo %d' % (esc(sh), group_of(img).lower(), i + 1), src=img,
                                  load='eager' if i == 0 else 'lazy', prio=' fetchpriority="high"' if i == 0 else '')
                     for i, img in enumerate(v['images']))
    s = s[:a] + slides + s[b:]
    s = sub1(s, '>1<!-- -->/<!-- -->32</span>', '>1<!-- -->/<!-- -->%d</span>' % len(v['images']), 'counter')

    # desktop mosaic (5 photos), wishlist toast, fav buttons
    for idx, img in {27: tg[0], 1: tg[1], 9: tg[2], 12: tg[3], 28: tg[4], 16: tg[1]}.items():
        s = s.replace('%s%02d.jpg' % (T_BASE, idx), img)
    s = s.replace('data-m="2 bed · 2.5 bath · 4 guests" data-a="Sanur"', 'data-m="%s" data-a="%s"' % (meta(v), esc(where(v))))

    # summary: location line, title, facts, rental type badges + sample notice
    s = sub1(s, '>Villa in Sanur</h2>', '>Villa in %s</h2>' % esc(where(v)), 'location line')
    facts = ('<div class="flex items-center flex-wrap w-full gap-1.5">'
             + '<p class="text-body text-tertiary font-normal" data-slot="text" aria-hidden="true">•</p>'.join(
                 '<p class="text-body-lg text-secondary font-normal" data-slot="text">%s</p>' % f for f in
                 ('%d bedroom%s' % (v['bedrooms'], '' if v['bedrooms'] == 1 else 's'),
                  '%g bathroom%s' % (v['bathrooms'], '' if v['bathrooms'] == 1 else 's'),
                  '%d guests' % v['guests']))
             + '</div><div class="flex items-center flex-wrap gap-2" style="margin-top:4px">'
             + ''.join(PILL.format(t=p + ' rental') for p in periods(v)) + SAMPLE_PILL + '</div>')
    s = replace_el(s, r'<div class="flex items-center flex-wrap w-full gap-1\.5">', facts)

    # about
    s = sub1(s, '>New 110 m2 two-storey townhouse', '>@@DESC@@', 'desc start')
    s = re.sub(r'>@@DESC@@[^<]*<', lambda m: '>' + esc(description(v)) + '<', s)

    # where you'll sleep
    beds = [i for i in v['images'] if 'bed-' in i] or v['images']
    items = ''.join(BED_ITEM.format(src=beds[i % len(beds)], alt='%s — bedroom %d' % (esc(sh), i + 1),
                                    label='Bedroom %d' % (i + 1), sub='Bed setup confirmed on request')
                    for i in range(v['bedrooms']))
    head = ('<h2 class="text-headline text-primary font-medium" data-slot="heading">Where you’ll sleep</h2></div>'
            '<div class="grid grid-cols-1 sm:grid-cols-2 gap-4">')
    a = s.find(head); assert a >= 0, 'sleep'
    a += len(head); b = s.find('</div></section>', a)
    s = s[:a] + items + s[b:]

    # amenities
    head = ('<h2 class="text-headline text-primary font-medium" data-slot="heading">Amenities</h2></div>'
            '<div class="grid grid-cols-[1fr] lg:grid-cols-[1fr_1fr] gap-3">')
    a = s.find(head); assert a >= 0, 'amenities'
    a += len(head); b = close_div(s, a)
    s = s[:a] + ''.join(AM_ITEM.format(ic=icon_for(x), txt=esc(x)) for x in v['amenities']) + s[b:]

    # guarantee block -> sample listing notice (same look, not a button)
    sp = _balanced(s, r'<button type="button" class="p-6 bg-surface-secondary rounded-xl', 'button')
    blk = s[sp[0]:sp[1]]
    icon = re.search(r'<div class="size-10 rounded-full.*?</div>', blk, re.S).group(0)
    note = ('<div class="p-6 bg-surface-secondary rounded-xl flex items-center gap-4 w-full text-left border-0 mb-12" role="note">'
            + icon + '<div class="flex flex-col items-start flex-1 relative z-10">'
            '<h3 class="text-headline-sm text-primary font-medium" data-slot="heading">Sample listing — real villas coming soon</h3>'
            '<p class="text-body text-secondary font-normal mt-1" data-slot="text">Photos and details on this page are illustrative. '
            'Tell us your dates on WhatsApp and we will send real, available villas in %s.</p></div></div>' % esc(place(v)))
    s = s[:sp[0]] + note + s[sp[1]:]

    # location
    sa, d = subarea(v), dest(v)
    s = sub1(s, '>Sanur, Bali, Indonesia</p>', '>%s, Thailand</p>' % esc(where(v)), 'location text')
    img = (sa or d)['image']
    w, h = jpeg_size(img)
    pic = ('<div class="relative h-[376px] self-stretch rounded-2xl overflow-hidden z-[1]" style="height:376px">'
           '<img src="%s" alt="%s" width="%d" height="%d" loading="lazy" decoding="async" '
           'style="position:absolute;inset:0;width:100%%;height:100%%;object-fit:cover">'
           '<span style="position:absolute;left:14px;bottom:14px;background:rgba(255,255,255,.94);color:#0a0a0a;border-radius:999px;'
           'padding:7px 14px;font-size:13.5px;font-weight:600">%s, Thailand</span></div>'
           % (img, esc(where(v)), w, h, esc(where(v))))
    s = replace_el(s, r'<div class="relative h-\[376px\] self-stretch rounded-2xl bg-gray-300', pic)
    s = resub(s, r'(<p class="text-body-lg-long text-primary font-normal" data-slot="text">)Modern 2BR Pool Townhouse is a new[^<]*(</p>)',
              lambda m: m.group(1) + esc('This sample villa is listed in %s. %s The exact address is shared when your booking is confirmed.'
                                         % (where(v), (sa or d)['short'])) + m.group(2), 'location para')
    lk = '<a href="%s">All villas in %s</a>' % (back_url(v), esc(place(v)))
    if sa:
        lk += '<a href="%s">All villas in %s</a>' % (area_url(v['areaSlug']), esc(v['area']))
    if v['areaSlug'] in MONTHLY_HUBS and v.get('monthly'):
        lk += '<a href="/monthly-rental/%s/">Monthly rentals in %s</a>' % (v['areaSlug'], esc(v['area']))
    area_txt = '<p>%s</p>' % esc(sa['short']) if sa else ''
    area_txt += '<p>%s %s</p>' % (esc(d['short']), esc(SEASONS) if v['areaSlug'] in ('phuket', 'krabi') else '')
    s = replace_el(s, r'<details class="thb-area">',
                   '<details class="thb-area"><summary>Learn more about %s</summary><div class="in">%s<div class="lk">%s</div></div></details>'
                   % (esc(place(v)), area_txt, lk), 'details')

    # booking card + mobile bar
    s = sub1(s, 'data-slot="booking-panel-header">Select dates for pricing</h3>',
             'data-slot="booking-panel-header">On request<span style="display:block;margin-top:4px;font-family:Inter,system-ui,sans-serif;'
             'font-size:14px;font-weight:400;color:#6b6b66">%s rental · sample listing</span></h3>' % ' &amp; '.join(periods(v)),
             'booking header')
    s = sub1(s, 'pt-[5px]">$0</div><div class="text-content-muted text-xs font-sans font-normal leading-5">for <!-- -->0 nights</div>',
             'pt-[5px]">On request</div><div class="text-content-muted text-xs font-sans font-normal leading-5">sample listing</div>', 'sticky price')
    s = sub1(s, '>Prices on request</span>', '>On request</span>', 'mobile price')
    s = sub1(s, ">You won't be charged yet.</p>", ">No payment now — we confirm on WhatsApp.</p>", 'no charge')

    s = s.replace('Select dates for pricing', 'Select your dates')
    # things to know: nothing invented
    for o, n in (('Cancel within 24 hours for a full refund.', 'Cancellation terms are confirmed in writing before you pay.'),
                 ('Pets allowed with fee', 'Pets on request'),
                 ('No smoking - fees will apply', 'House rules shared before booking'),
                 ('Events require approval', 'Events on request'),
                 ('Check-in after 3:00 pm', 'Check-in time agreed on booking'),
                 ('Check-out before 11:00 am', 'Check-out time agreed on booking'),
                 ('>4 guests maximum<', '>%d guests maximum<' % v['guests'])):
        s = sub1(s, o, n, 'rules: ' + o)

    # related villas (same beach first, then same destination)
    rel = ''.join('<a href="%s"><picture><img class="w-full rounded-xl object-cover aspect-136/93" src="%s" alt="%s" width="1200" '
                  'height="900" loading="lazy" decoding="async"></picture>'
                  '<p class="text-body-lg font-medium text-primary mt-2 t" data-slot="text">%s</p>'
                  '<p class="text-body text-secondary font-normal" data-slot="text">%s</p>'
                  '<p class="text-body text-secondary font-normal" data-slot="text">%s · On request</p></a>'
                  % (x['url'], x['cardImage'], esc(x['name']), esc(short(x)), esc(where(x)), meta(x)) for x in related(v))
    title = 'More villas in %s' % (place(v) if v.get('subAreaSlug') and all(x.get('subAreaSlug') == v['subAreaSlug'] for x in related(v)) else v['area'])
    if not any(x['areaSlug'] == v['areaSlug'] for x in related(v)):
        title = 'More villas in Thailand'
    relsec = ('<section id="section-related" class="py-8 lg:py-10 flex flex-col gap-6 lg:gap-8 @container">'
              '<div class="flex flex-col gap-6"><h2 class="text-headline text-primary font-medium" data-slot="heading">%s</h2></div>'
              '<div class="thv-rel">%s</div><p class="text-body text-secondary font-normal" data-slot="text">'
              '<a href="%s" style="color:#0a0a0a;font-weight:600;text-decoration:underline;text-underline-offset:3px">Back to all villas in %s</a>'
              ' &middot; <a href="/property-rental/" style="color:#0a0a0a;font-weight:600;text-decoration:underline;text-underline-offset:3px">Browse all villas</a></p></section>'
              % (esc(title), rel, back_url(v), esc(place(v))))
    sp = _balanced(s, r'<section id="section-rules"', 'section')
    s = s[:sp[1]] + relsec + s[sp[1]:]

    # scripts
    s = sub1(s, 'const MAX_GUESTS = 8;', 'const MAX_GUESTS = %d;' % v['guests'], 'max guests')
    s = sub1(s, "var fallback = '/villas/sanur/';", "var fallback = '%s';" % back_url(v), 'smart back')
    s = bookbar(s, v)
    s = sub1(s, "var WA='6285746499697';", "var WA='%s';" % WA_NUM, 'checkavail WA')
    s = sub1(s, "'Hi The Host Bali! Availability request for '", "'Hi Thai Villas! Availability request for '", 'checkavail text')
    s = sub1(s, "return 'https://thehostbali.com'+location.pathname;", "return location.origin+location.pathname;", 'checkavail url')
    s = sub1(s, "b.setAttribute('aria-label','The Host Bali \\u2014 home');\n        b.textContent='H';",
             "b.setAttribute('aria-label','Thai Villas \\u2014 home');\n        b.textContent='T';", 'secnav badge')
    s = s.replace('<a href="#section-rules">Things to know</a>', '<a href="#section-rules">Things to know</a><a href="#section-related">More villas</a>')
    s = s.replace('#section-location,#section-rules{', '#section-location,#section-rules,#section-related{')
    s = s.replace('<script defer src="/thb-totop.js"></script>\n<script defer src="/thb-enquiry.js"></script>',
                  '<script defer src="/thb-totop.js"></script>\n<script defer src="/thb-readmore.js"></script>\n<script defer src="/thb-enquiry.js"></script>')

    # names and paths last (markers above rely on the template text)
    s = s.replace(T_URL, url).replace(esc(T_NAME), esc(name)).replace(T_NAME, esc(name)).replace(T_SHORT, esc(sh))
    left = [x for x in ('/public-objects/', 'Sanur', 'Host', 'Airbnb', 'Guarantee', 'Hostex', '/villa/assets', '/brand/') if x in s]
    assert not left, '%s: template leftovers %s' % (v['id'], left)
    return s


# ---------------------------------------------------------------- gallery page
def build_gallery(v, tpl):
    name, url = v['name'], v['url']
    gs = groups(v)
    total = sum(len(g) for _, g in gs)
    sid = lambda n: re.sub(r'[^a-z0-9]+', '-', n.lower()).strip('-')
    s = strip_common(tpl)
    desc = 'Photo tour of %s (sample listing): %s. Daily and monthly villa rentals in Thailand, booked on WhatsApp.' % (
        name, ', '.join(n.lower() for n, _ in gs))
    s = clean_head(s, title='%s photo tour | %s' % (name, BRAND), desc=desc, jsonld=[ld_crumbs(v, gallery=True)], image=v['cardImage'])
    s = re.sub(r'<link rel="canonical"[^>]*>', '', s)

    tabs = '<nav class="category-tabs">' + ''.join('<span class="tab" data-target="%s">%s</span>' % (sid(n), esc(n)) for n, _ in gs) + '</nav>'
    a = s.find('<nav class="category-tabs">'); b = s.find('</nav>', a) + 6
    s = s[:a] + tabs + s[b:]

    out = ['<main class="gallery-content">',
           '<p style="margin:0 0 18px;padding:12px 16px;border:1px solid #e6e3dc;border-radius:14px;background:#fafaf7;font-size:14px;'
           'line-height:1.5;color:#3c3c39"><strong style="color:#0a0a0a">Sample listing — real villas coming soon.</strong> '
           'These photos are illustrative. <a href="%s" style="color:#0a0a0a;text-decoration:underline">Back to the villa</a> or '
           '<a href="%s" style="color:#0a0a0a;text-decoration:underline">see all villas in %s</a>.</p>' % (url, back_url(v), esc(place(v)))]
    for n, imgs in gs:
        out.append('<section class="category-section" id="%s"><div class="section-header"><h2 class="section-title">%s</h2>'
                   '<span class="section-count">%d photo%s</span></div><div class="photo-grid">'
                   % (sid(n), esc(n), len(imgs), '' if len(imgs) == 1 else 's'))
        for i, img in enumerate(imgs, 1):
            w, h = jpeg_size(img)
            out.append('<div class="photo-item"><picture><img loading="lazy" src="%s" alt="%s — %s photo %d" width="%d" height="%d">'
                       '</picture><span class="photo-caption">%s</span></div>' % (img, esc(name), esc(n), i, w, h, esc(n)))
        out.append('</div></section>')
    out.append('</main>')
    a = s.find('<main class="gallery-content">'); b = s.find('</main>', a) + 7
    s = s[:a] + ''.join(out) + s[b:]

    s = sub1(s, '1 / 32 photos', '1 / %d photos' % total, 'gallery counter')
    s = sub1(s, '<span id="totalCount">32</span>', '<span id="totalCount">%d</span>' % total, 'gallery total')
    s = resub(s, r'<button class="icon-btn" title="Save">.*?</button>', '', 'save btn')
    s = resub(s, r"""<button class="book-btn" onclick="location\.href='[^']*'">""",
              '<button class="book-btn" onclick="location.href=\'%s\'">' % wa("Hi Thai Villas! I'm interested in %s (%s). Is it available?" % (name, url)).replace("'", '%27'),
              'gallery wa')
    s = bookbar(s, v)
    s = s.replace(T_URL, url).replace(esc(T_NAME), esc(name)).replace(T_NAME, esc(name))
    left = [x for x in ('/public-objects/', 'Sanur', 'Host', 'Airbnb', 'Hostex', '/brand/') if x in s]
    assert not left, '%s gallery: template leftovers %s' % (v['id'], left)
    return s


# ---------------------------------------------------------------- assets + index
def copy_assets():
    dst = os.path.join(ROOT, 'villa', 'ui')
    os.makedirs(dst, exist_ok=True)
    css = open(os.path.join(TPL, 'villa/assets/css/main.css'), encoding='utf-8').read()
    css = re.sub(r'@font-face\{[^}]*instrument_sans[^}]*\}', '', css)      # font file is not shipped
    open(os.path.join(dst, 'main.css'), 'w', encoding='utf-8').write(css)
    for src, name in (('villa/assets/icon.svg', 'icon.svg'), ('villa/assets/wos.svg', 'wos.svg'), ('brand/amenities.svg', 'amenities.svg')):
        t = open(os.path.join(TPL, src), encoding='utf-8').read()
        t = re.sub(r'<!--.*?-->', '', t, flags=re.S)
        assert not audit(t), (name, audit(t))
        open(os.path.join(dst, name), 'w', encoding='utf-8').write(t)
    assert not audit(css), audit(css)

INDEX = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Villas in Thailand | Thai Villas</title>
<meta name="robots" content="noindex">
<meta http-equiv="refresh" content="0; url=/villas/">
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
</head>
<body style="font-family:Inter,system-ui,sans-serif;padding:40px 20px">
<p>Redirecting to <a href="/villas/">all villa destinations in Thailand</a>…</p>
</body>
</html>
'''


def main():
    copy_assets()
    tv, tg = read_tpl(TPL_V), read_tpl(TPL_G)
    for v in VILLAS:
        rel = v['url'].strip('/')
        write(rel + '/index.html', build_villa(v, tv))
        write(rel + '/gallery/index.html', build_gallery(v, tg))
        print('ok', v['url'], '+ gallery/')
    write('villa/index.html', INDEX)
    print('ok /villa/ -> /villas/')


if __name__ == '__main__':
    main()
