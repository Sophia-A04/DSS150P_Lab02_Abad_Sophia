# Ingestion Design

The ingestion pipeline will preserve source data in a raw area and avoid business transformations during ingestion. Duplicate prevention and incremental state will depend on the type of source.

| Source | Ingestion Method | Raw Destination | Duplicate Key | Incremental State |
|---|---|---|---|---|
| CSV / JSON / Parquet files | Copy source file and record it in a manifest | `raw/files/` | SHA-256 file hash | N/A |
| REST API events | Paginated HTTP GET requests | `raw/api/events.jsonl` | `event_id` | Maximum successfully ingested `updated_at` |
| PostgreSQL support_tickets | Inspection using bounded SQL queries | N/A for this laboratory | `ticket_id` | Not implemented for ingestion in this laboratory |

## File Sources

The CSV, JSON, and Parquet files will be treated as complete file-based sources. Each file will be copied to the raw area without changing its contents.

A SHA-256 hash will be calculated for each file. The hash will be stored in a manifest together with information such as the source filename, ingestion timestamp, and file size.

If the same file content is processed again and its SHA-256 hash already exists in the manifest, another raw copy should not be created.

## REST API

The REST API will be ingested using paginated GET requests.

The pipeline will:

1. Request the first page of events.
2. Save the returned records.
3. Continue requesting additional pages while `has_more` is true.
4. Use `event_id` to detect duplicate logical events.
5. When the same `event_id` appears more than once, retain the record with the greatest `updated_at`.
6. Write the resulting records to `raw/api/events.jsonl`.
7. Store the greatest successfully ingested `updated_at` value as the API watermark.

The API watermark will be used on later runs through the `updated_after` parameter so that the pipeline can request only newer records.

## PostgreSQL

The `support_tickets` table will be inspected through bounded SQL queries.

For this laboratory, PostgreSQL is used as a source-system inspection exercise rather than being loaded into the raw ingestion output.

`ticket_id` is the table's primary key and would be the logical duplicate key if PostgreSQL ingestion were added later.

## Raw Data Preservation

The pipeline will preserve source values during ingestion. It will not silently remove, correct, or transform source records for business purposes.

Observed data-quality issues, such as duplicate customer IDs or missing customer attributes, will be documented and validated separately rather than repaired in the raw ingestion stage.

## Watermark Semantics

For this laboratory, the API watermark represents the greatest `updated_at` value that has been successfully persisted to the raw output.

On the first run, no watermark exists, so the pipeline retrieves the available API events. After the raw output is written successfully, the maximum `updated_at` value is saved as the watermark.

On later runs, the pipeline sends the saved watermark through the API's `updated_after` parameter so that only records newer than the previous successful ingestion are requested.

The watermark is operational state used by the ingestion process. It is not part of the original source data.

### Why the watermark must be saved after the raw data

If the watermark is advanced before the raw file has been successfully written and the pipeline fails afterward, the next run may treat those records as already processed. This could cause data loss because the records were never actually persisted but the pipeline has already moved past them.

Therefore, the correct sequence is:

1. Retrieve the records.
2. Process and validate the records.
3. Successfully write the raw output.
4. Save the new watermark.

### Limitation of timestamp-only watermarks

A timestamp-only watermark can be problematic when multiple source records have exactly the same `updated_at` value.

For example, if several events have the same timestamp and the watermark is saved at that timestamp, a later query using `updated_at > watermark` could miss another record with the same timestamp that was not previously processed.

This simplified laboratory pipeline accepts this limitation.

A production-grade mitigation could use a compound watermark such as `(updated_at, event_id)` or use a small overlapping retrieval window together with duplicate prevention. This would reduce the risk of missing records that share the same timestamp.