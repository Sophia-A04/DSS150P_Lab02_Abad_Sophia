# Engineering Reflection

## 1. Why should source profiling occur before implementation of ingestion?

Source profiling should happen first because it helps us understand what the data actually looks like before writing the pipeline. It lets us see the columns, data types, missing values, duplicates, nested fields, and other possible issues that might affect ingestion.

## 2. What is the difference between source event time/updated_at and ingestion time?

The `updated_at` value tells us when the record was last updated in the source system. On the other hand, `_ingested_at` tells us when our pipeline actually retrieved and stored that record. Basically, one is source time and the other is pipeline time.

## 3. Why is event_id alone insufficient to decide which duplicate API record to keep in this exercise?

An `event_id` can appear more than once with different versions of the same event. Because of that, we also need to look at `updated_at` and keep the record with the latest timestamp so that we preserve the newest version.

## 4. Why must watermark state advance only after successful persistence?

The watermark should only be updated after the data has been successfully written. If the watermark moves forward before saving the records and the pipeline suddenly fails, some records could be skipped during the next run.

## 5. What limitation does updated_after > watermark have when multiple source records can share exactly the same timestamp?

If several records have the same timestamp as the watermark, using only `updated_after > watermark` may cause some of them to be skipped. A better approach in a larger system could use both the timestamp and another unique field such as an ID.

## 6. How is duplicate prevention related to idempotency?

Duplicate prevention helps make the pipeline idempotent because running it again with the same data should not keep creating extra copies. In this lab, SHA-256 hashes prevent duplicate file ingestion, while `event_id` and `updated_at` are used to prevent duplicate API events.

## 7. Why should the raw area preserve source values instead of applying business transformations?

The raw area should keep the original source values so that we always have a copy of what actually came from the source. Transformations can be done later, but keeping the raw data makes the process easier to audit, debug, and reproduce.

## 8. How could querying a production OLTP source for profiling or extraction degrade the application?

Large or inefficient queries can use too much CPU, memory, disk I/O, or database connections. This can slow down the actual application that depends on the database, so profiling and extraction queries should be limited and carefully designed.

## 9. What would you change if the API had a rate limit of 60 requests per minute?

I would add rate-limit handling so the pipeline does not send requests too quickly. I could add delays between requests, monitor the API response, and retry after waiting if the limit is reached.

## 10. How would you extend this pipeline from a local raw area to PostgreSQL while preserving rerun safety?

I would keep the raw ingestion step first, then load the validated records into PostgreSQL. I would use unique keys and upserts so rerunning the pipeline would not create duplicates. I would also only update the watermark after the database transaction has completed successfully.