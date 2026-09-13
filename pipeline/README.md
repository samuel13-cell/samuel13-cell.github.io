# pipeline

Fetch, transform and render for the five project pages. Each project follows
the same three stages:

```
*_fetch.py      download to raw/, record url + bytes + sha256 in a manifest
*_transform.py  DuckDB over the raw file -> data/*.json
*_render.py     fill *_template.html -> ../<slug>/index.html
```

| Project | Fetch | Transform | Render | Output |
|---|---|---|---|---|
| Leather margins | `fetch.py` | `transform.py` | `render.py` | `../retail-margins/` |
| IPL | `ipl_fetch.py` | `ipl_transform.py` | `ipl_render.py` | `../ipl-impact/` |
| Netflix | `ott_fetch.py` | `ott_transform.py` | `ott_render.py` | `../ott-india/` |
| EV | `owid_fetch.py` | `ev_transform.py` | `ev_render.py` | `../ev-india/` |
| Grid | `owid_fetch.py` | `grid_transform.py` | `grid_render.py` | `../grid-india/` |

`owid_fetch.py` downloads both Our World in Data CSVs, so it serves the last
two projects at once.

Shared modules:

- `lib.py` builds the inline-SVG charts: scales, gridlines, ticks, line and bar
  marks. One copy, used by every renderer.
- `buildnotes.py` renders the technical appendix each page ends with.
- `notes.py` holds that appendix's prose, per project.

## Why the raw files are kept

`raw/` holds each download byte for byte alongside its sha256. A parse change
re-runs without hitting the source again, and any figure on a published page
traces back to a specific file. The directory is gitignored; the fetch scripts
rebuild it.

## Sources

| Project | Publisher | Notes |
|---|---|---|
| Leather margins | Office of the Economic Adviser | Filenames carry a YYYYMM stamp, so `fetch.py` discovers the current release from the download page rather than pinning a URL |
| IPL | Cricsheet | Every delivery of every match |
| Netflix | Netflix Top 10 | The platform's own weekly country data, not an estimate |
| EV and grid | Our World in Data | Compiled from the IEA, Ember and the Energy Institute |

None require an API key. India's own portal, data.gov.in, was tried first and
abandoned: it disallows crawling in `robots.txt` and its API offers no search.
See `../HANDOFF.md`.

## Running it

```
pip install -r requirements.txt
python <project>_fetch.py
python <project>_transform.py
python <project>_render.py
python ../build_site.py
```
