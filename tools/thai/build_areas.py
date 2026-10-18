"""Catalog and area pages for Thai Villas (worker W2).

Writes
  property-rental/index.html              full catalogue: filters, sort, map
  villas/index.html                       all destinations hub
  villas/phuket/index.html                Phuket hub (canonical area design)
  villas/phuket/{beach}/index.html        12 Phuket beach areas
  villas/{destination}/index.html         other destinations

Layout comes from the reference pages (property-rental/, villas/, villas/umalas/); the shell is swapped by
thv.rebrand() and the page body (promo banner, chips, cards, SEO article, FAQ, filter drawer, search sheet,
inline scripts) is regenerated here from data/villas.json + data/areas.json.

    python3 -I tools/thai/build_areas.py
"""
import sys, os, re, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from thv import *  # noqa

OTHER = [d for d in AREAS if d['slug'] != 'phuket']
BEACHES = PHUKET['areas']
BEACH = {a['slug']: a for a in BEACHES}
DEST = {d['slug']: d for d in AREAS}

# ------------------------------------------------------------------ copy (general destination facts only)
STD_SEASON = ('The calmest sea and driest weather on Phuket\'s west coast run from November to April. From May to October '
              'the green season brings showers, bigger swell and red-flag days on some beaches, but also greener hills, '
              'fewer people and better availability &mdash; a good time for monthly stays.')

BEACH_TXT = {
 'bang-tao': dict(
   p=['Bang Tao is the long bay on Phuket\'s north-west coast, a single sweep of sand running roughly six kilometres from the Laguna resort area towards Layan. Behind the beach sits Cherng Talay, a residential town of cafés, gyms, international supermarkets and the Boat Avenue and Porto de Phuket shopping streets &mdash; which is why so many villas, and so many long-stay families, are here.',
      'Expect beach clubs along the sand, quieter stretches in front of the resorts and a wide choice of houses, from compact pool townhouses to large family villas. It is a practical base: almost everything you need day to day is within ten minutes by car.'],
   who='Families, groups of friends and remote workers who want a complete neighbourhood rather than a party strip. One of the most popular parts of Phuket for monthly stays.',
   go='Phuket International Airport is roughly 25&ndash;30 minutes by car, Patong about 25 minutes over the hill and Phuket Town around 35 minutes. A car or scooter helps &mdash; the beach and the shops are spread out.',
   season=STD_SEASON),
 'layan': dict(
   p=['Layan is the small, quiet bay just north of Bang Tao, backed by forest and part of the protected stretch of coast that runs up towards Nai Thon. There is no road along the sand and only a few beach restaurants, so the mood stays calm even in high season.',
      'Villas here sit mostly on the hillsides behind the beach, many with views over the Andaman Sea. Bang Tao\'s restaurants, supermarkets and beach clubs are a few minutes\' drive away when you want them.'],
   who='Couples and families who want privacy and a view, and larger groups looking for spacious hillside villas away from traffic.',
   go='About 20&ndash;25 minutes from Phuket International Airport, five minutes to Bang Tao and Cherng Talay, and around 30 minutes to Patong.',
   season=STD_SEASON),
 'surin': dict(
   p=['Surin is a short, steep beach tucked between Bang Tao and Kamala, framed by headlands and known for clear water in the dry season. The hills around it hold some of the island\'s most upscale villas and boutique hotels, including the cliff-top houses on the road towards Kamala.',
      'The beach itself is compact, with a park and a few casual restaurants behind it. For shopping and everyday errands, Cherng Talay and Bang Tao are five to ten minutes away.'],
   who='Couples and families who want a beautiful small beach and a quiet, polished setting close to Bang Tao\'s amenities.',
   go='Roughly 30 minutes from the airport, about 10 minutes to Bang Tao or Kamala and around 20 minutes to Patong.',
   season=STD_SEASON),
 'kamala': dict(
   p=['Kamala is a relaxed bay between Surin and Patong, with a small village behind a long sandy beach and an easy pace that suits families. Roads climbing the headlands at both ends of the bay lead to villas with wide views over the sea.',
      'There are enough restaurants, minimarts and massage shops to stay local, while Patong\'s nightlife and shopping are only about 15 minutes away &mdash; close, but not on your doorstep.'],
   who='Families and couples who want a calm beach with easy access to Patong, and guests looking for a sea-view villa on the hillside.',
   go='About 35&ndash;40 minutes from the airport, around 15 minutes to Patong and 10 minutes to Surin.',
   season=STD_SEASON),
 'patong': dict(
   p=['Patong is Phuket\'s busiest beach and its nightlife centre: Bangla Road, large shopping malls, hundreds of restaurants and every water sport on offer. The beach is long and wide, and the bay is lively from morning until late.',
      'Villas in Patong are usually not in the centre but on the quieter hillsides at either end of the bay, where you get the view and the calm while staying a few minutes from the action.'],
   who='Groups of friends and guests who want restaurants, nightlife and shopping close by. Less suited to anyone looking for a quiet beach.',
   go='About 45 minutes from the airport, 15 minutes to Kamala, around 20 minutes to Karon and 30 minutes to Phuket Town.',
   season=STD_SEASON),
 'karon': dict(
   p=['Karon is one of the longest beaches on the west coast &mdash; a wide, open stretch of pale sand that squeaks underfoot. Behind it is a compact strip of hotels, restaurants and shops, quieter than Patong and busier than the small bays further south.',
      'Its size means there is always room on the sand, and the flat promenade and easy walk to Kata make it comfortable for families and longer stays.'],
   who='Families, couples and long-stay guests who want a big beach with shops and restaurants within walking distance.',
   go='Around 50&ndash;60 minutes from the airport, about 20 minutes to Patong, 5 minutes to Kata and 25 minutes to Chalong.',
   season='Calm, swimmable sea from November to April. In the green season (May&ndash;October) Karon often has strong surf and rip currents &mdash; swim only where the lifeguards\' flags allow.'),
 'kata': dict(
   p=['Kata (Kata Yai) is a curved bay south of Karon with soft sand, a small island offshore and a relaxed, sociable atmosphere. The streets behind the beach are full of cafés, small restaurants, yoga studios and surf shops.',
      'From May to October Kata becomes one of Phuket\'s main surf beaches, with board rental and surf schools on the sand; in the dry season the water is calm, good for swimming and for snorkelling along the rocks at either end.'],
   who='Couples, families and surfers who like a lively but unhurried neighbourhood &mdash; popular with holidaymakers and monthly guests alike.',
   go='About an hour from the airport, 5 minutes to Karon or Kata Noi, 15 minutes to Nai Harn and around 20 minutes to Chalong.',
   season='November&ndash;April: calm, clear water and the busiest weeks. May&ndash;October: surf season, with bigger waves, greener hills and more choice of villas.'),
 'kata-noi': dict(
   p=['Kata Noi is the small bay just south of Kata, reached by a short road over the headland. With one large hotel, a few restaurants and no through traffic, it is quieter and more secluded than its neighbour &mdash; and often named among Phuket\'s prettiest beaches.',
      'The hills around it, including the road up towards the Karon viewpoint, have villas with sweeping views over the bay and the Andaman Sea.'],
   who='Couples and families who want a peaceful, beautiful beach while staying a few minutes from Kata\'s cafés and restaurants.',
   go='About an hour from the airport, 5 minutes to Kata and 10&ndash;15 minutes to Nai Harn.',
   season='Calm and clear from November to April; from May to October the bay gets swell and is popular with surfers, with red-flag days for swimmers.'),
 'nai-harn': dict(
   p=['Nai Harn is the southern bay loved by long-stayers: a sandy beach between green headlands, a freshwater lake with a walking and running loop, and a calm, community feel. Yoga studios, health cafés and Muay Thai gyms are all a few minutes away.',
      'Promthep Cape, Phuket\'s best-known sunset point, is just up the road, and Rawai\'s markets and boats to the southern islands are close by.'],
   who='Families, remote workers and anyone planning a month or more &mdash; one of the most popular areas for long stays in Phuket.',
   go='Roughly 60&ndash;75 minutes from the airport, 5&ndash;10 minutes to Rawai, about 15 minutes to Kata and 20 minutes to Chalong.',
   season=STD_SEASON),
 'rawai': dict(
   p=['Rawai sits at the southern tip of Phuket. Its shoreline is a working seafront rather than a swimming beach: longtail and speedboats leave from here for Coral Island, Racha and other southern islands, and at the seafood market you can pick your catch and have it cooked next door.',
      'Behind the coast is a large, settled residential area with gyms, international restaurants and everyday services, which makes Rawai one of the most popular places on the island for monthly and long-term rentals. Nai Harn and Ya Nui beaches are a few minutes away for swimming.'],
   who='Long-stay guests, families and remote workers who want everyday convenience and a local feel more than a beach on the doorstep.',
   go='About 60&ndash;75 minutes from the airport, 5&ndash;10 minutes to Nai Harn, 15 minutes to Chalong and around 30 minutes to Phuket Town.',
   season='The south works all year. November to April is best for island trips; May to October brings showers and rougher seas on boat days.'),
 'chalong': dict(
   p=['Chalong is Phuket\'s south-east hub rather than a beach destination. Chalong Pier is the departure point for many diving, snorkelling and island trips, and the bay is a base for yachts. Wat Chalong, the island\'s best-known temple, and the Big Buddha on the hill above are both close by.',
      'Because it sits between the south coast, Phuket Town and the west-coast beaches, Chalong is a practical base for longer stays: supermarkets, clinics and schools are within easy reach, and villas tend to offer more space and bigger gardens.'],
   who='Families on long stays, boating and diving enthusiasts, and guests who prefer a central location to a beachfront.',
   go='About 45&ndash;60 minutes from the airport, 15&ndash;20 minutes to Kata, Rawai or Nai Harn, and around 20 minutes to Phuket Town.',
   season='Usable all year; the dry season from November to April is the best time for boat trips and diving.'),
 'mai-khao': dict(
   p=['Mai Khao and Nai Yang are the long, quiet beaches of Phuket\'s north-west, inside Sirinat National Park. Mai Khao is around ten kilometres of almost empty sand, while Nai Yang has a shady, tree-lined beach with simple seafood restaurants.',
      'The airport is right next door, which makes the area ideal for short stays, first and last nights, or anyone who wants to get away from the crowds. Bang Tao\'s restaurants and shops are 20&ndash;30 minutes to the south.'],
   who='Couples and families who value peace and nature, and travellers who want to be close to the airport.',
   go='About 5&ndash;15 minutes from Phuket International Airport, 20&ndash;30 minutes to Bang Tao and around 45 minutes to Patong.',
   season=STD_SEASON),
}

DEST_TXT = {
 'koh-samui': dict(tag='Koh Samui villa rentals', sub='Pool villas on the palm-fringed island in the Gulf of Thailand',
   p=['Koh Samui is Thailand\'s second-largest island, in the Gulf of Thailand, with its own airport and a mix of busy and quiet coasts. Chaweng and Lamai on the east are the liveliest beaches; Bophut with Fisherman\'s Village, Choeng Mon and Maenam in the north are calmer; and the hills between them hold many sea-view pool villas.',
      'Samui has a different weather pattern from Phuket: the Gulf coast is usually driest from around January to August, with the heaviest rain from October to December &mdash; a natural alternative when the Andaman coast is in its green season.'],
   who='Couples, families and groups who want an island holiday with good restaurants and calm seas, and long-stay guests who like island life with full amenities.',
   go='Flights land at Samui Airport in the north-east of the island; ferries connect to Surat Thani on the mainland and to Koh Phangan.',
   season='Driest from about January to August; October to December is the main rainy season on the Gulf side.'),
 'pattaya': dict(tag='Pattaya villa rentals', sub='Large pool houses two hours from Bangkok, open all year',
   p=['Pattaya is a seaside city on the eastern Gulf coast, roughly two hours by road from Bangkok. Beyond the busy central beach, areas such as Pratumnak hill, Jomtien and Na Jomtien are quieter and residential, with large houses and pool villas popular with families and groups.',
      'Golf courses, water parks and islands such as Koh Larn, a short boat ride away, keep everyone busy, and the easy road from Bangkok\'s Suvarnabhumi airport makes Pattaya a common choice for both long weekends and monthly stays.'],
   who='Families and groups who want a big house with a pool, and long-stay guests who want city conveniences by the sea.',
   go='About 1.5&ndash;2 hours by road from Suvarnabhumi Airport and around two hours from central Bangkok, depending on traffic.',
   season='A year-round destination. November to February is the most comfortable; showers are more frequent from around June to October.'),
 'bangkok': dict(tag='Bangkok rentals', sub='Houses and serviced homes for monthly living in the capital',
   p=['Bangkok is Thailand\'s capital and largest city. For house-style living, guests usually look at neighbourhoods such as Sukhumvit, Thonglor&ndash;Ekkamai and Sathorn, close to the BTS Skytrain and MRT lines, with international schools, hospitals and restaurants nearby.',
      'Bangkok is above all a monthly destination: business trips, relocation, school terms or a comfortable base while exploring the country. The most pleasant weather is the cool season from roughly November to February; April and May are the hottest months.'],
   who='Professionals, relocating families and long-stay guests who need a home in the city rather than a hotel room.',
   go='Suvarnabhumi and Don Mueang airports both connect to the centre; journey times range from about 30 to 60 minutes depending on traffic.',
   season='Cool season November&ndash;February, hot season March&ndash;May, rainy season roughly June&ndash;October.'),
 'krabi': dict(tag='Krabi villa rentals', sub='Limestone cliffs, Ao Nang and Railay on the Andaman coast',
   p=['Krabi province lies across Phang Nga Bay from Phuket on the same Andaman coast, famous for limestone cliffs, the beaches of Railay and boat trips to Phi Phi and the Hong islands. Ao Nang is the main beach town; Klong Muang and Tubkaek to the north are quieter, with resorts and villas.',
      'The rhythm of the year matches Phuket: calm seas and dry weather from November to April, and a greener, quieter season from May to October when some boat routes run less often.'],
   who='Couples, families and adventurous travellers who want island-hopping, climbing and a slower pace than Phuket.',
   go='Krabi International Airport is roughly 30&ndash;40 minutes from Ao Nang by car; Phuket is about two to three hours by road.',
   season=STD_SEASON.replace("Phuket\'s west coast", 'the Andaman coast')),
 'koh-phangan': dict(tag='Koh Phangan villa rentals', sub='Jungle hills and quiet bays next to Koh Samui',
   p=['Koh Phangan is Samui\'s smaller, greener neighbour, reached by ferry. Beyond the famous Full Moon Party at Haad Rin, the island is quiet: jungle hills, small bays and a large community of long-stay guests around Srithanu and Thong Sala.',
      'Villas range from simple jungle houses to sea-view pool villas on the hillsides. Like Samui, the island is usually driest from around January to August.'],
   who='Remote workers, yoga and wellness travellers and anyone who wants island life at a slower pace, often for a month or more.',
   go='There is no airport on the island: fly to Koh Samui or Surat Thani and continue by ferry or speedboat to Thong Sala.',
   season='Driest from about January to August; October to December is the main rainy season on the Gulf side.'),
 'hua-hin': dict(tag='Hua Hin villa rentals', sub='A royal seaside town south of Bangkok, golf and calm beaches',
   p=['Hua Hin is a seaside town on the western Gulf coast, roughly three hours south of Bangkok by road and long a favourite retreat of the Thai royal family. It is known for a long, calm beach, night markets, golf courses and a relaxed, family-friendly pace.',
      'Pool villas on the edges of town and towards Khao Takiab and Pranburi give families space and quiet, and the town works well for longer stays, particularly in the cooler months.'],
   who='Families, golfers and long-stay guests who want a calm beach town within easy reach of Bangkok.',
   go='About three hours by road from Bangkok; Hua Hin also has a small airport with limited domestic flights.',
   season='Relatively dry compared with much of Thailand; November to February is the most comfortable, and showers are more common from about September to November.'),
 'chiang-mai': dict(tag='Chiang Mai rentals', sub='Houses with gardens and pool villas in the northern mountain city',
   p=['Chiang Mai is the main city of northern Thailand, surrounded by mountains, with hundreds of temples, a walled Old City and the café-filled Nimman neighbourhood. Houses with gardens and pool villas on the city\'s outskirts are popular with families and remote workers.',
      'The cool season from November to February is the most pleasant; March and April can be hot and hazy from agricultural burning, and the rainy season runs from around June to October. Chiang Mai is one of Thailand\'s most popular cities for monthly stays.'],
   who='Remote workers, families and long-stay guests who prefer mountains, culture and a lower-key city to the beach.',
   go='Chiang Mai International Airport is around 15&ndash;20 minutes from the Old City and Nimman.',
   season='Cool season November&ndash;February; hot and often hazy March&ndash;April; rainy season roughly June&ndash;October.'),
}

# ------------------------------------------------------------------ small helpers
def pl(n, w='villa'):
    return '%d %s%s' % (n, w, '' if n == 1 else 's')

def km(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a['lat'], a['lng'], b['lat'], b['lng']))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(h))

def nearby(slug, k=4):
    me = BEACH[slug]
    return sorted((a for a in BEACHES if a['slug'] != slug), key=lambda a: km(me, a))[:k]

def card(v):
    return prop_card(v)

CHIP_A = ('<a href="%s" style="font-size:13px;color:#0a0a0a;text-decoration:none;background:white;'
          'border:1px solid #e6e3dc;border-radius:999px;padding:8px 12px">%s</a>')
def chips(links):
    return '<div style="display:flex;flex-wrap:wrap;gap:8px">' + ''.join(CHIP_A % l for l in links) + '</div>'

H2 = "font-family:'Lora',Georgia,serif;font-size:%dpx;font-weight:700;margin:0 0 %dpx"
P_LEAD = 'font-size:15px;line-height:1.8;color:#3b3b36;margin:0 0 14px'
P_CARD = 'font-size:14px;line-height:1.7;color:#4b4b45;margin:0'
BOX = 'background:white;border:1px solid #e6e3dc;border-radius:22px;padding:22px'

def seo_section(sid, kicker, h2, paras, side_title, side_links, cards):
    """The reference area page SEO block: article + link box, then rows of three cards."""
    body = ''.join('<p style="%s">%s</p>' % (P_LEAD if i < len(paras) - 1 else P_LEAD.replace('0 0 14px', '0'), p)
                   for i, p in enumerate(paras))
    rows = ''
    for i in range(0, len(cards), 3):
        rows += ('<div class="thb-rgrid3" style="display:grid;grid-template-columns:repeat(3,1fr);gap:18px;margin-top:18px">'
                 + ''.join('<div style="%s"><h2 style="%s">%s</h2><p style="%s">%s</p></div>' % (BOX, H2 % (20, 8), t, P_CARD, x)
                           for t, x in cards[i:i + 3]) + '</div>')
    return f'''<section aria-labelledby="{sid}" style="max-width:1320px;margin:56px auto 0;padding:0 40px 56px">
  <div class="thb-rgrid2" style="background:#f2efe8;border:1px solid #e6e3dc;border-radius:28px;padding:32px;display:grid;grid-template-columns:1.35fr .85fr;gap:28px">
    <div>
      <p style="font-size:12px;color:#6b6b66;text-transform:uppercase;letter-spacing:0.18em;font-weight:700;margin-bottom:10px">{kicker}</p>
      <h2 id="{sid}" style="font-family:'Lora',Georgia,serif;font-size:34px;line-height:1.08;font-weight:700;margin:0 0 14px">{h2}</h2>
      {body}
    </div>
    <div style="background:#fafaf7;border:1px solid #e6e3dc;border-radius:22px;padding:22px">
      <h2 style="{H2 % (22, 14)}">{side_title}</h2>
      {chips(side_links)}
    </div>
  </div>
  {rows}
</section>'''

def faq_section(label, title, qa):
    det = ''.join('<details style="border:1px solid #e5e0d6;border-radius:12px;padding:14px 18px;margin:0 0 10px;background:#fff">'
                  '<summary style="cursor:pointer;font-weight:600;font-size:16px">%s</summary>'
                  '<p style="margin:10px 0 2px;color:#4c473f;line-height:1.55">%s</p></details>' % (q, a) for q, a in qa)
    return (f'<section aria-label="Frequently asked questions — {esc(label)}" style="max-width:1320px;margin:0 auto;padding:0 40px 56px">'
            f'<h2 style="{H2 % (22, 16)}">{title}</h2>{det}</section>')

def faq_ld(qa):
    strip = lambda t: re.sub(r'<[^>]+>', '', t).replace('&ndash;', '–').replace('&mdash;', '—').replace('&amp;', '&').replace('&#x27;', "'")
    return {"@context": "https://schema.org", "@type": "FAQPage",
            "mainEntity": [{"@type": "Question", "name": strip(q), "acceptedAnswer": {"@type": "Answer", "text": strip(a)}} for q, a in qa]}

def crumbs_ld(items):
    return {"@context": "https://schema.org", "@type": "BreadcrumbList",
            "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n, "item": u} for i, (n, u) in enumerate(items)]}

def crumbs_html(items):
    out = []
    for i, (n, u) in enumerate(items):
        if i == len(items) - 1:
            out.append('<span aria-current="page" style="color:#fff">%s</span>' % esc(n))
        else:
            out.append('<a href="%s" style="color:inherit;text-decoration:none">%s</a>' % (u, esc(n)))
    return ('<nav aria-label="Breadcrumb" style="font-size:12.5px;color:rgba(255,255,255,0.68);margin-bottom:12px;'
            'display:flex;flex-wrap:wrap;justify-content:center;gap:6px">' + ' <span aria-hidden="true">/</span> '.join(out) + '</nav>')

def more_places(title, links):
    return (f'<section aria-label="{esc(title)}" style="max-width:1320px;margin:0 auto;padding:0 40px 56px">'
            f'<h2 style="{H2 % (22, 16)}">{title}</h2>{chips(links)}</section>')

SAMPLE_NOTE = ('<p style="font-size:12.5px;color:#6b6b66;margin-top:6px">Sample listings while we onboard villas &middot; '
               'prices on request &middot; we reply on WhatsApp</p>')

def promo(crumbs, tag, h1, sub, code):
    return f'''  <!-- PROMO BANNER -->
  <div class="promo-banner">
    <div class="promo-inner">
      <!-- Center -->
      <div class="promo-center">
        {crumbs_html(crumbs) if crumbs else ''}
        <div class="promo-tag">{tag}</div>
        <h1 class="promo-title">{h1}</h1>
        <p class="promo-subtitle">{sub}</p>
        {code}
        <p style="color:rgba(255,255,255,0.55);font-size:11.5px;margin-top:10px"><span style="color:#b8f04a;font-weight:600">Daily &amp; monthly rentals</span> &nbsp;•&nbsp; prices on request &nbsp;•&nbsp; a real person on WhatsApp</p>
      </div>

    </div>
  </div>
'''

HERO_SEARCH = '''<div class="promo-search" id="thbHeroSearch">
  <div class="hs-row">
    <button type="button" class="hs-seg" id="hsWhere"><span class="hs-lab">Where</span><span class="hs-val" id="hsWhereVal">All Thailand</span></button>
    <div class="hs-div"></div>
    <button type="button" class="hs-seg" id="hsIn"><span class="hs-lab">Check in</span><span class="hs-val" id="hsInVal">Add date</span></button>
    <div class="hs-div"></div>
    <button type="button" class="hs-seg" id="hsOut"><span class="hs-lab">Check out</span><span class="hs-val" id="hsOutVal">Add date</span></button>
    <div class="hs-div"></div>
    <button type="button" class="hs-seg" id="hsGuests"><span class="hs-lab">Guests</span><span class="hs-val" id="hsGuestsVal">Any</span></button>
    <button type="button" class="hs-btn" id="hsGo">
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
      Search
    </button>
  </div>
  <div class="hs-pop" id="hsPopWhere" role="listbox"></div>
  <div class="hs-pop" id="hsPopCal">
    <div class="cal-wrap" id="calWrap"></div>
    <div class="cal-ft"><p id="calHint">Select check-in date</p><button type="button" id="calClear">Clear dates</button></div>
  </div>
  <div class="hs-pop" id="hsPopGuests">
    <div class="hs-step"><p>Guests<small>How many people</small></p>
      <div class="ctr"><button type="button" id="hsGm">&minus;</button><span id="hsGn">Any</span><button type="button" id="hsGp">+</button></div>
    </div>
  </div>
</div>'''

def area_keys():
    """(key, label, count) for every place: '' all, 'phuket', 'phuket/kata', 'koh-samui' ..."""
    out = [('', 'All Thailand', len(VILLAS)), ('phuket', 'Phuket', count('phuket'))]
    out += [('phuket/' + a['slug'], a['name'], count('phuket', a['slug'])) for a in BEACHES]
    out += [(d['slug'], d['name'], count(d['slug'])) for d in OTHER]
    return out

def qchip(key, label, n, on=False):
    return '        <button class="thb-qchip%s" data-area="%s">%s <b>%d</b></button>\n' % (' on' if on else '', key, label, n)

def pills_bar(chip_list, search_label, tools=True):
    return f'''  <!-- AMENITY PILLS + FILTERS -->
  <div class="pills-bar">
    <div class="pills-inner">
      <button id="thbSearchPill" aria-label="Search by area and dates">
        <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
        <span style="min-width:0"><span class="tsp-t" style="display:block">{search_label}</span><span class="tsp-s" style="display:block">Any dates &middot; Any guests</span></span>
      </button>
      <div id="thbAreaChips" aria-label="Quick area filter">
{''.join(qchip(*c) for c in chip_list)}      </div>
      <div class="pills-sep" style="display:none"></div>
      {TOOLS if tools else ''}
    </div>
  </div>
'''

TOOLS = '''<div class="thb-tools">
        <button class="filters-btn" onclick="openFilters()">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="4" y1="6" x2="20" y2="6"/><line x1="8" y1="12" x2="16" y2="12"/><line x1="11" y1="18" x2="13" y2="18"/></svg>
          Filters
          <span class="filter-count-badge" id="filterCountBadge">0</span>
        </button>
        <div class="thb-sortwrap">
        <select class="sort-select" id="sortSelect" aria-label="Sort the villas">
          <option value="rec">Recommended</option>
          <option value="beds-desc">Bedrooms: most first</option>
          <option value="beds-asc">Bedrooms: fewest first</option>
          <option value="guests-desc">Guests: most first</option>
        </select>
        <svg class="thb-sortchev" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 9l6 6 6-6"/></svg>
      </div>
      </div>'''

def results_bar(kicker, n, suffix):
    return f'''  <!-- RESULTS BAR -->
  <div class="results-bar">
    <div>
      <p style="font-size:12px;color:#6b6b66;text-transform:uppercase;letter-spacing:0.18em;font-weight:600;margin-bottom:3px">{kicker}</p>
      <p style="font-family:'Lora',Georgia,serif;font-size:26px;font-weight:700" id="resultsTitle" data-suffix="{esc(suffix)}">{(pl(n) + ' available' + suffix) if n else 'New listings coming' + suffix}</p>
      {SAMPLE_NOTE}
    </div>
  </div>
'''

NO_MATCH = ('<div id="thbNoMatch" hidden style="text-align:center;padding:40px 20px;border:1px dashed #dcd8cf;border-radius:20px;margin-top:8px">'
            '<p style="font-family:\'Lora\',Georgia,serif;font-size:20px;font-weight:700;margin-bottom:6px">No villas match these filters</p>'
            '<p style="font-size:14px;color:#6b6b66;margin:0 0 14px">Try fewer filters &mdash; or tell us what you need and we will look for you.</p>'
            '<button type="button" onclick="clearAllFilters()" style="height:42px;padding:0 18px;border-radius:999px;border:1.5px solid #0a0a0a;background:#fff;font-weight:600;cursor:pointer;margin:4px">Clear filters</button>'
            '<a href="%s" rel="noopener" style="display:inline-flex;align-items:center;height:42px;padding:0 18px;border-radius:999px;background:#0a0a0a;color:#fff;text-decoration:none;font-weight:600;margin:4px">Ask on WhatsApp</a></div>')

def empty_state(place, near_links):
    return (f'<div style="text-align:center;padding:44px 22px;background:white;border:1px solid #e6e3dc;border-radius:22px">'
            f'<p style="font-family:\'Lora\',Georgia,serif;font-size:24px;font-weight:700;margin-bottom:8px">No villas listed in {place} yet</p>'
            f'<p style="font-size:14.5px;line-height:1.7;color:#4b4b45;max-width:560px;margin:0 auto 18px">We are adding villas in {place} now. '
            f'Send us your dates, the number of guests and whether you need a daily or monthly stay &mdash; we will reply on WhatsApp with what is available.</p>'
            f'<a href="{wa("Hi Thai Villas! I am looking for a villa in %s." % re.sub("<[^>]+>|&[a-z]+;", "", place))}" rel="noopener" style="display:inline-flex;height:46px;align-items:center;padding:0 22px;border-radius:999px;background:#0a0a0a;color:#fff;text-decoration:none;font-weight:600;font-size:14.5px">Ask about {place} on WhatsApp</a>'
            + (f'<p style="font-size:13px;color:#6b6b66;margin:22px 0 10px">Villas nearby</p><div style="display:flex;flex-wrap:wrap;gap:8px;justify-content:center">'
               + ''.join(CHIP_A % l for l in near_links) + '</div>' if near_links else '')
            + '</div>')

def cards_wrap(vs, empty_html=''):
    if not vs:
        return f'''  <!-- CARDS GRID -->
  <div class="cards-wrap">
    {empty_html}
  </div>
'''
    return f'''  <!-- CARDS GRID -->
  <div class="cards-wrap">
    <div id="cardGrid" style="display:grid;grid-template-columns:repeat(4,1fr);gap:20px">
      {"".join(card(v) for v in vs)}
    </div>
    {NO_MATCH % wa()}
  </div>
'''

# destination / beach cards (villas/index.html design)
def place_card(url, img, name, badge, n, text, cta):
    meta = '<span>%s</span><span>daily &amp; monthly</span>' % (pl(n) if n else 'Villas on request')
    return f'''<div class="prop-card" onclick="window.location='{url}'">
          <div class="img-wrap">
            <img src="{img}" alt="Villas for rent in {esc(name)}" loading="lazy" decoding="async" width="1200" height="800">
            <span class="badge">{esc(badge)}</span>
          </div>
          <div style="padding:14px">
            <p style="font-family:'Lora',Georgia,serif;font-size:16px;font-weight:600;margin-bottom:6px;line-height:1.2"><a href="{url}" style="color:inherit;text-decoration:none">Villas in {esc(name)}</a></p>
            <div class="prop-meta" style="margin-bottom:10px">{meta}</div>
            <p style="font-size:13.5px;line-height:1.6;color:#4b4b45;margin:0 0 12px">{esc(text)}</p>
            <span style="font-size:13.5px;font-weight:600">{cta} →</span>
          </div>
        </div>'''

def beach_card(a):
    return place_card(area_url('phuket', a['slug']), a['image'], a['name'], 'Phuket', count('phuket', a['slug']),
                      a['short'], 'See %s' % a['name'])

def dest_card(d):
    return place_card(area_url(d['slug']), d['image'], d['name'], 'Thailand', count(d['slug']), d['short'], 'See %s' % d['name'])

PLACE_GRID_CSS = ('<style id="thb-placegrid-css">.thb-placegrid{display:grid;grid-template-columns:repeat(4,1fr);gap:20px}'
                  '@media(max-width:1023px){.thb-placegrid{grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}}'
                  '@media(max-width:639px){.thb-placegrid{grid-template-columns:1fr;gap:18px}}'
                  '@media(max-width:900px){.thb-sec-pad{padding-left:16px!important;padding-right:16px!important}}'
                  '#thbAreaChips{flex-wrap:nowrap;overflow-x:auto;scrollbar-width:thin;padding:4px 2px 6px}'
                  # thv nav: the listing pages' .btn-primary{display:inline-flex} beats Tailwind's .hidden
                  '@media(max-width:639px){#navbar a.mobile-menu-link{display:none!important}}</style>')

def place_grid_section(title, lead, cards_html, sid):
    return f'''<section aria-labelledby="{sid}" class="thb-sec-pad" style="max-width:1300px;margin:0 auto;padding:8px 40px 24px">
  <h2 id="{sid}" style="{H2 % (28, 6)}">{title}</h2>
  <p style="font-size:14px;color:#6b6b66;margin:0 0 18px">{lead}</p>
  <div class="thb-placegrid">{cards_html}</div>
</section>'''

# ------------------------------------------------------------------ filter drawer
def f_section(title, inner):
    return f'''    <div class="filter-section">
      <div class="filter-title" onclick="toggleFilter(this)">
        {title}
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M6 9l6 6 6-6"/></svg>
      </div>
      <div class="filter-body">
        {inner}
      </div>
    </div>
'''

def f_chip(group, value, label, n=None, on=False):
    return ('<label class="f-chip%s"><input type="checkbox"%s style="display:none" data-filter="%s" value="%s"> %s%s</label>'
            % (' active' if on else '', ' checked' if on else '', group, value, label, '' if n is None else ' <span class="count">%d</span>' % n))

def f_row(group, value, label, n, indent=False):
    return ('<label style="display:flex;align-items:center;justify-content:space-between;padding:6px 0%s;cursor:pointer;font-size:13.5px">'
            '<span style="display:flex;align-items:center;gap:8px"><input type="checkbox" data-filter="%s" value="%s" style="accent-color:#0a0a0a"> %s</span>'
            '<span style="font-size:12px;color:#8a877f">%d</span></label>' % (';padding-left:22px' if indent else '', group, value, label, n))

AMEN_F = [('pool', 'Private pool'), ('beach', 'Near the beach'), ('view', 'Sea view'), ('wifi', 'Wi-Fi'), ('kitchen', 'Kitchen'),
          ('work', 'Workspace'), ('ac', 'Air con'), ('parking', 'Parking'), ('garden', 'Garden'), ('chef', 'Chef on request')]
VIBE_F = [('family', '👨‍👩‍👧 Family'), ('romantic', '🌹 Romantic escape'), ('surf', '🏄 Surf'), ('work', '💻 Work &amp; live'), ('luxury', '✨ Luxury')]

def drawer(vs, with_location):
    tk = {v['id']: set(tokens(v).split()) for v in vs}
    c = lambda pred: sum(1 for v in vs if pred(v))
    period = f_section('Rental period', '<div style="display:flex;flex-wrap:wrap;gap:6px">' + ''.join([
        f_chip('period', 'any', 'Any', len(vs), True),
        f_chip('period', 'daily', 'Daily', c(lambda v: v.get('daily'))),
        f_chip('period', 'monthly', 'Monthly', c(lambda v: v.get('monthly')))]) + '</div>')
    beds = f_section('Bedrooms', '<div style="display:flex;flex-wrap:wrap;gap:6px">' + f_chip('beds', 'any', 'Any', None, True)
                     + ''.join(f_chip('beds', str(b), '5+' if b == 5 else str(b)) for b in range(1, 6)) + '</div>')
    guests = f_section('Guests', '<div style="display:flex;flex-wrap:wrap;gap:6px">' + f_chip('guests', '0', 'Any', None, True)
                       + ''.join(f_chip('guests', str(g), '%d+' % g, c(lambda v, g=g: v['guests'] >= g)) for g in (2, 4, 6, 8, 10, 12)) + '</div>')
    loc = ''
    if with_location:
        rows = []
        for d in AREAS:
            n = c(lambda v, d=d: v['areaSlug'] == d['slug'])
            rows.append(f_row('location', d['slug'], d['name'], n))
            if d['slug'] == 'phuket':
                rows += [f_row('sub', a['slug'], a['name'], c(lambda v, a=a: v.get('subAreaSlug') == a['slug']), True) for a in BEACHES]
        loc = f_section('Location', '<div style="display:flex;flex-direction:column;gap:2px">' + ''.join(rows) + '</div>')
    am = [(t, l, c(lambda v, t=t: t in tk[v['id']])) for t, l in AMEN_F]
    amen = f_section('Amenities', '<div style="display:flex;flex-wrap:wrap;gap:6px">'
                     + ''.join(f_chip('amenity', t, l, n) for t, l, n in am if n) + '</div>')
    vb = [(t, l, c(lambda v, t=t: t in tk[v['id']])) for t, l in VIBE_F]
    vibe = f_section('Type of stay', '<div style="display:flex;flex-wrap:wrap;gap:6px">'
                     + ''.join(f_chip('vibe', t, l, n) for t, l, n in vb if n) + '</div>')
    return f'''<div id="filterDrawer">
  <div id="filterBackdrop" onclick="closeFilters()"></div>
  <div id="filterPanel">
    <!-- Header -->
    <div style="display:flex;align-items:center;justify-content:space-between;padding:20px 28px 16px;border-bottom:1px solid #e6e3dc;position:sticky;top:0;background:#fafaf7;z-index:1">
      <span style="font-family:'Lora',Georgia,serif;font-size:18px;font-weight:700">Filters</span>
      <div style="display:flex;align-items:center;gap:12px">
        <button onclick="clearAllFilters()" style="font-size:12px;color:#6b6b66;background:none;border:none;cursor:pointer;font-family:'Inter',sans-serif;text-decoration:underline">Clear all</button>
        <button onclick="closeFilters()" aria-label="Close filters" style="width:32px;height:32px;border-radius:50%;border:1.5px solid #e6e3dc;background:white;cursor:pointer;display:flex;align-items:center;justify-content:center">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M18 6L6 18M6 6l12 12"/></svg>
        </button>
      </div>
    </div>

{period}{beds}{guests}{loc}{amen}{vibe}
    <!-- Apply -->
    <div style="padding:20px 28px;position:sticky;bottom:0;background:#fafaf7;border-top:1px solid #e6e3dc">
      <button class="btn-primary" style="width:100%;justify-content:center;font-size:15px" onclick="closeFilters()">Show {pl(len(vs))}</button>
    </div>
  </div>
</div>'''

def sheet(keys, cur, title):
    chips_ = '\n'.join('<button class="tsh-chip%s" data-area="%s">%s <b>%d</b></button>' % (' on' if k == cur else '', k, l, n)
                       for k, l, n in keys)
    return f'''<div id="thbSheet" role="dialog" aria-modal="true" aria-label="Search villas">
  <div class="tsh-hd"><p>Search villas</p><button class="tsh-x" aria-label="Close" onclick="thbSheetClose()"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M18 6 6 18M6 6l12 12"/></svg></button></div>
  <div class="tsh-bd">
    <div class="tsh-sec"><p class="tsh-lbl">{title}</p><div class="tsh-chips" id="thbSheetAreas">{chips_}</div></div>
    <div class="tsh-sec"><p class="tsh-lbl">When?</p>
      <div class="tsh-dates">
        <div><label for="thbCi">Check in</label><input type="date" id="thbCi"></div>
        <div><label for="thbCo">Check out</label><input type="date" id="thbCo"></div>
      </div>
    </div>
    <div class="tsh-sec"><p class="tsh-lbl">Who?</p>
      <div class="tsh-guests"><p>Guests</p>
        <div class="tsh-step"><button id="thbGm" aria-label="Fewer guests">&minus;</button><span id="thbGn">Any</span><button id="thbGp" aria-label="More guests">+</button></div>
    </div></div>
  </div>
  <div class="tsh-ft"><button class="tsh-clear" onclick="thbSheetClear()">Clear all</button><button class="tsh-apply" id="thbSheetApply">Show villas</button></div>
</div>'''

# One script for the quick area chips, the mobile search sheet and the hero search bar. On the catalogue
# (IS_CAT) they set the drawer filters through window.thbFilterSet (thb-filters.js); on an area page they
# navigate to the chosen area page. Dates/guests are carried to the villa page in the URL.
PAGE_JS = r'''<script id="thai-search-js">
(function(){
  var IS_CAT=%(is_cat)s, CUR=%(cur)s, KEYS=%(keys)s;
  var NAMES={}; KEYS.forEach(function(k){NAMES[k[0]]=k[1];});
  var q={area:CUR,ci:'',co:'',g:0};
  function urlOf(k){if(!k)return '/property-rental/';var p=k.split('/');return '/villas/'+p[0]+'/'+(p[1]?p[1]+'/':'');}
  function gChip(g){var v=[2,4,6,8,10,12];for(var i=0;i<v.length;i++){if(v[i]>=g)return String(v[i]);}return '12';}
  function qs(){var ps=new URLSearchParams();if(q.ci)ps.set('checkin',q.ci);if(q.co)ps.set('checkout',q.co);if(q.g)ps.set('guests',q.g);var s=ps.toString();return s?'?'+s:'';}
  function apply(){
    if(!IS_CAT){ if(q.area!==CUR){window.location=urlOf(q.area)+qs();return false;} }
    if(window.thbFilterSet){
      var o={guests:q.g?[gChip(q.g)]:[]};
      if(IS_CAT){var p=q.area?q.area.split('/'):[];o.location=p[0]&&!p[1]?[p[0]]:[];o.sub=p[1]?[p[1]]:[];}
      window.thbFilterSet(o);
    }
    syncUi(); return true;
  }
  function fmt(d){if(!d)return'';var p=d.split('-');return p[2]+'.'+p[1];}
  function syncUi(){
    document.querySelectorAll('.thb-qchip').forEach(function(k){k.classList.toggle('on',k.getAttribute('data-area')===q.area);});
    var t=document.querySelector('#thbSearchPill .tsp-t'),st=document.querySelector('#thbSearchPill .tsp-s');
    if(t)t.textContent=NAMES[q.area]||NAMES['']||'Anywhere';
    var bits=[];bits.push(q.ci&&q.co?fmt(q.ci)+' – '+fmt(q.co):'Any dates');bits.push(q.g?q.g+' guests':'Any guests');
    if(st)st.textContent=bits.join(' · ');
    var hv=document.getElementById('hsWhereVal');if(hv){hv.textContent=NAMES[q.area]||'All Thailand';hv.classList.toggle('set',!!q.area);}
  }
  window.thbSearchQ=q;
  /* quick chips */
  document.querySelectorAll('.thb-qchip').forEach(function(c){
    c.addEventListener('click',function(){q.area=c.getAttribute('data-area');apply();});
  });
  /* mobile sheet */
  var sheet=document.getElementById('thbSheet');
  if(sheet){
    var pill=document.getElementById('thbSearchPill');
    var ci=document.getElementById('thbCi'),co=document.getElementById('thbCo'),gn=document.getElementById('thbGn');
    function count(){
      var n=0;document.querySelectorAll('#cardGrid .prop-card').forEach(function(k){
        var p=q.area?q.area.split('/'):[];
        var ok=(!p[0]||k.getAttribute('data-location')===p[0])&&(!p[1]||k.getAttribute('data-sub')===p[1])&&(!q.g||Number(k.getAttribute('data-guests')||0)>=q.g);
        if(ok)n++;});
      return n;
    }
    function upd(){var b=document.getElementById('thbSheetApply');
      if(IS_CAT||q.area===CUR){var n=count();b.textContent='Show '+n+(n===1?' villa':' villas');}
      else b.textContent='Show villas in '+(NAMES[q.area]||'Thailand');}
    window.thbSheetOpen=function(){sheet.classList.add('open');document.body.style.overflow='hidden';upd();};
    window.thbSheetClose=function(){sheet.classList.remove('open');document.body.style.overflow='';};
    window.thbSheetClear=function(){q.area=IS_CAT?'':CUR;q.ci='';q.co='';q.g=0;ci.value='';co.value='';gn.textContent='Any';
      sheet.querySelectorAll('.tsh-chip').forEach(function(c){c.classList.toggle('on',c.getAttribute('data-area')===q.area);});upd();};
    if(pill)pill.addEventListener('click',window.thbSheetOpen);
    sheet.querySelectorAll('.tsh-chip').forEach(function(c){c.addEventListener('click',function(){
      sheet.querySelectorAll('.tsh-chip').forEach(function(k){k.classList.remove('on');});c.classList.add('on');q.area=c.getAttribute('data-area');upd();});});
    ci.addEventListener('change',function(){q.ci=ci.value;if(co.value&&co.value<=ci.value){co.value='';q.co='';}co.min=ci.value;upd();});
    co.addEventListener('change',function(){q.co=co.value;upd();});
    document.getElementById('thbGm').addEventListener('click',function(){if(q.g>0)q.g--;gn.textContent=q.g||'Any';upd();});
    document.getElementById('thbGp').addEventListener('click',function(){if(q.g<16)q.g++;gn.textContent=q.g;upd();});
    document.getElementById('thbSheetApply').addEventListener('click',function(){
      if(apply()){window.thbSheetClose();var rb=document.querySelector('.cards-wrap');if(rb)rb.scrollIntoView({behavior:'smooth',block:'start'});}
    });
  }
  /* hero search (catalogue) */
  var root=document.getElementById('thbHeroSearch');
  if(root){
    var MN=['January','February','March','April','May','June','July','August','September','October','November','December'];
    var today=new Date();today.setHours(0,0,0,0);var view=new Date(today.getFullYear(),today.getMonth(),1);
    function iso(d){return d.getFullYear()+'-'+('0'+(d.getMonth()+1)).slice(-2)+'-'+('0'+d.getDate()).slice(-2);}
    function nice(s){if(!s)return'';var p=s.split('-');return p[2].replace(/^0/,'')+' '+MN[parseInt(p[1],10)-1].slice(0,3);}
    function closeAll(){['hsPopWhere','hsPopCal','hsPopGuests'].forEach(function(id){document.getElementById(id).classList.remove('open');});
      root.querySelectorAll('.hs-seg').forEach(function(s){s.classList.remove('act');});}
    function open(id,segs){var el=document.getElementById(id);var was=el.classList.contains('open');closeAll();
      if(!was){el.classList.add('open');segs.forEach(function(x){document.getElementById(x).classList.add('act');});}}
    function drawWhere(){var w=document.getElementById('hsPopWhere');w.innerHTML='';
      KEYS.forEach(function(a){var b=document.createElement('button');b.type='button';b.className='hs-opt'+(q.area===a[0]?' sel':'');
        b.innerHTML=(a[0].indexOf('/')>0?'&nbsp;&nbsp;&nbsp;':'')+a[1]+' <b>'+a[2]+'</b>';
        b.addEventListener('click',function(e){e.stopPropagation();q.area=a[0];syncUi();closeAll();});w.appendChild(b);});}
    document.getElementById('hsWhere').addEventListener('click',function(e){e.stopPropagation();drawWhere();open('hsPopWhere',['hsWhere']);});
    function drawCal(){var wrap=document.getElementById('calWrap');wrap.innerHTML='';
      for(var k=0;k<2;k++){var m=new Date(view.getFullYear(),view.getMonth()+k,1);var div=document.createElement('div');div.className='cal-m';
        var hd=document.createElement('div');hd.className='cal-hd';hd.innerHTML='<p>'+MN[m.getMonth()]+' '+m.getFullYear()+'</p>';
        if(k===0){var pv=document.createElement('button');pv.type='button';pv.className='cal-nav';pv.id='calPrev';pv.textContent='‹';
          pv.addEventListener('click',function(e){e.stopPropagation();view=new Date(view.getFullYear(),view.getMonth()-1,1);drawCal();});hd.appendChild(pv);}
        if(k===1){var nx=document.createElement('button');nx.type='button';nx.className='cal-nav';nx.id='calNext';nx.textContent='›';
          nx.addEventListener('click',function(e){e.stopPropagation();view=new Date(view.getFullYear(),view.getMonth()+1,1);drawCal();});hd.appendChild(nx);}
        div.appendChild(hd);var g=document.createElement('div');g.className='cal-g';
        ['Mo','Tu','We','Th','Fr','Sa','Su'].forEach(function(d){var c=document.createElement('div');c.className='cal-dow';c.textContent=d;g.appendChild(c);});
        var first=(m.getDay()+6)%%7;for(var i=0;i<first;i++){g.appendChild(document.createElement('div'));}
        var days=new Date(m.getFullYear(),m.getMonth()+1,0).getDate();
        for(var d=1;d<=days;d++){(function(d){var dt=new Date(m.getFullYear(),m.getMonth(),d);var s=iso(dt);
          var b=document.createElement('button');b.type='button';b.className='cal-d';b.textContent=d;if(dt<today)b.disabled=true;
          if(q.ci&&q.co&&s>q.ci&&s<q.co)b.classList.add('rng');if(s===q.ci||s===q.co)b.classList.add('sel');
          b.addEventListener('click',function(e){e.stopPropagation();if(!q.ci||(q.ci&&q.co)){q.ci=s;q.co='';}else if(s<=q.ci){q.ci=s;q.co='';}else{q.co=s;}
            syncDates();drawCal();if(q.ci&&q.co){setTimeout(closeAll,350);}});g.appendChild(b);})(d);}
        div.appendChild(g);wrap.appendChild(div);}
      document.getElementById('calHint').textContent=!q.ci?'Select check-in date':(q.co?nice(q.ci)+' → '+nice(q.co):'Select check-out date');}
    function syncDates(){var vi=document.getElementById('hsInVal'),vo=document.getElementById('hsOutVal');
      vi.textContent=q.ci?nice(q.ci):'Add date';vi.classList.toggle('set',!!q.ci);vo.textContent=q.co?nice(q.co):'Add date';vo.classList.toggle('set',!!q.co);}
    function openCal(e){e.stopPropagation();drawCal();open('hsPopCal',['hsIn','hsOut']);}
    document.getElementById('hsIn').addEventListener('click',openCal);document.getElementById('hsOut').addEventListener('click',openCal);
    document.getElementById('calClear').addEventListener('click',function(e){e.stopPropagation();q.ci='';q.co='';syncDates();drawCal();});
    document.getElementById('hsPopCal').addEventListener('click',function(e){e.stopPropagation();});
    function syncG(){var v=document.getElementById('hsGuestsVal');v.textContent=q.g?q.g+' guest'+(q.g>1?'s':''):'Any';v.classList.toggle('set',!!q.g);
      document.getElementById('hsGn').textContent=q.g||'Any';document.getElementById('hsGm').disabled=!q.g;}
    document.getElementById('hsGuests').addEventListener('click',function(e){e.stopPropagation();open('hsPopGuests',['hsGuests']);});
    document.getElementById('hsPopGuests').addEventListener('click',function(e){e.stopPropagation();});
    document.getElementById('hsGm').addEventListener('click',function(){if(q.g>0)q.g--;syncG();});
    document.getElementById('hsGp').addEventListener('click',function(){if(q.g<16)q.g++;syncG();});
    document.addEventListener('click',closeAll);
    document.getElementById('hsGo').addEventListener('click',function(e){e.stopPropagation();closeAll();apply();
      var rb=document.querySelector('.cards-wrap');if(rb)rb.scrollIntoView({behavior:'smooth',block:'start'});});
    window.thbHeroSync=function(){syncDates();syncG();};
  }
  /* carry dates/guests to the villa page */
  var grid=document.getElementById('cardGrid');
  if(grid)grid.addEventListener('click',function(e){
    if(!q.ci&&!q.g)return; if(e.target.closest('.thb-fav'))return;
    var card=e.target.closest('.prop-card');if(!card)return;
    var m=(card.getAttribute('onclick')||'').match(/window\.location='([^']+)'/);if(!m)return;
    e.stopPropagation();e.preventDefault();window.location=m[1]+qs();
  },true);
  /* state from the URL, after thb-filters.js (deferred) has applied it */
  document.addEventListener('DOMContentLoaded',function(){
    try{
      var up=new URLSearchParams(location.search);
      if(IS_CAT){var l=(up.get('location')||'').split(',')[0],s=(up.get('sub')||'').split(',')[0];
        q.area=s?'phuket/'+s:(l||'');if(!NAMES.hasOwnProperty(q.area))q.area='';}
      if(up.get('checkin'))q.ci=up.get('checkin');if(up.get('checkout'))q.co=up.get('checkout');
      if(up.get('guests'))q.g=parseInt(up.get('guests'),10)||0;
      var ci=document.getElementById('thbCi'),co=document.getElementById('thbCo');if(ci&&q.ci)ci.value=q.ci;if(co&&q.co)co.value=q.co;
      var gn=document.getElementById('thbGn');if(gn&&q.g)gn.textContent=q.g;
      if(!IS_CAT&&q.g&&window.thbFilterApply)window.thbFilterApply();
      if(window.thbHeroSync)window.thbHeroSync();
      if(sheet)sheet.querySelectorAll('.tsh-chip').forEach(function(c){c.classList.toggle('on',c.getAttribute('data-area')===q.area);});
      syncUi();
      if(IS_CAT&&window.clearAllFilters){var ca=window.clearAllFilters;window.clearAllFilters=function(){q.area='';q.g=0;ca();syncUi();};}
      var on=document.querySelector('.thb-qchip.on'),box=document.getElementById('thbAreaChips');
      if(on&&box&&box.scrollWidth>box.clientWidth)box.scrollLeft=on.offsetLeft-box.offsetLeft-16;
    }catch(err){}
  });
})();
</script>'''

MOBILE_MENU_JS = '''<script>
(function(){
  var btn=document.getElementById('mobileMenuBtn'),menu=document.getElementById('mobileMenu'),
      b=document.getElementById('burgerIcon'),x=document.getElementById('closeIcon');
  if(!btn||!menu)return;
  function toggle(force){
    var open=typeof force==='boolean'?force:menu.classList.contains('hidden');
    menu.classList.toggle('hidden',!open);
    b.classList.toggle('hidden',open);
    x.classList.toggle('hidden',!open);
    btn.setAttribute('aria-expanded',open);
  }
  btn.addEventListener('click',function(){toggle()});
  menu.querySelectorAll('a').forEach(function(a){a.addEventListener('click',function(){toggle(false)})});
})();
</script>'''

# ------------------------------------------------------------------ page assembly
def assemble(tpl, title, desc, image, page_html, after_footer_html, jsonld, has_filters, has_map):
    s = rebrand(read_tpl(tpl), title=title, desc=desc, jsonld=jsonld, image=image)
    # reference mobile menu (Bali links) -> the thv nav's own menu + its toggle
    s = remove_el(s, r'<div id="thbMobileMenu"')
    s = re.sub(r"<script>\(function\(\)\{var b=document\.getElementById\('thbBurger'\).*?</script>\s*", '', s, flags=re.S)
    s = s.replace('</nav>', '</nav>\n' + MOBILE_MENU_JS, 1)
    # promo banner photo
    s = re.sub(r"url\('/public-objects/[^']+'\)", "url('%s')" % image, s)
    s = re.sub(r"(\.promo-banner::before\s*\{[^}]*?url\()'[^']+'", lambda m: m.group(1) + "'%s'" % image, s)
    # page body: everything between <!-- PAGE --> and the footer, keeping only the <style> blocks
    i, j = s.index('<!-- PAGE -->'), s.index('<footer class="thb-ft"')
    styles = ''.join(re.findall(r'<style[^>]*>.*?</style>\s*', s[i:j], flags=re.S))
    s = s[:i] + styles + PLACE_GRID_CSS + '\n' + page_html + '\n' + s[j:]
    # after the footer: drawer, sheet and the reference inline search scripts are replaced
    s = remove_el(s, r'<!-- FILTER DRAWER -->\s*<div id="filterDrawer">') if False else s
    s = re.sub(r'<!-- FILTER DRAWER -->\s*', '', s)
    s = remove_el(s, r'<div id="filterDrawer">')
    s = remove_el(s, r'<div id="thbSheet"')
    s = re.sub(r'<script>\s*\(function\(\)\{\s*var q=\{area.*?</script>\s*', '', s, flags=re.S)        # sheet
    s = re.sub(r'<script>\s*\(function\(\)\{\s*var IS_CAT=(?:true|false), CUR.*?</script>\s*', '', s, flags=re.S)  # chips
    s = re.sub(r"<script>\s*\(function\(\)\{\s*var root=document\.getElementById\('thbHeroSearch'\).*?</script>\s*", '', s, flags=re.S)
    for pat in (r'var q=\{area:', r'thb-qchip', r"getElementById\('thbHeroSearch'\)"):
        assert not re.search(r'<script>(?:(?!</script>).)*' + pat, s, flags=re.S), (tpl, pat)
    # scripts: no API-only or analytics/consent scripts on the static site
    s = re.sub(r'<script defer src="/thb-(bot|consent)\.js[^"]*"></script>\s*', '', s)
    s = re.sub(r'<script defer src="/thb-filters\.js[^"]*"></script>', '', s)
    tail = after_footer_html
    if has_filters:
        tail += '\n<script defer src="/thb-filters.js?v=thai1"></script>'
    if has_map:
        tail += '\n<script defer src="/thb-rent-map.js?v=thai1"></script>'
    s = s.replace('</body>', tail + '\n</body>', 1)
    return s

def faq_common(place, season, go, monthly_note=True):
    qa = [
        ('How do I book a villa in %s?' % place,
         'Open a villa, choose your dates and send the request &mdash; it comes straight to us on WhatsApp. We reply with availability '
         'and the price for your dates, and confirm everything in writing before you pay.'),
        ('Can I rent a villa in %s by the month?' % place,
         'Yes. Every villa is offered for daily stays, and many also for monthly or longer stays. Monthly rates and what they include '
         '(electricity, cleaning, pool care) are set per villa &mdash; filter by "Monthly" or ask us and we will list the options.'),
        ('When is the best time to stay in %s?' % place, season),
        ('How do I get to %s?' % place, go),
        ('Why do the villas show "On request" instead of a price?',
         'The villas shown are sample listings while we onboard properties, and rates depend on the dates and the length of stay. '
         'Send your dates and we will quote the exact price.'),
    ]
    return qa

# ------------------------------------------------------------------ 1. catalogue
def build_catalog():
    vs = VILLAS
    keys = [k for k in area_keys() if k[2] or k[0] in ('', 'phuket')]
    allkeys = area_keys()
    page = '<!-- PAGE -->\n<div style="padding-top:72px;min-height:100vh">\n\n'
    page += promo(None, '🌴 Book direct', 'Private pool villas for rent in Thailand',
                  'Phuket first &mdash; Bang Tao, Kata, Nai Harn and the rest of the west coast &mdash; plus Koh Samui, Pattaya and more. '
                  'Daily holidays or monthly stays, arranged with a real person on WhatsApp.', HERO_SEARCH)
    page += '\n' + pills_bar([(k, ('All Thailand' if not k else l), n, not k) for k, l, n in keys], 'Where in Thailand?')
    page += '\n' + results_bar('Thailand villa rentals', len(vs), '')
    page += '\n' + cards_wrap(vs) + '</div>\n\n'
    page += seo_section('th-rent-seo-title', 'Thailand villa rentals', 'Renting a pool villa in Thailand',
        ['This catalogue brings together private villas for rent across Thailand, starting with Phuket &mdash; the island with the widest '
         'choice of pool villas, from family houses in Bang Tao and Layan to sea-view homes above Kata and long-stay favourites in Nai Harn and Rawai. '
         'Koh Samui, Pattaya and other destinations are being added.',
         'Use the filters to narrow the list by beach area, bedrooms, guests, amenities and rental period. Every villa can be booked for a '
         'holiday by the night, and many also by the month; send the dates and we come back on WhatsApp with availability and the price.'],
        'Villas by destination',
        [(area_url('phuket'), 'Villas in Phuket')] + [(area_url('phuket', a['slug']), a['name']) for a in BEACHES[:6]]
        + [(area_url(d['slug']), d['name']) for d in OTHER[:3]] + [('/villas/', 'All destinations'), ('/monthly-rental/', 'Monthly rentals')],
        [('Daily or monthly', 'Two ways to rent: daily stays for holidays, and monthly stays for anyone spending a season in Thailand. '
          'Monthly rates are set per villa and cover a fixed term with the conditions spelled out in the quote.'),
         ('When to come', 'On Phuket, Krabi and the Andaman coast the dry, calm season runs from November to April. Koh Samui and Koh Phangan '
          'are usually driest from about January to August, and Chiang Mai is most pleasant from November to February.'),
         ('How booking works', 'Pick a villa, choose dates and send the request &mdash; it lands on our WhatsApp. We confirm availability, '
          'the total and the conditions in writing before anything is paid. Nothing is charged on this website.')])
    qa = [
        ('How do I book a villa in Thailand?', 'Open a villa page, choose your dates and guests and send the request. It comes straight to our WhatsApp and we reply with availability and the price for those dates.'),
        ('Which area of Phuket is best for a villa?', 'Bang Tao and Layan suit families and groups who want space and amenities; Kata and Karon are sociable beach towns; Nai Harn and Rawai are favourites for long stays; Mai Khao is quiet and close to the airport. Each beach has its own page with the villas there.'),
        ('Can I rent a villa by the month?', 'Yes. Choose "Monthly" in the filters to see villas offered for monthly stays, or see the monthly rentals guide. Monthly rates and what they include are set per villa.'),
        ('Why is the price "On request"?', 'The villas shown are sample listings while we onboard properties, and rates depend on dates and length of stay. Send your dates and we quote the exact price.'),
        ('Do you offer anything besides villas?', 'Yes &mdash; yacht charters, helicopter flights, supercars, superbikes and concierge services in Phuket. See the VIP section.'),
    ]
    page += faq_section('Thailand', 'Renting a villa in Thailand — FAQ', qa)
    page += more_places('Browse by place', [(area_url('phuket'), 'Phuket')] + [(area_url('phuket', a['slug']), a['name']) for a in BEACHES]
                        + [(area_url(d['slug']), d['name']) for d in OTHER] + [('/vip/', 'VIP services')])
    tail = drawer(vs, True) + '\n' + sheet(allkeys, '', 'Where in Thailand?') + '\n' + PAGE_JS % dict(
        is_cat='true', cur='""', keys=json.dumps(allkeys, ensure_ascii=False))
    ld = [crumbs_ld([('Home', '/'), ('Villas for rent in Thailand', '/property-rental/')]), faq_ld(qa),
          {"@context": "https://schema.org", "@type": "ItemList", "name": "Villas for rent in Thailand", "numberOfItems": len(vs),
           "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": v['name'], "url": v['url']} for i, v in enumerate(vs)]}]
    s = assemble('property-rental/index.html', 'Villas for Rent in Thailand — Phuket Pool Villas, Daily & Monthly | Thai Villas',
                 'Private pool villas for rent in Phuket and across Thailand. Filter by beach, bedrooms, guests and daily or monthly stays; book on WhatsApp.',
                 '/images/hero.jpg', page, tail, ld, True, True)
    write('property-rental/index.html', s)

# ------------------------------------------------------------------ 2. destinations hub
def build_hub():
    page = '<!-- PAGE -->\n<div style="padding-top:72px;min-height:100vh">\n\n'
    page += promo([('Home', '/'), ('Villas', '/villas/')], '📍 By destination', 'Villas in Thailand, by destination',
                  'Start with Phuket and its beaches, or pick another part of the country. Each page shows the villas there, '
                  'what the area is like and when to go.', '')
    page += f'''
  <!-- RESULTS BAR -->
  <div class="results-bar">
    <div>
      <p style="font-size:12px;color:#6b6b66;text-transform:uppercase;letter-spacing:0.18em;font-weight:600;margin-bottom:3px">Where to stay</p>
      <p style="font-family:'Lora',Georgia,serif;font-size:26px;font-weight:700" id="resultsTitle">Phuket, 12 beaches and {len(OTHER)} more destinations</p>
    </div>
  </div>
'''
    sub = lambda t: ('<div style="grid-column:1/-1;margin:18px 0 0"><h2 style="%s">%s</h2></div>' % (H2 % (24, 0), t))
    ph = PHUKET
    grid = (place_card(area_url('phuket'), ph['image'], 'Phuket', 'Main destination', count('phuket'), ph['short'], 'See all Phuket villas')
            + sub('Phuket beaches') + ''.join(beach_card(a) for a in BEACHES)
            + sub('More of Thailand') + ''.join(dest_card(d) for d in OTHER)
            + f'''<div class="prop-card" style="cursor:default;grid-column:1/-1">
          <div style="padding:24px">
            <p style="font-family:'Lora',Georgia,serif;font-size:19px;font-weight:700;margin-bottom:6px">Not fussy about the area?</p>
            <p style="font-size:14px;line-height:1.7;color:#4b4b45;margin:0 0 14px">Open the full catalogue and filter by bedrooms, guests, amenities and daily or monthly stays instead &mdash; all {pl(len(VILLAS))} in one list.</p>
            <a href="/property-rental/" style="display:inline-flex;height:44px;align-items:center;padding:0 20px;border-radius:999px;background:#0a0a0a;color:#fff;text-decoration:none;font-weight:600;font-size:14px">See all {pl(len(VILLAS))} →</a>
          </div>
        </div>''')
    page += f'''
  <!-- CARDS GRID -->
  <div class="cards-wrap">
    <div id="cardGrid" style="display:grid;grid-template-columns:repeat(4,1fr);gap:20px">{grid}</div>
  </div>
</div>

'''
    page += seo_section('areas-seo-title', 'Where to stay in Thailand', 'Phuket first, then the rest of Thailand',
        ['Phuket has the largest choice of private pool villas in the country, spread along a west coast of very different beaches: '
         'quiet Mai Khao and Layan in the north, the villa neighbourhoods of Bang Tao and Surin, lively Patong, family-friendly Karon and Kata, '
         'and the long-stay south around Nai Harn, Rawai and Chalong.',
         'Beyond Phuket, Koh Samui and Koh Phangan in the Gulf of Thailand have their dry season when the Andaman coast is green; Krabi shares '
         'Phuket\'s rhythm; Pattaya and Hua Hin are easy drives from Bangkok; and Bangkok and Chiang Mai are city bases for monthly living.'],
        'Popular destinations', [(area_url('phuket'), 'Phuket')] + [(area_url('phuket', a['slug']), a['name']) for a in BEACHES[:6]]
        + [(area_url(d['slug']), d['name']) for d in OTHER] + [('/property-rental/', 'All villas')],
        [('Beach holidays', 'For a classic beach holiday, choose a Phuket west-coast beach between November and April, or Koh Samui from January to August.'),
         ('Long stays', 'For a month or more, Nai Harn, Rawai, Chalong and Bang Tao on Phuket, plus Koh Phangan, Pattaya, Bangkok and Chiang Mai, are the usual choices.'),
         ('Not sure?', 'Tell us who is travelling, your dates and what matters most &mdash; we will suggest the area and the villas that fit.')])
    qa = [('Which destination is best for a villa holiday in Thailand?', 'Phuket offers the widest choice of pool villas and beaches. Koh Samui is a good alternative, especially from January to August when its weather is at its best.'),
          ('Where do people stay for a month or longer?', 'On Phuket, Nai Harn, Rawai, Chalong and Bang Tao are the most popular long-stay areas. Koh Phangan, Pattaya, Bangkok and Chiang Mai are also common monthly bases.'),
          ('Can you help me choose an area?', 'Yes &mdash; message us on WhatsApp with your dates, the group and what you want nearby, and we will suggest areas and villas.')]
    page += faq_section('destinations', 'Choosing a destination — FAQ', qa)
    ld = [crumbs_ld([('Home', '/'), ('Villas by destination', '/villas/')]), faq_ld(qa)]
    s = assemble('villas/index.html', 'Villas in Thailand by Destination — Phuket Beaches, Samui & More | Thai Villas',
                 'Pick where to stay: Phuket and its 12 beach areas, Koh Samui, Pattaya, Bangkok, Krabi, Koh Phangan, Hua Hin and Chiang Mai.',
                 '/images/all-thailand.jpg', page, '', ld, False, True)
    write('villas/index.html', s)

# ------------------------------------------------------------------ 3-5. area pages (canonical area design)
def area_page(rel, place, kicker, crumbs, h1, sub, image, vs, chip_list, cur, sheet_keys, sheet_title, seo_html, qa,
              extra_html, title, desc, empty_html, fullplace=None):
    fullplace = fullplace or place
    code = '<div class="promo-code">Villas in <strong>%s</strong> &middot; daily &amp; monthly</div>' % fullplace
    page = '<!-- PAGE -->\n<div style="padding-top:72px;min-height:100vh">\n\n'
    page += promo(crumbs, kicker, h1, sub, code)
    page += '\n' + pills_bar(chip_list, sheet_title, tools=bool(vs))
    page += '\n' + results_bar('%s villa rentals' % place, len(vs), ' in %s' % place)
    page += '\n' + cards_wrap(vs, empty_html) + '</div>\n\n'
    page += extra_html + seo_html + faq_section(place, '%s villa rental — FAQ' % place, qa)
    tail = (drawer(vs, False) + '\n' if vs else '') + sheet(sheet_keys, cur, sheet_title) + '\n' + PAGE_JS % dict(
        is_cat='false', cur=json.dumps(cur), keys=json.dumps(sheet_keys, ensure_ascii=False))
    ld = [crumbs_ld(crumbs), faq_ld(qa)]
    if vs:
        ld.append({"@context": "https://schema.org", "@type": "ItemList", "name": "Villas for rent in %s" % re.sub('<[^>]+>', '', fullplace),
                   "numberOfItems": len(vs), "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": v['name'], "url": v['url']}
                                                                 for i, v in enumerate(vs)]})
    s = assemble('villas/umalas/index.html', title, desc, image, page, tail, ld, bool(vs), bool(vs))
    write(rel, s)

def phuket_keys():
    return [('phuket', 'All Phuket', count('phuket'))] + [('phuket/' + a['slug'], a['name'], count('phuket', a['slug'])) for a in BEACHES]

def build_phuket():
    vs = [v for v in VILLAS if v['areaSlug'] == 'phuket']
    keys = phuket_keys()
    beaches = place_grid_section('Phuket beaches', 'Twelve areas, each with its own page and villas. Pick the one that fits the trip.',
                                 ''.join(beach_card(a) for a in BEACHES), 'phuket-beaches-title')
    seo = seo_section('phuket-seo-title', 'Phuket villa rentals', 'Renting a villa in Phuket',
        ['Phuket is Thailand\'s largest island and the country\'s main villa destination. Almost all of the beaches face west onto the Andaman Sea, '
         'so sunsets come with the view, and the choice runs from compact pool townhouses to hillside estates with staff.',
         'The north-west &mdash; Mai Khao, Nai Yang, Layan, Bang Tao and Surin &mdash; is quieter and close to the airport, with Bang Tao\'s Cherng Talay '
         'as the island\'s villa capital. The middle of the coast is the busiest: Kamala, Patong, Karon and Kata. The south &mdash; Kata Noi, Nai Harn, Rawai '
         'and Chalong &mdash; is greener and calmer, and the favourite of long-stay guests.',
         'High season runs from November to April, with calm seas and dry weather; the green season from May to October brings showers and swell on the '
         'west coast, but also more choice and a quieter island. Villas can be rented daily for a holiday or monthly for a season.'],
        'Popular Phuket searches', [(area_url('phuket', a['slug']), 'Villas in ' + a['name']) for a in BEACHES[:8]]
        + [('/property-rental/?location=phuket&period=monthly', 'Monthly villas in Phuket'), ('/monthly-rental/phuket/', 'Phuket long-stay guide'),
           ('/property-rental/?location=phuket', 'Filter all Phuket villas')],
        [('West coast beaches', 'Bang Tao, Surin and Kamala combine beaches with full neighbourhoods; Patong is the nightlife centre; Karon and Kata are sociable, '
          'walkable beach towns, with surf at Kata from May to October.'),
         ('North and south', 'Mai Khao, Nai Yang and Layan in the north are quiet and 5&ndash;25 minutes from the airport. Nai Harn, Rawai and Chalong in the south '
          'are about an hour away, with island boats, markets and a big long-stay community.'),
         ('Seasons', STD_SEASON),
         ('Daily or monthly', 'Daily stays suit holidays of a few days to a few weeks. Monthly stays are priced per villa for a month or more &mdash; popular in '
          'Bang Tao, Nai Harn, Rawai and Chalong, especially in the green season.'),
         ('Getting around', 'Phuket International Airport is in the north of the island. A car or scooter is the practical way to get around; taxis and ride-hailing '
          'apps work across the island, and we can arrange transfers.'),
         ('How to book', 'Open a villa, choose dates and send the request &mdash; it comes to our WhatsApp. We confirm availability and the price for your dates '
          'before anything is paid.')])
    qa = faq_common('Phuket', 'November to April is high season, with calm seas and dry weather on the west coast. May to October is the green season: '
                    'showers, surf at Kata and Karon, and quieter beaches &mdash; good for monthly stays.',
                    'Phuket International Airport is in the north of the island, with domestic and international flights. Mai Khao and Layan are 5&ndash;25 minutes away, '
                    'Bang Tao about 30, Patong about 45 and the southern beaches about an hour by car.')
    qa.insert(2, ('Which Phuket beach is best for a villa?', 'For families and amenities, Bang Tao and Layan; for a lively beach town, Kata and Karon; for nightlife, Patong; '
                  'for long stays, Nai Harn, Rawai and Chalong; for peace and quick airport access, Mai Khao and Nai Yang.'))
    other = more_places('Other destinations in Thailand', [(area_url(d['slug']), 'Villas in ' + d['name']) for d in OTHER] + [('/villas/', 'All destinations'), ('/vip/', 'VIP services in Phuket')])
    area_page('villas/phuket/index.html', 'Phuket', '🌴 Phuket villa rentals',
              [('Home', '/'), ('Villas', '/villas/'), ('Phuket', '/villas/phuket/')],
              'Villas for rent in <em>Phuket</em>', 'Pool villas along the west coast &mdash; from quiet Mai Khao and Bang Tao to Kata and the long-stay south',
              '/images/phuket.jpg', vs, [(k, l, n, k == 'phuket') for k, l, n in keys], 'phuket', keys, 'Where in Phuket?',
              seo + other, qa, beaches,
              'Villas for Rent in Phuket — Pool Villas by Beach, Daily & Monthly | Thai Villas',
              'Private pool villas for rent in Phuket: Bang Tao, Layan, Surin, Kamala, Patong, Karon, Kata, Nai Harn, Rawai and more. Daily or monthly, book on WhatsApp.',
              '')

def build_beach(a):
    slug, name = a['slug'], a['name']
    t = BEACH_TXT[slug]
    vs = [v for v in VILLAS if v['areaSlug'] == 'phuket' and v.get('subAreaSlug') == slug]
    keys = phuket_keys()
    near = nearby(slug)
    near_with = sorted(nearby(slug, 11), key=lambda b: (count('phuket', b['slug']) == 0, km(a, b)))[:4]
    empty = empty_state(name, [(area_url('phuket', b['slug']), '%s <b style="font-weight:400;color:#8a877f">%d</b>' % (b['name'], count('phuket', b['slug'])))
                               for b in near_with] + [(area_url('phuket'), 'All Phuket villas')])
    seo = seo_section('%s-seo-title' % slug, '%s villa rentals' % name, 'Villas in %s, Phuket' % name, t['p'],
        'Nearby beaches', [(area_url('phuket', b['slug']), 'Villas in ' + b['name']) for b in near]
        + [('/property-rental/?sub=%s' % slug, 'Filtered catalogue'), (area_url('phuket'), 'All Phuket villas'), ('/monthly-rental/phuket/', 'Monthly in Phuket')],
        [('Who is %s for?' % name, t['who']), ('Getting there', t['go']), ('When to go', t['season'])])
    qa = faq_common(name, t['season'], t['go'])
    qa.insert(2, ('What is %s like?' % name, re.sub(r'<[^>]+>', '', t['p'][0])))
    others = more_places('Other Phuket beaches', [(area_url('phuket', b['slug']), b['name']) for b in BEACHES if b['slug'] != slug]
                         + [(area_url('phuket'), 'All Phuket'), ('/villas/', 'All destinations')])
    n = len(vs)
    area_page('villas/phuket/%s/index.html' % slug, name, '🌴 %s, Phuket' % name,
              [('Home', '/'), ('Villas', '/villas/'), ('Phuket', '/villas/phuket/'), (name, area_url('phuket', slug))],
              'Villas for rent in <em>%s</em>, Phuket' % name, esc(a['short']), a['image'], vs,
              [(k, l, c, k == 'phuket/' + slug) for k, l, c in keys], 'phuket/' + slug, keys, 'Where in Phuket?',
              seo + others, qa, '',
              'Villas for Rent in %s, Phuket — Pool Villas, Daily & Monthly | Thai Villas' % name,
              ('%s for rent in %s, Phuket. ' % (pl(n, 'private villa'), name) if n else 'Private villas for rent in %s, Phuket. ' % name)
              + re.sub(r'<[^>]+>|&[a-z]+;', '', a['short']) + ' Daily or monthly, book on WhatsApp.',
              empty, '%s, Phuket' % name)

def build_dest(d):
    slug, name = d['slug'], d['name']
    t = DEST_TXT[slug]
    vs = [v for v in VILLAS if v['areaSlug'] == slug]
    keys = [('', 'All Thailand', len(VILLAS)), ('phuket', 'Phuket', count('phuket'))] + [(o['slug'], o['name'], count(o['slug'])) for o in OTHER]
    empty = empty_state(name, [(area_url(o['slug']), '%s <b style="font-weight:400;color:#8a877f">%d</b>' % (o['name'], count(o['slug'])))
                               for o in sorted(AREAS, key=lambda o: (count(o['slug']) == 0, km(d, o))) if o['slug'] != slug][:4])
    seo = seo_section('%s-seo-title' % slug, t['tag'], 'Villas in %s, Thailand' % name, t['p'],
        'More destinations', [(area_url('phuket'), 'Villas in Phuket')] + [(area_url(o['slug']), 'Villas in ' + o['name']) for o in OTHER if o['slug'] != slug]
        + [('/property-rental/?location=%s' % slug, 'Filtered catalogue')]
        + ([('/monthly-rental/%s/' % slug, 'Monthly in %s' % name)] if slug in ('koh-samui', 'pattaya', 'bangkok', 'chiang-mai') else []),
        [('Who is %s for?' % name, t['who']), ('Getting there', t['go']), ('When to go', t['season'])])
    qa = faq_common(name, t['season'], t['go'])
    qa.insert(2, ('What is %s like?' % name, re.sub(r'<[^>]+>', '', t['p'][0])))
    others = more_places('Phuket beaches', [(area_url('phuket', b['slug']), b['name']) for b in BEACHES] + [('/villas/', 'All destinations')])
    n = len(vs)
    area_page('villas/%s/index.html' % slug, name, '🌴 ' + t['tag'],
              [('Home', '/'), ('Villas', '/villas/'), (name, area_url(slug))],
              'Villas for rent in <em>%s</em>' % name, t['sub'], d['image'], vs,
              [(k, ('All Thailand' if not k else l), c, k == slug) for k, l, c in keys], slug, keys, 'Where in Thailand?',
              seo + others, qa, '',
              'Villas for Rent in %s, Thailand — Daily & Monthly | Thai Villas' % name,
              ('%s for rent in %s. ' % (pl(n, 'private villa'), name) if n else 'Private villas for rent in %s, Thailand. ' % name)
              + d['short'] + ' Daily or monthly, book on WhatsApp.', empty, '%s, Thailand' % name)

if __name__ == '__main__':
    build_catalog()
    build_hub()
    build_phuket()
    for a in BEACHES:
        build_beach(a)
    for d in OTHER:
        build_dest(d)
    print('ok: property-rental, villas hub, phuket hub, %d beaches, %d destinations' % (len(BEACHES), len(OTHER)))
