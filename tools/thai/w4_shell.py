"""Shared page shell + components for the W4 pages (monthly-rental, vip, about, contacts, terms, privacy).

Shell = the reference home page (index.html) passed through thv.rebrand(): Thai nav + mega-menu,
footer, WhatsApp pill, favourites script. Everything between the mega-menu and the footer is
replaced with the page body built here. Home-only hero CSS/JS (slideshow, glass navbar) is stripped.
"""
import json, re
from thv import *  # noqa: F401,F403
from thv import _balanced  # noqa: F401

CSS = r"""
<style id="w4-css">
.w4{font-family:'Inter',sans-serif;color:#0a0a0a}
.w4 *{box-sizing:border-box}
.w4 a{color:inherit;text-decoration:none}
.w4-wrap{max-width:1400px;margin:0 auto;padding:0 24px}
@media(min-width:1024px){.w4-wrap{padding:0 40px}}
.w4-narrow{max-width:860px}
.w4-sec{padding:84px 0;border-top:1px solid #e6e3dc;background:#fafaf7}
.w4-sec.paper{background:#f4f2ed}
.w4-sec.ink{background:#0a0a0a;color:#fff;border-top-color:#0a0a0a}
.w4-kicker{text-transform:uppercase;letter-spacing:.22em;font-size:11px;font-weight:600;color:#6b6b66;margin:0 0 14px}
.ink .w4-kicker,.w4-hero .w4-kicker{color:rgba(255,255,255,.62)}
.w4-h2{font-family:'Lora',Georgia,serif;font-weight:400;font-size:clamp(30px,4vw,54px);line-height:1.02;margin:0 0 16px}
.w4-h2 i,.w4-h1 i{font-style:italic}
.w4-sub{color:#6b6b66;font-size:16px;line-height:1.65;max-width:62ch;margin:0 0 34px}
.ink .w4-sub{color:rgba(255,255,255,.66)}
.w4-crumbs{font-size:12.5px;color:#8a877f;padding:16px 0 0}.w4-crumbs a{color:#6b6b66}.w4-crumbs span{margin:0 6px}
/* hero with photo */
.w4-hero{position:relative;background:#0a0a0a;color:#fff;padding-top:72px;min-height:min(86vh,820px);display:flex;align-items:flex-end;overflow:hidden}
.w4-hero>img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
.w4-hero::after{content:'';position:absolute;inset:0;background:linear-gradient(to top,rgba(10,10,10,.88) 0%,rgba(10,10,10,.45) 45%,rgba(10,10,10,.18) 75%,rgba(10,10,10,.35) 100%)}
.w4-hero .w4-wrap{position:relative;z-index:2;width:100%;padding-bottom:72px;padding-top:72px}
.w4-hero.short{min-height:min(64vh,620px)}
.w4-h1{font-family:'Lora',Georgia,serif;font-weight:400;font-size:clamp(40px,6.4vw,84px);line-height:.98;margin:0 0 22px;max-width:16ch}
.w4-lead{font-size:clamp(16px,1.5vw,19px);line-height:1.6;color:rgba(255,255,255,.78);max-width:58ch;margin:0 0 30px}
.w4-chiprow{display:flex;gap:8px;flex-wrap:wrap;margin:0 0 26px}
.w4-chiprow span{font-size:11px;font-weight:600;letter-spacing:.18em;text-transform:uppercase;border:1px solid rgba(255,255,255,.3);border-radius:999px;padding:6px 14px;color:rgba(255,255,255,.82)}
/* plain dark header (info pages) */
.w4-head{background:#0a0a0a;color:#fff;padding:72px 0 0}
.w4-head .w4-wrap{padding-top:76px;padding-bottom:76px}
.w4-head .w4-lead{color:rgba(255,255,255,.66)}
.w4-head .w4-meta{color:rgba(255,255,255,.42);font-size:13px;margin-top:20px}
/* buttons */
.w4-btns{display:flex;gap:10px;flex-wrap:wrap}
.w4-btn{display:inline-flex;align-items:center;justify-content:center;gap:9px;border-radius:999px;padding:15px 24px;font-size:15px;font-weight:600;transition:background .15s,transform .15s;cursor:pointer;border:0;font-family:inherit}
.w4-btn:hover{transform:translateY(-1px)}
.w4-btn.wa{background:#22c55e;color:#fff}.w4-btn.wa:hover{background:#16a34a}
.w4-btn.dark{background:#0a0a0a;color:#fff}.w4-btn.dark:hover{background:#2b2b28}
.w4-btn.light{background:#fff;color:#0a0a0a;border:1px solid #d9d4c9}
.w4-btn.ghost{background:transparent;color:#fff;border:1px solid rgba(255,255,255,.42)}.w4-btn.ghost:hover{background:#fff;color:#0a0a0a}
.w4-btn svg{width:18px;height:18px}
/* grids & tiles */
.w4-grid{display:grid;gap:16px;grid-template-columns:repeat(auto-fill,minmax(250px,1fr))}
.w4-grid.g3{grid-template-columns:repeat(3,1fr)}.w4-grid.g2{grid-template-columns:repeat(2,1fr)}.w4-grid.g4{grid-template-columns:repeat(4,1fr)}
.w4-tile{background:#fff;border:1px solid #e6e3dc;border-radius:20px;padding:24px 24px 22px}
.ink .w4-tile{background:#151514;border-color:#2a2926;color:#fff}
.w4-tile h3{font-family:'Lora',Georgia,serif;font-size:19px;font-weight:600;margin:0 0 8px;line-height:1.25}
.w4-tile p,.w4-tile li{font-size:14.5px;line-height:1.62;color:#55524b;margin:0}
.ink .w4-tile p,.ink .w4-tile li{color:rgba(255,255,255,.66)}
.w4-tile ul{margin:0;padding-left:18px}.w4-tile li{margin:0 0 6px}
.w4-tile .ic{width:42px;height:42px;border-radius:50%;background:#0a0a0a;color:#fff;display:flex;align-items:center;justify-content:center;margin-bottom:16px}
.ink .w4-tile .ic{background:#fff;color:#0a0a0a}
.w4-tile .ic svg{width:20px;height:20px}
/* photo cards */
.w4-pcard{position:relative;display:block;border-radius:24px;overflow:hidden;aspect-ratio:4/5;background:#1b1b1a;color:#fff}
.w4 .w4-pcard{color:#fff}
.w4-pcard.wide{aspect-ratio:16/10}
.w4-pcard img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;transition:transform .6s cubic-bezier(.2,.6,.2,1)}
.w4-pcard:hover img{transform:scale(1.05)}
.w4-pcard::after{content:'';position:absolute;inset:0;background:linear-gradient(to top,rgba(0,0,0,.86) 0%,rgba(0,0,0,.55) 42%,rgba(0,0,0,.08) 72%,rgba(0,0,0,0) 100%)}
.w4-pcard .in{position:absolute;left:0;right:0;bottom:0;padding:22px;z-index:2}
.w4-pcard h3{font-family:'Lora',Georgia,serif;font-size:24px;font-weight:500;margin:0 0 6px;line-height:1.1}
.w4-pcard p{text-shadow:0 1px 8px rgba(0,0,0,.4);font-size:13.5px;line-height:1.5;color:rgba(255,255,255,.8);margin:0}
.w4-pcard .go{display:inline-flex;align-items:center;gap:6px;margin-top:12px;font-size:13px;font-weight:600}
.w4-pcard .cnt{position:absolute;top:14px;left:14px;z-index:2;background:rgba(255,255,255,.92);color:#0a0a0a;font-size:12px;font-weight:600;border-radius:999px;padding:5px 11px}
/* villa cards (thv.acard) as a grid */
.w4-cards{display:grid;gap:16px;grid-template-columns:repeat(auto-fill,minmax(250px,1fr))}
.w4-cards .thb-acw{flex:none;max-width:none;width:100%}
.w4-cards .thb-acard{max-width:none;width:100%}
/* steps */
.w4-steps{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;counter-reset:step}
.w4-steps.s3{grid-template-columns:repeat(3,1fr)}
.w4-step{background:#fff;border:1px solid #e6e3dc;border-radius:20px;padding:24px 22px}
.ink .w4-step{background:#151514;border-color:#2a2926}
.w4-step::before{counter-increment:step;content:counter(step,decimal-leading-zero);font-family:'Lora',Georgia,serif;font-size:34px;font-weight:300;color:#c9c2b4;display:block;margin-bottom:10px}
.ink .w4-step::before{color:#C1B59D}
.w4-step h3{font-family:'Lora',Georgia,serif;font-size:18px;font-weight:600;margin:0 0 7px}
.w4-step p{font-size:14px;color:#6b6b66;line-height:1.58;margin:0}
.ink .w4-step p{color:rgba(255,255,255,.62)}
/* prose */
.w4-prose p{margin:0 0 16px;color:#3b3b36;font-size:16px;line-height:1.75}
.w4-prose ul{margin:0 0 18px 20px;padding:0;color:#3b3b36;font-size:15.5px;line-height:1.7}.w4-prose li{margin:0 0 8px}
.w4-prose h3{font-family:'Lora',Georgia,serif;font-size:21px;font-weight:600;margin:28px 0 10px}
.w4-prose a{text-decoration:underline;text-underline-offset:3px}
/* legal */
.w4-legal section{margin:0 0 46px}
.w4-legal h2{font-family:'Lora',Georgia,serif;font-size:clamp(24px,2.6vw,30px);font-weight:400;line-height:1.15;margin:0 0 14px}
.w4-legal p,.w4-legal li{color:rgba(10,10,10,.72);font-size:15px;line-height:1.8}
.w4-legal p{margin:0 0 14px}.w4-legal ul{margin:0 0 14px 20px;padding:0}
.w4-legal a{text-decoration:underline;text-underline-offset:3px}
.w4-notice{background:#fff8e6;border:1px solid #e8d9a8;border-radius:14px;padding:14px 18px;margin:0 0 36px;font-size:14px;line-height:1.7;color:#3b3b36}
/* chips */
.w4-rel{display:flex;flex-wrap:wrap;gap:10px}
.w4-rel a{border:1px solid #e6e3dc;background:#fff;border-radius:999px;padding:9px 16px;font-size:13.5px;font-weight:500;color:#0a0a0a}
.w4-rel a:hover{border-color:#0a0a0a}
.ink .w4-rel a{background:transparent;border-color:#3a3935;color:#fff}
/* faq */
.w4-faq details{background:#fff;border:1px solid #e6e3dc;border-radius:16px;margin-bottom:10px;overflow:hidden}
.w4-faq summary{cursor:pointer;list-style:none;padding:18px 20px;font-weight:600;font-size:15px;display:flex;justify-content:space-between;align-items:center;gap:12px}
.w4-faq summary::-webkit-details-marker{display:none}
.w4-faq summary::after{content:'+';font-family:'Lora',Georgia,serif;font-size:22px;font-weight:300;color:#8a877f;transition:transform .2s;flex:0 0 auto}
.w4-faq details[open] summary::after{transform:rotate(45deg)}
.w4-faq .a{padding:0 20px 18px;color:#55524b;font-size:14.5px;line-height:1.68}
/* final CTA */
.w4-final{background:#f4f2ed;border:1px solid #e6e3dc;border-radius:28px;text-align:center;padding:72px 24px}
.w4-final.ink{background:#0a0a0a;border-color:#0a0a0a;color:#fff}
.w4-final p.t{color:#6b6b66;max-width:54ch;margin:0 auto 26px;font-size:15.5px;line-height:1.65}
.w4-final.ink p.t{color:rgba(255,255,255,.66)}
.w4-final .w4-btns{justify-content:center}
/* forms */
.w4-form{background:#fff;border:1px solid #e6e3dc;border-radius:24px;padding:26px}
.ink .w4-form{background:#151514;border-color:#2a2926}
.w4-form label{display:block;font-size:12.5px;font-weight:600;color:#6b6b66;margin:0 0 6px}
.ink .w4-form label{color:rgba(255,255,255,.6)}
.w4-form input,.w4-form select,.w4-form textarea{width:100%;border:1px solid #d9d4c9;border-radius:12px;padding:12px 13px;font-size:15px;margin:0 0 16px;background:#fafaf7;color:#0a0a0a;font-family:inherit}
.w4-form textarea{min-height:96px;resize:vertical}
.w4-form .row{display:grid;grid-template-columns:1fr 1fr;gap:0 14px}
.w4-form .w4-btn{width:100%}
.w4-form .fine{font-size:12.5px;color:#8a877f;margin:12px 0 0;line-height:1.5}
/* split */
.w4-split{display:grid;grid-template-columns:1fr 1fr;gap:56px;align-items:center}
.w4-split.top{align-items:start}
.w4-img{border-radius:28px;overflow:hidden;background:#1b1b1a}
.w4-img img{width:100%;height:100%;object-fit:cover;display:block;aspect-ratio:4/3}
.w4-gal{display:grid;grid-template-columns:2fr 1fr;gap:12px}
.w4-gal.one{grid-template-columns:1fr}
.w4-gal img{width:100%;height:100%;object-fit:cover;border-radius:22px;display:block;min-height:0}
.w4-gal .side{display:grid;gap:12px}
.w4-gal>img{aspect-ratio:16/10}
.w4-opts{grid-template-columns:repeat(auto-fill,minmax(210px,1fr))}
.w4-sample{background:#fff8e6;border:1px solid #e8d9a8;border-radius:12px;padding:10px 14px;font-size:13px;color:#55524b;margin:0 0 20px;display:inline-block}
@media(max-width:1023px){.w4-grid.g4{grid-template-columns:repeat(2,1fr)}.w4-steps{grid-template-columns:repeat(2,1fr)}.w4-split{grid-template-columns:1fr;gap:34px}.w4-grid.g3{grid-template-columns:repeat(2,1fr)}}
@media(max-width:640px){.w4-sec{padding:58px 0}.w4-grid.g2,.w4-grid.g3,.w4-grid.g4,.w4-steps,.w4-steps.s3{grid-template-columns:1fr}.w4-hero .w4-wrap{padding-bottom:48px}.w4-head .w4-wrap{padding-top:52px;padding-bottom:52px}.w4-final{padding:52px 20px;border-radius:22px}.w4-form .row{grid-template-columns:1fr}.w4-gal{grid-template-columns:1fr}.w4-pcard{aspect-ratio:4/4.4}.w4-btns .w4-btn{flex:1 1 auto}.w4-opts{grid-template-columns:1fr 1fr;gap:10px}.w4-opts .w4-tile{padding:16px 14px}.w4-opts .ic{display:none}.w4-opts h3{font-size:15.5px}.w4-opts p{font-size:12.5px}}
</style>
"""

ICON = {
    'wa': '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M17.5 14.4c-.3-.2-1.9-.9-2.2-1-.3-.1-.5-.2-.7.1-.2.3-.8 1-1 1.2-.2.2-.4.2-.7.1-.3-.2-1.3-.5-2.5-1.6-.9-.8-1.5-1.8-1.7-2.1-.2-.3 0-.5.1-.6l.5-.6c.2-.2.2-.4.3-.6.1-.2 0-.4 0-.5l-.9-2.3c-.2-.6-.5-.5-.7-.5h-.6c-.2 0-.6.1-.9.4-.3.4-1.1 1.1-1.1 2.6s1.1 3 1.3 3.2c.2.2 2.2 3.4 5.4 4.7 2.7 1.1 3.2.9 3.8.8.6-.1 1.9-.8 2.2-1.5.3-.7.3-1.4.2-1.5-.1-.1-.3-.2-.6-.3zM12 2a10 10 0 0 0-8.6 15.1L2 22l5-1.3A10 10 0 1 0 12 2z"/></svg>',
    'arrow': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M5 12h14"/><path d="M13 6l6 6-6 6"/></svg>',
    'cal': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/></svg>',
    'key': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><circle cx="8" cy="15" r="4"/><path d="M11 12l9-9M17 6l3 3M14 9l2 2"/></svg>',
    'bolt': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="M13 2L4 14h7l-1 8 9-12h-7z"/></svg>',
    'doc': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/><path d="M14 3v6h6M8 13h8M8 17h6"/></svg>',
    'pin': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>',
    'mail': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><rect x="2" y="4" width="20" height="16" rx="3"/><path d="M2 7l10 6 10-6"/></svg>',
    'phone': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1.9.4 1.8.7 2.7a2 2 0 0 1-.5 2.1L8 9.8a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.4c.9.3 1.8.6 2.7.7a2 2 0 0 1 1.7 2z"/></svg>',
    'clock': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 3"/></svg>',
    'star': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="M12 2l3.1 6.3 6.9 1-5 4.9 1.2 6.8L12 17.8 5.8 21l1.2-6.8-5-4.9 6.9-1z"/></svg>',
    'shield': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="M9 12l2 2 4-4"/></svg>',
    'home': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="M3 11l9-8 9 8"/><path d="M5 10v10h14V10"/><path d="M10 20v-6h4v6"/></svg>',
    'wifi': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="M5 12.5a10 10 0 0 1 14 0M8.5 16a5 5 0 0 1 7 0M2 9a15 15 0 0 1 20 0"/><circle cx="12" cy="19.5" r="1"/></svg>',
    'globe': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18"/></svg>',
}


def page(title, desc, body, jsonld=None, image='/images/hero.jpg', extra=''):
    """Home-page shell (rebranded) with `body` in place of the home content."""
    s = rebrand(read_tpl('index.html'), title=title, desc=desc, jsonld=jsonld, image=image)
    for sid in ('thb-hero-show', 'thb-hero-fit'):
        s = re.sub(r'<style id="%s">.*?</style>\s*' % sid, '', s, flags=re.S)
    # home-only scripts: hero slideshow, glass navbar toggle, logo smooth-scroll
    s = re.sub(r'<script>\s*\(function\(\)\{\s*var box=document\.querySelector\(\'\.hs-show\'\).*?</script>\s*', '', s, flags=re.S)
    s = re.sub(r'<script>\s*\(function\(\)\{var nb=document\.getElementById\(\'navbar\'\).*?</script>\s*', '', s, flags=re.S)
    s = re.sub(r'<script>\s*/\* Logo click on the home page.*?</script>\s*', '', s, flags=re.S)
    i = s.index('<section id="thbHero"')
    j = s.index('<style id="thb-footer-css">')
    s = s[:i] + '<main class="w4">\n' + body + '\n</main>\n\n' + s[j:]
    s = s.replace('</head>', CSS + '</head>', 1)
    if extra:
        s = s.replace('</body>', extra + '\n</body>', 1)
    return s


def faq(items):
    """items: [(question, answer_html)] -> (html, FAQPage dict)."""
    h = '<div class="w4-faq">' + ''.join(
        '<details><summary>%s</summary><div class="a">%s</div></details>' % (esc(q), a) for q, a in items) + '</div>'
    ld = {"@context": "https://schema.org", "@type": "FAQPage",
          "mainEntity": [{"@type": "Question", "name": q,
                          "acceptedAnswer": {"@type": "Answer", "text": re.sub('<[^>]+>', '', a)}} for q, a in items]}
    return h, ld


def crumbs_ld(items):
    return {"@context": "https://schema.org", "@type": "BreadcrumbList",
            "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n, "item": u}
                                for i, (n, u) in enumerate(items)]}


def crumbs_html(items):
    parts = []
    for k, (n, u) in enumerate(items):
        parts.append(esc(n) if k == len(items) - 1 else '<a href="%s">%s</a>' % (u, esc(n)))
    return '<div class="w4-crumbs">' + '<span>/</span>'.join(parts) + '</div>'


def section(kicker, h2, inner, sub='', cls='', sid='', narrow=False):
    return ('<section class="w4-sec %s"%s>\n  <div class="w4-wrap%s">\n    <p class="w4-kicker">%s</p>\n    <h2 class="w4-h2">%s</h2>\n%s%s\n  </div>\n</section>\n'
            % (cls, ' id="%s"' % sid if sid else '', ' w4-narrow' if narrow else '', kicker, h2,
               '    <p class="w4-sub">%s</p>\n' % sub if sub else '', inner))


def hero(img, kicker, h1, lead, buttons, chips=None, short=False, alt=''):
    ch = '<div class="w4-chiprow">' + ''.join('<span>%s</span>' % c for c in chips) + '</div>' if chips else ''
    return ('<header class="w4-hero%s">\n  <img src="%s" alt="%s" fetchpriority="high" decoding="async" width="1600" height="1000">\n'
            '  <div class="w4-wrap">\n    %s<p class="w4-kicker">%s</p>\n    <h1 class="w4-h1">%s</h1>\n    <p class="w4-lead">%s</p>\n'
            '    <div class="w4-btns">%s</div>\n  </div>\n</header>\n'
            % (' short' if short else '', img, esc(alt or re.sub('<[^>]+>', '', h1)), ch, kicker, h1, lead, buttons))


def head(kicker, h1, lead, meta='', chips=None):
    ch = '<div class="w4-chiprow">' + ''.join('<span>%s</span>' % c for c in chips) + '</div>' if chips else ''
    return ('<header class="w4-head">\n  <div class="w4-wrap">\n    %s<p class="w4-kicker" style="color:rgba(255,255,255,.5)">%s</p>\n'
            '    <h1 class="w4-h1">%s</h1>\n    <p class="w4-lead">%s</p>\n%s  </div>\n</header>\n'
            % (ch, kicker, h1, lead, '    <p class="w4-meta">%s</p>\n' % meta if meta else ''))


def btn(href, label, kind='dark', icon=None, ext=False):
    ic = ICON.get(icon, '') if icon else ''
    return '<a class="w4-btn %s" href="%s"%s>%s%s</a>' % (kind, esc(href), ' rel="noopener"' if ext else '', ic, label)


def wa_btn(text, label='Message us on WhatsApp', kind='wa'):
    return btn(wa(text), label, kind, 'wa', True)


def tile(title, text, icon=None):
    ic = '<span class="ic">%s</span>' % ICON[icon] if icon else ''
    return '<div class="w4-tile">%s<h3>%s</h3>%s</div>' % (ic, title, text if text.startswith('<') else '<p>%s</p>' % text)


def steps(items, s3=False):
    return ('<div class="w4-steps%s">' % (' s3' if s3 else '')
            + ''.join('<div class="w4-step"><h3>%s</h3><p>%s</p></div>' % (t, p) for t, p in items) + '</div>')


def final(kicker, h2, text, buttons, ink=False):
    return ('<section class="w4-sec" style="border-top:0;padding-top:24px"><div class="w4-wrap"><div class="w4-final%s">'
            '<p class="w4-kicker">%s</p><h2 class="w4-h2" style="margin-bottom:12px">%s</h2><p class="t">%s</p>'
            '<div class="w4-btns">%s</div></div></div></section>\n' % (' ink' if ink else '', kicker, h2, text, buttons))


def villa_card(v, foot='Rate on request <span>&middot; reply on WhatsApp</span>'):
    """thv.acard with a 'Sample listing' badge and our own price line (no prices exist yet)."""
    c = acard(v)
    c = re.sub(r'<p class="p">.*?</p>', '<p class="p">%s</p>' % foot, c, flags=re.S)
    if v.get('sample'):
        c = c.replace('</a>', '</a>' + SAMPLE_BADGE.replace('bottom:10px', 'top:10px'), 1)
    return c


def wa_form_script():
    """Forms with data-wa-form: build a WhatsApp message from the fields and open wa.me (no backend)."""
    return '''<script>
(function(){
  document.querySelectorAll('form[data-wa-form]').forEach(function(f){
    f.addEventListener('submit',function(e){
      e.preventDefault();
      var lines=[f.getAttribute('data-wa-form')];
      f.querySelectorAll('[data-label]').forEach(function(el){
        var v=(el.value||'').trim(); if(v) lines.push(el.getAttribute('data-label')+': '+v);
      });
      var url='https://wa.me/%s?text='+encodeURIComponent(lines.join('\\n'));
      window.open(url,'_blank','noopener');
    });
  });
})();
</script>''' % WA_NUM
