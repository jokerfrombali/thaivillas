"""Price facts computed from the listing data — unique, citable numbers for area / sale pages and their FAQ.

Used by build_areas.py (rent) and build_sale.py (sale, projects). Everything is derived from data/*.json,
so the numbers refresh on every rebuild.
"""
import collections
import statistics


def _num(v):
    try:
        f = float(v)
        return f if f > 0 else None
    except (TypeError, ValueError):
        return None


def low(xs):
    """'From' price: 10th percentile, so a single mistyped listing does not set the floor."""
    xs = sorted(xs)
    return xs[int(len(xs) * 0.1)] if xs else None


def thb(v):
    if v >= 1e6:
        return '{:,.1f} million THB'.format(v / 1e6).replace('.0 million', ' million')
    return '{:,.0f} THB'.format(round(v, -2) if v >= 10000 else v)


def _beds(v):
    try:
        b = int(float(v.get('bedrooms') or 0))
    except (TypeError, ValueError):
        b = 0
    return b


def rent_stats(vs):
    month = [(p, _beds(v)) for v in vs for p in [_num(v.get('priceMonth'))] if p and p >= 10000]
    night = [p for v in vs for p in [_num(v.get('priceNight'))] if p and p >= 1000]
    groups = collections.OrderedDict([('1–2 bedrooms', (1, 2)), ('3 bedrooms', (3, 3)), ('4+ bedrooms', (4, 99))])
    by_beds = []
    for label, (lo, hi) in groups.items():
        xs = [p for p, b in month if lo <= b <= hi]
        if len(xs) >= 5:
            by_beds.append((label, statistics.median(xs), low(xs), len(xs)))
    # show the bedroom split only when it makes sense (bigger villas cost more); otherwise the data is too noisy
    meds = [m for _, m, _, _ in by_beds]
    if len(by_beds) < 2 or any(b <= a for a, b in zip(meds, meds[1:])):
        by_beds = []
    return {
        'n': len(vs),
        'villas': sum(1 for v in vs if v.get('propertyType') == 'villa'),
        'month_n': len(month), 'month_med': statistics.median([p for p, _ in month]) if month else None,
        'month_min': low([p for p, _ in month]),
        'night_n': len(night), 'night_med': statistics.median(night) if night else None,
        'night_min': low(night),
        'by_beds': by_beds,
    }


def rent_price_qa(place, vs):
    """FAQ answers with real prices; empty list when there is not enough data."""
    s = rent_stats(vs)
    qa = []
    if s['month_n'] >= 3:
        parts = '; '.join('%s — around %s a month (from %s)' % (l, thb(m), thb(mn)) for l, m, mn, _ in s['by_beds'])
        qa.append(('How much does it cost to rent a villa or apartment in %s per month?' % place,
                   'Across %d listings with a monthly rate, the median is %s per month%s. '
                   'Long stays are usually priced below the nightly rate; electricity is often billed separately.'
                   % (s['month_n'], thb(s['month_med']), (': ' + parts) if parts else '')))
    if s['night_n'] >= 3:
        qa.append(('How much does a villa or apartment in %s cost per night?' % place,
                   'Nightly rates start from about %s; the median across %d listings is %s per night. '
                   'Prices rise in high season (December–February) and for the holidays.' % (thb(s['night_min']), s['night_n'], thb(s['night_med']))))
    return qa


def rent_price_para(place, vs):
    s = rent_stats(vs)
    if s['month_n'] < 3 and s['night_n'] < 3:
        return ''
    bits = []
    if s['night_n'] >= 3:
        bits.append('nightly rates from about %s (median %s)' % (thb(s['night_min']), thb(s['night_med'])))
    if s['month_n'] >= 3:
        bits.append('monthly rates from %s (median %s)' % (thb(s['month_min']), thb(s['month_med'])))
    return ('Prices in %s today: %d listings, %s. Figures are calculated from the live listings on this page '
            'and updated with every refresh.' % (place, s['n'], ' and '.join(bits)))


def sale_stats(vs):
    price = [p for v in vs for p in [_num(v.get('priceSale'))] if p]
    own = collections.Counter(v.get('ownership') for v in vs if v.get('ownership'))
    sub = collections.Counter(v.get('subArea') for v in vs if v.get('subArea'))
    types = collections.Counter(v.get('propertyTypeName') or v.get('propertyType') for v in vs if v.get('propertyType'))
    return {'n': len(vs), 'price_n': len(price), 'med': statistics.median(price) if price else None,
            'min': low(price), 'own': own, 'sub': sub, 'types': types}


def sale_price_qa(place, vs):
    s = sale_stats(vs)
    qa = []
    if s['price_n'] >= 3:
        top = ', '.join('%s (%d)' % (k, n) for k, n in s['sub'].most_common(5))
        qa.append(('How much does property cost in %s?' % place,
                   'Asking prices start from about %s; the median across %d listings is %s. '
                   'Most properties for sale are in %s.' % (thb(s['min']), s['price_n'], thb(s['med']), top)))
    if s['own']:
        qa.append(('Freehold or leasehold?',
                   'Where the ownership type is stated: %s. Foreigners can hold condominium units freehold within the 49%% foreign quota; '
                   'villas and land are usually bought leasehold (30 years, often with renewal options) or through a structure set up by a lawyer.'
                   % ', '.join('%d %s' % (n, k.lower()) for k, n in s['own'].most_common())))
    return qa
