"""data/ -> ../retail-margins/index.html

One self-contained page: no chart library, no build step. Charts are inline
SVG generated here; the hover layer is a small amount of vanilla JS over the
same coordinates.
"""
import json
from datetime import date
from pathlib import Path

HERE = Path(__file__).parent
DATA = HERE / 'data'
OUT = HERE.parent / 'retail-margins'

# dataviz categorical slots 1 and 2, validated against this page's surfaces
# (light #fdfdfc, dark #15181e) -- all six checks pass in both modes.
INPUT_L, OUTPUT_L = '#2a78d6', '#eb6834'
INPUT_D, OUTPUT_D = '#3987e5', '#d95926'

MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July',
          'August', 'September', 'October', 'November', 'December']

W, H = 760, 300
PAD = {'t': 18, 'r': 108, 'b': 30, 'l': 44}


def scales(months, lo, hi):
    iw = W - PAD['l'] - PAD['r']
    ih = H - PAD['t'] - PAD['b']
    x = lambda i: PAD['l'] + iw * i / (len(months) - 1)
    y = lambda v: PAD['t'] + ih * (1 - (v - lo) / (hi - lo))
    return x, y


def path(xs, ys, values):
    return 'M' + ' L'.join(f'{xs(i):.1f},{ys(v):.1f}' for i, v in enumerate(values))


def year_ticks(months):
    out = []
    for i, m in enumerate(months):
        if m.endswith('-01') and int(m[:4]) % 2 == 0:
            out.append((i, m[:4]))
    return out


def line_chart(months, series, lo, hi, gridline_step=10):
    """series: list of (key, label, colour-var, values)"""
    xs, ys = scales(months, lo, hi)
    parts = []

    # gridlines + y labels
    v = lo
    while v <= hi:
        yy = ys(v)
        parts.append(f'<line class="grid" x1="{PAD["l"]}" y1="{yy:.1f}" '
                     f'x2="{W - PAD["r"]}" y2="{yy:.1f}"/>')
        parts.append(f'<text class="ax" x="{PAD["l"] - 8}" y="{yy + 3.5:.1f}" '
                     f'text-anchor="end">{v:g}</text>')
        v += gridline_step

    for i, lab in year_ticks(months):
        parts.append(f'<text class="ax" x="{xs(i):.1f}" y="{H - 10}" '
                     f'text-anchor="middle">{lab}</text>')

    for key, label, var, values in series:
        parts.append(f'<path class="ln" stroke="var({var})" d="{path(xs, ys, values)}"/>')
        last = len(values) - 1
        parts.append(f'<circle class="dot" cx="{xs(last):.1f}" cy="{ys(values[last]):.1f}" '
                     f'r="4.5" fill="var({var})"/>')
        parts.append(f'<text class="dl" x="{xs(last) + 11:.1f}" y="{ys(values[last]) + 4:.1f}" '
                     f'fill="var({var})">{label}</text>')

    parts.append(f'<line class="cross" x1="0" y1="{PAD["t"]}" x2="0" '
                 f'y2="{H - PAD["b"]}" style="opacity:0"/>')
    return '\n    '.join(parts)


def pretty(ym: str) -> str:
    """'2012-04' -> 'April 2012'"""
    y, m = ym.split('-')
    return f"{MONTHS[int(m) - 1]} {y}"


def main() -> None:
    d = json.loads((DATA / 'retail_margins.json').read_text())
    s, h = d['series'], d['headline']
    months, inp, outp, spread = s['month'], s['input'], s['output'], s['spread']

    chain = line_chart(months,
                       [('input', 'Inputs', '--c-input', inp),
                        ('output', 'Finished', '--c-output', outp)],
                       90, 140)
    spread_chart = line_chart(months,
                              [('spread', 'Spread', '--c-output', spread)],
                              95, 130, gridline_step=10)

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
        'first': pretty(d['first_month']), 'last': pretty(last_m),
        'months': str(d['months']),
        'src_url': src['url'], 'sha': src['sha256'][:12], 'built': built,
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
