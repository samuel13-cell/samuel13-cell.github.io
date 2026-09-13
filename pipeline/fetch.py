"""Download the WPI workbooks, unmodified, into raw/ with a manifest.

The Office of the Economic Adviser publishes each month's release under a
date-stamped filename, so the current URL has to be discovered from the
download page rather than hard-coded.
"""
import hashlib, json, re, sys
from datetime import datetime, timezone
from pathlib import Path

import requests

RAW = Path(__file__).parent / 'raw'
BASE = 'https://eaindustry.nic.in/'
UA = {'User-Agent': 'retail-margins/1.0 (+https://samuel13-cell.github.io)'}

# The 2011-12 base runs from Apr 2012 and is still published; the 2022-23 base
# starts Apr 2023. The long series is what carries the analysis.
PAGES = {
    'wpi_1112': ('download_data_1112.asp', r'indx_download_1112/monthly_index_\d+\.xls'),
    'wpi_2223': ('download_data_2223.asp', r'indx_download_2223/wpi_monthly_index_\d+\.xlsx'),
}


def discover(page: str, pattern: str) -> str:
    html = requests.get(BASE + page, headers=UA, timeout=90).text
    matches = re.findall(pattern, html)
    if not matches:
        raise SystemExit(f'no file matching {pattern!r} on {page} -- the site layout changed')
    # Filenames carry a YYYYMM stamp; the highest is the newest release.
    return BASE + max(matches)


def main() -> None:
    RAW.mkdir(exist_ok=True)
    manifest = {'retrieved_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
                'files': {}}

    for key, (page, pattern) in PAGES.items():
        url = discover(page, pattern)
        body = requests.get(url, headers=UA, timeout=180).content
        name = f'{key}{Path(url).suffix}'
        (RAW / name).write_bytes(body)
        manifest['files'][key] = {
            'url': url,
            'saved_as': name,
            'bytes': len(body),
            'sha256': hashlib.sha256(body).hexdigest(),
        }
        print(f'{name:<16} {len(body):>9,} B  {url}', file=sys.stderr)

    (RAW / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')


if __name__ == '__main__':
    main()
