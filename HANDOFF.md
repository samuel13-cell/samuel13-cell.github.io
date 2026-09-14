# Handoff

Everything needed to pick this site up cold.

**Live:** https://samuel13-cell.github.io
**Repo:** https://github.com/samuel13-cell/samuel13-cell.github.io (public)
**Hosting:** GitHub Pages, serving `main`. No build config, no Actions, no
third-party host. Push to `main` and it deploys.

## Architecture

Static HTML. No framework, no chart library, no build step. Each project page
comes from a three-stage pipeline:

```
*_fetch.py      download to pipeline/raw/, record url + bytes + sha256
*_transform.py  DuckDB over the raw file -> pipeline/data/*.json
*_render.py     fill *_template.html -> <slug>/index.html
build_site.py   inject the shared nav into every page
```

Raw files are kept byte for byte so a parse change re-runs without a refetch,
and so any number on a page traces back to a specific file. `pipeline/raw/` is
gitignored; the fetch scripts regenerate it.

| Module | Does |
|---|---|
| `pipeline/lib.py` | inline-SVG line and bar charts, scales, gridlines, ticks |
| `pipeline/buildnotes.py` | markup for the technical appendix each page carries |
| `pipeline/notes.py` | the per-project appendix prose |
| `build_site.py` | nav injection, current-tab marking, per-page link depth |
| `assets/site.css` | the whole design system, one file |

`build_site.py` generates the nav from pages that exist on disk, so a project
that has not been built yet never appears as a dead tab.

## The five projects

| Page | Question | Source |
|---|---|---|
| `/retail-margins` | Input cost against finished-goods price, Indian leather | eaindustry.nic.in, WPI monthly |
| `/ipl-impact` | Did the 2023 Impact Player rule change how teams bat? | cricsheet.org ball-by-ball |
| `/ott-india` | How much of what India watches is made for India? | Netflix official weekly Top 10 |
| `/ev-india` | How fast are Indian cars going electric? | Our World in Data, from the IEA |
| `/grid-india` | What is powering them? | Our World in Data, from Ember |

### Exact source URLs

```
https://eaindustry.nic.in/indx_download_1112/monthly_index_202606.xls
https://eaindustry.nic.in/indx_download_2223/wpi_monthly_index_202608.xlsx
https://cricsheet.org/downloads/ipl_csv2.zip
https://www.netflix.com/tudum/top10/data/all-weeks-countries.tsv
https://ourworldindata.org/grapher/electric-car-sales-share.csv
https://ourworldindata.org/grapher/electricity-prod-source-stacked.csv
```

The WPI filenames carry a YYYYMM stamp and change every month, so `fetch.py`
discovers the current release from the download page rather than pinning a URL.
The other five are stable.

### Findings, so nothing gets contradicted

**Leather.** Input prices +5.2%, finished goods +29.9%, April 2012 to April
2026, 169 months, no gaps. Inputs are volatile rather than flat: the endpoints
are flat, the path swings about twenty index points.

**IPL.** 1,243 matches, 295,732 balls, 2008 to 2026. Powerplay scoring +1.70
runs per over before against after 2023; death overs +0.74. First innings
passing 200 went from 18% in 2022 to 51% in 2026.

**Netflix.** 5,420 Indian slots, 271 weeks, 1,383 titles. India ranks 24th of
93 markets on local share at 6.9%, against Japan 41.8% and South Korea 39.3%.
Films 11.5% local, TV 2.3%.

**EV.** India 4.0% of new car sales in 2025, up from 2.1%. Ranks 55th of 59.
World average 25%.

**Grid.** Coal fell 43.75 TWh in 2025 while demand rose 45.08. Coal has fallen
three times since 2000; 2019 was 0.10 TWh on a base of 1,199, and 2020 came
with demand itself falling 37.55. Only 2025 has coal falling into rising
demand. Do not write "the first year coal fell": the data does not support it.

## Two constraints

**data.gov.in is a dead end.** Its `robots.txt` is `Disallow: /`, its API
ignores every search parameter tried (each returns the unfiltered 287,810
records), and the maximum page size is 100 at roughly 4.5 seconds a request.
A working API key exists but authenticates against a catalogue that cannot be
searched. Both energy projects were pivoted to Our World in Data for this
reason.

**Annual data ends at 2025.** The EV and grid series carry zero rows for 2026,
because the year is not over. Re-running the fetch in early 2027 picks up 2026
automatically; the transforms read the latest year rather than hard-coding it.

## Design system

One committed light palette on a plain white page, no dark mode and no card.
Source Sans 3 for all text, IBM Plex Mono only inside code blocks, both
self-hosted in `fonts/` as a latin subset, so the page makes no third-party
request. Headings are normal case and bold; there are no uppercase
letterspaced labels anywhere, which was the strongest generated-looking tell
in earlier versions. Templates carry no CSS: `assets/site.css` is the whole
design system, and every page loads only that. Chart colours are blue `#2a78d6`, orange `#eb6834` and violet
`#4a3aa7`, each validated against the page surface for lightness, chroma,
colour-blind separation and contrast. Every green candidate for a third series
failed: all of them collided with the orange under protanopia.

**No em dashes anywhere.** This is deliberate. Rewrite the sentence rather than
substituting the character.

### The alignment rule

The content column **is** the reading measure. `--measure` sets it, and the
sheet width derives from it. Nothing carries its own `max-width`.

Every block-level element starts at the content left edge, and nothing passes
the right edge: headings, prose, charts, tables, nav and code blocks alike.

To change the column, change `--measure` and let the rest follow. Do not add a
`max-width` to a text block. Doing so caps prose below the column width, and
the text can then never share a right edge with the rules and charts. That was
the cause of three failed attempts at fixing the alignment, each of which moved
gridlines and markers while leaving the real mismatch in place.

Verify with: walk every element inside `.sheet`, compare against the computed
content box, expect zero outside it. Check markers and bars, not just gridlines
and text, since the overhang that survived two passes was a line's end dot.

## Rebuilding

```
git clone https://github.com/samuel13-cell/samuel13-cell.github.io
cd samuel13-cell.github.io/pipeline
pip install -r requirements.txt

python fetch.py           && python transform.py      && python render.py
python ipl_fetch.py       && python ipl_transform.py  && python ipl_render.py
python ott_fetch.py       && python ott_transform.py  && python ott_render.py
python owid_fetch.py      && python ev_transform.py   && python ev_render.py
                             python grid_transform.py && python grid_render.py

python ../build_site.py   # inject the shared nav into every page
```

`owid_fetch.py` pulls the EV and grid CSVs together, so it runs once for both.

The resume PDF is rendered from `index.html` by printing it in a headless
browser at A4 with 14mm side and 15mm bottom margins. The print stylesheet
lives in `assets/site.css`; it is tuned to hold two pages, so check the page
count after adding anything to the resume.
