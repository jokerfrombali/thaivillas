#!/usr/bin/env python3
"""Sale and new-project catalogues: /sale/, /sale/{destination}/, /projects/.

Same catalogue design as /property-rental/ (build_areas.assemble), cards from data/sale.json and
data/projects.json. Listing pages themselves are built by build_villas.py.

    python3 -I tools/thai/build_sale.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_areas as A
from thv import *  # noqa


def page(rel, crumbs, tag, h1, sub, vs, kicker, seo_title, seo_paras, side, qa, title, desc, image):
    html = '<!-- PAGE -->\n<div style="padding-top:72px;min-height:100vh">\n\n'
    html += A.promo(crumbs, tag, h1, sub, '')
    html += '\n' + A.results_bar(kicker, len(vs), '')
    html += '\n' + A.cards_wrap(vs, '<p style="padding:40px 0;color:#6b6b66">New listings are being added — message us on WhatsApp.</p>') + '</div>\n\n'
    html += A.seo_section('th-sale-seo', kicker, seo_title, seo_paras, 'Browse', side, [])
    html += A.faq_section(kicker, '%s — FAQ' % kicker, qa)
    ld = [A.crumbs_ld([('Home', '/')] + [(n, u) for n, u in (crumbs or [])]), A.faq_ld(qa),
          {"@context": "https://schema.org", "@type": "ItemList", "name": h1, "numberOfItems": len(vs),
           "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": v['name'], "url": v['url']} for i, v in enumerate(vs)]}]
    s = A.assemble('property-rental/index.html', title, desc, image, html, '', ld, False, False)
    write(rel, s)


SALE_QA = [
    ('Can foreigners buy property in Thailand?', 'Foreigners can own a condominium unit outright (freehold) within the foreign quota of a building. '
     'Villas and land are usually bought on a long-term lease or through a structure your lawyer sets up. Each listing states the ownership type when known.'),
    ('How do viewings work?', 'Message us on WhatsApp with the listings you like. We arrange viewings in person or by video call and send the documents for each property.'),
    ('Are the prices final?', 'Prices are the asking or developer prices at the time of listing in Thai baht. Send us a message to confirm the current price and availability.'),
]
PROJECT_QA = [
    ('What is an off-plan project?', 'A residence that is under construction or about to start. Developers sell units at earlier-stage prices with a payment plan tied to construction.'),
    ('What do I get from you?', 'Layouts, price lists, payment plans and completion dates for each project, plus viewings of the show units and the site.'),
    ('Can a project unit be rented out?', 'Many projects run a rental programme or allow private rental. We share the expected occupancy and terms per project.'),
]


def main():
    dests = [d for d in AREAS if any(v['areaSlug'] == d['slug'] for v in SALE)]
    side = [('/sale/', 'All properties for sale')] + [('/sale/%s/' % d['slug'], 'For sale in ' + d['name']) for d in dests] + \
           [('/projects/', 'New projects'), ('/property-rental/', 'Villas for rent')]
    page('sale/index.html', [('For sale', '/sale/')], '🏡 Buy in Thailand', 'Villas and apartments for sale in Thailand',
         'Pool villas, condos and penthouses for sale in Phuket and beyond — with prices, layouts and photos. Viewings arranged on WhatsApp.',
         SALE, 'Property for sale in Thailand', 'Buying property in Thailand',
         ['Every listing shows the asking price in Thai baht, the size, bedrooms and the ownership type where known.',
          'Message us with the properties you like: we send documents, arrange viewings and connect you with a lawyer.'],
         side, SALE_QA, 'Property for Sale in Thailand — Villas & Condos in Phuket | Thai Villas',
         '%d villas, apartments and penthouses for sale in Phuket and Thailand, with prices and photos.' % len(SALE), '/images/phuket.jpg')
    for d in dests:
        vs = [v for v in SALE if v['areaSlug'] == d['slug']]
        page('sale/%s/index.html' % d['slug'], [('For sale', '/sale/'), (d['name'], '/sale/%s/' % d['slug'])], '🏡 ' + d['name'],
             'Property for sale in %s' % d['name'], d['short'], vs, 'For sale in ' + d['name'], 'Buying in ' + d['name'],
             ['%d properties for sale in %s, sorted as listed by the owners and developers.' % (len(vs), d['name'])],
             side, SALE_QA, 'Property for Sale in %s, Thailand | Thai Villas' % d['name'],
             '%d villas and apartments for sale in %s, Thailand.' % (len(vs), d['name']), d['image'])
    page('projects/index.html', [('New projects', '/projects/')], '🏗 New developments', 'New residential projects in Phuket',
         'Villa and condo developments — completion dates, price ranges, layouts and photos of every project.',
         PROJECTS, 'New projects in Thailand', 'Investing in a new project',
         ['Each project page lists the price range, unit sizes, completion and the developer details we have.',
          'Ask us on WhatsApp for the price list, payment plan and available units.'],
         side, PROJECT_QA, 'New Real Estate Projects in Phuket — Villas & Condos Off-Plan | Thai Villas',
         '%d new villa and condo projects in Phuket and Thailand.' % len(PROJECTS), '/images/phuket-2.jpg')
    print('ok: /sale/ (%d), %d destinations, /projects/ (%d)' % (len(SALE), len(dests), len(PROJECTS)))


if __name__ == '__main__':
    main()
