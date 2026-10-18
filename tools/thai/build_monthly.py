#!/usr/bin/env python3
"""/monthly-rental/ hub + /monthly-rental/{phuket,koh-samui,pattaya,bangkok,chiang-mai}/.

Based on the reference monthly-rental section (tools/monthly/build.py there), but the shell is the
guest-facing home page (no owner/management blocks) and there are no monthly rates yet: every
price is "On request". Run from the site root: python3 -I tools/thai/build_monthly.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from w4_shell import *  # noqa: F401,F403

DEST = ['phuket', 'koh-samui', 'pattaya', 'bangkok', 'chiang-mai']
D = {d['slug']: d for d in AREAS}
monthly = lambda v: v.get('monthly')

# Long-stay notes per destination: general, well-known facts only.
NOTES = {
    'phuket': {
        'title': 'Monthly Villa Rental in Phuket — Long-Stay Pool Villas | Thai Villas',
        'desc': 'Rent a pool villa in Phuket by the month: Rawai, Nai Harn, Bang Tao, Kata and Chalong. How long stays work, deposits, utilities. Rates on request via WhatsApp.',
        'h1': 'Monthly villa rental <i>in Phuket.</i>',
        'lead': 'A month or a whole season on Thailand\'s biggest island: private pool villas near the beaches long-stayers actually choose, rented by the month and arranged with a real person on WhatsApp.',
        'life': ['Phuket is the easiest place in Thailand to live in a villa for a month or more: an international airport, hospitals, supermarkets, gyms, coworking spaces and schools are all on the island, and the west-coast beaches are 20–60 minutes from each other by car.',
                 'Long-stayers tend to settle in the south (Rawai, Nai Harn, Chalong) for a calmer, residential feel, or on the north-west coast (Bang Tao) for beach clubs and cafés. Kata sits in between — walkable, with a beach town feel.',
                 'High season runs roughly November to April (dry, calm sea on the west coast); May to October is the green season, with short tropical showers, surf on the west coast and more choice of villas.'],
    },
    'koh-samui': {
        'title': 'Monthly Villa Rental in Koh Samui — Long Stays | Thai Villas',
        'desc': 'Monthly and long-term villa rentals on Koh Samui: how it works, deposits, utilities, what to check. Monthly rates on request via WhatsApp.',
        'h1': 'Monthly villa rental <i>on Koh Samui.</i>',
        'lead': 'Hillside villas with sea views and quiet beaches in the Gulf of Thailand — rented by the month, arranged on WhatsApp.',
        'life': ['Koh Samui has its own airport, international hospitals and a relaxed island rhythm. Chaweng and Lamai are the busiest areas; Bophut, Mae Nam and the west coast are quieter and popular with people staying a month or longer.',
                 'The Gulf has a different weather pattern to Phuket: the sunniest months are usually around January to August, and the heaviest rain tends to fall around October to December.',
                 'Many villas sit on hillsides, so a car or scooter makes day-to-day life easier — ask us about access roads when you shortlist.'],
    },
    'pattaya': {
        'title': 'Monthly Villa Rental in Pattaya — Pool Houses for Long Stays | Thai Villas',
        'desc': 'Rent a pool house or villa in Pattaya by the month: Pratumnak, Jomtien and beyond. How long stays work, deposits, utilities. Rates on request.',
        'h1': 'Monthly villa rental <i>in Pattaya.</i>',
        'lead': 'Large pool houses about two hours from Bangkok, open all year — rented by the month for families, remote workers and long winters.',
        'life': ['Pattaya is the closest beach city to Bangkok, with big supermarkets, international hospitals and schools. Pratumnak Hill and Jomtien are calmer than central Pattaya and popular for monthly stays.',
                 'Villas here are often larger houses with private pools in residential estates — good value for families who want space.',
                 'The weather is warm all year; the wetter months are usually around September and October.'],
    },
    'bangkok': {
        'title': 'Monthly Rental in Bangkok — Houses for Long Stays | Thai Villas',
        'desc': 'Monthly and long-term rentals in Bangkok: houses and serviced homes, how deposits and utilities usually work. Ask us on WhatsApp — rates on request.',
        'h1': 'Monthly rental <i>in Bangkok.</i>',
        'lead': 'Serviced houses and homes for living in the capital for a month or more — arranged on WhatsApp.',
        'life': ['Bangkok long stays are mostly about location: being close to the BTS/MRT lines saves hours each week. Sukhumvit, Sathorn and Ari are popular with people moving here for work or study.',
                 'Private pool houses are rarer than on the islands, so it pays to start looking early and to be flexible on the exact area.',
                 'The cooler, drier months are usually November to February; the rainy season peaks around September and October.'],
    },
    'chiang-mai': {
        'title': 'Monthly Villa Rental in Chiang Mai — Long Stays | Thai Villas',
        'desc': 'Monthly villa and house rentals in Chiang Mai: how it works, deposits, utilities, best season. Rates on request via WhatsApp.',
        'h1': 'Monthly villa rental <i>in Chiang Mai.</i>',
        'lead': 'Houses with gardens and pools in the northern mountain city — a long-time favourite for monthly stays and remote work.',
        'life': ['Chiang Mai is known for its old city, temples, cafés and a large community of remote workers. Nimman, Hang Dong and the areas around the old city are common choices for a long stay.',
                 'The cool season (roughly November to February) is the most popular time. In the late dry season, around March and April, smoke from agricultural burning can affect air quality — worth keeping in mind when you pick your dates.',
                 'Pool villas are usually a short drive outside the centre, so plan for a car or scooter.'],
    },
}

# Phuket beach areas popular for long stays (general facts only)
LONG_PHUKET = [
    ('rawai', 'Residential southern tip with a big long-stay community, the seafood market and boats to the islands.'),
    ('nai-harn', 'One of the island\'s prettiest bays, with a lake loop for running, yoga studios and a calm pace.'),
    ('bang-tao', 'Six kilometres of beach, beach clubs, cafés and gyms around Cherng Talay and Laguna.'),
    ('kata', 'Walkable beach town with cafés and restaurants, and surf in the green season.'),
    ('chalong', 'Central and practical: the pier for island trips, supermarkets, gyms and Muay Thai camps.'),
]
SUB = {a['slug']: a for a in PHUKET['areas']}

HOW = [
    ('Minimum term', 'Monthly rentals usually start at one month. Several months, a full season or longer can be arranged — just tell us your dates.', 'cal'),
    ('Security deposit', 'A refundable deposit is normal for long stays — usually one to two months\' rent, returned at check-out after the villa is checked and final bills are settled.', 'key'),
    ('Utilities', 'Electricity, and sometimes water, are often billed separately by the meter. Wi-Fi, pool and garden care are frequently included. We confirm exactly what is included for each villa before you commit.', 'bolt'),
    ('Agreement', 'A short written rental agreement sets out the dates, rate, deposit, what is included and the house rules. Read it before you pay anything.', 'doc'),
]

INCL = ('<div class="w4-grid g2">'
        + tile('Often included in a monthly rate', '<ul><li>The furnished villa with private pool</li><li>Pool and garden care</li><li>Wi-Fi</li><li>Regular cleaning (frequency varies by villa)</li><li>Bed linen and towels</li></ul>')
        + tile('Often billed separately', '<ul><li>Electricity, by the meter (air-con is the biggest factor)</li><li>Water and drinking-water delivery</li><li>Extra cleaning, laundry, a private chef</li><li>Airport transfers and car or bike rental</li></ul>')
        + '</div><p class="w4-sub" style="margin:18px 0 0;font-size:14px">Every villa is different — we confirm what is included in writing before you commit.</p>')

VISA = ('<div class="w4-notice" style="margin:26px 0 0"><b>A note on visas.</b> How long you can stay in Thailand depends on your nationality and visa type, '
        'and the rules change from time to time. Please check the current requirements with the Thai embassy or consulate, or official government sources, '
        'before you plan a long stay. We rent villas — we can\'t give visa advice.</div>')

STEPS = [
    ('Tell us your dates', 'Message us on WhatsApp with your dates, how many of you there are, the area and your must-haves (office, pool size, pets, schools nearby).'),
    ('Get a shortlist', 'We come back with villas that are genuinely free for your dates, with photos, what is included and the monthly rate.'),
    ('See it first', 'A video walkthrough on WhatsApp, or a viewing if you are already in Thailand. Ask anything about the villa and the neighbourhood.'),
    ('Agreement & move in', 'Sign a short agreement, pay the first month and the refundable deposit, and move in. We stay reachable for the whole stay.'),
]

def faq_items(name=None):
    where = (' in ' + name) if name else ' in Thailand'
    return [
        ('How much does a monthly villa rental cost%s?' % where,
         'It depends on the season, the area, the size of the villa and how long you stay. We don\'t publish monthly rates yet — they are on request. Send us your dates on WhatsApp and we\'ll reply with the rates for villas that are actually free.'),
        ('What is the minimum rental period?',
         'Monthly rentals usually start at one month. Shorter stays are booked as daily rentals; longer stays — a season or more — can be arranged villa by villa.'),
        ('How much is the security deposit?',
         'For long stays a refundable deposit of one to two months\' rent is common. It is returned at the end of the stay after the villa is checked and any unpaid utility bills are settled. The exact amount is written into the agreement.'),
        ('Are electricity and water included?',
         'Often not: electricity, and sometimes water, are usually billed separately by the meter, and air-conditioning makes the biggest difference. Wi-Fi, pool and garden care are frequently included. We confirm what is included for each villa before you commit.'),
        ('Do I need a special visa for a long stay?',
         'That depends on your nationality and the type of visa, and the rules change from time to time. Please check the current requirements with the Thai embassy or consulate or official government sources. We can\'t advise on visas.'),
        ('When is the best time to book?',
         'For the high season (roughly November to April on the Andaman coast) start early — the best long-stay villas go first. In the green season there is usually more choice.'),
        ('Can I see the villa before I pay?',
         'Yes. We can do a video walkthrough on WhatsApp, or arrange a viewing if you are already in Thailand. Nothing is paid until you have seen the agreement.'),
    ]

def dest_card(slug):
    d = D[slug]
    n = count(slug, pred=monthly)
    cnt = '<span class="cnt">%d villa%s by the month</span>' % (n, '' if n == 1 else 's') if n else '<span class="cnt">On request</span>'
    return ('<a class="w4-pcard" href="/monthly-rental/%s/">%s<img src="%s" alt="Monthly villa rental in %s" loading="lazy" decoding="async" width="900" height="1100">'
            '<div class="in"><h3>%s</h3><p>%s</p><span class="go">Monthly in %s %s</span></div></a>'
            % (slug, cnt, d['image'], esc(d['name']), esc(d['name']), esc(d['short']), esc(d['name']), ICON['arrow'].replace('<svg', '<svg width="14" height="14"')))

def villa_grid(vs):
    return '<div class="w4-cards">' + ''.join(villa_card(v, 'Monthly rate on request <span>&middot; reply on WhatsApp</span>') for v in vs) + '</div>'

def none_yet(name):
    return ('<div class="w4-tile" style="max-width:720px"><h3>Monthly villas in %s are on request</h3>'
            '<p>We are still adding long-stay villas here. Tell us your dates, budget and what you need, and we\'ll look for you and come back with options.</p>'
            '<div class="w4-btns" style="margin-top:18px">%s%s</div></div>'
            % (esc(name), wa_btn("Hi Thai Villas! I'm looking for a monthly villa rental in %s." % name, 'Ask on WhatsApp'),
               btn('/property-rental/?period=monthly', 'All monthly villas', 'light')))

SAMPLE_NOTE = '<p class="w4-sample">Listings shown are sample villas while the site is in preview — real availability and rates on request.</p>'

def itemlist(name, vs):
    return {"@context": "https://schema.org", "@type": "ItemList", "name": name, "numberOfItems": len(vs),
            "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": v['url'], "name": v['name']} for i, v in enumerate(vs)]}

# ------------------------------------------------------------------ hub
def build_hub():
    vs = [v for v in VILLAS if monthly(v)]
    body = hero('/images/phuket-2.jpg', 'Monthly &amp; long stay',
                'Rent a villa in Thailand <i>by the month.</i>',
                'Private pool villas for a month, a season or longer — in Phuket first, plus Koh Samui, Pattaya, Bangkok and Chiang Mai. '
                'One person on WhatsApp handles your shortlist, viewing and agreement.',
                wa_btn("Hi Thai Villas! I'm looking for a monthly villa rental in Thailand.", 'Ask about a long stay')
                + btn('#destinations', 'Choose a destination', 'ghost'),
                chips=['From one month', 'Deposit 1–2 months', 'Rates on request'], alt='Pool villa in Phuket for a monthly stay')
    body += '<div class="w4-wrap">' + crumbs_html([('Home', '/'), ('Monthly rentals', '/monthly-rental/')]) + '</div>'
    body += section('Where we rent by the month', 'Five places <i>to live for a while</i>',
                    '<div class="w4-grid g3" style="grid-template-columns:repeat(auto-fill,minmax(240px,1fr))">' + ''.join(dest_card(s) for s in DEST) + '</div>',
                    sub='Phuket has the widest choice. Elsewhere we search on request — tell us where and when.', sid='destinations')
    body += section('How it works in Thailand', 'Monthly renting, <i>explained simply</i>',
                    '<div class="w4-grid g4">' + ''.join(tile(t, p, i) for t, p, i in HOW) + '</div>' + VISA,
                    sub='Long stays in Thailand follow a few common rules. Here is what to expect before you message anyone.', cls='paper')
    body += section('What is in the rate', 'Included — <i>and billed separately</i>', INCL)
    body += section('Available by the month', 'Villas you can rent <i>monthly</i>',
                    SAMPLE_NOTE + villa_grid(vs)
                    + '<div class="w4-rel" style="margin-top:22px"><a href="/property-rental/?period=monthly">All monthly villas in the catalogue</a>'
                    + ''.join('<a href="/monthly-rental/%s/">%s</a>' % (s, esc(D[s]['name'])) for s in DEST) + '</div>', sid='villas')
    body += section('Step by step', 'From first message <i>to moving in</i>', steps(STEPS), cls='paper')
    fh, fld = faq(faq_items())
    body += section('Questions', 'Monthly rentals: <i>your questions</i>', fh, narrow=True, sid='faq')
    body += final('Long stays', 'Tell us your dates.',
                  'Send your dates, the destination and how many of you there are. We reply with what is free and the monthly rate.',
                  wa_btn("Hi Thai Villas! I'm looking for a monthly villa rental in Thailand.") + btn('/property-rental/', 'All villas', 'light'))
    ld = [fld, crumbs_ld([('Home', '/'), ('Monthly rentals', '/monthly-rental/')]), itemlist('Villas for monthly rent in Thailand', vs)]
    write('monthly-rental/index.html', page('Monthly Villa Rental in Thailand — Long-Stay Pool Villas | Thai Villas',
          'Rent a private pool villa in Thailand by the month — Phuket, Koh Samui, Pattaya, Bangkok, Chiang Mai. How long stays work: minimum term, deposit, utilities. Rates on request.',
          body, ld, '/images/phuket-2.jpg'))

# ------------------------------------------------------------------ destination pages
def build_dest(slug):
    d, n = D[slug], NOTES[slug]
    name = d['name']
    vs = [v for v in VILLAS if monthly(v) and v['areaSlug'] == slug]
    wtxt = "Hi Thai Villas! I'm looking for a monthly villa rental in %s." % name
    img = '/images/phuket.jpg' if slug == 'phuket' else d['image']
    body = hero(img, 'Monthly &amp; long stay · %s' % esc(name), n['h1'], n['lead'],
                wa_btn(wtxt, 'Ask about monthly rates') + btn('#villas', 'See the villas', 'ghost'),
                chips=['From one month', 'Rates on request'], short=True, alt='Monthly villa rental in %s' % name)
    body += '<div class="w4-wrap">' + crumbs_html([('Home', '/'), ('Monthly rentals', '/monthly-rental/'), (name, '/monthly-rental/%s/' % slug)]) + '</div>'
    inner = (SAMPLE_NOTE + villa_grid(vs)) if vs else none_yet(name)
    inner += ('<div class="w4-rel" style="margin-top:22px"><a href="/property-rental/?period=monthly&amp;location=%s">Monthly villas in %s — catalogue</a>'
              '<a href="%s">Daily stays in %s</a></div>' % (slug, esc(name), area_url(slug), esc(name)))
    body += section('Available by the month', 'Villas in %s <i>for a long stay</i>' % esc(name), inner, sid='villas')
    if slug == 'phuket':
        cards = ''.join(
            '<a class="w4-pcard wide" href="%s"><img src="%s" alt="%s, Phuket" loading="lazy" decoding="async" width="1200" height="750">'
            '<div class="in"><h3>%s</h3><p>%s</p><span class="go">Villas in %s %s</span></div></a>'
            % (area_url('phuket', s), SUB[s]['image'], esc(SUB[s]['name']), esc(SUB[s]['name']), esc(t), esc(SUB[s]['name']),
               ICON['arrow'].replace('<svg', '<svg width="14" height="14"'))
            for s, t in LONG_PHUKET)
        body += section('Where long-stayers live', 'Phuket beaches <i>popular for long stays</i>',
                        '<div class="w4-grid g3" style="grid-template-columns:repeat(auto-fill,minmax(280px,1fr))">' + cards + '</div>'
                        '<div class="w4-rel" style="margin-top:22px"><a href="/villas/phuket/">All Phuket beaches</a></div>',
                        sub='Five areas where people most often settle for a month or more.', cls='paper', sid='areas')
    body += section('Living here', 'A month or more <i>in %s</i>' % esc(name),
                    '<div class="w4-prose">' + ''.join('<p>%s</p>' % p for p in n['life']) + '</div>', narrow=True,
                    cls='' if slug == 'phuket' else 'paper')
    body += section('How it works', 'Minimum term, deposit, <i>utilities</i>',
                    '<div class="w4-grid g4">' + ''.join(tile(t, p, i) for t, p, i in HOW) + '</div>' + VISA,
                    cls='paper' if slug == 'phuket' else '')
    body += section('Step by step', 'From first message <i>to moving in</i>', steps(STEPS))
    fh, fld = faq(faq_items(name))
    body += section('Questions', 'Monthly rentals in %s: <i>your questions</i>' % esc(name), fh, narrow=True, cls='paper', sid='faq')
    others = ''.join('<a href="/monthly-rental/%s/">Monthly in %s</a>' % (s, esc(D[s]['name'])) for s in DEST if s != slug)
    body += section('Elsewhere', 'Monthly rentals <i>in other places</i>',
                    '<div class="w4-rel"><a href="/monthly-rental/">All monthly rentals</a>%s<a href="/vip/">VIP services</a></div>' % others)
    body += final('Long stays', 'Tell us your dates.',
                  'Send your dates and how many of you there are, and we\'ll come back with what is free in %s and the monthly rate.' % esc(name),
                  wa_btn(wtxt) + btn('/property-rental/?period=monthly', 'All monthly villas', 'light'))
    ld = [fld, crumbs_ld([('Home', '/'), ('Monthly rentals', '/monthly-rental/'), (name, '/monthly-rental/%s/' % slug)])]
    if vs:
        ld.append(itemlist('Villas for monthly rent in %s' % name, vs))
    write('monthly-rental/%s/index.html' % slug, page(n['title'], n['desc'], body, ld, img))

if __name__ == '__main__':
    build_hub()
    for s in DEST:
        build_dest(s)
    print('monthly-rental: hub + %d destination pages' % len(DEST))
