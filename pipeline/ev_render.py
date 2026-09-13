"""data/ev_india.json -> ../ev-india/index.html"""
import html
import json
from datetime import date
from pathlib import Path

import lib
import notes

HERE = Path(__file__).parent
OUT = HERE.parent / 'ev-india'


def bars(names, values, highlight):
    top = max(values)
    rows = []
    for name, v in zip(names, values):
        me = ' me' if name == highlight else ''
        rows.append(f'<div class="hbar{me}">'
                    f'<span class="nm">{html.escape(name)}</span>'
                    f'<span class="track"><span class="fill" '
                    f'style="width:{100 * v / top:.1f}%"></span></span>'
                    f'<span class="v">{v:.1f}%</span></div>')
    return '\n    '.join(rows)


def main() -> None:
    d = json.loads((HERE / 'data' / 'ev_india.json').read_text())
    years = [str(y) for y in d['years']]
    ctx = d['context']

    trend = lib.line_chart(
        years,
        [('World', '--c-ctx', ctx['World']),
         ('China', '--c-ctx', ctx['China']),
         ('US', '--c-ctx', ctx['United States']),
         (d['focus'], '--c-output', d['focus_series'])],
        lo=0, hi=60, step=10, every=3)

    names = list(d['top']['countries']); vals = list(d['top']['share'])
    if d['focus'] not in names:
        names.append(d['focus']); vals.append(d['india_now'])

    def cell(v):
        return '' if v is None else f'{v:.2f}'

    rows = [[years[i], cell(d['focus_series'][i]), cell(ctx['World'][i]), cell(ctx['China'][i])]
            for i in range(len(years))]

    man = d['manifest']['files']['ev_share']
    fields = {
        'trend_chart': trend,
        'ranking_bars': bars(names, vals, d['focus']),
        'rows_js': json.dumps(rows),
        'india_now': f"{d['india_now']:.1f}", 'india_prev': f"{d['india_prev']:.1f}",
        'world_now': f"{d['world_now']:.0f}",
        'rank': str(d['rank']), 'of': str(d['of_countries']),
        'first': str(d['first_year']), 'last': str(d['last_year']),
        'prev': str(d['last_year'] - 1),
        'src_url': man['url'], 'sha': man['sha256'][:12],
        'built': date.today().strftime('%d %B %Y'),
        'build_notes': notes.EV,
    }
    page = (HERE / 'ev_template.html').read_text()
    for k, v in fields.items():
        page = page.replace('@@' + k + '@@', v)
    assert '@@' not in page, 'unfilled placeholder remains'

    OUT.mkdir(exist_ok=True)
    (OUT / 'index.html').write_text(page)
    print(f'wrote {OUT / "index.html"}  ({len(page):,} bytes)')


if __name__ == '__main__':
    main()
