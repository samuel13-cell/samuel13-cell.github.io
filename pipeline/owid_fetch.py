"""Download the two Our World in Data series used by the energy projects.

OWID serves each chart's underlying data as a plain CSV at a stable URL, with
no key and no crawl restriction, which is why these replaced the government
portals originally planned for these two pages.
"""
import hashlib, json
from datetime import datetime, timezone
from pathlib import Path

import requests

RAW = Path(__file__).parent / 'raw'
UA = {'User-Agent': 'india-energy/1.0 (+https://samuel13-cell.github.io)'}
FILES = {
    'ev_share': 'https://ourworldindata.org/grapher/electric-car-sales-share.csv',
    'power_mix': 'https://ourworldindata.org/grapher/electricity-prod-source-stacked.csv',
}


def main() -> None:
    RAW.mkdir(exist_ok=True)
    manifest = {'retrieved_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
                'files': {}}
    for key, url in FILES.items():
        body = requests.get(url, headers=UA, timeout=180).content
        (RAW / f'{key}.csv').write_bytes(body)
        manifest['files'][key] = {'url': url, 'bytes': len(body),
                                  'sha256': hashlib.sha256(body).hexdigest()}
        print(f'{key:<10} {len(body):>9,} B')
    (RAW / 'owid_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')


if __name__ == '__main__':
    main()
