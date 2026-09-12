"""Week 3 starter: rerunnable ingestion to a raw area.
Students implement file ingestion + paginated REST API ingestion + watermark + duplicate prevention.
"""
from pathlib import Path
from datetime import datetime, timezone
import json, hashlib, shutil, csv, uuid
import requests

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'; RAW=ROOT/'raw'; STATE=ROOT/'state'
API_URL='http://127.0.0.1:8000/api/events'

RUN_LOG = ROOT / 'pipeline_run_log.csv'

def utc_now(): return datetime.now(timezone.utc).isoformat()

def append_run_log(
    run_id,
    started_at,
    finished_at,
    status,
    source,
    records_read,
    records_written,
    duplicates_removed,
    watermark_before,
    watermark_after,
    error_message=''
):
    fieldnames = [
        'run_id',
        'started_at',
        'finished_at',
        'status',
        'source',
        'records_read',
        'records_written',
        'duplicates_removed',
        'watermark_before',
        'watermark_after',
        'error_message',
    ]

    file_exists = RUN_LOG.exists() and RUN_LOG.stat().st_size > 0

    with RUN_LOG.open('a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        writer.writerow({
            'run_id': run_id,
            'started_at': started_at,
            'finished_at': finished_at,
            'status': status,
            'source': source,
            'records_read': records_read,
            'records_written': records_written,
            'duplicates_removed': duplicates_removed,
            'watermark_before': watermark_before or '',
            'watermark_after': watermark_after or '',
            'error_message': error_message,
        })

def sha256_file(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()

def load_watermark():
    p=STATE/'api_watermark.json'
    if not p.exists(): return None
    return json.loads(p.read_text())['updated_at']

def save_watermark(value):
    STATE.mkdir(exist_ok=True)
    (STATE/'api_watermark.json').write_text(json.dumps({'updated_at':value},indent=2))

def ingest_files():
    raw_files = RAW / 'files'
    raw_files.mkdir(parents=True, exist_ok=True)

    manifest_path = raw_files / 'manifest.jsonl'

    # Read hashes that were already successfully ingested.
    existing_hashes = set()

    if manifest_path.exists():
        with manifest_path.open('r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()

                if not line:
                    continue

                entry = json.loads(line)
                existing_hashes.add(entry['sha256'])

    source_files = [
        DATA / 'customers.csv',
        DATA / 'orders.json',
        DATA / 'products.parquet',
    ]

    files_written = 0
    files_skipped = 0

    for source in source_files:
        file_hash = sha256_file(source)
        file_size = source.stat().st_size

        # Do not create another raw copy when identical content
        # has already been ingested.
        if file_hash in existing_hashes:
            files_skipped += 1
            print(f'SKIPPED: {source.name} already ingested')
            continue

        # Preserve the source contents exactly.
        # The short hash in the filename also prevents a changed
        # version of the same source file from overwriting an older one.
        destination = (
            raw_files
            / f'{source.stem}__{file_hash[:12]}{source.suffix}'
        )

        shutil.copy2(source, destination)

        manifest_entry = {
            'source_file': source.name,
            'raw_file': destination.name,
            'ingested_at': utc_now(),
            'bytes': file_size,
            'sha256': file_hash,
        }

        with manifest_path.open('a', encoding='utf-8') as f:
            f.write(json.dumps(manifest_entry) + '\n')

        existing_hashes.add(file_hash)
        files_written += 1

        print(f'INGESTED: {source.name} -> {destination.name}')

    return {
        'records_read': len(source_files),
        'records_written': files_written,
        'duplicates_removed': files_skipped,
    }

def fetch_api_page(page, per_page=20, updated_after=None):
    params={'page':page,'per_page':per_page}
    if updated_after: params['updated_after']=updated_after
    r=requests.get(API_URL,params=params,timeout=30); r.raise_for_status(); return r.json()

def ingest_api():
    raw_api = RAW / 'api'
    raw_api.mkdir(parents=True, exist_ok=True)

    output_path = raw_api / 'events.jsonl'
    temp_path = raw_api / 'events.jsonl.tmp'

    # Read the watermark from the previous successful run.
    watermark_before = load_watermark()

    print(f'API watermark before: {watermark_before}')

    new_records = []
    page = 1

    # Retrieve every page from the API.
    while True:
        payload = fetch_api_page(
            page=page,
            per_page=20,
            updated_after=watermark_before
        )

        items = payload.get('items', [])
        ingested_at = utc_now()

        for item in items:
            record = dict(item)

            # Add operational ingestion metadata.
            record['_ingested_at'] = ingested_at
            record['_source'] = 'local_api_events'

            new_records.append(record)

        print(f'API page {page}: {len(items)} records retrieved')

        if not payload.get('has_more', False):
            break

        next_page = payload.get('next_page')

        if next_page is None:
            break

        page = next_page

    # Load API records already persisted from previous runs.
    existing_records = []

    if output_path.exists():
        with output_path.open('r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()

                if line:
                    existing_records.append(json.loads(line))

    combined_records = existing_records + new_records

    # Deduplicate by event_id.
    # If the same event exists more than once,
    # retain the record with the greatest updated_at.
    latest_by_event = {}

    for record in combined_records:
        event_id = record['event_id']

        current = latest_by_event.get(event_id)

        if (
            current is None
            or record['updated_at'] > current['updated_at']
        ):
            latest_by_event[event_id] = record

    final_records = sorted(
        latest_by_event.values(),
        key=lambda r: (r['updated_at'], r['event_id'])
    )

    duplicates_removed = (
        len(combined_records) - len(final_records)
    )

    # Write to a temporary file first.
    with temp_path.open('w', encoding='utf-8') as f:
        for record in final_records:
            f.write(json.dumps(record) + '\n')

    # Only replace the real output after the temporary
    # file has been written successfully.
    temp_path.replace(output_path)

    # Advance the watermark only AFTER the raw output
    # has been successfully persisted.
    if final_records:
        watermark_after = max(
            record['updated_at']
            for record in final_records
        )

        save_watermark(watermark_after)
    else:
        watermark_after = watermark_before

    print(f'API records retrieved this run: {len(new_records)}')
    print(f'API records persisted: {len(final_records)}')
    print(f'Duplicates removed: {duplicates_removed}')
    print(f'API watermark after: {watermark_after}')

    return {
        'records_read': len(new_records),
        'records_written': len(final_records),
        'duplicates_removed': duplicates_removed,
        'watermark_before': watermark_before,
        'watermark_after': watermark_after,
    }


if __name__ == '__main__':
    RAW.mkdir(exist_ok=True)
    STATE.mkdir(exist_ok=True)

    run_id = str(uuid.uuid4())
    started_at = utc_now()

    watermark_before = load_watermark()

    try:
        file_stats = ingest_files()
        api_stats = ingest_api()

        finished_at = utc_now()

        append_run_log(
            run_id=run_id,
            started_at=started_at,
            finished_at=finished_at,
            status='success',
            source='files+api_events',
            records_read=(
                file_stats['records_read']
                + api_stats['records_read']
            ),
            records_written=(
                file_stats['records_written']
                + api_stats['records_written']
            ),
            duplicates_removed=(
                file_stats['duplicates_removed']
                + api_stats['duplicates_removed']
            ),
            watermark_before=api_stats['watermark_before'],
            watermark_after=api_stats['watermark_after'],
            error_message='',
        )

    except Exception as exc:
        finished_at = utc_now()
        watermark_after = load_watermark()

        append_run_log(
            run_id=run_id,
            started_at=started_at,
            finished_at=finished_at,
            status='failed',
            source='files+api_events',
            records_read=0,
            records_written=0,
            duplicates_removed=0,
            watermark_before=watermark_before,
            watermark_after=watermark_after,
            error_message=f'{type(exc).__name__}: {exc}',
        )

        raise
