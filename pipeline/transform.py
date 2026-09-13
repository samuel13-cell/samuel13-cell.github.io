"""raw/ -> DuckDB -> tidy monthly series + derived measures in data/.

The value chain, as the WPI codes it:

    raw hides & skins  ->  tanned leather  ->  finished footwear

All three stages come from one publisher, one base year and one methodology,
so the spread between them is a like-for-like comparison rather than a
mash-up of two different baskets.
"""
import json
from pathlib import Path

import duckdb
import pandas as pd

HERE = Path(__file__).parent
RAW, DATA = HERE / 'raw', HERE / 'data'
BASE_LABEL = 'Apr 2012'

# WPI commodity codes, 2011-12 base.
SERIES = {
    1102030001: ('hides_raw',      'Hides (raw)',        'input'),
    1102030002: ('skins_raw',      'Skins (raw)',        'input'),
    1306010000: ('tanned_leather', 'Tanned leather',     'intermediate'),
    1306030001: ('leather_shoes',  'Leather shoes',      'output'),
    1306030000: ('footwear',       'Footwear',           'output'),
}


def load_long() -> pd.DataFrame:
    """Wide monthly columns (INDXMMYYYY) -> one row per series per month."""
    df = pd.read_excel(RAW / 'wpi_1112.xls', sheet_name=0)
    month_cols = [c for c in df.columns if str(c).startswith('INDX')]

    df = df[df['COMM_CODE'].isin(SERIES)].copy()
    df['series'] = df['COMM_CODE'].map(lambda c: SERIES[c][0])
    df['label'] = df['COMM_CODE'].map(lambda c: SERIES[c][1])
    df['stage'] = df['COMM_CODE'].map(lambda c: SERIES[c][2])

    long = df.melt(id_vars=['series', 'label', 'stage', 'COMM_WT'],
                   value_vars=month_cols, var_name='col', value_name='index_value')
    # INDX + MM + YYYY -> a real date
    long['month'] = pd.to_datetime(long['col'].str[4:6] + '-' + long['col'].str[6:],
                                   format='%m-%Y')
    long['index_value'] = pd.to_numeric(long['index_value'], errors='coerce')
    long = long.rename(columns={'COMM_WT': 'weight'})
    return long.dropna(subset=['index_value'])[
        ['month', 'series', 'label', 'stage', 'weight', 'index_value']]


def main() -> None:
    DATA.mkdir(exist_ok=True)
    con = duckdb.connect()
    con.register('wpi', load_long())

    # Weight-average the two raw inputs into one input-cost series, and the two
    # finished-goods series into one output series, so the headline chart
    # compares one stage against another rather than five lines against
    # each other.
    con.execute("""
        CREATE TABLE stage_monthly AS
        SELECT month,
               stage,
               SUM(index_value * weight) / SUM(weight) AS index_value
        FROM wpi
        WHERE stage IN ('input', 'output')
        GROUP BY month, stage
        ORDER BY month, stage
    """)

    # Rebase every stage to 100 at the first common month, so the two are
    # directly comparable on one axis. (Never two y-scales.)
    con.execute("""
        CREATE TABLE stage_indexed AS
        WITH base AS (
            SELECT stage, index_value AS base_value
            FROM stage_monthly
            WHERE month = (SELECT MIN(month) FROM stage_monthly)
        )
        SELECT s.month, s.stage,
               ROUND(100.0 * s.index_value / b.base_value, 2) AS rebased
        FROM stage_monthly s JOIN base b USING (stage)
        ORDER BY s.month, s.stage
    """)

    # The margin proxy: how far finished-goods prices have run ahead of input
    # costs since the base month. 100 = the two have moved together.
    con.execute("""
        CREATE TABLE margin_proxy AS
        SELECT month,
               ROUND(100.0 * MAX(CASE WHEN stage='output' THEN rebased END)
                           / MAX(CASE WHEN stage='input'  THEN rebased END), 2) AS spread
        FROM stage_indexed
        GROUP BY month
        HAVING COUNT(DISTINCT stage) = 2
        ORDER BY month
    """)

    # Per-series annual averages, for the table under the charts.
    con.execute("""
        CREATE TABLE annual AS
        SELECT YEAR(month) AS year, series, label, stage,
               ROUND(AVG(index_value), 1) AS avg_index
        FROM wpi GROUP BY 1,2,3,4 ORDER BY year, stage, series
    """)

    indexed = con.execute('SELECT * FROM stage_indexed').df()
    spread = con.execute('SELECT * FROM margin_proxy').df()
    annual = con.execute('SELECT * FROM annual').df()

    wide = indexed.pivot(index='month', columns='stage', values='rebased').reset_index()
    first, last = spread.iloc[0], spread.iloc[-1]
    ends = con.execute("""
        SELECT stage,
               MAX(CASE WHEN month=(SELECT MIN(month) FROM stage_indexed) THEN rebased END) AS start,
               MAX(CASE WHEN month=(SELECT MAX(month) FROM stage_indexed) THEN rebased END) AS end
        FROM stage_indexed GROUP BY stage
    """).df().set_index('stage')

    payload = {
        'base_label': BASE_LABEL,
        'first_month': wide['month'].min().strftime('%Y-%m'),
        'last_month': wide['month'].max().strftime('%Y-%m'),
        'months': len(wide),
        'series': {
            'month': [m.strftime('%Y-%m') for m in wide['month']],
            'input': [None if pd.isna(v) else float(v) for v in wide['input']],
            'output': [None if pd.isna(v) else float(v) for v in wide['output']],
            'spread': [float(v) for v in spread['spread']],
        },
        'headline': {
            'input_change_pct': round(float(ends.loc['input', 'end']) - 100, 1),
            'output_change_pct': round(float(ends.loc['output', 'end']) - 100, 1),
            'spread_start': float(first['spread']),
            'spread_end': float(last['spread']),
            'spread_change_pct': round(float(last['spread']) - float(first['spread']), 1),
        },
        'manifest': json.loads((RAW / 'manifest.json').read_text()),
    }

    (DATA / 'retail_margins.json').write_text(json.dumps(payload, indent=2) + '\n')
    annual.to_csv(DATA / 'annual_by_series.csv', index=False)

    h = payload['headline']
    print(f"months {payload['months']}  {payload['first_month']} -> {payload['last_month']}")
    print(f"inputs  {h['input_change_pct']:+.1f}%   outputs {h['output_change_pct']:+.1f}%")
    print(f"spread  {h['spread_start']:.1f} -> {h['spread_end']:.1f}  ({h['spread_change_pct']:+.1f} pts)")


if __name__ == '__main__':
    main()
