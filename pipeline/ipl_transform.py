"""Ball-by-ball IPL -> season and phase aggregates in data/.

The question: IPL introduced the Impact Player in 2023, letting a side swap
in a substitute mid-match. Did it change how teams bat -- and if so, where in
the innings?
"""
import json
from pathlib import Path

import duckdb

HERE = Path(__file__).parent
RAW, DATA = HERE / 'raw', HERE / 'data'
RULE_SEASON = 2023

BALLS = """
    SELECT *,
           CASE WHEN FLOOR(ball) < 6  THEN 'powerplay'
                WHEN FLOOR(ball) < 15 THEN 'middle'
                ELSE 'death' END              AS phase,
           runs_off_bat + extras              AS runs
    FROM read_csv_auto('{src}', sample_size=-1)
    -- innings 3 and up are super overs: every one is "over 0", so left in
    -- they would all be counted as powerplay, at super-over scoring rates
    WHERE innings IN (1, 2)
"""


def main() -> None:
    DATA.mkdir(exist_ok=True)
    src = RAW / 'ipl' / 'all_matches.csv'
    con = duckdb.connect()
    con.execute('CREATE VIEW b AS ' + BALLS.format(src=src.as_posix()))
    # Cricsheet labels some seasons '2007/08'; the calendar year of the first
    # match is the unambiguous key.
    con.execute("""CREATE VIEW s AS
        SELECT season, CAST(strftime(MIN(start_date), '%Y') AS INT) AS yr
        FROM b GROUP BY season""")

    season = con.execute("""
        SELECT s.yr AS year,
               COUNT(DISTINCT b.match_id) AS matches,
               ROUND(SUM(runs) * 6.0 / COUNT(*), 2) AS rpo,
               ROUND(SUM(CASE WHEN phase='powerplay' THEN runs END) * 6.0
                     / SUM(CASE WHEN phase='powerplay' THEN 1 END), 2) AS powerplay,
               ROUND(SUM(CASE WHEN phase='middle' THEN runs END) * 6.0
                     / SUM(CASE WHEN phase='middle' THEN 1 END), 2) AS middle,
               ROUND(SUM(CASE WHEN phase='death' THEN runs END) * 6.0
                     / SUM(CASE WHEN phase='death' THEN 1 END), 2) AS death,
               ROUND(100.0 * SUM(CASE WHEN runs_off_bat = 6 THEN 1 ELSE 0 END)
                     / COUNT(*), 2) AS six_pct,
               ROUND(COUNT(player_dismissed) * 1.0
                     / COUNT(DISTINCT b.match_id), 1) AS wickets_per_match
        FROM b JOIN s ON b.season = s.season
        GROUP BY 1 ORDER BY 1""").df()

    big = con.execute("""
        WITH totals AS (
            SELECT b.match_id, s.yr AS year, SUM(runs) AS total
            FROM b JOIN s ON b.season = s.season
            WHERE innings = 1 GROUP BY 1, 2)
        SELECT year,
               COUNT(*) AS innings,
               SUM(CASE WHEN total >= 200 THEN 1 ELSE 0 END) AS over_200,
               ROUND(100.0 * SUM(CASE WHEN total >= 200 THEN 1 ELSE 0 END)
                     / COUNT(*), 1) AS pct_200,
               ROUND(AVG(total), 1) AS avg_total
        FROM totals GROUP BY 1 ORDER BY 1""").df()

    era = con.execute(f"""
        SELECT CASE WHEN s.yr >= {RULE_SEASON} THEN 'after' ELSE 'before' END AS era,
               ROUND(SUM(CASE WHEN phase='powerplay' THEN runs END) * 6.0
                     / SUM(CASE WHEN phase='powerplay' THEN 1 END), 2) AS powerplay,
               ROUND(SUM(CASE WHEN phase='middle' THEN runs END) * 6.0
                     / SUM(CASE WHEN phase='middle' THEN 1 END), 2) AS middle,
               ROUND(SUM(CASE WHEN phase='death' THEN runs END) * 6.0
                     / SUM(CASE WHEN phase='death' THEN 1 END), 2) AS death,
               ROUND(COUNT(player_dismissed) * 1.0
                     / COUNT(DISTINCT b.match_id), 1) AS wickets_per_match
        FROM b JOIN s ON b.season = s.season
        GROUP BY 1""").df().set_index('era')

    merged = season.merge(big[['year', 'pct_200', 'avg_total', 'over_200', 'innings']],
                          on='year')
    scope = con.execute('SELECT COUNT(*) n, COUNT(DISTINCT match_id) m FROM b').df().iloc[0]

    payload = {
        'rule_season': RULE_SEASON,
        'balls': int(scope['n']), 'matches': int(scope['m']),
        'first_year': int(merged['year'].min()), 'last_year': int(merged['year'].max()),
        'years': [int(y) for y in merged['year']],
        'matches_by_year': [int(v) for v in merged['matches']],
        'series': {k: [float(v) for v in merged[k]]
                   for k in ['rpo', 'powerplay', 'middle', 'death', 'six_pct',
                             'wickets_per_match', 'pct_200', 'avg_total']},
        'era': {e: {k: float(era.loc[e, k]) for k in era.columns} for e in era.index},
        'manifest': json.loads((RAW / 'ipl_manifest.json').read_text()),
    }
    (DATA / 'ipl_impact.json').write_text(json.dumps(payload, indent=2) + '\n')
    merged.to_csv(DATA / 'ipl_by_season.csv', index=False)

    b_, a_ = payload['era']['before'], payload['era']['after']
    print(f"{payload['matches']:,} matches / {payload['balls']:,} balls")
    for ph in ('powerplay', 'middle', 'death'):
        print(f"  {ph:<10} {b_[ph]:.2f} -> {a_[ph]:.2f}  ({a_[ph] - b_[ph]:+.2f})")
    print(f"  wickets    {b_['wickets_per_match']:.1f} -> {a_['wickets_per_match']:.1f}")


if __name__ == '__main__':
    main()
