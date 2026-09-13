"""Per-project content for the Build notes appendix.

Kept apart from the renderers so the prose sits in one place and the
renderers stay about rendering.
"""
import buildnotes

CLONE = ('git clone https://github.com/samuel13-cell/samuel13-cell.github.io\n'
         'cd samuel13-cell.github.io/pipeline\n'
         'pip install -r requirements.txt\n')

_OWID_SOURCE = (
    'Our World in Data, compiled from Ember and the Energy Institute. Chosen '
    'after India’s own portal proved unusable: data.gov.in disallows '
    'crawling in its robots.txt, and its API offers no search, so finding a '
    'dataset would have meant paging 287,810 records at 100 per request.')

_RENDER = ('Static HTML with inline SVG. No chart library, no build step and no '
           'JavaScript beyond the hover layer, so the page has nothing to rot.')

_COLOURS = ('The categorical blue, orange and violet, each validated against '
            'this page’s own surface for lightness, chroma, colour-blind '
            'separation and contrast rather than assumed to carry over. Every '
            'green candidate for a third series failed: all of them collided '
            'with the orange under protanopia.')

GRID = buildnotes.section(
    repo_path='pipeline/',
    stack=[
        ('Source', _OWID_SOURCE),
        ('Fetch', 'owid_fetch.py, plain requests. The CSV is stored byte for byte '
                  'with its sha256, so a parse change re-runs without a refetch and '
                  'every number here traces back to a specific file.'),
        ('Transform', 'grid_transform.py, DuckDB straight over the raw CSV. No '
                      'database server and no ORM: the query is the analysis.'),
        ('Render', _RENDER),
        ('Colour', _COLOURS),
    ],
    steps=[
        'Download the generation CSV and record url, size and sha256 in a manifest.',
        'Load it into DuckDB and filter to India from 2000, keeping the eight '
        'published sources.',
        'Derive a combined solar-and-wind series and a total, so shares are of '
        'generation rather than of installed capacity.',
        'Compute every year-on-year change in coal with a window function, which is '
        'what turns &ldquo;coal fell&rdquo; from an impression into a checkable claim.',
        'Write a JSON payload plus a CSV, then render the page from the payload.',
    ],
    code_caption='The query the headline rests on',
    code='''<b>SELECT</b> Year,
       <b>ROUND</b>(coal  - <b>LAG</b>(coal)  <b>OVER</b> (<b>ORDER BY</b> Year), 2) <b>AS</b> d_coal,
       <b>ROUND</b>(total - <b>LAG</b>(total) <b>OVER</b> (<b>ORDER BY</b> Year), 2) <b>AS</b> d_total
<b>FROM</b> g
<b>QUALIFY</b> d_coal &lt; 0
<b>ORDER BY</b> Year;

-- Year   d_coal   d_total
-- 2019    -0.10    +29.33
-- 2020   -54.98    -37.55
-- 2025   -43.75    +45.08''',
    checks=[
        'Every prior year in which coal fell, not only the latest. An early draft of '
        'this page claimed 2025 was the first fall, which the data does not support.',
        'The 2019 fall is 0.10 TWh against a base of 1,199, a rounding margin rather '
        'than a turn.',
        'The 2020 fall came with total generation falling 37.55 TWh, so coal fell '
        'because everything fell.',
        'Totals are summed from the eight published sources rather than read from a '
        'total column, so the parts and the whole cannot disagree.',
    ],
    repro=CLONE + 'python owid_fetch.py      # download + manifest\n'
                  'python grid_transform.py  # DuckDB -> data/grid_india.json\n'
                  'python grid_render.py     # -> ../grid-india/index.html\n'
                  'python ../build_site.py   # inject the shared nav',
)

EV = buildnotes.section(
    repo_path='pipeline/',
    stack=[
        ('Source', 'Our World in Data, compiled from the IEA Global EV Outlook. One '
                   'CSV, no key, no crawl restriction.'),
        ('Fetch', 'owid_fetch.py pulls this alongside the generation series, sharing '
                  'one manifest.'),
        ('Transform', 'ev_transform.py, DuckDB. The ranking counts only entities '
                      'carrying a country code, which is what excludes aggregates '
                      'like the world average from a list of countries.'),
        ('Render', _RENDER),
        ('Colour', 'An emphasis chart rather than a categorical one: India carries the '
                   'accent and the comparison markets recede to a neutral. When one '
                   'series is the point, colouring all four equally buries it.'),
    ],
    steps=[
        'Download the EV share CSV and record its sha256.',
        'Build a year axis from the focus country’s own first year, so the chart '
        'does not open on a decade of flat lines.',
        'Read each comparison market into the same axis, leaving gaps where a country '
        'has no figure rather than filling them with zero.',
        'Rank the latest year across countries only, then locate India within it.',
        'Render the trend as an emphasis chart and the ranking as horizontal bars.',
    ],
    code_caption='Excluding aggregates from a ranking of countries',
    code='''<b>SELECT</b> Entity, <b>ROUND</b>(share, 1) <b>AS</b> share
<b>FROM</b> e
<b>WHERE</b> Year = 2025
  <b>AND</b> Code <b>IS NOT NULL</b>      -- aggregates carry no country code
  <b>AND</b> Code &lt;&gt; 'OWID_WRL'   -- and the world total carries a synthetic one
<b>ORDER BY</b> share <b>DESC</b>;''',
    checks=[
        'Aggregates are absent from the ranking. Leaving the world average in would '
        'have placed a non-country above most countries.',
        'Countries with no figure for the latest year are absent rather than counted '
        'as zero, which would have flattered India’s rank.',
        'Gaps in a series break the line instead of being drawn through, so a country '
        'that starts reporting late does not appear to have been at zero.',
        'The claim is about share of new car sales, and the page says so plainly: two '
        'and three wheelers are where India’s electrification actually is.',
    ],
    repro=CLONE + 'python owid_fetch.py    # download + manifest\n'
                  'python ev_transform.py  # DuckDB -> data/ev_india.json\n'
                  'python ev_render.py     # -> ../ev-india/index.html\n'
                  'python ../build_site.py',
)


IPL = buildnotes.section(
    repo_path='pipeline/',
    stack=[
        ('Source', 'Cricsheet, which publishes every delivery of every IPL match as '
                   'open data. 295,732 rows across 1,243 matches.'),
        ('Fetch', 'ipl_fetch.py downloads the archive and extracts only the '
                  'consolidated file; the per-match CSVs hold the same rows.'),
        ('Transform', 'ipl_transform.py, DuckDB. Phases are derived from the over '
                      'number rather than hard-coded per season, so the split holds '
                      'if the format changes.'),
        ('Render', _RENDER),
        ('Colour', _COLOURS),
    ],
    steps=[
        'Download the ball-by-ball archive and record its sha256.',
        'Derive a phase for every delivery from its over: powerplay, middle, death.',
        'Key seasons by the calendar year of their first match, since Cricsheet '
        'labels some as 2007/08 and one as 2020/21.',
        'Aggregate runs, boundaries, wickets and first-innings totals per season and '
        'per phase.',
        'Split before and after the rule year and compare phase by phase.',
    ],
    code_caption='Deriving the phase, and the season key',
    code='''<b>SELECT</b> *,
       <b>CASE WHEN</b> <b>FLOOR</b>(ball) &lt; 6  <b>THEN</b> 'powerplay'
            <b>WHEN</b> <b>FLOOR</b>(ball) &lt; 15 <b>THEN</b> 'middle'
            <b>ELSE</b> 'death' <b>END</b>              <b>AS</b> phase,
       runs_off_bat + extras              <b>AS</b> runs
<b>FROM</b> read_csv_auto('all_matches.csv');

-- Cricsheet labels seasons '2007/08' and '2020/21'; the calendar
-- year of the first match is the one unambiguous key.
<b>SELECT</b> season, <b>CAST</b>(<b>strftime</b>(<b>MIN</b>(start_date), '%Y') <b>AS</b> <b>INT</b>) <b>AS</b> yr
<b>FROM</b> b <b>GROUP BY</b> season;''',
    checks=[
        'The phase split is computed from the data, so an over misfiled in the source '
        'lands in the right bucket rather than a hard-coded range.',
        'Season keys were checked against the mixed labelling before use; naive '
        'sorting of &ldquo;2007/08&rdquo; against &ldquo;2009&rdquo; would have '
        'reordered the series.',
        'Runs per over counts extras as well as runs off the bat, because those are '
        'runs the fielding side conceded.',
        'The alternative explanation was tested, not waved away: a pure hitting-power '
        'story predicts the death overs move most, and they moved least.',
    ],
    repro=CLONE + 'python ipl_fetch.py      # download + manifest\n'
                  'python ipl_transform.py  # DuckDB -> data/ipl_impact.json\n'
                  'python ipl_render.py     # -> ../ipl-impact/index.html\n'
                  'python ../build_site.py',
)

OTT = buildnotes.section(
    repo_path='pipeline/',
    stack=[
        ('Source', 'Netflix’s own weekly Top 10 per country, published as a 32 MB '
                   'TSV. Platform data rather than a third-party estimate.'),
        ('Fetch', 'ott_fetch.py, one request, stored whole with its sha256.'),
        ('Transform', 'ott_transform.py, DuckDB. The reach measure is a self-join of '
                      'the table against its own distinct-country count per title.'),
        ('Render', _RENDER),
        ('Colour', 'One accent against a neutral: the ranking is a list of names where '
                   'only India needs to stand out, so colour marks the subject rather '
                   'than the category.'),
    ],
    steps=[
        'Download the country TSV and record its sha256.',
        'Count, for every title, how many distinct countries it ever charts in.',
        'Join that count back onto each row, so every Indian slot carries the reach '
        'of the title occupying it.',
        'Band the slots by reach and compute the locally anchored share per year.',
        'Repeat per country to rank markets, excluding those with thin coverage.',
    ],
    code_caption='Inferring origin from behaviour rather than from a title',
    code='''<b>CREATE VIEW</b> reach <b>AS</b>
  <b>SELECT</b> show_title, category,
         <b>COUNT</b>(<b>DISTINCT</b> country_name) <b>AS</b> countries
  <b>FROM</b> t <b>GROUP BY</b> 1, 2;

<b>CREATE VIEW</b> j <b>AS</b>
  <b>SELECT</b> i.*, r.countries
  <b>FROM</b> t i <b>JOIN</b> reach r <b>USING</b> (show_title, category);''',
    checks=[
        'The threshold was tested rather than trusted: India sits far below Japan and '
        'Korea whether locally anchored means three countries or ten.',
        'Markets with thin coverage are excluded from the ranking, so a country with a '
        'handful of weeks cannot top it.',
        'Titles are keyed on name and category together, so a film and a series '
        'sharing a name are not merged.',
        'No language or country-of-origin field exists in this data, and the page says '
        'so rather than implying one was used.',
    ],
    repro=CLONE + 'python ott_fetch.py      # download + manifest\n'
                  'python ott_transform.py  # DuckDB -> data/ott_india.json\n'
                  'python ott_render.py     # -> ../ott-india/index.html\n'
                  'python ../build_site.py',
)

RETAIL = buildnotes.section(
    repo_path='pipeline/',
    stack=[
        ('Source', 'The Office of the Economic Adviser publishes the Wholesale Price '
                   'Index monthly. Each release carries a YYYYMM stamp in its '
                   'filename, so the URL cannot be hard-coded.'),
        ('Fetch', 'fetch.py reads the download page and picks the highest-stamped '
                  'file, which is why the page keeps working after a new release.'),
        ('Transform', 'transform.py, DuckDB. Wide monthly columns are melted to one '
                      'row per series per month before anything else happens.'),
        ('Render', _RENDER),
        ('Colour', _COLOURS),
    ],
    steps=[
        'Scrape the download page for the current release URL and fetch it.',
        'Melt the wide INDXMMYYYY columns into a tidy month-by-series table.',
        'Weight-average the raw inputs into one series and the finished goods into '
        'another, using the WPI’s own basket weights.',
        'Rebase both to 100 at a common month so one axis carries both.',
        'Divide one rebased index by the other to get the spread.',
    ],
    code_caption='Weighting by the basket, then rebasing to a common month',
    code='''<b>CREATE TABLE</b> stage_monthly <b>AS</b>
  <b>SELECT</b> month, stage,
         <b>SUM</b>(index_value * weight) / <b>SUM</b>(weight) <b>AS</b> index_value
  <b>FROM</b> wpi <b>WHERE</b> stage <b>IN</b> ('input', 'output')
  <b>GROUP BY</b> month, stage;

<b>CREATE TABLE</b> stage_indexed <b>AS</b>
  <b>WITH</b> base <b>AS</b> (
    <b>SELECT</b> stage, index_value <b>AS</b> base_value <b>FROM</b> stage_monthly
    <b>WHERE</b> month = (<b>SELECT</b> <b>MIN</b>(month) <b>FROM</b> stage_monthly))
  <b>SELECT</b> s.month, s.stage,
         <b>ROUND</b>(100.0 * s.index_value / b.base_value, 2) <b>AS</b> rebased
  <b>FROM</b> stage_monthly s <b>JOIN</b> base b <b>USING</b> (stage);''',
    checks=[
        'Series are weighted by the WPI’s own basket weights, not averaged flat, '
        'so a tiny commodity cannot swing the input series.',
        'Both stages are rebased to the same month, because comparing two indices on '
        'different base years is the error this page exists to avoid.',
        'The first draft described input prices as flat. The endpoints are flat; the '
        'path swings about twenty index points, and the text now says so.',
        'The fetch discovers the current release rather than pinning a filename, so '
        'the page does not quietly go stale.',
    ],
    repro=CLONE + 'python fetch.py      # discover + download + manifest\n'
                  'python transform.py  # DuckDB -> data/retail_margins.json\n'
                  'python render.py     # -> ../retail-margins/index.html\n'
                  'python ../build_site.py',
)
