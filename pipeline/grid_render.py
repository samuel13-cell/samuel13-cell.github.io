"""data/grid_india.json -> ../grid-india/index.html"""
import json
from datetime import date
from pathlib import Path

import lib

HERE = Path(__file__).parent
OUT = HERE.parent / 'grid-india'


def main() -> None:
    d = json.loads((HERE / 'data' / 'grid_india.json').read_text())
    years = [str(y) for y in d['years']]
    s = d['series']
    i_now, i_prev = len(years) - 1, len(years) - 2

    mix = lib.line_chart(
        years,
        [('Coal', '--c-output', s['coal']),
         ('Solar and wind', '--c-input', s['solar_wind'])],
        lo=0, hi=1600, step=400, every=5)

    share = [round(100 * c / t, 1) for c, t in zip(s['coal'], s['total'])]
    share_chart = lib.line_chart(
        years, [('Coal share', '--c-output', share)],
        lo=60, hi=80, step=5, every=5)

    rows = [[years[i], f"{s['coal'][i]:.0f}", f"{s['solar'][i]:.0f}", f"{s['wind'][i]:.0f}",
             f"{s['hydropower'][i]:.0f}", f"{s['nuclear'][i]:.0f}", f"{s['total'][i]:.0f}",
             f"{s['solar_wind'][i]:.0f}"]
            for i in range(len(years))]

    total_change = s['total'][i_now] - s['total'][i_prev]
    sw_change = s['solar_wind'][i_now] - s['solar_wind'][i_prev]
    man = d['manifest']['files']['power_mix']

    fields = {
        'mix_chart': mix, 'share_chart': share_chart, 'rows_js': json.dumps(rows),
        'coal_change': f"{d['coal_change']:.0f}",
        'coal_drop': f"{abs(d['coal_change']):.0f}",
        'coal_now': f"{d['coal_now']:.0f}", 'coal_prev': f"{d['coal_prev']:.0f}",
        'sw_change': f'{sw_change:.0f}', 'total_change': f'{total_change:.0f}',
        'coal_share_now': f"{d['coal_share_now']:.1f}",
        'coal_share_peak': f"{d['coal_share_peak']:.1f}",
        'coal_share_peak_year': str(d['coal_share_peak_year']),
        'first': str(d['first_year']), 'last': str(d['last_year']),
        'prev': str(d['last_year'] - 1), 'next': str(d['last_year'] + 1),
        'y2019': '2019', 'y2020': '2020', 'd2019': '0.1',
        'src_url': man['url'], 'sha': man['sha256'][:12],
        'built': date.today().strftime('%d %B %Y'),
    }
    page = (HERE / 'grid_template.html').read_text()
    for k, v in fields.items():
        page = page.replace('@@' + k + '@@', v)
    assert '@@' not in page, 'unfilled placeholder remains'

    OUT.mkdir(exist_ok=True)
    (OUT / 'index.html').write_text(page)
    print(f'wrote {OUT / "index.html"}  ({len(page):,} bytes)')


if __name__ == '__main__':
    main()
