#!/usr/bin/env python3
"""Inject the shared nav into every built page and mark the current tab.

The nav is generated from the pages that actually exist on disk, so a
project that has not been built yet never appears as a dead tab. Each page
carries a <!--NAV--><!--/NAV--> slot; links are rewritten per page depth so
they resolve from the site root and from a project subdirectory alike.
"""
import html as html_mod
import re
from pathlib import Path

ROOT = Path(__file__).parent
SLOT = re.compile(r'<!--NAV-->.*?<!--/NAV-->', re.S)

# file -> (slug, label, href-from-root, prefix-back-to-root)
PAGES = [
    ('index.html',                  'home',           'Resume',            '',                  ''),
    ('retail-margins/index.html',   'retail-margins', 'Margins',   'retail-margins/',   '../'),
    ('ipl-impact/index.html',       'ipl-impact',     'IPL', 'ipl-impact/',       '../'),
    ('ott-india/index.html',        'ott-india',      'Netflix',     'ott-india/',        '../'),
    ('ev-india/index.html',         'ev-india',       'EV cars',     'ev-india/',         '../'),
    ('grid-india/index.html',       'grid-india',     'Coal',         'grid-india/',       '../'),
]


def main() -> None:
    template = (ROOT / 'assets' / 'nav.html').read_text().strip()
    live = [p for p in PAGES if (ROOT / p[0]).exists()]
    missing = [p[0] for p in PAGES if p not in live]
    for m in missing:
        print(f'not built yet, omitted from nav: {m}')

    for rel, slug, _, _, back in live:
        tabs = []
        for _, other_slug, label, href, _ in live:
            target = (back + href) or './'
            current = ' aria-current="page"' if other_slug == slug else ''
            tabs.append(f'<li><a href="{target}"{current}>{html_mod.escape(label)}</a></li>')

        nav = (template
               .replace('@@root@@', back or './')
               .replace('@@tabs@@', '\n    ' + '\n    '.join(tabs) + '\n  '))
        if slug == 'home':
            nav = nav.replace('<nav class="nav"', '<nav class="nav is-home"', 1)

        path = ROOT / rel
        page = path.read_text()
        if not SLOT.search(page):
            print(f'skip {rel} (no NAV slot)')
            continue
        path.write_text(SLOT.sub('<!--NAV-->' + nav + '<!--/NAV-->', page))
        print(f'nav -> {rel}  ({len(live)} tabs, current: {slug})')


if __name__ == '__main__':
    main()
