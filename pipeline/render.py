"""data/ -> ../retail-margins/index.html

One self-contained page: no chart library, no build step. Charts are inline
SVG generated here; the hover layer is a small amount of vanilla JS over the
same coordinates.
"""
import json
from datetime import date
from pathlib import Path

import lib
import notes

HERE = Path(__file__).parent
DATA = HERE / 'data'
OUT = HERE.parent / 'retail-margins'

# dataviz categorical slots 1 and 2, validated against this page's surfaces
# (light #fdfdfc, dark #15181e) -- all six checks pass in both modes.
INPUT_L, OUTPUT_L = '#2a78d6', '#eb6834'
INPUT_D, OUTPUT_D = '#3987e5', '#d95926'

def year_ticks(months):
    """One tick per even year, placed at that year's January."""
    return [(i, m[:4]) for i, m in enumerate(months)
            if m.endswith('-01') and int(m[:4]) % 2 == 0]


def main() -> None:
    d = json.loads((DATA / 'retail_margins.json').read_text())
    s, h = d['series'], d['headline']
    months, inp, outp, spread = s['month'], s['input'], s['output'], s['spread']

    ticks = year_ticks(months)
    chain = lib.line_chart(months,
                           [('Inputs', '--c-input', inp),
                            ('Finished', '--c-output', outp)],
                           lo=90, hi=140, step=10, ticks=ticks)
    spread_chart = lib.line_chart(months,
                                  [('Spread', '--c-output', spread)],
                                  lo=95, hi=130, step=5, ticks=ticks)

    rows = []
    for i in range(len(months)):
        rows.append(f'[{json.dumps(months[i])},{inp[i]},{outp[i]},{spread[i]}]')
    series_js = '[' + ','.join(rows) + ']'

    src = d['manifest']['files']['wpi_1112']
    built = date.today().strftime('%d %B %Y')
    last_m = d['last_month']

    OUT.mkdir(exist_ok=True)
    fields = {
        'chain': chain, 'spread_chart': spread_chart, 'series_js': series_js,
        'input_pct': f"{h['input_change_pct']:+.1f}",
        'output_pct': f"{h['output_change_pct']:+.1f}",
        'spread_end': f"{h['spread_end']:.0f}",
        'spread_pts': f"{h['spread_change_pct']:+.0f}",
        'first': lib.pretty_month(d['first_month']), 'last': lib.pretty_month(last_m),
        'months': str(d['months']),
        'src_url': src['url'], 'sha': src['sha256'][:12], 'built': built,
        'build_notes': notes.RETAIL,
        'input_l': INPUT_L, 'output_l': OUTPUT_L,
        'input_d': INPUT_D, 'output_d': OUTPUT_D,
    }
    html = TEMPLATE
    for key, value in fields.items():
        html = html.replace('@@' + key + '@@', value)
    assert '@@' not in html, 'unfilled placeholder remains'
    (OUT / 'index.html').write_text(html)
    print(f'wrote {OUT / "index.html"}  ({len(html):,} bytes)')


TEMPLATE = Path(__file__).with_name('template.html').read_text()

if __name__ == '__main__':
    main()
