# Source Profiling Report

## 1. Source Inventory

| Source | Type | Rows/Records | Key | Update Pattern | Quality Findings |
|---|---|---:|---|---|---|
| customers.csv | CSV | 250 rows | customer_id | Batch/file-based | 3 missing emails, 2 missing cities, 2 exact duplicate rows, customer_id is not unique |
| orders.json | JSON | 250 records | order_id | Batch/file-based | No missing top-level values; contains nested shipping data |
| products.parquet | Parquet | 200 rows | product_id | Batch/file-based | No missing values observed |
| REST API events | REST API / JSON | 122 events | event_id | Incremental using updated_at | Paginated source; metadata is nested |
| support_tickets | PostgreSQL | 250 rows | ticket_id | Database table | assigned_agent and resolved_at are nullable; 4 tickets have no assigned agent |

## 2. Schema Findings

### customers.csv
The file contains seven fields: customer_id, first_name, last_name, email, city, signup_date, and customer_segment. Most fields are strings, while signup_date represents a date. customer_id is a possible business key, but profiling showed that it is not currently unique.

### orders.json
The JSON source contains order_id, customer_id, order_timestamp, status, item_count, subtotal, shipping_fee, total_amount, and shipping. The shipping field is nested and contains region and method.

### products.parquet
The Parquet source contains seven fields: product_id, product_name, category, brand, unit_price, stock_quantity, and weight_kg. Numeric data types are stored explicitly, including float and integer fields.

### REST API
Each API event contains event_id, customer_id, event_type, amount, updated_at, and metadata. The API response also provides pagination fields such as page, per_page, total, has_more, and next_page.

### PostgreSQL support_tickets
The support_tickets table contains ticket_id, customer_id, category, priority, assigned_agent, opened_at, resolved_at, and status. ticket_id is defined as the primary key. assigned_agent and resolved_at are nullable.

## 3. Data Quality Findings

The customers CSV presents the most visible data-quality issues. It contains missing email and city values, duplicate rows, and non-unique customer_id values. These issues should be detected during validation rather than silently corrected during raw ingestion.

The orders JSON has no missing top-level values, but its nested shipping structure must be considered by downstream systems.

The products Parquet file has no missing values in the profiled fields and preserves explicit column data types.

The REST API requires pagination because one page does not contain the complete dataset. event_id can be used for duplicate detection, while updated_at can support incremental ingestion and watermarking.

The PostgreSQL table allows null values for assigned_agent and resolved_at. Four records currently contain a null assigned_agent value.

## 4. Recommended Acquisition Method

CSV, JSON, and Parquet sources should be acquired as batch files and preserved in the raw ingestion area without modifying their original content.

The REST API should be acquired incrementally using pagination. event_id should be used for duplicate prevention, and updated_at should be used as the watermark for incremental ingestion.

The PostgreSQL source should be inspected and acquired using bounded SQL queries rather than destructive or unrestricted operations.

## 5. Risks and Assumptions

The customers source contains duplicate and missing data that may affect downstream processing.

Nested JSON fields may require flattening or another defined representation in later processing stages.

API ingestion must process every page; retrieving only the first page would produce an incomplete dataset.

The API watermark must only advance after data has been written successfully. Advancing it too early could cause records to be skipped after a failed run.

Nullable PostgreSQL fields should not automatically be treated as errors because values such as resolved_at may legitimately be absent for unresolved tickets.

Raw source values should be preserved during ingestion. Business transformations and cleaning should be performed later in the data lifecycle.