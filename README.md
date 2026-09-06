# Pharmacovigilance Intelligence Platform

An end-to-end data engineering pipeline that replaces manual adverse-event
report review with automated, auditable signal detection.

**Stack:** AWS S3 · Dataiku DSS · Snowflake (Warehouse + Native ML) · Streamlit

## What it does
- Ingests raw adverse event report CSVs into an AWS S3 landing zone via a
  scoped IAM role and Snowflake storage integration
- Cleanses and standardizes the data in Dataiku DSS deduplication with
  documented conflict resolution, casing/date normalization, and
  missing-value handling with an automated Data Quality gate
- Models the cleaned data into a Snowflake star schema (5 dimensions,
  1 fact table), including a composite key on manufacturing batch after
  discovering batch codes are not globally unique in the source data
- Runs Snowflake's native ML anomaly detection on monthly report volume
  per drug, cross-validated against an independent statistical (z-score)
  method
- Surfaces results in a live Streamlit dashboard covering trend, volume,
  serious-event rate, and flagged anomalies

## Key finding
The pipeline identified a genuine statistical anomaly in December 2025
report volume for one drug. Drilling into the underlying reports showed
mixed clinical causality assessments — demonstrating that a statistical
signal flags where to look, not a conclusion about drug safety.

## Documentation
Full architecture diagram, data dictionary, data quality rulebook, ERD,
and test report included in `/docs`.
