"""data/ipl_impact.json -> ../ipl-impact/index.html"""
import json
from datetime import date
from pathlib import Path

import lib

HERE = Path(__file__).parent
OUT = HERE.parent / 'ipl-impact'


def main() -> None:
    d = json.loads((HERE / 'data' / 'ipl_impact.json').read_text())
    years = [str(y) for y in d['years']]
    s = d['series']
    before, after = d['era']['before'], d['era']['after']
    rule_idx = d['years'].index(d['rule_season'])

    phase_chart = lib.line_chart(
        years,
        [('Powerplay', '--c-input',  s['powerplay']),
         ('Middle',    '--c-middle', s['middle']),
         ('Death',     '--c-output', s['death'])],
        lo=6, hi=11, step=1, every=2,
        annotate=(rule_idx, f"{d['rule_season']} · Impact Player"))

    big_chart = lib.bar_chart(years, s['pct_200'], lo=0, hi=60, step=10,
                              var='--c-input', every=2, mark=rule_idx)

    rows = [[year,
             d['matches_by_year'][i],
             f"{s['powerplay'][i]:.2f}",
             f"{s['middle'][i]:.2f}",
             f"{s['death'][i]:.2f}",
             f"{s['six_pct'][i]:.2f}",
             f"{s['wickets_per_match'][i]:.1f}",
             f"{s['pct_200'][i]:.1f}"]
            for i, year in enumerate(years)]

    pct_2022 = s['pct_200'][d['years'].index(2022)]
    man = d['manifest']

    fields = {
        'phase_chart': phase_chart,
        'big_chart': big_chart,
        'rows_js': json.dumps(rows),
        'pp_delta': f"{after['powerplay'] - before['powerplay']:+.2f}",
        'death_delta': f"{after['death'] - before['death']:+.2f}",
        'pct200_last': f"{s['pct_200'][-1]:.0f}",
        'pct200_2022': f"{pct_2022:.0f}",
        'rule_season': str(d['rule_season']),
        'balls': f"{d['balls']:,}", 'matches': f"{d['matches']:,}",
        'first': str(d['first_year']), 'last': str(d['last_year']),
        'src_url': man['url'], 'sha': man['sha256'][:12],
        'built': date.today().strftime('%d %B %Y'),
    }

    html = (HERE / 'ipl_template.html').read_text()
    for k, v in fields.items():
        html = html.replace('@@' + k + '@@', v)
    assert '@@' not in html, 'unfilled placeholder remains'

    OUT.mkdir(exist_ok=True)
    (OUT / 'index.html').write_text(html)
    print(f'wrote {OUT / "index.html"}  ({len(html):,} bytes)')


if __name__ == '__main__':
    main()
