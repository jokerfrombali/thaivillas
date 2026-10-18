#!/usr/bin/env python3
"""/about/, /contacts/, /terms/, /privacy/ for Thai Villas.

Modelled on the reference about/contacts/terms/privacy pages, rewritten for a new business in
Thailand: no management, owners, sale, company registration numbers, office address or map embed,
no invented team names or numbers. Legal texts are generic drafts — the site is in preview.
Run from the site root: python3 -I tools/thai/build_info.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from w4_shell import *  # noqa: F401,F403

UPDATED = '19 October 2026'
PREVIEW = ('<div class="w4-notice"><b>Preview.</b> This website is in preview. The details below are a working draft and will be finalised '
           '— including the legal entity operating the service — before bookings open. This page is not legal advice.</div>')

# ------------------------------------------------------------------ about
def build_about():
    body = ('<header class="w4-head" style="padding-bottom:0"><div class="w4-wrap w4-split" style="padding-bottom:76px">'
            '<div><div class="w4-chiprow"><span>Daily rentals</span><span>Monthly stays</span><span>VIP</span></div>'
            '<p class="w4-kicker" style="color:rgba(255,255,255,.5)">About us</p>'
            '<h1 class="w4-h1">About <i>Thai Villas.</i></h1>'
            '<p class="w4-lead">A local team in Phuket renting private pool villas by the night and by the month — in Phuket first, and across Thailand. '
            'You talk to a real person on WhatsApp from the first question to check-out.</p>'
            '<div class="w4-btns">%s%s</div></div>'
            '<div class="w4-img"><img src="/images/phuket.jpg" alt="Phuket coastline" fetchpriority="high" decoding="async" width="1200" height="900"></div>'
            '</div></header>\n') % (btn('/property-rental/', 'See the villas', 'light'), btn('/contacts/', 'Contact us', 'ghost'))
    body += '<div class="w4-wrap">' + crumbs_html([('Home', '/'), ('About', '/about/')]) + '</div>'
    what = ''.join(tile(t, p, i) for t, p, i in [
        ('Daily villa rentals', 'Private pool villas for holidays of a few nights or a few weeks — beachfront, hillside and family villas around Phuket and beyond.', 'home'),
        ('Monthly &amp; long stays', 'A month, a season or longer: villas set up for living, with clear terms on deposit and utilities before you commit.', 'cal'),
        ('VIP services', 'Yacht charters, helicopter flights, supercars, superbikes and concierge, arranged with vetted local partners.', 'star'),
    ])
    body += section('What we do', 'Villas and the extras, <i>one contact</i>', '<div class="w4-grid g3">' + what + '</div>',
                    sub='Two kinds of rental — daily and monthly — plus VIP services around your stay.')
    pick = ''.join(tile(t, p, i) for t, p, i in [
        ('Honest photos &amp; descriptions', 'What you see is what you get: the real pool, the real view, the real distance to the beach.', 'doc'),
        ('A pool, and it works', 'Private pools that are cleaned and maintained on a schedule — the reason most people choose a villa.', 'shield'),
        ('Ready for real life', 'Reliable Wi-Fi, air-conditioning in the bedrooms and a kitchen you can actually cook in.', 'wifi'),
        ('Clear terms', 'Deposit, utilities, cleaning and house rules agreed in writing before you pay — no surprises at check-out.', 'key'),
        ('Someone on the ground', 'A local contact who answers when the air-con stops or you need a doctor, a driver or a boat.', 'pin'),
        ('The right area', 'We\'ll tell you honestly if a villa is too far from the beach, too steep for a pram or too lively for a quiet month.', 'globe'),
    ])
    body += section('How we pick villas', 'What a villa needs <i>to make the list</i>', '<div class="w4-grid g3">' + pick + '</div>',
                    sub='Our standards for every villa we offer.', cls='paper')
    dest = ''.join('<a href="%s">%s</a>' % (area_url(d['slug']), esc(d['name'])) for d in AREAS)
    phk = ''.join('<a href="%s">%s</a>' % (area_url('phuket', a['slug']), esc(a['name'])) for a in PHUKET['areas'])
    body += section('Where we work', 'Phuket first, <i>Thailand next</i>',
                    '<div class="w4-split top"><div class="w4-prose"><p>We are based in Phuket, so that is where you\'ll find the widest choice — '
                    'from Bang Tao and Layan in the north-west to Kata, Nai Harn and Rawai in the south.</p>'
                    '<p>We also help with villas in Koh Samui, Pattaya, Bangkok, Krabi, Koh Phangan, Hua Hin and Chiang Mai.</p>'
                    '<p class="w4-sample">This site is in preview: the villas shown are sample listings while we finish onboarding. Availability and rates are on request.</p></div>'
                    '<div><p class="w4-kicker">Phuket beaches</p><div class="w4-rel" style="margin-bottom:24px">%s</div>'
                    '<p class="w4-kicker">Destinations</p><div class="w4-rel">%s</div></div></div>' % (phk, dest))
    body += section('How to reach us', 'A real person, <i>on WhatsApp</i>',
                    '<div class="w4-grid g3">%s%s%s</div>' % (
                        tile('WhatsApp', '<p><a href="%s" rel="noopener">%s</a><br>The fastest way to reach us.</p>' % (WA, esc(PHONE)), 'phone'),
                        tile('Email', '<p><a href="mailto:%s">%s</a></p>' % (EMAIL, EMAIL), 'mail'),
                        tile('Hours', '<p>Every day 9:00–21:00 (GMT+7)<br>Guest support 24/7 during your stay</p>', 'clock')), cls='paper')
    body += final('Ready when you are', 'Now you know us. <i>Let\'s find your villa.</i>',
                  'Tell us your dates and what matters most — we\'ll suggest the right villa.',
                  btn('/property-rental/', 'Browse villas', 'dark', 'arrow') + wa_btn("Hi Thai Villas! I'm looking for a villa in Thailand.", 'WhatsApp us', 'light'))
    ld = [crumbs_ld([('Home', '/'), ('About', '/about/')]),
          {"@context": "https://schema.org", "@type": "AboutPage", "name": "About Thai Villas", "url": "/about/"}]
    write('about/index.html', page('About Thai Villas — Villa Rentals in Phuket & Thailand',
          'Thai Villas is a local team in Phuket renting private pool villas by the night and by the month, plus VIP services: yachts, helicopters, supercars.',
          body, ld, '/images/phuket.jpg'))

# ------------------------------------------------------------------ contacts
def build_contacts():
    body = head('Contacts · Phuket', 'Talk to a human, <i>not a ticket queue.</i>',
                'Message us on WhatsApp and you reach the people who arrange your villa — usually quickly, every day.')
    body += '<div class="w4-wrap">' + crumbs_html([('Home', '/'), ('Contacts', '/contacts/')]) + '</div>'
    cards = ''.join([
        tile('WhatsApp — fastest', '<p><a href="%s" rel="noopener"><b>%s</b></a><br>Bookings, monthly stays, VIP — anything at all.</p>' % (wa(), esc(PHONE)), 'phone'),
        tile('Phone', '<p><a href="tel:+%s"><b>%s</b></a><br>Calls during office hours.</p>' % (WA_NUM, esc(PHONE)), 'phone'),
        tile('Email', '<p><a href="mailto:%s"><b>%s</b></a><br>Longer questions, agreements, partnerships.</p>' % (EMAIL, EMAIL), 'mail'),
        tile('Where we are', '<p><b>Phuket, Thailand</b><br>We meet guests at the villa.</p>', 'pin'),
        tile('Hours', '<p><b>Every day 9:00–21:00</b><br>Thailand time (GMT+7)</p>', 'clock'),
        tile('Guest support', '<p><b>24/7</b><br>For guests during their stay.</p>', 'shield'),
    ])
    form = ('<form class="w4-form" data-wa-form="Hi Thai Villas!">'
            '<label for="ct">What is it about?</label><select id="ct" data-label="Topic"><option>Daily villa rental</option><option>Monthly / long stay</option>'
            '<option>VIP services</option><option>Something else</option></select>'
            '<div class="row"><div><label for="cn">Your name</label><input id="cn" type="text" autocomplete="name" data-label="Name"></div>'
            '<div><label for="cg">Guests</label><input id="cg" type="number" min="1" max="50" inputmode="numeric" data-label="Guests"></div></div>'
            '<div class="row"><div><label for="ci">From</label><input id="ci" type="date" data-label="From"></div>'
            '<div><label for="co">To</label><input id="co" type="date" data-label="To"></div></div>'
            '<label for="cm">Message</label><textarea id="cm" placeholder="Area, budget, must-haves…" data-label="Message"></textarea>'
            '<button class="w4-btn wa" type="submit">%sSend on WhatsApp</button>'
            '<p class="fine">Opens WhatsApp with your message ready to send. Nothing is stored on this site — see our <a href="/privacy/" style="text-decoration:underline">privacy notice</a>.</p></form>'
            % ICON['wa'])
    body += ('<section class="w4-sec" style="border-top:0"><div class="w4-wrap w4-split top">'
             '<div><p class="w4-kicker">Get in touch</p><h2 class="w4-h2">Pick <i>what suits you.</i></h2>'
             '<div class="w4-grid g2" style="margin-top:26px">%s</div></div>'
             '<div><p class="w4-kicker">Send a message</p><h2 class="w4-h2">Tell us <i>your dates.</i></h2><div style="margin-top:26px">%s</div></div>'
             '</div></section>\n') % (cards, form)
    fq = [
        ('How quickly do you reply?', 'WhatsApp is the fastest way to reach us — during office hours (9:00–21:00 Thailand time) we usually reply quickly. Messages sent at night are answered the next morning, except urgent ones from guests staying with us.'),
        ('Can I visit an office?', 'We work across Phuket and meet guests at the villas. If you would like a viewing, message us and we\'ll arrange a time.'),
        ('Do you speak languages other than English?', 'Ask us on WhatsApp — we\'ll do our best to help in your language.'),
    ]
    fh, fld = faq(fq)
    body += section('Questions', 'Before you <i>message us</i>', fh, narrow=True, cls='paper')
    body += final('Fastest way', 'WhatsApp us.', 'Dates, number of guests and the area are enough to get started.',
                  wa_btn("Hi Thai Villas! I'm looking for a villa in Thailand.") + btn('/property-rental/', 'Browse villas', 'light'))
    ld = [fld, crumbs_ld([('Home', '/'), ('Contacts', '/contacts/')]),
          {"@context": "https://schema.org", "@type": "ContactPage", "name": "Contact Thai Villas", "url": "/contacts/"}]
    write('contacts/index.html', page('Contact Thai Villas — WhatsApp, Phone, Email | Phuket',
          'Contact Thai Villas in Phuket: WhatsApp, phone and email, every day 9:00–21:00 (GMT+7). Villa rentals by the night or month and VIP services.',
          body, ld, '/images/phuket-2.jpg', extra=wa_form_script()))

# ------------------------------------------------------------------ legal
def legal(path, kicker, h1, lead, sections, title, desc):
    body = head(kicker, h1, lead, meta='Last updated: ' + UPDATED)
    body += '<div class="w4-wrap">' + crumbs_html([('Home', '/'), (kicker, path)]) + '</div>'
    secs = ''.join('<section><h2>%d. %s</h2>%s</section>' % (i + 1, t, ''.join(
        ('<ul>%s</ul>' % ''.join('<li>%s</li>' % li for li in p) if isinstance(p, list) else '<p>%s</p>' % p) for p in ps))
        for i, (t, ps) in enumerate(sections))
    body += ('<section class="w4-sec" style="border-top:0;padding-top:48px"><div class="w4-wrap w4-narrow w4-legal">%s%s</div></section>\n'
             % (PREVIEW, secs))
    write(path.strip('/') + '/index.html', page(title, desc, body, [crumbs_ld([('Home', '/'), (kicker, path)])]))

TERMS = [
    ('Who we are', [
        'These terms apply to this website and to stays and services arranged through Thai Villas (“we”, “us”). The legal entity operating Thai Villas, '
        'and its registered details, will be published here before bookings open.',
        'By requesting a booking, confirming a stay or using this website you accept these terms. If you book a villa through another platform, '
        'that platform\'s terms govern the payment and cancellation of that booking, and these terms apply to the stay itself.']),
    ('What we do', [
        'We offer private villas in Thailand for daily (short) stays and monthly (long) stays, and arrange VIP services — such as yacht charters, '
        'helicopter flights, vehicle rental and concierge — with independent local partners.',
        'While the site is in preview, villas shown are sample listings. Descriptions, photos and amenity lists of real villas will be kept as accurate as we can make them; '
        'if something that materially affects your stay changes, we will tell you before arrival.']),
    ('Booking and confirmation', [
        'A booking is confirmed only when we have confirmed it to you in writing (for example on WhatsApp or by email) with the dates, villa, price and payment terms, '
        'and any required payment has been received.',
        'Prices on this site are shown as “on request”. The price that applies is the one in your written confirmation.']),
    ('Cancellation and changes', [
        'Cancellation terms depend on the villa, the season and the length of stay, and are stated in your booking confirmation or rental agreement. '
        'Please read them before you pay.',
        'If we have to cancel a confirmed booking, we will offer a comparable alternative or a refund of amounts paid to us.']),
    ('Monthly and long stays', [
        'Monthly stays are covered by a written rental agreement setting out the dates, rate, security deposit, what is included (for example cleaning, pool care, Wi-Fi) '
        'and what is billed separately (for example electricity and water by the meter).',
        'You are responsible for making sure you are allowed to stay in Thailand for the length of your rental. We do not give visa or immigration advice.']),
    ('Staying in the villa', [[
        'Respect the maximum number of guests and the house rules of the villa.',
        'Parties and events need our prior written agreement.',
        'Keep noise reasonable, especially at night — villas are often in residential areas.',
        'Report any damage or problem as soon as you notice it, so we can fix it.']]),
    ('Security deposit and damage', [
        'A refundable security deposit may be required. Its amount and how it is held are confirmed before arrival. After check-out the villa is inspected and the deposit '
        'is returned, less the cost of any damage beyond normal wear, missing items or unpaid bills, which we will explain to you.']),
    ('VIP services', [
        'VIP services are provided by independent partners under their own terms, which we share with you before you confirm. Activities at sea or in the air depend on weather '
        'and on the decision of the captain or pilot. Driving or riding requires a valid licence for the vehicle class; you are responsible for complying with Thai traffic law.']),
    ('Liability', [
        'We take reasonable care in arranging your stay and services. To the extent permitted by applicable law, we are not liable for indirect losses, or for events outside '
        'our reasonable control such as weather, natural events, or the acts of third parties. Nothing in these terms limits liability that cannot be limited by law.',
        'We recommend travel insurance that covers your stay and any activities you book.']),
    ('Complaints', [
        'If something is not right, tell us straight away on WhatsApp so we can fix it during your stay. You can also write to <a href="mailto:%s">%s</a>.' % (EMAIL, EMAIL)]),
    ('Changes to these terms', [
        'We may update these terms, in particular when the site leaves preview. The version that applies to your booking is the one in force when your booking was confirmed. '
        'The governing law and jurisdiction will be stated here once the operating entity is finalised.']),
]

PRIVACY = [
    ('Who is responsible for your data', [
        'Thai Villas (“we”, “us”) is responsible for personal data collected through this website and when you contact us. The legal entity and its contact details '
        'will be published here before bookings open. Until then, you can reach us at <a href="mailto:%s">%s</a>.' % (EMAIL, EMAIL)]),
    ('What we collect', [[
        'What you send us — for example your name, phone number, email, travel dates, number of guests and your messages on WhatsApp or by email.',
        'Booking details once a stay is confirmed, such as guest names and arrival information.',
        'Villas you save on this site are stored only in your own browser (local storage) and are not sent to us.',
        'Basic technical data needed to deliver the website (such as your browser type), processed by our hosting provider.']]),
    ('Why we use it', [[
        'To answer your questions and prepare offers.',
        'To arrange and manage your stay or the VIP services you book.',
        'To meet legal obligations, for example where guest registration is required by Thai law.']]),
    ('Who else sees it', [
        'We share data only where needed to deliver what you asked for — for example with the villa\'s on-site staff or a VIP service partner — and with service providers '
        'such as our hosting and messaging providers. WhatsApp messages are handled under WhatsApp\'s own privacy policy. We do not sell personal data.']),
    ('How long we keep it', [
        'Enquiries that do not lead to a booking are deleted after a reasonable period. Booking records are kept as long as required for legal and accounting purposes.']),
    ('Your rights', [
        'Depending on applicable law, including Thailand\'s Personal Data Protection Act, you may ask to access, correct or delete your data, or object to how it is used. '
        'Write to <a href="mailto:%s">%s</a> and we will respond.' % (EMAIL, EMAIL)]),
    ('Cookies', [
        'This preview site does not use advertising cookies. If analytics are added later, they will only be used in line with your choices and this notice will be updated.']),
    ('Changes', [
        'We will update this notice when the site leaves preview and whenever our practices change. The date at the top shows the latest version.']),
]

if __name__ == '__main__':
    build_about()
    build_contacts()
    legal('/terms/', 'Terms', 'Terms of stay <i>and booking conditions.</i>',
          'The rules that apply when you book a villa or a VIP service with Thai Villas — in plain English.', TERMS,
          'Terms of Stay & Booking Conditions | Thai Villas',
          'Terms that apply to villa stays (daily and monthly) and VIP services arranged through Thai Villas. Draft — the site is in preview.')
    legal('/privacy/', 'Privacy', 'Privacy <i>notice.</i>',
          'What personal data we collect when you use this site or contact us, why, and what you can ask us to do with it.', PRIVACY,
          'Privacy Notice | Thai Villas',
          'How Thai Villas handles personal data from enquiries and bookings. Draft — the site is in preview.')
    print('info: about, contacts, terms, privacy')
