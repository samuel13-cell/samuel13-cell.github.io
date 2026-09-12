# retail-margins pipeline

Builds `/retail-margins` on the site: input cost vs retail price for Indian
leather goods, and what the gap between them does to margin.

## Question

When hides and leather get more expensive, do retail footwear prices follow?
The gap between the two is a proxy for margin at the retail end of the chain.

## Sources

| Series | Publisher | Role |
|---|---|---|
| WPI — hides, skins and leather (base 2011-12) | Office of the Economic Adviser, `eaindustry.nic.in` | what suppliers charge |
| CPI — footwear | Ministry of Statistics, `www.mospi.gov.in` | what customers pay |
| India CPI, all items | World Bank API | cross-check, deflator |

All three are published without an API key.

## Shape

```
fetch.py      download source workbooks to raw/, unmodified, with a manifest
transform.py  raw/ -> DuckDB -> tidy monthly series in data/
render.py     data/ -> ../retail-margins/index.html
```

Raw files are kept byte-for-byte so a parse change can be re-run without
re-downloading, and so the numbers on the page can always be traced back to a
specific published file.

## Method

Both indices are rebased to 100 at a common month. The margin proxy is
`CPI_footwear / WPI_leather`, indexed to the same base: above 100 means retail
prices have outrun input costs since the base period, below 100 means they
have not.

## Limitations

These are national indices. They describe the industry, not any single
business, and they cannot capture what one retailer negotiates with one
supplier. Treat the direction as signal and the level as approximate.
