"""India's electricity generation by source, and the 2025 turn.

Generation, not capacity: capacity is what is built, generation is what is
actually produced, and for a grid dominated by coal the gap between the two
is the whole argument.
"""
import json
from pathlib import Path

import duckdb

HERE = Path(__file__).parent
RAW, DATA = HERE / 'raw', HERE / 'data'
FOCUS = 'India'
START = 2000
SOURCES = ['Coal', 'Solar', 'Wind', 'Hydropower', 'Nuclear', 'Gas', 'Bioenergy', 'Oil']


def main() -> None:
    DATA.mkdir(exist_ok=True)
    con = duckdb.connect()
    cols = ', '.join(f'"{s}" AS {s.lower()}' for s in SOURCES)
    con.execute(f"""CREATE VIEW g AS SELECT Entity, Year, {cols}
        FROM read_csv_auto('{(RAW / 'power_mix.csv').as_posix()}', sample_size=-1)
        WHERE Entity = '{FOCUS}' AND Year >= {START}""")

    df = con.execute("""
        SELECT Year,
               coal, solar, wind, hydropower, nuclear, gas, bioenergy, oil,
               solar + wind AS solar_wind,
               coal + solar + wind + hydropower + nuclear + gas + bioenergy + oil AS total
        FROM g ORDER BY Year""").df()

    last = int(df.Year.max())
    prev = df[df.Year == last - 1].iloc[0]
    now = df[df.Year == last].iloc[0]

    # Every year-on-year change in coal generation, so "first fall" is a
    # claim the data supports rather than an impression.
    coal_deltas = con.execute("""
        SELECT Year, ROUND(coal - LAG(coal) OVER (ORDER BY Year), 1) AS delta
        FROM g ORDER BY Year""").df().dropna()
    falls = [int(r.Year) for r in coal_deltas.itertuples() if r.delta < 0]

    payload = {
        'focus': FOCUS, 'first_year': int(df.Year.min()), 'last_year': last,
        'years': [int(y) for y in df.Year],
        'series': {k: [round(float(v), 1) for v in df[k]]
                   for k in ['coal', 'solar', 'wind', 'solar_wind', 'hydropower',
                             'nuclear', 'gas', 'total']},
        'coal_now': round(float(now.coal), 0), 'coal_prev': round(float(prev.coal), 0),
        'coal_change': round(float(now.coal - prev.coal), 0),
        'sw_now': round(float(now.solar_wind), 0), 'sw_prev': round(float(prev.solar_wind), 0),
        'solar_growth_pct': round(100 * (now.solar - prev.solar) / prev.solar, 0),
        'coal_share_now': round(100 * now.coal / now.total, 1),
        'coal_share_peak': round(100 * (df.coal / df.total).max(), 1),
        'coal_share_peak_year': int(df.Year[(df.coal / df.total).idxmax()]),
        'sw_share_now': round(100 * now.solar_wind / now.total, 1),
        'coal_fall_years': falls,
        'manifest': json.loads((RAW / 'owid_manifest.json').read_text()),
    }
    (DATA / 'grid_india.json').write_text(json.dumps(payload, indent=2) + '\n')
    df.to_csv(DATA / 'grid_india_by_year.csv', index=False)

    print(f"coal {payload['coal_prev']:.0f} -> {payload['coal_now']:.0f} TWh "
          f"({payload['coal_change']:+.0f})")
    print(f"solar+wind {payload['sw_prev']:.0f} -> {payload['sw_now']:.0f} TWh")
    print(f"coal share {payload['coal_share_peak']}% ({payload['coal_share_peak_year']}) "
          f"-> {payload['coal_share_now']}%")
    print(f"years coal generation fell since {START}: {falls}")


if __name__ == '__main__':
    main()
