"""llms.txt for luxuryphuket.net — a short, factual map of the site for AI assistants (https://llmstxt.org).

Called from tools/cloudflare_build.py; numbers are computed from data/*.json on every deploy.
"""
import collections
import json
import os
import statistics

SITE = 'https://luxuryphuket.net'


def _num(v):
    try:
        f = float(v)
        return f if f > 0 else None
    except (TypeError, ValueError):
        return None


def _thb(v):
    return '{:,.0f} THB'.format(v)


def build(root):
    load = lambda n: json.load(open(os.path.join(root, 'data', n), encoding='utf-8'))
    rent, sale, proj = load('villas.json'), load('sale.json'), load('projects.json')
    areas = load('areas.json')['destinations']
    phuket = next((d for d in areas if d['slug'] == 'phuket'), {})

    by_sub = collections.defaultdict(list)
    for x in rent:
        if x.get('areaSlug') == 'phuket' and x.get('subAreaSlug'):
            by_sub[x['subAreaSlug']].append(x)

    month = [p for p in (_num(x.get('priceMonth')) for x in rent) if p and p >= 10000]
    night = [p for p in (_num(x.get('priceNight')) for x in rent) if p and p >= 1000]
    price_sale = [p for p in (_num(x.get('priceSale')) for x in sale) if p]
    sale_sub = collections.Counter(x.get('subArea') for x in sale if x.get('subArea'))

    L = []
    L.append('# Luxury Phuket')
    L.append('')
    L.append('> Luxury Phuket (luxuryphuket.net) lists villas and apartments for daily and monthly rent, '
             'property for sale and new off-plan projects on Phuket, Thailand. '
             f'{len(rent):,} rentals, {len(sale):,} properties for sale and {len(proj):,} new projects. '
             'Enquiries go directly to the Luxury Phuket team by WhatsApp (+66 81 123 7388), '
             'the booking form on each listing, or email hello@luxuryphuket.net.')
    L.append('')
    L.append('Key facts:')
    if night:
        L.append(f'- Daily villa rentals: typically {_thb(statistics.median(night))} per night (median), '
                 f'from about {_thb(min(night))}.')
    if month:
        L.append(f'- Monthly rentals: median {_thb(statistics.median(month))} per month, from about {_thb(min(month))}.')
    if price_sale:
        L.append(f'- Property for sale: from {_thb(min(price_sale))}, median {_thb(statistics.median(price_sale))}.')
    L.append('- Most listings are on the west coast of Phuket: Bang Tao / Laguna, Layan, Surin, Kamala, '
             'Karon, Kata, Nai Harn and Rawai.')
    L.append('- Prices are shown in Thai baht; availability and the final price are confirmed by the team.')
    L.append('')
    L.append('## Main sections')
    L.append(f'- [All rentals in Phuket]({SITE}/property-rental/): villas and apartments with filters and a map')
    L.append(f'- [Phuket villas by area]({SITE}/villas/phuket/): private pool villas grouped by beach')
    L.append(f'- [Monthly rentals]({SITE}/monthly-rental/phuket/): long stays from 1 month')
    L.append(f'- [Property for sale]({SITE}/sale/): villas, condos and townhouses for sale in Phuket')
    L.append(f'- [New projects]({SITE}/projects/): off-plan developments, completion dates, ownership type')
    L.append(f'- [VIP services]({SITE}/vip/): yachts, supercars, superbikes, helicopters, concierge')
    L.append(f'- [About]({SITE}/about/) · [Contacts]({SITE}/contacts/)')
    L.append('')
    L.append('## Phuket rental areas')
    names = {'mai-khao': 'Mai Khao & Nai Yang', 'bang-tao': 'Bang Tao & Laguna'}
    for slug, xs in sorted(by_sub.items(), key=lambda kv: -len(kv[1])):
        name = names.get(slug) or collections.Counter(x.get('subArea') or slug for x in xs).most_common(1)[0][0]
        m = [p for p in (_num(x.get('priceMonth')) for x in xs) if p and p >= 10000]
        tail = f', monthly from {_thb(min(m))}' if m else ''
        L.append(f'- [{name}]({SITE}/villas/phuket/{slug}/): {len(xs)} rentals{tail}')
    L.append('')
    L.append('## Property for sale by area')
    for name, n in sale_sub.most_common(12):
        L.append(f'- {name}: {n} properties')
    L.append('')
    if phuket.get('short'):
        L.append('## About Phuket')
        L.append(phuket['short'])
        L.append('')
    L.append('## Optional')
    L.append(f'- [Sitemap]({SITE}/sitemap.xml): every listing page')
    L.append(f'- [Other destinations]({SITE}/villas/): Koh Samui, Pattaya, Bangkok, Chiang Mai, Krabi, Hua Hin, Koh Phangan')
    return '\n'.join(L) + '\n'


if __name__ == '__main__':
    print(build(os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))))
