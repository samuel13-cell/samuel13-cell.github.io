"""Download Netflix's official weekly country Top 10 into raw/, with a manifest.

Netflix publishes this itself, so the numbers on the page come from the
platform rather than a third-party estimate.
"""
import hashlib, json
from datetime import datetime, timezone
from pathlib import Path

import requests

RAW = Path(__file__).parent / 'raw'
URL = 'https://www.netflix.com/tudum/top10/data/all-weeks-countries.tsv'
UA = {'User-Agent': 'ott-india/1.0 (+https://samuel13-cell.github.io)'}


def main() -> None:
    RAW.mkdir(exist_ok=True)
    body = requests.get(URL, headers=UA, timeout=300).content
    (RAW / 'netflix_countries.tsv').write_bytes(body)
    (RAW / 'ott_manifest.json').write_text(json.dumps({
        'retrieved_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'url': URL, 'bytes': len(body),
        'sha256': hashlib.sha256(body).hexdigest(),
    }, indent=2) + '\n')
    print(f'{len(body):,} B -> {RAW / "netflix_countries.tsv"}')


if __name__ == '__main__':
    main()
