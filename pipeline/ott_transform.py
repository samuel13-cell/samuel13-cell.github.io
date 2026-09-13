"""Netflix country Top 10 -> how far India's hits travel.

There is no language column in this data, so rather than guess at one, a
title's origin is inferred from its behaviour: count how many of the 90-odd
countries it ever charts in. A title that appears only in India is made for
India; one that charts in 60 countries is a global release that India happens
to watch. That is measured, not assumed.
"""
import json
from pathlib import Path

import duckdb

HERE = Path(__file__).parent
RAW, DATA = HERE / 'raw', HERE / 'data'
COUNTRY = 'India'
LOCAL_MAX = 5          # charts in at most this many countries = locally anchored
MIN_SLOTS = 2000       # exclude countries with thin coverage from the ranking


def main() -> None:
    DATA.mkdir(exist_ok=True)
    con = duckdb.connect()
    con.execute(f"""CREATE VIEW t AS SELECT * FROM read_csv_auto(
        '{(RAW / 'netflix_countries.tsv').as_posix()}',
        delim='\t', header=true, sample_size=-1)""")
    con.execute("""CREATE VIEW reach AS
        SELECT show_title, category, COUNT(DISTINCT country_name) AS countries
        FROM t GROUP BY 1, 2""")
    con.execute("""CREATE VIEW j AS
        SELECT i.*, r.countries FROM t i JOIN reach r USING (show_title, category)""")

    bands = con.execute(f"""
        SELECT CASE WHEN countries = 1  THEN 'India only'
                    WHEN countries <= 5 THEN '2 to 5'
                    WHEN countries <= 20 THEN '6 to 20'
                    WHEN countries <= 50 THEN '21 to 50'
                    ELSE '51 or more' END AS band,
               MIN(countries) AS ord, COUNT(*) AS slots,
               ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct
        FROM j WHERE country_name = '{COUNTRY}'
        GROUP BY 1 ORDER BY ord""").df()

    yearly = con.execute(f"""
        SELECT CAST(strftime(week, '%Y') AS INT) AS year,
               COUNT(*) AS slots,
               ROUND(100.0 * SUM(CASE WHEN countries <= {LOCAL_MAX} THEN 1 ELSE 0 END)
                     / COUNT(*), 1) AS pct_local
        FROM j WHERE country_name = '{COUNTRY}'
        GROUP BY 1 ORDER BY 1""").df()

    ranked = con.execute(f"""
        WITH per_country AS (
            SELECT country_name,
                   ROUND(100.0 * SUM(CASE WHEN countries <= {LOCAL_MAX} THEN 1 ELSE 0 END)
                         / COUNT(*), 1) AS pct_local
            FROM j GROUP BY 1 HAVING COUNT(*) >= {MIN_SLOTS})
        SELECT country_name, pct_local,
               RANK() OVER (ORDER BY pct_local DESC) AS rank,
               COUNT(*) OVER () AS of_countries
        FROM per_country ORDER BY pct_local DESC""").df()

    split = con.execute(f"""
        SELECT category, COUNT(*) AS slots,
               ROUND(100.0 * SUM(CASE WHEN countries <= {LOCAL_MAX} THEN 1 ELSE 0 END)
                     / COUNT(*), 1) AS pct_local,
               ROUND(AVG(countries), 1) AS avg_reach
        FROM j WHERE country_name = '{COUNTRY}'
        GROUP BY 1 ORDER BY 1""").df().set_index('category')

    scope = con.execute(f"""
        SELECT COUNT(*) AS slots, COUNT(DISTINCT show_title) AS titles,
               COUNT(DISTINCT week) AS weeks, MIN(week) AS first_wk, MAX(week) AS last_wk
        FROM t WHERE country_name = '{COUNTRY}'""").df().iloc[0]

    india = ranked[ranked.country_name == COUNTRY].iloc[0]
    top = ranked.head(12)

    payload = {
        'country': COUNTRY, 'local_max': LOCAL_MAX,
        'slots': int(scope['slots']), 'titles': int(scope['titles']),
        'weeks': int(scope['weeks']),
        'first_week': str(scope['first_wk'])[:10], 'last_week': str(scope['last_wk'])[:10],
        'bands': {'labels': list(bands['band']), 'pct': [float(v) for v in bands['pct']],
                  'slots': [int(v) for v in bands['slots']]},
        'yearly': {'years': [int(v) for v in yearly['year']],
                   'pct_local': [float(v) for v in yearly['pct_local']]},
        'ranking': {'countries': list(top['country_name']),
                    'pct_local': [float(v) for v in top['pct_local']]},
        'india_rank': int(india['rank']), 'india_pct': float(india['pct_local']),
        'of_countries': int(india['of_countries']),
        'split': {c: {'pct_local': float(split.loc[c, 'pct_local']),
                      'avg_reach': float(split.loc[c, 'avg_reach'])} for c in split.index},
        'manifest': json.loads((RAW / 'ott_manifest.json').read_text()),
    }
    (DATA / 'ott_india.json').write_text(json.dumps(payload, indent=2) + '\n')
    ranked.to_csv(DATA / 'ott_country_ranking.csv', index=False)
    yearly.to_csv(DATA / 'ott_india_yearly.csv', index=False)

    print(f"{payload['slots']:,} slots, {payload['titles']:,} titles, "
          f"{payload['weeks']} weeks ({payload['first_week']} to {payload['last_week']})")
    print(f"India ranks {payload['india_rank']} of {payload['of_countries']} "
          f"at {payload['india_pct']}% locally anchored")
    for c in payload['split']:
        print(f"  {c:<6} local {payload['split'][c]['pct_local']}%  "
              f"avg reach {payload['split'][c]['avg_reach']} countries")


if __name__ == '__main__':
    main()
