"""Download Cricsheet's IPL ball-by-ball archive into raw/, with a manifest."""
import hashlib, json, zipfile
from datetime import datetime, timezone
from pathlib import Path

import requests

RAW = Path(__file__).parent / 'raw'
URL = 'https://cricsheet.org/downloads/ipl_csv2.zip'
UA = {'User-Agent': 'ipl-impact/1.0 (+https://samuel13-cell.github.io)'}


def main() -> None:
    RAW.mkdir(exist_ok=True)
    body = requests.get(URL, headers=UA, timeout=300).content
    zip_path = RAW / 'ipl_csv2.zip'
    zip_path.write_bytes(body)

    out = RAW / 'ipl'
    out.mkdir(exist_ok=True)
    with zipfile.ZipFile(zip_path) as z:
        # only the consolidated file is needed; the per-match CSVs are the same data
        z.extract('all_matches.csv', out)

    (RAW / 'ipl_manifest.json').write_text(json.dumps({
        'retrieved_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'url': URL,
        'bytes': len(body),
        'sha256': hashlib.sha256(body).hexdigest(),
    }, indent=2) + '\n')
    print(f'{len(body):,} B -> {out / "all_matches.csv"}')


if __name__ == '__main__':
    main()
