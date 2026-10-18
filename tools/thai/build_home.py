"""Home page, 404, /saved/ and favicon for Thai Villas.

Base layout: the reference home (index.html), 404.html and saved/index.html. The shell is swapped by
thv.rebrand(); everything between the HERO and FOOTER markers of the home page is rebuilt here.

    python3 -I tools/thai/build_home.py      (from the site root)
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from thv import *

ARR = '<svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14"/><path d="M13 6l6 6-6 6"/></svg>'
ARR_GRP = '<svg class="w-4 h-4 opacity-70 group-hover:translate-x-1 transition-transform" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14"/><path d="M13 6l6 6-6 6"/></svg>'
CHEV_R = '<svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 6l6 6-6 6"/></svg>'
WA_SVG = ('<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 2.2C6.6 2.2 2.2 6.6 2.2 12c0 1.7.4 3.4 1.3 4.9L2 22l5.3-1.4c1.4.8 3 1.2 4.7 1.2 5.4 0 9.8-4.4 9.8-9.8S17.4 2.2 12 2.2zm5.5 12.2c-.3-.2-1.9-.9-2.2-1-.3-.1-.5-.2-.7.1-.2.3-.8 1-1 1.2-.2.2-.4.2-.7.1-.3-.2-1.3-.5-2.5-1.6-.9-.8-1.5-1.8-1.7-2.1-.2-.3 0-.5.1-.6.1-.2.5-.6.6-.8.2-.2.2-.4.3-.6.1-.2 0-.4 0-.5 0-.2-.7-1.7-.9-2.3-.2-.6-.5-.5-.7-.5h-.6c-.2 0-.6.1-.9.4-.3.4-1.1 1.1-1.1 2.6s1.1 3 1.3 3.2c.1.2 2.1 3.3 5.2 4.5 3.1 1.2 3.5 1 4.1.9.6-.1 2-.8 2.2-1.6.3-.8.3-1.5.2-1.6-.1-.2-.3-.2-.6-.4z"/></svg>')

def plural(n, word='villa'):
    return '%d %s%s' % (n, word, '' if n == 1 else 's')

N_PHK = count('phuket')
N_BEACH = len(PHUKET['areas'])
N_DEST = len(AREAS)
OTHERS = [d for d in AREAS if d['slug'] != 'phuket']

# ------------------------------------------------------------------ hero
SLIDES = [('/images/hero.jpg', 'Private pool villa in Phuket'),
          ('/images/beaches/kata.jpg', 'Kata Beach on Phuket\'s west coast'),
          ('/images/beaches/bang-tao.jpg', 'Bang Tao Beach, Phuket'),
          ('/images/villas/ext-4.jpg', 'Pool villa terrace in Thailand')]

def hero():
    sl = []
    for i, (src, alt) in enumerate(SLIDES):
        if i == 0:
            img = '<img src="%s" alt="%s" width="1200" height="800" loading="eager" fetchpriority="high" decoding="async">' % (src, esc(alt))
        else:
            img = '<img data-src="%s" alt="%s" width="1200" height="800" loading="lazy" decoding="async">' % (src, esc(alt))
        sl.append('<picture class="hs-slide%s" data-i="%d">%s</picture>' % (' is-on' if i == 0 else '', i, img))
    slides = '\n      '.join(sl)
    cards = [
        ('/property-rental/?period=daily', True, 'Stay', 'Daily rentals', 'Private pool villas for a few nights or a few weeks · Phuket &amp; across Thailand'),
        ('/monthly-rental/', False, 'Live', 'Monthly &amp; long stay', 'A month or longer in Phuket, Koh Samui, Pattaya, Bangkok or Chiang Mai'),
        ('/vip/', False, 'VIP', 'Yachts, helicopters, supercars', 'Charters, transfers and rentals arranged alongside your villa'),
    ]
    ch = []
    for href, dark, kick, title, desc in cards:
        if dark:
            ch.append(f'''            <a href="{href}" class="group rounded-[20px] bg-ink text-white p-6 flex flex-col justify-between min-h-[170px] transition hover:shadow-[0_12px_32px_rgba(0,0,0,0.35)]">
              <div class="flex items-center justify-between mb-6"><span class="text-[11px] font-semibold tracking-[0.18em] uppercase text-white/55">{kick}</span>{ARR_GRP}</div>
              <div><p class="font-display text-[24px] leading-tight mb-1.5">{title}</p>
              <p class="text-white/65 text-[13px] leading-relaxed">{desc}</p></div>
            </a>''')
        else:
            ch.append(f'''            <a href="{href}" class="group rounded-[20px] bg-paper border border-line p-6 flex flex-col justify-between min-h-[170px] transition hover:border-ink">
              <div class="flex items-center justify-between mb-6"><span class="text-[11px] font-semibold tracking-[0.18em] uppercase text-ink/45">{kick}</span>{ARR_GRP}</div>
              <div><p class="font-display text-[24px] leading-tight mb-1.5">{title}</p>
              <p class="text-ink/60 text-[13px] leading-relaxed">{desc}</p></div>
            </a>''')
    return f'''<!-- =============== HERO =============== -->
<section id="thbHero" class="relative bg-off">
  <div class="absolute inset-0 w-full overflow-hidden">
    <div class="hs-show" aria-label="Villas and beaches in Phuket">{slides}</div>
    <div class="absolute inset-0" style="background: linear-gradient(180deg, rgba(0,0,0,0.34) 0%, rgba(0,0,0,0.10) 20%, rgba(0,0,0,0) 58%, rgba(10,10,10,0.55) 100%);"></div>
    <div class="absolute inset-0" style="background: radial-gradient(ellipse at 50% 46%, rgba(0,0,0,0.30) 0%, rgba(0,0,0,0.16) 48%, rgba(0,0,0,0) 78%);"></div>
  </div>
  <div class="thb-hero-txt relative z-10 h-[58vh] min-h-[470px] max-h-[620px] pt-[92px] pb-6 px-6 lg:px-10 flex items-center">
      <div class="max-w-[1400px] mx-auto w-full text-center">
        <h1 class="hero-title font-display text-white text-[44px] sm:text-[60px] lg:text-[84px] leading-[0.92] tracking-tightest font-normal mb-5">
          Your perfect villa in Phuket,<br> <span class="italic font-light">booked direct.</span>
        </h1>
        <p class="hero-sub text-white/90 text-[15px] lg:text-[17px] max-w-xl mx-auto">
          Private pool villas on Phuket's west-coast beaches and across Thailand — by the night or by the month. Book straight with us on WhatsApp, with no booking-site fee on top.
        </p>
      </div>
    </div>

  <!-- Directions panel -->
      <div class="thb-hero-panel relative z-20 max-w-[1080px] mx-auto px-4 lg:px-10 pb-12 lg:pb-16">
        <div class="thb-glass-card rounded-[28px] shadow-[0_30px_80px_rgba(0,0,0,0.22)] p-3 sm:p-4">
          <div class="grid sm:grid-cols-3 gap-3">
{chr(10).join(ch)}
          </div>
        </div>
      </div>
</section>

'''

# ------------------------------------------------------------------ locations
LOC_CSS = '''<style id="thb-loc-css">
.thb-loc{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}
@media(min-width:768px){.thb-loc{grid-template-columns:repeat(3,minmax(0,1fr));gap:16px}}
@media(min-width:1024px){.thb-loc{grid-template-columns:repeat(4,minmax(0,1fr))}}
.thb-lc{position:relative;display:block;border-radius:22px;overflow:hidden;aspect-ratio:4/3;background:#1b2a22;color:#fff;text-decoration:none}
.thb-lc img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;transition:transform .7s}
.thb-lc:hover img{transform:scale(1.05)}
.thb-lc::after{content:'';position:absolute;inset:0;background:linear-gradient(0deg,rgba(0,0,0,.72) 0%,rgba(0,0,0,.12) 55%,rgba(0,0,0,0) 100%)}
.thb-lc .in{position:absolute;left:14px;right:14px;bottom:12px;z-index:1}
.thb-lc .n{font-family:'Lora',Georgia,serif;font-size:clamp(17px,2vw,22px);font-weight:600;line-height:1.15;margin:0 0 3px}
.thb-lc .c{font-size:12px;color:rgba(255,255,255,.82);margin:0}
.thb-lc .c.soon{display:inline-block;background:rgba(255,255,255,.18);border:1px solid rgba(255,255,255,.35);border-radius:999px;padding:1px 9px;font-weight:600}
.thb-lc.big{aspect-ratio:auto;min-height:240px;grid-column:1/-1}
.thb-lc.big .in{left:22px;bottom:20px;right:22px}
.thb-lc.big .n{font-size:clamp(30px,4vw,44px);margin-bottom:6px}
.thb-lc.big .d{font-size:14px;color:rgba(255,255,255,.86);max-width:520px;margin:0 0 8px}
@media(min-width:1024px){.thb-lc.big{grid-column:span 2;grid-row:span 2;min-height:0}}
.thb-loc-h{font-family:'Lora',Georgia,serif;font-size:clamp(21px,2.6vw,28px);font-weight:600;margin:40px 0 14px}
</style>'''

def loc_card(href, img, name, n, extra=''):
    c = '<p class="c">%s</p>' % plural(n) if n else '<p class="c soon">Coming soon</p>'
    return ('<a class="thb-lc" href="%s"><img src="%s" alt="%s" loading="lazy" decoding="async" width="800" height="600">'
            '<div class="in"><p class="n">%s</p>%s</div></a>' % (href, img, esc(name), name, c))

def rail(title, href, villas):
    cards = '\n    '.join(acard(v) for v in villas)
    return f'''  <div class="max-w-[1400px] mx-auto px-6 lg:px-10">
    <a href="{href}" class="thb-arh"><h3>{title} {CHEV_R}</h3><span class="cnt">{plural(len(villas))}</span></a>
  </div>
  <div class="max-w-[1400px] mx-auto"><div class="thb-arow">
    {cards}
  </div></div>
  <div style="height:26px"></div>
'''

def locations():
    big = (f'<a class="thb-lc big" href="{area_url("phuket")}"><img src="{PHUKET["image"]}" alt="Phuket" loading="lazy" decoding="async" width="1200" height="800">'
           f'<div class="in"><p class="n">Phuket</p><p class="d">{esc(PHUKET["short"])}</p><p class="c">{plural(N_PHK)} · {N_BEACH} beach areas</p></div></a>')
    beaches = [loc_card(area_url('phuket', a['slug']), a['image'], a['name'], count('phuket', a['slug'])) for a in PHUKET['areas']]
    others = [loc_card(area_url(d['slug']), d['image'], d['name'], count(d['slug'])) for d in OTHERS]
    phk_villas = [v for v in VILLAS if v['areaSlug'] == 'phuket']
    rails = rail('Popular in Phuket', area_url('phuket'), phk_villas)
    for a in PHUKET['areas']:
        vs = [v for v in phk_villas if v.get('subAreaSlug') == a['slug']]
        if len(vs) >= 2:
            rails += rail('Villas in %s' % a['name'], area_url('phuket', a['slug']), vs)
    beyond = [v for v in VILLAS if v['areaSlug'] != 'phuket']
    if beyond:
        rails += rail('Beyond Phuket', '/villas/', beyond)
    return f'''<!-- =============== LOCATIONS =============== -->
<section id="locations" class="bg-off py-16 lg:py-20 border-t border-line">
  <div class="max-w-[1400px] mx-auto px-6 lg:px-10">
    <div class="flex items-end justify-between mb-10 flex-wrap gap-4">
      <div>
        <p class="kicker mb-3">Explore Phuket by beach</p>
        <h2 class="font-display text-[40px] lg:text-[56px] leading-[1] tracking-tightest">Where would you<br><span class="italic">like to stay?</span></h2>
      </div>
      <a href="/property-rental/" class="btn-outline inline-flex items-center gap-2">All villas
        {ARR}
      </a>
    </div>
    <div class="thb-loc">
      {big}
      {chr(10).join('      ' + b for b in beaches).lstrip()}
    </div>
    <p class="thb-loc-h">More of Thailand</p>
    <div class="thb-loc">
      {chr(10).join('      ' + b for b in others).lstrip()}
    </div>
  </div>
  <div style="height:48px" id="matches"></div>
  <div class="max-w-[1400px] mx-auto px-6 lg:px-10"><p class="text-ink/50 text-[13px]" style="margin:-20px 0 22px">Villas shown are sample listings while the catalogue is being built — prices on request on WhatsApp.</p></div>
{rails}</section>

'''

# ------------------------------------------------------------------ vibe
VIBES = [('romantic', '/images/romantic.jpg', 'Romantic Escape', 'Private pool villas for two, perfect for couples.',
          '<path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>'),
         ('surf', '/images/surf.jpg', 'Beach &amp; Friends', 'Villas close to the sand, surf and sunsets.',
          '<path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7z"/><circle cx="12" cy="12" r="3"/>'),
         ('family', '/images/family.jpg', 'Family Retreat', 'Spacious villas for the whole family.',
          '<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/>'),
         ('work', '/images/work.jpg', 'Work &amp; Live', 'Fast Wi-Fi, a proper desk and a calm pace.',
          '<rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/>')]

def vibe():
    cards = ''.join(f'''      <a href="/property-rental/?vibe={k}" class="group card-hover relative rounded-3xl overflow-hidden aspect-[3/4] bg-ink block">
        <img src="{img}" alt="{t}" class="absolute inset-0 w-full h-full object-cover group-hover:scale-105 transition-transform duration-700" loading="lazy" decoding="async" width="1080" height="1350">
        <div class="absolute inset-0 bg-gradient-to-t from-black/80 via-black/10 to-transparent"></div>
        <div class="absolute top-5 right-5 w-10 h-10 bg-white/90 rounded-full flex items-center justify-center">
          <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">{ic}</svg>
        </div>
        <div class="absolute bottom-6 left-6 right-6 text-white">
          <h3 class="font-display text-[26px] leading-tight mb-1">{t}</h3>
          <p class="text-sm text-white/80">{d}</p>
        </div>
      </a>
''' for k, img, t, d, ic in VIBES)
    return f'''<!-- =============== VIBE SELECTOR =============== -->
<section class="bg-off py-24 border-t border-line">
  <div class="max-w-[1400px] mx-auto px-6 lg:px-10">
    <div class="flex items-end justify-between mb-12 flex-wrap gap-4">
      <div>
        <p class="kicker mb-3">Choose your vibe</p>
        <h2 class="font-display text-[44px] lg:text-[60px] leading-[1] tracking-tightest max-w-2xl">What kind of stay<br>are you looking for?</h2>
      </div>
      <p class="text-ink/60 max-w-xs text-[15px]">Pick a style and we'll show the villas that fit it.</p>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
{cards}    </div>
  </div>
</section>

'''

# ------------------------------------------------------------------ long-term + VIP
def longterm():
    return f'''<!-- =============== LONG-TERM + VIP =============== -->
<section id="longterm" class="bg-off py-16 border-t border-line">
  <div class="max-w-[1400px] mx-auto px-6 lg:px-10 grid grid-cols-1 lg:grid-cols-2 gap-6">
    <!-- Long-term — BLACK card -->
    <div class="bg-ink text-white rounded-[28px] p-10 lg:p-12 flex flex-col justify-between min-h-[420px] relative overflow-hidden">
      <div class="relative z-10">
        <p class="kicker !text-white/60 mb-4">Long-term living</p>
        <h3 class="font-display text-[40px] lg:text-[48px] leading-[0.95] tracking-tightest mb-5">Looking for<br><span class="italic">long-term</span> rentals<br>in Phuket?</h3>
        <p class="text-white/75 mb-8 max-w-sm">Villas for a month or longer — for remote workers, families and anyone spending the season in Thailand.</p>
        <ul class="space-y-2 mb-10 text-sm text-white/85">
          <li class="flex items-center gap-2">— Monthly stays, extend as long as you like</li>
          <li class="flex items-center gap-2">— Phuket, Koh Samui, Pattaya, Bangkok &amp; Chiang Mai</li>
          <li class="flex items-center gap-2">— Monthly price and what's included, in writing</li>
        </ul>
        <a href="/monthly-rental/" class="bg-white text-ink hover:bg-paper rounded-full px-6 py-3.5 font-semibold text-sm transition inline-block">Explore monthly rentals →</a>
      </div>
      <div class="absolute right-0 top-0 bottom-0 w-2/5 opacity-80 hidden lg:block">
        <img src="/images/villas/living-1.jpg" class="w-full h-full object-cover" alt="" loading="lazy" decoding="async">
        <div class="absolute inset-0 bg-gradient-to-l from-transparent to-ink"></div>
      </div>
    </div>

    <!-- VIP — PAPER card -->
    <div id="vip" class="bg-paper rounded-[28px] p-10 lg:p-12 flex flex-col justify-between min-h-[420px] relative overflow-hidden">
      <div class="relative z-10">
        <p class="kicker mb-4">VIP services</p>
        <h3 class="font-display text-[40px] lg:text-[48px] leading-[0.95] tracking-tightest mb-5">More than<br>a <span class="italic">villa.</span></h3>
        <p class="text-ink/70 mb-8 max-w-sm">Add the extras to your stay and arrange them in the same WhatsApp thread as your villa.</p>
        <ul class="space-y-2 mb-10 text-sm text-ink/85">
          <li>— Yacht &amp; catamaran charters</li>
          <li>— Helicopter transfers &amp; sightseeing</li>
          <li>— Supercar rental</li>
          <li>— Superbike rental &amp; private chef</li>
        </ul>
        <a href="/vip/" class="btn-outline inline-block">Explore VIP services →</a>
      </div>
      <div class="absolute -right-8 top-1/2 -translate-y-1/2 w-56 hidden lg:block">
        <img src="/images/vip/yacht.jpg" class="w-full rounded-2xl shadow-2xl" alt="Yacht charter in Phuket" loading="lazy" decoding="async">
      </div>
    </div>
  </div>
</section>

'''

# ------------------------------------------------------------------ why direct, how it works, about, CTA
def direct():
    items = [('No platform fee', 'Booking sites add their own service fee on top of the rate. Book here and that part simply is not charged.'),
             ('One WhatsApp thread', 'Questions, the booking, check-in details and help during your stay — all with the same people, in one chat.'),
             ('Flexible on dates', 'Early check-in, a late flight, an extra night, a month instead of a week — just ask, no platform in the middle.'),
             ('Daily, monthly &amp; VIP', 'A villa for a week, a home for the season, a yacht for the day — arranged in one place.')]
    cards = ''.join(f'''      <div class="rounded-[20px] border border-line bg-white p-7">
        <h3 class="font-display text-[20px] mb-2">{t}</h3>
        <p class="text-[14px] text-ink/70 leading-relaxed">{d}</p>
      </div>
''' for t, d in items)
    return f'''<!-- =============== WHY BOOK DIRECT =============== -->
<section class="py-20 lg:py-24 border-t border-line" id="book-direct">
  <div class="max-w-[1400px] mx-auto px-6 lg:px-10">
    <p class="kicker mb-3">Booking direct</p>
    <h2 class="font-display text-[40px] lg:text-[56px] leading-[1.02] tracking-tightest mb-4">Why book straight<br><span class="italic">with us.</span></h2>
    <p class="text-ink/70 max-w-[62ch] mb-12">No middleman between you and your villa: you message us, get the price for your dates and book — the simple way.</p>
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
{cards}    </div>
    <div class="mt-10 flex flex-wrap gap-3">
      <a href="{esc(wa("Hi Thai Villas! I would like to check availability for a villa in Phuket."))}" rel="noopener" class="btn-primary inline-flex items-center gap-2">Check dates on WhatsApp</a>
      <a href="{area_url('phuket')}" class="btn-outline inline-flex items-center gap-2">See villas in Phuket</a>
    </div>
  </div>
</section>

'''

def how():
    steps = [('01', 'Browse or message us', 'Look through the villas or just tell us your dates, group size and the beach you like.'),
             ('02', 'Get a shortlist', 'We reply with the villas that fit, their availability and the price for your dates.'),
             ('03', 'Book &amp; relax', 'Confirm on WhatsApp and get your check-in details. We stay reachable throughout your stay.')]
    st = ''.join(f'''        <div class="flex gap-5">
          <span class="font-display text-[56px] text-ink/15 leading-none">{n}</span>
          <div class="pt-3">
            <p class="font-semibold mb-1 text-lg">{t}</p>
            <p class="text-ink/60 text-[15px] max-w-md">{d}</p>
          </div>
        </div>
''' for n, t, d in steps)
    return f'''<!-- =============== HOW IT WORKS =============== -->
<section class="bg-off py-24 border-t border-line">
  <div class="max-w-[1400px] mx-auto px-6 lg:px-10 grid grid-cols-1 lg:grid-cols-2 gap-16">
    <div>
      <p class="kicker mb-3">How it works</p>
      <h2 class="font-display text-[44px] lg:text-[60px] leading-[1] tracking-tightest mb-12">3 easy steps to<br><span class="italic">your perfect stay.</span></h2>

      <div class="space-y-8">
{st}      </div>
    </div>

  </div>
</section>

'''

def about():
    stats = [(str(N_BEACH), 'Phuket beach areas covered'), (str(N_DEST), 'destinations in Thailand'),
             ('24/7', 'WhatsApp support'), ('0%', 'booking-site fee booking direct')]
    st = ''.join('          <div><p class="font-display text-[36px] leading-none mb-1">%s</p><p class="text-ink/50 text-[13px]">%s</p></div>\n' % s for s in stats)
    vals = [('Honest listings', 'Clear descriptions, and sample listings are marked as samples.'),
            ('Clear prices', 'The price for your dates in writing before you pay — nothing added at checkout.'),
            ('A real person', 'One WhatsApp thread from the first question to check-out.'),
            ('Daily or monthly', 'Two simple ways to stay: by the night, or by the month.')]
    vh = ''.join(f'''          <div class="flex gap-4">
            <span class="font-display text-[40px] text-white/15 leading-none">0{i}</span>
            <div class="pt-1"><p class="font-semibold mb-1">{t}</p><p class="text-white/60 text-[14px]">{d}</p></div>
          </div>
''' for i, (t, d) in enumerate(vals, 1))
    return f'''<!-- =============== ABOUT US =============== -->
<section id="about" class="bg-off py-24 border-t border-line">
  <div class="max-w-[1400px] mx-auto px-6 lg:px-10">
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-16 items-start">
      <div>
        <p class="kicker mb-3">Who we are</p>
        <h2 class="font-display text-[44px] lg:text-[60px] leading-[1] tracking-tightest mb-8">Phuket first.<br><span class="italic">The simple way to rent a villa.</span></h2>
        <div class="space-y-5 text-ink/60 text-[15px] max-w-xl">
          <p>{BRAND} is a villa rental service for Phuket and the rest of Thailand. We focus on the island's west-coast beaches — from Mai Khao and Bang Tao in the north down to Kata, Nai Harn and Rawai in the south — plus Koh Samui, Pattaya, Bangkok, Krabi, Koh Phangan, Hua Hin and Chiang Mai.</p>
          <p>You can rent by the night for a holiday or by the month for a longer season. Either way you deal with real people on WhatsApp, get the price for your dates in writing and pay no booking-site fee on top.</p>
          <p>Planning something bigger? We also arrange yacht charters, helicopter transfers, supercars and superbikes, so the whole trip sits in one conversation.</p>
        </div>
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-6 mt-12">
{st}        </div>
      </div>
      <div class="bg-ink text-white rounded-[28px] p-10">
        <p class="kicker !text-white/60 mb-3">What we stand for</p>
        <h3 class="font-display text-[32px] leading-[1.05] tracking-tightest mb-8">Fewer promises.<br><span class="italic">All of them kept.</span></h3>
        <div class="space-y-7">
{vh}        </div>
      </div>
    </div>
  </div>
</section>

'''

def cta():
    return f'''<!-- =============== FINAL CTA =============== -->
<section class="bg-off py-24 border-t border-line">
  <div class="max-w-[1200px] mx-auto px-6 lg:px-10 text-center">
    <p class="kicker mb-5">Ready to find your villa?</p>
    <h2 class="font-display text-[56px] lg:text-[88px] leading-[0.95] tracking-tightest mb-8">Stop searching.<br><span class="italic">Start experiencing.</span></h2>
    <p class="text-ink/60 text-[17px] max-w-xl mx-auto mb-10">Your villa in Phuket is one message away.</p>
    <a href="/property-rental/" class="btn-primary inline-flex items-center gap-2 !px-8 !py-4 !text-base">
      Find my villa now
      <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14"/><path d="M13 6l6 6-6 6"/></svg>
    </a>
  </div>
</section>

'''

def drop_scripts(s, names):
    for n in names:
        s = re.sub(r'<script[^>]*src="/%s[^"]*"[^>]*></script>\s*' % re.escape(n), '', s)
    return s

# ------------------------------------------------------------------ home
def build_home():
    s = read_tpl('index.html')
    title = 'Thai Villas — Private Pool Villas in Phuket & Thailand, Booked Direct'
    desc = ('Private pool villas on Phuket\'s beaches and across Thailand — daily and monthly rentals booked direct on '
            'WhatsApp, no booking-site fee. Plus VIP: yachts, helicopters, supercars.')
    site = {"@context": "https://schema.org", "@type": "WebSite", "name": BRAND}
    s = rebrand(s, title=title, desc=desc, jsonld=[site])
    s = s.replace('<meta name="theme-color" content="#343537">', '<meta name="theme-color" content="#0a0a0a">')
    s = s.replace('</head>', '<link rel="preload" as="image" fetchpriority="high" href="/images/hero.jpg">\n' + LOC_CSS + '\n</head>', 1)
    a = s.index('<!-- =============== HERO =============== -->')
    b = s.index('<!-- =============== FOOTER =============== -->')
    s = s[:a] + hero() + locations() + vibe() + longterm() + direct() + how() + about() + cta() + s[b:]
    s = drop_scripts(s, ['thb-consent.js', 'thb-bot.js'])
    write('index.html', s)

# ------------------------------------------------------------------ 404
def build_404():
    s = read_tpl('404.html')
    s = clean_head(s, 'Page not found — %s' % BRAND, 'This page does not exist. Browse villas in Phuket and Thailand or ask us on WhatsApp.')
    s = s.replace('<meta name="robots" content="noindex, follow">\n', '')
    s = s.replace("image-set(url('/public-objects/hero/slide-05-1200.avif') type('image/avif'),\n    url('/public-objects/hero/slide-05-1200.jpg') type('image/jpeg'))",
                  "url('/images/hero.jpg')")
    s = s.replace('<a class="logo" href="/" aria-label="The Host Bali — home"><i>The</i><b>HOST</b></a>',
                  '<a class="logo" href="/" aria-label="Thai Villas — home"><i>Thai</i><b>VILLAS</b></a>')
    s = s.replace('Everything we run is one tap away', 'Every villa is one tap away')
    s = re.sub(r'href="https://wa\.me/[^"]*"', 'href="%s"' % esc(wa('Hi Thai Villas! I hit a broken link on your site — can you help me find a villa?')), s)
    chips = [('/villas/phuket/', 'Phuket')] + [(area_url('phuket', x), n) for x, n in (('bang-tao', 'Bang Tao'), ('kata', 'Kata'), ('nai-harn', 'Nai Harn'))] \
        + [('/monthly-rental/', 'Monthly rentals'), ('/vip/', 'VIP'), ('/saved/', 'Saved villas'), ('/contacts/', 'Contacts')]
    s = replace_el(s, r'<div class="chips">', '<div class="chips">\n' + ''.join('    <a class="chip" href="%s">%s</a>\n' % c for c in chips) + '  </div>')
    s = s.replace('The Host Bali &middot; villas we run ourselves in Bali', '%s &middot; villa rentals in Thailand' % BRAND)
    s = drop_scripts(s, ['thb-consent.js', 'thb-bot.js'])
    write('404.html', s)

# ------------------------------------------------------------------ saved
def build_saved():
    s = read_tpl('saved/index.html')
    s = clean_head(s, 'Saved villas | %s' % BRAND,
                   'Your shortlist of villas in Phuket and Thailand. Save the ones you like and send the whole list to us on WhatsApp.')
    s = s.replace('<meta name="robots" content="noindex, follow">\n', '')
    s = re.sub(r'<link href="https://fonts\.googleapis\.com[^>]*>', '<link rel="stylesheet" href="/fonts/fonts.css">', s)
    s = s.replace('</style>\n</style>', '</style>')
    hdr = f'''<header class="hd">
  <div class="hd-in">
    <a href="/" data-hostpill class="hostpill" aria-label="Thai Villas"><em>Thai</em>&nbsp;<b>VILLAS</b></a>
    <nav>
      <a href="/property-rental/?period=daily" class="hm">Daily rentals</a>
      <a href="/monthly-rental/" class="hm">Monthly</a>
      <a href="/vip/" class="hm">VIP</a>
      <a href="/about/" class="hm">About</a>
      <a href="/contacts/" class="hm">Contacts</a>
      <a href="/saved/" data-fav-link aria-label="Saved villas" style="width:40px;height:40px;border-radius:50%;flex-shrink:0">
        <svg style="width:20px;height:20px;fill:none;stroke:#0a0a0a;stroke-width:1.8" viewBox="0 0 24 24"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>
        <span data-fav-badge>0</span>
      </a>
      <a class="cta" href="{WA}" rel="noopener">
        {WA_SVG.replace('<svg ', '<svg width="16" height="16" ', 1)}
        WhatsApp
      </a>
    </nav>
  </div>
</header>'''
    s = replace_el(s, r'<header class="hd">', hdr, 'header')
    ft = f'''<footer class="ft">
  <div class="ft-in">
    <span>&copy; <span id="yr">2026</span> {BRAND} &middot; villa rentals in Thailand</span>
    <nav class="ft-nav">
      <a href="/property-rental/">All villas</a>
      <a href="/monthly-rental/">Monthly rentals</a>
      <a href="/vip/">VIP</a>
      <a href="/about/">About</a>
      <a href="/contacts/">Contacts</a>
      <a href="/terms/">Terms</a>
      <a href="/privacy/">Privacy</a>
    </nav>
  </div>
</footer>'''
    s = replace_el(s, r'<footer class="ft">', ft, 'footer')
    s = s.replace("var WA = 'https://wa.me/6285746499697?text=';", "var WA = '%s?text=';" % WA)
    s = s.replace("(v.a ? '<p class=\"a\">'+esc(v.a)+', Bali</p>' : '')", "(v.a ? '<p class=\"a\">'+esc(v.a)+'</p>' : '')")
    s = s.replace("' — https://thehostbali.com' + v.u", "' — ' + location.origin + v.u")
    s = s.replace("'Hi The Host Bali! These are the villas on my shortlist:", "'Hi Thai Villas! These are the villas on my shortlist:")
    s = s.replace('Nothing is sent anywhere', 'Nothing is sent anywhere')
    s = drop_scripts(s, ['thb-consent.js', 'thb-bot.js'])
    write('saved/index.html', s)

# ------------------------------------------------------------------ favicon
FAVICON = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <rect width="64" height="64" rx="14" fill="#0a0a0a"/>
  <text x="32" y="42" text-anchor="middle" font-family="Lora, Georgia, 'Times New Roman', serif" font-size="27" fill="#fafaf7"><tspan font-style="italic">T</tspan><tspan font-weight="700" dx="1">V</tspan></text>
</svg>
'''

def build_favicon():
    write('favicon.svg', FAVICON)

if __name__ == '__main__':
    build_home(); build_404(); build_saved(); build_favicon()
    print('ok: index.html, 404.html, saved/index.html, favicon.svg')
