"""Shared shell for every Thai Villas page generator.

Page generators take a page from the reference template site (the "wrapper" design), swap in the
Thai shell with `rebrand()`, then replace the page body with Thai content. Everything brand-,
contact- and inventory-specific lives here so the pages stay consistent.

    from thv import *           # (with tools/thai on sys.path)
    html = rebrand(read_tpl('villas/umalas/index.html'), title=..., desc=..., path='/villas/phuket/')
    ...
    write('villas/phuket/index.html', html)
"""
import html as _html, json, os, re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
# Reference design (read-only). Override with THAI_TPL=/path/to/checkout.
TPL = os.environ.get('THAI_TPL', '/private/tmp/claude-501/-Users-macbookm4-Projects-Whatsapp-crm/'
                     'f6949ea3-892b-4504-be21-647ce2cb4d05/scratchpad/src/thebalihost')

BRAND = 'Thai Villas'
WA_NUM = '66000000000'                      # TODO: real number
PHONE = '+66 00 000 0000'                   # TODO
EMAIL = 'hello@thaivillas.example'          # TODO
WA = 'https://wa.me/' + WA_NUM
def wa(text="Hi Thai Villas! I'm looking for a villa in Thailand."):
    from urllib.parse import quote
    return WA + '?text=' + quote(text)

esc = lambda s: _html.escape(str(s), quote=True)

def load(name):
    return json.load(open(os.path.join(ROOT, 'data', name), encoding='utf-8'))

VILLAS = load('villas.json')
AREAS = load('areas.json')['destinations']
VIP = load('vip.json')['categories']
PHUKET = next(d for d in AREAS if d['slug'] == 'phuket')

def count(area=None, sub=None, pred=None):
    return sum(1 for v in VILLAS if (area is None or v['areaSlug'] == area)
               and (sub is None or v.get('subAreaSlug') == sub) and (pred is None or pred(v)))

def area_url(slug, sub=None):
    return '/villas/%s/' % slug + ('%s/' % sub if sub else '')

def read_tpl(rel):
    return open(os.path.join(TPL, rel), encoding='utf-8').read()

def write(rel, s):
    p = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, 'w', encoding='utf-8').write(s)
    hits = audit(s)
    if hits:
        print('WARN', rel, 'banned terms:', hits)

# ---------------------------------------------------------------- shell pieces
LOGO = ('<a href="/" data-hostpill class="flex items-center text-ink border-[1.5px] border-ink/30 rounded-full px-3.5 py-1" aria-label="Thai Villas">'
        '<span class="thb-logo-text font-display text-[19px] tracking-tight ml-2.5 whitespace-nowrap"><span class="italic">Thai</span>&nbsp;<span class="font-semibold tracking-[0.09em]">VILLAS</span></span></a>')

CHEV = '<svg class="w-3 h-3 opacity-60 mega-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 9l6 6 6-6"/></svg>'
HEART = '<svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>'
ARROW = '<svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14"/><path d="M13 6l6 6-6 6"/></svg>'

NAV_LINKS = [('/property-rental/?period=daily', 'Daily rentals'), ('/monthly-rental/', 'Monthly & long stay'),
             ('/vip/', 'VIP'), ('/about/', 'About'), ('/contacts/', 'Contacts')]

def nav():
    desk = ''.join('        <a href="%s" class="nav-link">%s</a>\n' % l for l in NAV_LINKS)
    mob = ''.join('      <a href="%s" class="py-3 border-b border-line">%s</a>\n' % l for l in NAV_LINKS)
    return f'''<style id="thv-nav-fix">@media(max-width:639px){{#navbar a.mobile-menu-link{{display:none!important}}}}</style>
<nav id="navbar" class="fixed top-0 left-0 right-0 z-50 transition-all duration-300 bg-off/80 backdrop-blur-md border-b border-line" style="position:fixed;top:0;left:0;right:0;z-index:50;background:rgba(250,250,247,.88);-webkit-backdrop-filter:blur(12px);backdrop-filter:blur(12px);border-bottom:1px solid #e6e3dc">
  <div class="max-w-[1400px] mx-auto px-6 lg:px-10">
    <div class="flex items-center justify-between h-[72px]">
      {LOGO}

      <div class="hidden lg:flex items-center gap-9">
        <div class="mega-trigger">
          <a href="/property-rental/" class="nav-link flex items-center gap-1">Villas {CHEV}</a>
        </div>
{desk}      </div>

      <div class="flex items-center gap-2">
        <a href="/saved/" data-fav-link aria-label="Saved villas" class="w-10 h-10 flex items-center justify-center rounded-full hover:bg-paper transition">{HEART}<span data-fav-badge>0</span></a>
        <a href="/property-rental/" class="btn-primary mobile-menu-link hidden sm:inline-flex items-center gap-2"> Browse villas {ARROW} </a>
        <button id="mobileMenuBtn" aria-label="Menu" aria-expanded="false" class="lg:hidden w-10 h-10 flex items-center justify-center rounded-full hover:bg-paper transition">
          <svg id="burgerIcon" class="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="4" y1="7" x2="20" y2="7"/><line x1="4" y1="12" x2="20" y2="12"/><line x1="4" y1="17" x2="20" y2="17"/></svg>
          <svg id="closeIcon" class="w-6 h-6 hidden" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="6" y1="6" x2="18" y2="18"/><line x1="18" y1="6" x2="6" y2="18"/></svg>
        </button>
      </div>
    </div>
  </div>
  <div id="mobileMenu" class="hidden lg:hidden bg-off border-t border-line px-6 py-6">
    <div class="flex flex-col gap-1 text-[16px] font-medium">
      <a href="/saved/" class="thb-saved-item py-3 border-b border-line" style="display:flex;align-items:center;justify-content:space-between;color:#e11d48">Saved villas <span data-fav-count style="display:none;background:#e11d48;color:#fff;border-radius:999px;min-width:20px;height:20px;line-height:20px;text-align:center;font-size:11.5px;font-weight:700;padding:0 6px"></span></a>
      <a href="/property-rental/" class="py-3 border-b border-line">All villas</a>
      <a href="/villas/phuket/" class="py-3 border-b border-line">Phuket</a>
{mob}      <a href="{wa()}" class="btn-primary text-center mt-5" rel="noopener">WhatsApp us</a>
    </div>
  </div>
</nav>'''

def mega():
    def col(title, items, w=140):
        rows = ''.join('              <a href="%s" class="mega-item"%s>%s%s</a>\n' % (
            h, ' style="font-weight:600"' if bold else '', t,
            '' if c is None else ' <span class="mega-count">%d</span>' % c) for h, t, c, bold in items)
        return (f'    <div style="width:{w}px;flex-shrink:0;padding-right:28px">\n      <p class="mega-col-title">{title}</p>\n'
                f'{rows}              </div>\n    <div class="mega-divider" style="margin-right:28px"></div>\n')
    n = len(VILLAS)
    rent = [('/property-rental/?period=daily', 'Daily', count(pred=lambda v: v.get('daily')), False),
            ('/property-rental/?period=monthly', 'Monthly', count(pred=lambda v: v.get('monthly')), False),
            ('/monthly-rental/', 'Long stay guide &rarr;', None, True),
            ('/property-rental/', 'All villas', n, False)]
    phk = [(area_url('phuket', a['slug']), a['name'], count('phuket', a['slug']), False) for a in PHUKET['areas'][:9]]
    phk.append((area_url('phuket'), 'All Phuket &rarr;', count('phuket'), True))
    other = [(area_url(d['slug']), d['name'], count(d['slug']), False) for d in AREAS if d['slug'] != 'phuket']
    beds = [('/property-rental/?beds=%d' % b, '%s bedroom%s' % ('5+' if b == 5 else b, '' if b == 1 else 's'),
             count(pred=lambda v, b=b: v['bedrooms'] >= 5 if b == 5 else v['bedrooms'] == b), False) for b in range(1, 6)]
    vip = [('/vip/%s/' % c['slug'], c['name'].split(' &')[0].replace(' rental', ''), None, False) for c in VIP]
    vip.append(('/vip/', 'All VIP &rarr;', None, True))
    return ('<div id="villasPanel">\n  <div class="mega-inner">\n' + col('Rental period', rent, 150) + col('Phuket beaches', phk, 170)
            + col('Thailand', other, 150) + col('Bedrooms', beds, 140) + col('VIP', vip, 170)
            + '    <div style="flex:1"></div>\n  </div>\n</div>')

def footer():
    dest = ''.join('          <li><a href="%s">%s<span class="thb-ft-c">%d</span></a></li>\n' % (area_url(d['slug']), d['name'], count(d['slug']))
                   for d in AREAS[:6])
    phk = ''.join('          <li><a href="%s">%s</a></li>\n' % (area_url('phuket', a['slug']), a['name']) for a in PHUKET['areas'][:7])
    return f'''<style id="thv-ft5">@media(min-width:981px){{.thb-ft .thb-ft-grid{{grid-template-columns:1.5fr 1fr 1fr 1fr 1.2fr}}}}</style>
<footer class="thb-ft">
  <div class="thb-ft-in">
    <div class="thb-ft-grid">
      <div class="thb-ft-brand">
        <p class="thb-ft-name">{BRAND}</p>
        <p class="thb-ft-lead">Pool villas in Phuket and across Thailand — daily and monthly rentals, booked direct with a real person on WhatsApp. Plus VIP: yachts, helicopters, supercars.</p>
        <div class="thb-ft-soc">
          <a href="{WA}" rel="noopener">WhatsApp</a>
          <a href="mailto:{EMAIL}">Email</a>
        </div>
      </div>
      <div>
        <h4>Destinations</h4>
        <ul>
          <li><a href="/property-rental/">All villas<span class="thb-ft-c">{len(VILLAS)}</span></a></li>
{dest}          <li><a href="/villas/">All destinations</a></li>
        </ul>
      </div>
      <div>
        <h4>Phuket beaches</h4>
        <ul>
{phk}          <li><a href="/villas/phuket/">All Phuket</a></li>
        </ul>
      </div>
      <div>
        <h4>Rent &amp; VIP</h4>
        <ul>
          <li><a href="/property-rental/?period=daily">Daily rentals</a></li>
          <li><a href="/monthly-rental/">Monthly &amp; long stay</a></li>
          <li><a href="/vip/yachts/">Yacht charter</a></li>
          <li><a href="/vip/helicopters/">Helicopters</a></li>
          <li><a href="/vip/supercars/">Supercars</a></li>
          <li><a href="/vip/superbikes/">Superbikes</a></li>
          <li><a href="/vip/">All VIP services</a></li>
        </ul>
      </div>
      <div>
        <h4>Get in touch</h4>
        <dl class="thb-ft-ct">
          <dt>WhatsApp</dt>
          <dd><a href="{WA}" rel="noopener">{PHONE}</a></dd>
          <dt>Email</dt>
          <dd><a href="mailto:{EMAIL}">{EMAIL}</a></dd>
          <dt>Office</dt>
          <dd>Phuket, Thailand</dd>
          <dt>Hours</dt>
          <dd>Every day 9:00–21:00 (GMT+7)<br>Guest support 24/7</dd>
        </dl>
      </div>
    </div>
    <div class="thb-ft-bar">
      <span>© 2026 {BRAND} · Villa rentals in Thailand</span>
      <nav>
        <a href="/property-rental/">All villas</a>
        <a href="/about/">About</a>
        <a href="/contacts/">Contacts</a>
        <a href="/terms/">Terms</a>
        <a href="/privacy/">Privacy</a>
      </nav>
    </div>
  </div>
</footer>'''

def wapill():
    return (f'<div id="thbWaPill">\n  <span class="ava" aria-hidden="true"></span>\n  <p>Need help choosing? Tell us your dates and what matters — we\'ll suggest the right villa.</p>\n'
            f'  <a class="wa-go" href="{wa()}" rel="noopener" aria-label="Chat on WhatsApp">WhatsApp</a>\n</div>')

# ---------------------------------------------------------------- transforms
def _balanced(s, start_pat, tag='div'):
    """Return (i, j) span of the element starting at regex start_pat, balancing <tag>."""
    m = re.search(start_pat, s)
    if not m:
        return None
    i = m.start(); depth = 0
    for t in re.finditer(r'<(/?)%s\b[^>]*>' % tag, s[i:]):
        depth += -1 if t.group(1) else 1
        if depth == 0:
            return i, i + t.end()
    return None

def replace_el(s, start_pat, new, tag='div'):
    sp = _balanced(s, start_pat, tag)
    return s if not sp else s[:sp[0]] + new + s[sp[1]:]

def remove_el(s, start_pat, tag='div'):
    return replace_el(s, start_pat, '', tag)

def org_ld():
    return json.dumps({"@context": "https://schema.org", "@type": "Organization", "name": BRAND,
                       "telephone": "+" + WA_NUM, "email": EMAIL,
                       "address": {"@type": "PostalAddress", "addressLocality": "Phuket", "addressCountry": "TH"},
                       "areaServed": [d['name'] for d in AREAS]}, ensure_ascii=False)

def clean_head(s, title, desc, jsonld=None, image='/images/hero.jpg'):
    head_end = s.index('</head>')
    h, body = s[:head_end], s[head_end:]
    h = re.sub(r'<!-- Google tag.*?</script>\s*<script>.*?</script>\s*', '', h, flags=re.S)
    h = re.sub(r'<script[^>]*googletagmanager[^>]*></script>\s*', '', h)
    h = re.sub(r'<script>\s*window\.dataLayer.*?</script>\s*', '', h, flags=re.S)
    h = re.sub(r'<meta name="(msvalidate\.01|google-site-verification|yandex-verification)"[^>]*>\s*', '', h)
    h = re.sub(r'<link rel="(canonical|alternate|preconnect)"[^>]*>\s*', '', h)
    h = re.sub(r'<link rel="preload" as="image"[^>]*>\s*', '', h)
    h = re.sub(r'<meta property="og:[^"]*"[^>]*>\s*', '', h)
    h = re.sub(r'<meta name="twitter:[^"]*"[^>]*>\s*', '', h)
    h = re.sub(r'<script type="application/ld\+json">.*?</script>\s*', '', h, flags=re.S)
    h = re.sub(r'<link rel="(icon|apple-touch-icon|manifest)"[^>]*>\s*', '', h)
    h = re.sub(r'<title>.*?</title>', '<title>%s</title>' % esc(title), h, flags=re.S)
    h = re.sub(r'<meta name="description"[^>]*>', '<meta name="description" content="%s">' % esc(desc), h)
    lds = [org_ld()] + ([jsonld] if isinstance(jsonld, str) else list(jsonld or []))
    add = ('<meta name="robots" content="noindex">\n<link rel="icon" type="image/svg+xml" href="/favicon.svg">\n'
           '<meta property="og:title" content="%s">\n<meta property="og:description" content="%s">\n'
           '<meta property="og:type" content="website">\n<meta property="og:site_name" content="%s">\n<meta property="og:image" content="%s">\n'
           % (esc(title), esc(desc), BRAND, image)
           + ''.join('<script type="application/ld+json">%s</script>\n' % (l if isinstance(l, str) else json.dumps(l, ensure_ascii=False)) for l in lds))
    return h + add + body

def rebrand(s, title, desc, jsonld=None, image='/images/hero.jpg'):
    """Swap the reference site's shell (head tags, nav, mega-menu, footer, WhatsApp pill) for Thai Villas."""
    s = clean_head(s, title, desc, jsonld, image)
    s = replace_el(s, r'<nav id="navbar"', nav(), 'nav')
    s = replace_el(s, r'<div id="villasPanel">', mega())
    s = replace_el(s, r'<footer class="thb-ft"', footer(), 'footer')
    s = replace_el(s, r'<div id="thbWaPill">', wapill())
    s = re.sub(r'<!-- thb-guides:begin -->.*?<!-- thb-guides:end -->', '', s, flags=re.S)
    # mega-menu slideshow in the reference pages: point it at Thai photos
    s = re.sub(r'var slides = \[.*?\];', '''var slides = [
    { img: '/images/beaches/kata.jpg', title: 'Sea Views<br>& Sunsets', desc: 'Kata — laid-back bay on Phuket\\'s west coast', btn: 'Explore Kata' },
    { img: '/images/beaches/bang-tao.jpg', title: 'Beach Clubs<br>& Pool Villas', desc: 'Bang Tao — the villa capital of Phuket', btn: 'Explore Bang Tao' },
    { img: '/images/vip/yacht.jpg', title: 'Yachts<br>& Islands', desc: 'Charter a yacht to Phang Nga Bay', btn: 'VIP services' }
  ];''', s, flags=re.S)
    s = s.replace('wa.me/6285746499697', 'wa.me/' + WA_NUM).replace('+62 857 4649 9697', PHONE)
    s = s.replace('hello@thehostbali.com', EMAIL).replace('tel:+6285746499697', 'tel:+' + WA_NUM)
    s = re.sub(r'<script[^>]*src="/thb-(ru|it|lang|sale|sale-map|bot|consent|currency|cards)\.js[^"]*"[^>]*></script>\s*', '', s)
    return s

BANNED = re.compile(r'bali|thehost|the host|sanur|canggu|umalas|ungasan|seminyak|uluwatu|jimbaran|pererenan|berawa|'
                    r'6285746499697|mitra vila|nusantara|gianyar|indonesia|\bWITA\b|\bIDR\b|rupiah|guesty|hostex|'
                    r'ubud|kuta\b|legian|nusa dua|denpasar|ngurah|tabanan|villa management|property management|villas for sale|for sale|G-PF1FJQN7ME|public-objects|villa/assets|'
                    r'airbnb\.com/rooms|booking\.com/hotel', re.I)

def audit(s):
    return sorted(set(m.group(0).lower() for m in BANNED.finditer(s)))

# ---------------------------------------------------------------- villa cards (same markup as the reference site)
AMEN = [('pool', 'pool'), ('wi-fi', 'wifi'), ('wifi', 'wifi'), ('kitchen', 'kitchen'), ('air conditioning', 'ac'),
        ('parking', 'parking'), ('workspace', 'work'), ('garden', 'garden'), ('beach', 'beach'), ('sea view', 'view'),
        ('washing', 'washer'), ('chef', 'chef')]
SVG_PIN = ('<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">'
           '<path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>')
SVG_FAV = ('<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 '
           '7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" stroke-linecap="round" stroke-linejoin="round"/></svg>')

def where(v):
    return ', '.join(x for x in (v.get('subArea'), v['area']) if x)

def meta(v):
    return '%d bed · %g bath · %d guests' % (v['bedrooms'], v['bathrooms'], v['guests'])

def tokens(v):
    low = ' | '.join(v['amenities']).lower()
    out = {tok for w, tok in AMEN if w in low} | set(v.get('filterTags', []))
    if v['bedrooms'] >= 3:
        out.add('family')
    return ' '.join(sorted(out))

def fav(v):
    img = v.get('cardImage') or v['images'][0]
    return ('<button type="button" class="thb-fav" data-fav-btn aria-pressed="false" aria-label="Save this villa" '
            'data-u="%s" data-t="%s" data-i="%s" data-m="%s" data-a="%s">%s</button>'
            % (v['url'], esc(v['name']), img, meta(v), esc(where(v)), SVG_FAV))

SAMPLE_BADGE = '<span class="thb-sample" style="position:absolute;left:10px;bottom:10px;background:rgba(10,10,10,.72);color:#fff;font-size:10.5px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;padding:4px 9px;border-radius:999px">Sample listing</span>'

def prop_card(v):
    """Catalog grid card (.prop-card). data-* attributes drive thb-filters.js."""
    img = v.get('cardImage') or v['images'][0]
    period = ' '.join(p for p, ok in (('daily', v.get('daily')), ('monthly', v.get('monthly'))) if ok)
    return ('<div class="prop-card" data-location="%s" data-sub="%s" data-beds="%d" data-guests="%d" data-type="villa" '
            'data-period="%s" data-amenities="%s" onclick="window.location=\'%s\'">\n'
            '          <div class="img-wrap">\n'
            '            <img src="%s" alt="%s — villa in %s" loading="lazy" decoding="async" width="1200" height="800">\n'
            '            <span class="badge">%s</span>\n            %s\n            %s\n'
            '          </div>\n          <div style="padding:14px">\n'
            '            <p style="font-family:\'Lora\',Georgia,serif;font-size:16px;font-weight:600;margin-bottom:6px;line-height:1.2">%s</p>\n'
            '            <div class="prop-meta" style="margin-bottom:10px"><span>%d bed</span><span>%g bath</span><span>%d guests</span></div>\n'
            '            <div style="display:flex;align-items:center;justify-content:space-between">'
            '<div><span style="font-family:\'Lora\',Georgia,serif;font-size:19px;font-weight:700">On request</span></div></div>\n'
            '          </div>\n        </div>'
            % (v['areaSlug'], v.get('subAreaSlug') or '', v['bedrooms'], v['guests'], period, tokens(v), v['url'],
               img, esc(v['name']), esc(where(v)), esc(v.get('subArea') or v['area']), fav(v),
               SAMPLE_BADGE if v.get('sample') else '', esc(v['name']), v['bedrooms'], v['bathrooms'], v['guests']))

def acard(v):
    """Horizontal-rail card (.thb-acard) used on the home page."""
    img = v.get('cardImage') or v['images'][0]
    return ('<div class="thb-acw"><a class="thb-acard" href="%s">\n'
            '      <img src="%s" alt="%s" loading="lazy" decoding="async" width="600" height="450">\n'
            '      <div class="in">\n        <p class="t">%s</p>\n        <p class="a">%s %s</p>\n'
            '        <p class="m">%s</p>\n        <p class="p">On request <span>&middot; fast reply on WhatsApp</span></p>\n'
            '      </div>\n    </a>%s</div>'
            % (v['url'], img, esc(v['name']), esc(v['name']), SVG_PIN, esc(where(v)), meta(v).replace(' · ', ' &middot; '), fav(v)))
