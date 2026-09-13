"""EV share of new car sales: where India sits, and how fast it moved.

The measure is the share of new cars sold that are electric, so it is a
statement about what people are buying now, not about the fleet on the road,
which turns over slowly.
"""
import json
from pathlib import Path

import duckdb

HERE = Path(__file__).parent
RAW, DATA = HERE / 'raw', HERE / 'data'
VALUE = '"Share of new cars that are electric"'
FOCUS = 'India'
CONTEXT = ['World', 'China', 'United States']


def main() -> None:
    DATA.mkdir(exist_ok=True)
    con = duckdb.connect()
    con.execute(f"""CREATE VIEW e AS SELECT Entity, Code, Year,
        {VALUE} AS share FROM read_csv_auto('{(RAW / 'ev_share.csv').as_posix()}',
        sample_size=-1)""")

    last = con.execute('SELECT MAX(Year) FROM e').fetchone()[0]
    first = con.execute(f"SELECT MIN(Year) FROM e WHERE Entity = '{FOCUS}'").fetchone()[0]

    years = [int(r[0]) for r in con.execute(
        f"SELECT DISTINCT Year FROM e WHERE Year >= {first} ORDER BY Year").fetchall()]

    def series(entity):
        rows = dict(con.execute(
            f"SELECT Year, share FROM e WHERE Entity = '{entity}'").fetchall())
        return [None if rows.get(y) is None else round(float(rows[y]), 2) for y in years]

    # Countries are ranked on the latest year; only sovereign entities carry a
    # three-letter code, which drops aggregates like 'World' and 'Europe'.
    ranking = con.execute(f"""
        SELECT Entity, ROUND(share, 1) AS share FROM e
        WHERE Year = {last} AND Code IS NOT NULL AND Code <> 'OWID_WRL'
        ORDER BY share DESC""").df()

    india_rank = int(ranking.index[ranking.Entity == FOCUS][0]) + 1
    india_now = float(ranking.loc[ranking.Entity == FOCUS, 'share'].iloc[0])
    india_prev = con.execute(
        f"SELECT share FROM e WHERE Entity = '{FOCUS}' AND Year = {last - 1}").fetchone()[0]
    world_now = con.execute(
        f"SELECT share FROM e WHERE Entity = 'World' AND Year = {last}").fetchone()[0]

    payload = {
        'first_year': first, 'last_year': last, 'years': years,
        'focus': FOCUS, 'focus_series': series(FOCUS),
        'context': {c: series(c) for c in CONTEXT},
        'rank': india_rank, 'of_countries': int(len(ranking)),
        'india_now': india_now, 'india_prev': round(float(india_prev), 2),
        'world_now': round(float(world_now), 1),
        'top': {'countries': list(ranking.Entity.head(10)),
                'share': [float(v) for v in ranking.share.head(10)]},
        'manifest': json.loads((RAW / 'owid_manifest.json').read_text()),
    }
    (DATA / 'ev_india.json').write_text(json.dumps(payload, indent=2) + '\n')
    ranking.to_csv(DATA / 'ev_ranking.csv', index=False)

    print(f"{FOCUS}: {payload['india_prev']}% ({last-1}) -> {india_now}% ({last}); "
          f"world {payload['world_now']}%; rank {india_rank} of {payload['of_countries']}")


if __name__ == '__main__':
    main()
