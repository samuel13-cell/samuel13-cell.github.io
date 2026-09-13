"""data/ott_india.json -> ../ott-india/index.html"""
import html
import json
from datetime import date
from pathlib import Path

import lib

HERE = Path(__file__).parent
OUT = HERE.parent / 'ott-india'


def ranking_bars(countries, pcts, highlight):
    """A ranked list reads better than a chart here: the names are the point,
    and a horizontal bar per row keeps them left-aligned and legible."""
    top = max(pcts)
    rows = []
    for name, pct in zip(countries, pcts):
        me = ' me' if name == highlight else ''
        width = 100 * pct / top
        rows.append(
            f'<div class="hbar{me}">'
            f'<span class="nm">{html.escape(name)}</span>'
            f'<span class="track"><span class="fill" style="width:{width:.1f}%"></span></span>'
            f'<span class="v">{pct:.1f}%</span></div>')
    return '\n    '.join(rows)


def main() -> None:
    d = json.loads((HERE / 'data' / 'ott_india.json').read_text())
    years = [str(y) for y in d['yearly']['years']]
    pct_local = d['yearly']['pct_local']

    ranked_names = list(d['ranking']['countries'])
    ranked_pcts = list(d['ranking']['pct_local'])
    if d['country'] not in ranked_names:          # always show India in the list
        ranked_names.append(d['country'])
        ranked_pcts.append(d['india_pct'])

    yearly_chart = lib.line_chart(
        years, [('Local share', '--c-input', pct_local)],
        lo=0, hi=12, step=2, every=1)

    bands = [[f'{lbl} {"country" if lbl == "India only" else "countries"}'
              if lbl != 'India only' else 'India only',
              f'{s:,}', f'{p}%']
             for lbl, s, p in zip(d['bands']['labels'], d['bands']['slots'], d['bands']['pct'])]

    india_only = next((p for l, p in zip(d['bands']['labels'], d['bands']['pct'])
                       if l == 'India only'), 0.0)
    peak_year = str(d['yearly']['years'][pct_local.index(max(pct_local))])
    man = d['manifest']

    fields = {
        'ranking_bars': ranking_bars(ranked_names, ranked_pcts, d['country']),
        'yearly_chart': yearly_chart,
        'bands_js': json.dumps(bands),
        'yearly_js': json.dumps([[y, p] for y, p in zip(years, pct_local)]),
        'india_pct': f"{d['india_pct']:.1f}",
        'rank': str(d['india_rank']), 'of': str(d['of_countries']),
        'top_pct': f"{d['ranking']['pct_local'][0]:.0f}",
        'film_local': f"{d['split']['Films']['pct_local']:.1f}",
        'tv_local': f"{d['split']['TV']['pct_local']:.1f}",
        'film_reach': f"{d['split']['Films']['avg_reach']:.0f}",
        'tv_reach': f"{d['split']['TV']['avg_reach']:.0f}",
        'india_only_pct': f'{india_only:.1f}',
        'peak_year': peak_year,
        'first_year': years[0], 'last_year': years[-1],
        'first_week': d['first_week'], 'last_week': d['last_week'],
        'slots': f"{d['slots']:,}", 'titles': f"{d['titles']:,}",
        'weeks': str(d['weeks']),
        'src_url': man['url'], 'sha': man['sha256'][:12],
        'built': date.today().strftime('%d %B %Y'),
    }

    page = (HERE / 'ott_template.html').read_text()
    for k, v in fields.items():
        page = page.replace('@@' + k + '@@', v)
    assert '@@' not in page, 'unfilled placeholder remains'

    OUT.mkdir(exist_ok=True)
    (OUT / 'index.html').write_text(page)
    print(f'wrote {OUT / "index.html"}  ({len(page):,} bytes)')


if __name__ == '__main__':
    main()
