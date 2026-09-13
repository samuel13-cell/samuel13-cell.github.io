# samuel13-cell.github.io

Personal site: a resume and five data analysis projects, all static HTML with
no framework, no chart library and no build step.

**Live at https://samuel13-cell.github.io**

| Page | About |
|---|---|
| `/` | Resume, and the source of `resume.pdf` |
| `/retail-margins` | Input cost against finished-goods price in Indian leather, 2012 to 2026 |
| `/ipl-impact` | Whether the 2023 Impact Player rule changed how IPL teams bat |
| `/ott-india` | How much of what India watches on Netflix is made for India |
| `/ev-india` | India's share of new car sales that are electric, against 60 other countries |
| `/grid-india` | The year Indian coal generation fell while demand grew |

Each project page carries its own method, limitations and build notes, including
the query the headline rests on and the commands to reproduce it.

## Layout

```
index.html          resume
<slug>/index.html   generated project pages
assets/             site.css, nav.html
fonts/              self-hosted IBM Plex subset
pipeline/           fetch, transform and render for every project
build_site.py       injects the shared nav into every page
```

Charts are inline SVG generated in `pipeline/lib.py`. Transforms run in DuckDB
against files downloaded to `pipeline/raw/`, which is gitignored and rebuilt by
the fetch scripts.

## Working on this

Read **[HANDOFF.md](HANDOFF.md)** first. It covers the data sources and their
quirks, the findings so they do not get contradicted, the design system, and
the alignment rule that governs the whole layout.
