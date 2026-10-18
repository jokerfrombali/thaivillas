#!/usr/bin/env python3
"""/vip/ hub + /vip/{yachts,helicopters,supercars,superbikes,concierge}/ from data/vip.json.

No partner names, fleet models or prices exist yet: everything is "On request" via WhatsApp.
Run from the site root: python3 -I tools/thai/build_vip.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from w4_shell import *  # noqa: F401,F403

C = {c['slug']: c for c in VIP}

# Per-category copy (general, no named operators or models)
EXTRA = {
    'yachts': {
        'title': 'Yacht Charter in Phuket — Phang Nga Bay, Phi Phi, Racha | Thai Villas VIP',
        'h1': 'Yacht charter <i>from Phuket.</i>',
        'lead': 'Speedboats, sailing catamarans and crewed motor yachts for a day, a sunset or several days among the islands of the Andaman Sea.',
        'ideas': [
            ('Phang Nga Bay', 'Limestone islands rising straight out of calm, emerald water, sea caves and lagoons explored by canoe. Usually sheltered, even in the green season.'),
            ('Phi Phi Islands', 'The classic day out: dramatic cliffs, clear water and snorkelling stops around Phi Phi Don and Phi Phi Leh.'),
            ('Racha Islands', 'South of Phuket, with white sand and some of the clearest water near the island — great for snorkelling and swimming.'),
            ('Coral Island', 'A short hop from Chalong: easy, relaxed and ideal with children or for a half day on the water.'),
            ('Sunset cruise', 'A couple of hours along the west coast or around Promthep Cape with drinks on deck as the sun goes down.'),
        ],
        'faq': [
            ('When is the best season for a yacht charter?', 'On the Andaman coast the sea is usually calmest from about November to April. In the green season (May to October) the west coast can be rough, but sheltered routes such as Phang Nga Bay often still run. The captain always has the final word on safety.'),
            ('What happens if the weather is bad?', 'If the captain decides conditions are unsafe, the trip is moved to another day or another route. How cancellations are handled is confirmed with your booking.'),
            ('Is a deposit required?', 'Usually yes — the amount and terms depend on the boat and the length of the charter, and are confirmed in writing before you pay.'),
            ('Are national park fees included?', 'Some islands are in marine national parks with entry fees. Whether they are included is confirmed with each offer.'),
        ],
        'wa': "Hi Thai Villas! I'd like to charter a yacht in Phuket.",
    },
    'helicopters': {
        'title': 'Helicopter Flights & Transfers in Phuket | Thai Villas VIP',
        'h1': 'Helicopter flights <i>over Phuket.</i>',
        'lead': 'Scenic flights over the beaches and Phang Nga Bay, and private transfers between Phuket and the islands or the mainland.',
        'ideas': [
            ('Scenic island flight', 'The west-coast beaches, the Big Buddha and the southern capes from above — a short flight with a big view.'),
            ('Phang Nga Bay from the air', 'Hundreds of limestone islands seen from above: one of the most striking flights in Thailand.'),
            ('Transfer to Krabi', 'Skip the drive and the ferry — across the bay in a fraction of the time.'),
            ('Transfer to Koh Samui or Bangkok', 'Longer private transfers across the country, arranged on request.'),
        ],
        'faq': [
            ('Where does the helicopter take off and land?', 'From approved helipads and airports. Landing at a private villa needs suitable space and permission, so we check each case before confirming.'),
            ('What about the weather?', 'Flights depend on visibility and weather. If the pilot decides it is not safe, the flight is rescheduled; the terms are confirmed with your booking.'),
            ('Are there weight or luggage limits?', 'Yes — helicopters have passenger and luggage limits. Tell us the number of people and bags and we\'ll confirm what is possible.'),
            ('Is a deposit required?', 'Usually yes. Payment and cancellation terms are confirmed in writing before anything is paid.'),
        ],
        'wa': "Hi Thai Villas! I'm interested in a helicopter flight in Phuket.",
    },
    'supercars': {
        'title': 'Supercar & Luxury Car Rental in Phuket | Thai Villas VIP',
        'h1': 'Supercars <i>delivered to your villa.</i>',
        'lead': 'Supercars, convertibles and premium SUVs brought to your door — drive yourself or sit back with a chauffeur.',
        'ideas': [
            ('Delivered to the villa', 'The car arrives at your villa with a handover, and is collected at the end — no rental desk.'),
            ('With a chauffeur', 'Dinner, a beach club or a day of sightseeing without worrying about parking or the drive back.'),
            ('Airport pick-up in style', 'Start the holiday the right way: met at the airport and driven straight to the villa.'),
            ('Coastal drive', 'The west-coast road between the beaches and the viewpoints in the south make a beautiful half-day drive.'),
        ],
        'faq': [
            ('What licence do I need to drive?', 'You need a valid driving licence and, for most visitors, an International Driving Permit. Requirements and minimum age can vary by car — we confirm before booking.'),
            ('Is there a security deposit?', 'Yes, a security deposit is normal for premium cars. The amount and how it is held are confirmed in writing before you pay.'),
            ('Is insurance included?', 'Insurance terms differ from car to car; what is covered and the excess are confirmed with each offer.'),
            ('Can I have a driver instead?', 'Yes — most cars can be booked with a chauffeur by the hour or the day.'),
        ],
        'wa': "Hi Thai Villas! I'd like to rent a supercar in Phuket.",
    },
    'superbikes': {
        'title': 'Superbike & Premium Bike Rental in Phuket | Thai Villas VIP',
        'h1': 'Superbikes <i>for island roads.</i>',
        'lead': 'Big bikes, touring bikes and premium scooters delivered to your villa with helmets — or join a guided ride.',
        'ideas': [
            ('Delivered with helmets', 'The bike comes to your villa with proper helmets and a handover; collected at the end of the rental.'),
            ('Guided ride', 'Ride with someone who knows the roads, the viewpoints and where to stop for lunch.'),
            ('Premium scooter for the stay', 'An easy, comfortable way to get to the beach and the cafés every day.'),
            ('Touring day', 'Hills, viewpoints and quiet roads on the island and across the bridge to the mainland.'),
        ],
        'faq': [
            ('Do I need a motorcycle licence?', 'Yes. To ride legally in Thailand you need a motorcycle licence valid for the bike\'s class — for most visitors a home licence with a motorcycle endorsement plus an International Driving Permit. Without it, insurance may not cover you. Check the current rules before you ride.'),
            ('Are helmets provided?', 'Yes, helmets are always provided, and wearing one is required by law.'),
            ('Is there a deposit?', 'A security deposit is normal for big bikes. The amount and terms are confirmed in writing before you pay.'),
            ('Is it safe to ride in Phuket?', 'Roads can be busy and hilly, and tropical rain makes them slippery. We recommend big bikes only to experienced riders — a guided ride is a good way to start.'),
        ],
        'wa': "Hi Thai Villas! I'd like to rent a superbike in Phuket.",
    },
    'concierge': {
        'title': 'Luxury Villa Concierge in Phuket — Private Chef, Spa, Events | Thai Villas VIP',
        'h1': 'Luxury concierge <i>at your villa.</i>',
        'lead': 'Private chef, in-villa spa, celebrations, childcare, security and reservations — arranged around your stay.',
        'ideas': [
            ('Private chef dinner', 'Thai or international menus cooked in your villa kitchen and served on the terrace.'),
            ('Spa day at the villa', 'Massage and treatments by the pool, without leaving the villa.'),
            ('Celebration set-up', 'Birthdays, anniversaries, proposals: decoration, cake, music and a photographer.'),
            ('Ready on arrival', 'Groceries stocked, cots and high chairs in place, transfers waiting at the airport.'),
            ('Tables & tickets', 'Reservations at restaurants and beach clubs, and help planning day trips.'),
        ],
        'faq': [
            ('How far in advance should I book?', 'As early as you can, especially in the high season (roughly November to April). Some things can be arranged the same day — just ask.'),
            ('Can services be added during the stay?', 'Yes. Message us on WhatsApp at any time and we\'ll arrange what is possible.'),
            ('How is it paid?', 'Each service is quoted separately and confirmed in writing before you pay.'),
            ('Do I need to rent a villa with you?', 'Concierge works best together with a villa stay, but ask us — we\'ll tell you what is possible.'),
        ],
        'wa': "Hi Thai Villas! I'd like to arrange concierge services for my villa stay.",
    },
}

CAT_ICON = {'yachts': 'globe', 'helicopters': 'star', 'supercars': 'bolt', 'superbikes': 'bolt', 'concierge': 'home'}

HOW = [
    ('Tell us the date & group size', 'Send the date, how many people and what you have in mind — on WhatsApp or with the form.'),
    ('We propose options', 'We come back with options from vetted local partners, with what is included and the price for your date.'),
    ('Confirm on WhatsApp', 'Pick the option you like and confirm on WhatsApp. One contact for everything, before and during your stay.'),
]

def short_name(c):
    return c['name'].split(' &')[0].replace(' rental', '')

def cat_card(c, cls=''):
    return ('<a class="w4-pcard %s" href="/vip/%s/"><img src="%s" alt="%s in Phuket" loading="lazy" decoding="async" width="900" height="1100">'
            '<span class="cnt">On request</span><div class="in"><h3>%s</h3><p>%s</p><span class="go">Explore %s</span></div></a>'
            % (cls, c['slug'], c['image'], esc(c['name']), esc(c['name']), esc(c['short']), ICON['arrow'].replace('<svg', '<svg width="14" height="14"')))

def lux_villas():
    vs = [v for v in VILLAS if 'luxury' in v.get('filterTags', [])]
    return '<div class="w4-cards">' + ''.join(villa_card(v) for v in vs) + '</div>'

def form(c=None):
    opts = (c['options'] if c else [short_name(x) for x in VIP])
    title = ("Hi Thai Villas! VIP enquiry — %s" % c['name']) if c else "Hi Thai Villas! VIP enquiry"
    sel = ''.join('<option>%s</option>' % esc(o) for o in opts)
    return ('<form class="w4-form" data-wa-form="%s">'
            '<div class="row"><div><label for="vd">Date</label><input id="vd" type="date" data-label="Date"></div>'
            '<div><label for="vg">Group size</label><input id="vg" type="number" min="1" max="200" inputmode="numeric" placeholder="e.g. 6" data-label="Group size"></div></div>'
            '<label for="vo">%s</label><select id="vo" data-label="Interested in"><option value="">Choose…</option>%s</select>'
            '<label for="vn">Anything else?</label><textarea id="vn" placeholder="Times, where you are staying, special requests" data-label="Notes"></textarea>'
            '<button class="w4-btn wa" type="submit">%sSend on WhatsApp</button>'
            '<p class="fine">Opens WhatsApp with your message ready to send. Nothing is stored on this site.</p></form>'
            % (esc(title), 'What would you like?' if c else 'Service', sel, ICON['wa']))

# ------------------------------------------------------------------ hub
def build_hub():
    body = hero('/images/vip/yacht.jpg', 'Thai Villas VIP',
                'Yachts, helicopters <i>&amp; supercars.</i>',
                'The extras that turn a villa holiday into something else: yacht charters, helicopter flights, supercars and superbikes delivered to your door, '
                'and a concierge for everything in between. Arranged with vetted local partners, on request.',
                wa_btn("Hi Thai Villas! I'm interested in your VIP services.", 'Ask on WhatsApp') + btn('#services', 'See services', 'ghost'),
                chips=['Phuket', 'On request', 'One contact'], alt='Yacht on the Andaman Sea near Phuket')
    body += '<div class="w4-wrap">' + crumbs_html([('Home', '/'), ('VIP', '/vip/')]) + '</div>'
    cards = ''.join(cat_card(c) for c in VIP)
    body += section('VIP services', 'Five ways <i>to go further</i>',
                    '<div class="w4-grid" style="grid-template-columns:repeat(auto-fill,minmax(250px,1fr))">' + cards + '</div>',
                    sub='Every service is arranged to your date and group — prices on request.', sid='services')
    body += section('How it works', 'Three messages, <i>no paperwork</i>', steps(HOW, s3=True)
                    + '<div class="w4-btns" style="margin-top:30px">%s</div>' % wa_btn("Hi Thai Villas! I'm interested in your VIP services.", 'Start on WhatsApp'),
                    sub='You talk to one person who knows the partners and the island.', cls='ink')
    combo = ('<div class="w4-split"><div><p class="w4-sub" style="margin-bottom:22px">Stay in a luxury pool villa and let us line up the yacht, the car and the chef around it. '
             'One conversation covers the villa and every extra.</p><div class="w4-btns">%s%s</div></div>'
             '<div class="w4-img"><img src="/images/villas/ext-2.jpg" alt="Luxury pool villa in Phuket" loading="lazy" decoding="async" width="1200" height="900"></div></div>'
             '<div style="margin-top:40px">%s%s</div>'
             % (btn('/property-rental/?vibe=luxury', 'Luxury villas', 'dark'), wa_btn("Hi Thai Villas! I'd like a luxury villa plus VIP services.", 'Plan it on WhatsApp', 'light'),
                '<p class="w4-sample">Listings shown are sample villas while the site is in preview.</p>', lux_villas()))
    body += section('Villa + VIP', 'Combine it <i>with a luxury villa</i>', combo, cls='paper')
    body += section('Enquiry', 'Tell us <i>what you have in mind</i>',
                    '<div class="w4-split top"><div class="w4-prose"><p>Pick a service, a date and the size of your group. The form opens WhatsApp with the message written — '
                    'you just press send. We reply with options for your date.</p><p>Prefer to talk? Message us directly at '
                    '<a href="%s" rel="noopener">%s</a>.</p></div>%s</div>' % (WA, esc(PHONE), form()), sid='enquiry')
    fq = [
        ('How much do VIP services cost?', 'Prices depend on the date, duration, group size and the exact option, so everything is quoted on request. Tell us what you have in mind and we\'ll send options with prices.'),
        ('Who provides the services?', 'Vetted local partners — licensed operators for boats, aircraft and vehicles. We arrange it and stay your single point of contact.'),
        ('Do I need a licence to drive a supercar or ride a superbike?', 'Yes — a valid licence for the vehicle class and, for most visitors, an International Driving Permit. We confirm the requirements for each vehicle before booking.'),
        ('Is a deposit required?', 'Often yes, especially for yachts and premium vehicles. Amounts and cancellation terms are confirmed in writing before you pay.'),
        ('What if the weather is bad?', 'Sea and air activities depend on the weather and the captain\'s or pilot\'s decision. If it is not safe, we move it to another day or route; terms are confirmed with each booking.'),
    ]
    fh, fld = faq(fq)
    body += section('Questions', 'VIP services: <i>your questions</i>', fh, narrow=True, cls='paper', sid='faq')
    body += final('Thai Villas VIP', 'Make it unforgettable.',
                  'Send the date and the group size — we\'ll come back with options from our partners.',
                  wa_btn("Hi Thai Villas! I'm interested in your VIP services.") + btn('/property-rental/?vibe=luxury', 'Luxury villas', 'ghost'), ink=True)
    ld = [fld, crumbs_ld([('Home', '/'), ('VIP', '/vip/')]),
          {"@context": "https://schema.org", "@type": "ItemList", "name": "Thai Villas VIP services",
           "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": '/vip/%s/' % c['slug'], "name": c['name']} for i, c in enumerate(VIP)]}]
    write('vip/index.html', page('VIP Services in Phuket — Yachts, Helicopters, Supercars | Thai Villas',
          'Yacht charter, helicopter flights, supercar and superbike rental and luxury concierge in Phuket — arranged with vetted partners. Prices on request via WhatsApp.',
          body, ld, '/images/vip/yacht.jpg', extra=wa_form_script()))

# ------------------------------------------------------------------ category pages
def build_cat(c):
    x = EXTRA[c['slug']]
    url = '/vip/%s/' % c['slug']
    body = hero(c['image'], 'Thai Villas VIP · %s' % esc(short_name(c)), x['h1'], x['lead'],
                wa_btn(x['wa'], 'Ask on WhatsApp') + btn('#enquiry', 'Send an enquiry', 'ghost'),
                chips=['On request', 'Vetted partners'], short=True, alt='%s in Phuket' % c['name'])
    body += '<div class="w4-wrap">' + crumbs_html([('Home', '/'), ('VIP', '/vip/'), (c['name'], url)]) + '</div>'
    imgs = [c['image']] + c['gallery']
    if len(imgs) >= 3:
        gal = ('<div class="w4-gal"><img src="%s" alt="%s" loading="lazy" decoding="async" width="1400" height="875"><div class="side">%s</div></div>'
               % (imgs[0], esc(c['name']), ''.join('<img src="%s" alt="%s" loading="lazy" decoding="async" width="700" height="440">' % (i, esc(c['name'])) for i in imgs[1:3])))
    elif len(imgs) == 2:
        gal = '<div class="w4-grid g2">' + ''.join('<div class="w4-img"><img src="%s" alt="%s" loading="lazy" decoding="async" width="1200" height="900"></div>' % (i, esc(c['name'])) for i in imgs) + '</div>'
    else:
        gal = '<div class="w4-img" style="max-width:900px"><img src="%s" alt="%s" loading="lazy" decoding="async" width="1200" height="900"></div>' % (imgs[0], esc(c['name']))
    body += section('What\'s possible', '%s, <i>your way</i>' % esc(c['name']),
                    '<p class="w4-sub">%s</p>' % esc(c['short'])
                    + '<div class="w4-grid w4-opts" style="margin-bottom:34px">'
                    + ''.join(tile(esc(o), 'On request', CAT_ICON[c['slug']]) for o in c['options']) + '</div>' + gal, sid='options')
    body += section('Popular ideas', 'Where to go &amp; <i>what to do</i>',
                    '<div class="w4-grid g3" style="grid-template-columns:repeat(auto-fill,minmax(260px,1fr))">' + ''.join(tile(t, p) for t, p in x['ideas']) + '</div>', cls='ink')
    body += section('Enquiry', 'Tell us the date <i>&amp; group size</i>',
                    '<div class="w4-split top"><div>%s<p class="w4-sub" style="margin-top:24px">We reply with options from vetted local partners, what is included and the price for your date. '
                    'Prices are on request — nothing is booked until you confirm on WhatsApp.</p>'
                    '<div class="w4-btns">%s</div></div>%s</div>'
                    % (steps(HOW, s3=True).replace('w4-steps s3', 'w4-steps s3" style="grid-template-columns:1fr'), wa_btn(x['wa'], 'Message us directly', 'light'), form(c)),
                    cls='paper', sid='enquiry')
    fh, fld = faq(x['faq'])
    body += section('Questions', '%s: <i>good to know</i>' % esc(short_name(c)), fh, narrow=True, sid='faq')
    others = ''.join(cat_card(o) for o in VIP if o['slug'] != c['slug'])
    body += section('More VIP', 'Add something <i>else</i>',
                    '<div class="w4-grid g4">' + others + '</div><div class="w4-rel" style="margin-top:22px"><a href="/vip/">All VIP services</a>'
                    '<a href="/property-rental/?vibe=luxury">Luxury villas</a></div>', cls='paper')
    body += final('Thai Villas VIP', 'Send us the date.', 'Tell us the date, the group size and what you have in mind — we\'ll come back with options.',
                  wa_btn(x['wa']) + btn('/vip/', 'All VIP services', 'ghost'), ink=True)
    ld = [fld, crumbs_ld([('Home', '/'), ('VIP', '/vip/'), (c['name'], url)]),
          {"@context": "https://schema.org", "@type": "Service", "name": c['name'], "serviceType": c['name'],
           "areaServed": "Phuket, Thailand", "provider": {"@type": "Organization", "name": BRAND}, "description": c['short']}]
    write('vip/%s/index.html' % c['slug'], page(x['title'], c['short'], body, ld, c['image'], extra=wa_form_script()))

if __name__ == '__main__':
    build_hub()
    for c in VIP:
        build_cat(c)
    print('vip: hub + %d category pages' % len(VIP))
