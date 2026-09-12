"""Validation checks for raw ingestion outputs."""

from pathlib import Path
from datetime import datetime
import json

ROOT = Path(__file__).resolve().parents[1]

RAW = ROOT / 'raw'
STATE = ROOT / 'state'


def main():
    raw_files = RAW / 'files'
    raw_api = RAW / 'api'

    manifest_path = raw_files / 'manifest.jsonl'
    events_path = raw_api / 'events.jsonl'
    watermark_path = STATE / 'api_watermark.json'

    # 1. Required generated outputs must exist.
    assert raw_files.exists(), 'raw/files directory is missing'
    assert raw_api.exists(), 'raw/api directory is missing'
    assert manifest_path.exists(), 'manifest.jsonl is missing'
    assert events_path.exists(), 'events.jsonl is missing'
    assert watermark_path.exists(), 'api_watermark.json is missing'

    print('PASS: Required raw output files exist')

    # 2. Check that each required source file has a raw copy.
    manifest_entries = []

    with manifest_path.open('r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()

            if line:
                manifest_entries.append(json.loads(line))

    source_files = {
        entry['source_file']
        for entry in manifest_entries
    }

    expected_sources = {
        'customers.csv',
        'orders.json',
        'products.parquet',
    }

    assert expected_sources.issubset(source_files), (
        'One or more required source files are missing from the manifest'
    )

    print('PASS: Required source files are represented in the manifest')

    # 3. Load API records.
    events = []

    with events_path.open('r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()

            if line:
                events.append(json.loads(line))

    assert events, 'No API events were found'

    print(f'PASS: Loaded {len(events)} persisted API events')

    # 4. event_id must be unique.
    event_ids = [
        record['event_id']
        for record in events
    ]

    assert len(event_ids) == len(set(event_ids)), (
        'Duplicate event_id values found'
    )

    print('PASS: event_id values are unique')

    # 5. Required ingestion metadata must exist.
    for record in events:
        assert '_ingested_at' in record, (
            f"Missing _ingested_at for {record.get('event_id')}"
        )

        assert '_source' in record, (
            f"Missing _source for {record.get('event_id')}"
        )

    print('PASS: Required ingestion metadata is present')

    # 6. updated_at values must be parseable timestamps.
    for record in events:
        datetime.fromisoformat(record['updated_at'])

    print('PASS: All updated_at values are parseable')

    # 7. Watermark must equal the greatest persisted updated_at.
    watermark = json.loads(
        watermark_path.read_text(encoding='utf-8')
    )['updated_at']

    max_updated_at = max(
        record['updated_at']
        for record in events
    )

    assert watermark == max_updated_at, (
        f'Watermark mismatch: '
        f'watermark={watermark}, '
        f'max_updated_at={max_updated_at}'
    )

    print('PASS: Watermark equals maximum persisted updated_at')

    print()
    print('ALL RAW VALIDATION CHECKS PASSED')


if __name__ == '__main__':
    main()