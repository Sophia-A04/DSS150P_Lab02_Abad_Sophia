# DSS150P Laboratory Activity #2

**Student Name:** Sophia Abad

## About This Laboratory

This laboratory activity focuses on profiling different data sources and building a simple but rerunnable ingestion pipeline.

For this activity, I worked with several types of data sources including CSV, JSON, Parquet, a REST API, and PostgreSQL. The main goal was to understand the sources first, document their structure, and then create an ingestion process that can safely run more than once without creating unnecessary duplicates.

The pipeline also uses a watermark for incremental API ingestion, keeps a run log, and includes validation checks to make sure the raw data is still consistent after each run.

## What I Did

For this laboratory, I completed the following:

- Profiled `customers.csv`
- Profiled `orders.json`
- Profiled `products.parquet`
- Inspected the paginated REST API
- Inspected the PostgreSQL `support_tickets` table
- Created source metadata documentation
- Created a basic schema
- Created a data contract for `customers.csv`
- Documented the ingestion design
- Implemented file ingestion using SHA-256 hashes
- Added duplicate prevention for unchanged files
- Implemented paginated API ingestion
- Added `_ingested_at` and `_source` metadata to API records
- Deduplicated API records using `event_id`
- Kept the latest record based on `updated_at`
- Implemented a persistent API watermark
- Added a pipeline run log
- Tested an unchanged rerun for idempotency
- Tested API failure behavior
- Confirmed that the watermark does not advance after a failed run
- Tested recovery after the API was restored
- Added validation checks for the generated raw data

## Repository Structure

```text
DSS150P_Lab02_Abad_Sophia/
├── config/
│   ├── basic_schema.yml
│   ├── data_contract_customers.yml
│   ├── source_metadata.yml
│   └── source_metadata_template.yml
│
├── data/
│
├── evidence/
│   ├── 01_postgresql_inspection.png
│   ├── 02_api_pagination.png
│   ├── 03_first_ingestion.png
│   ├── 04_idempotent_rerun.png
│   ├── 05_api_failure.png
│   ├── 06_api_recovery.png
│   └── 07_validation_passed.png
│
├── sql/
│
├── src/
│   ├── ingest_pipeline.py
│   ├── local_api_server.py
│   ├── profile_sources.py
│   └── validate_raw.py
│
├── templates/
│   ├── pipeline_run_log_template.csv
│   └── profiling_report_template.md
│
├── .gitignore
├── docker-compose.yml
├── engineering_reflection.md
├── ingestion_design.md
├── pipeline_run_log.csv
├── README.md
└── requirements.txt
```

## AI Usage

I used ChatGPT and Gemini as an AI tool during this laboratory activity. I needed help to understand some of the laboratory instructions, I asked questions about some steps and asked them to explain technical terms in simpler words, troubleshoot errors on my laptop that appeared while running commands, and organize some parts of the Python code and documentation.

I ran the commands and scripts myself and used the actual outputs from my environment when recording profiling results. I read the generated code and documentation before adding them to the repository. I would ask what this and that would do, because I was unfamiliar with GitHub. I think I am familiarized with how to navigate GitHub and VS code, words like "git status" and "git add" appear a lot while I am working on the terminal.