# Forensic eDiscovery – Conversation Export Transformation Pipeline

## Context

This project is a small but realistic example of the type of data preparation work encountered in **forensic investigations and eDiscovery engagements**.

The input dataset represents a conversation export coming from an investigation context, where:
- metadata and messages are interleaved,
- conversation boundaries are not explicitly defined,
- identifiers are inconsistent or non-standard,
- deleted messages must be preserved as evidence signals.

The objective is **not** to clean or “beautify” the data, but to transform it into an **analysis-ready, defensible structure** while preserving traceability to the original extract.

---

## What the pipeline does

Starting from a raw CSV export, the pipeline:

- Reconstructs conversation blocks from extraction markers
- Separates **conversation-level** and **message-level** concepts
- Preserves all source identifiers exactly as provided
- Flags data quality aspects without modifying evidence
- Produces two structured outputs ready for investigation or review

No enrichment, inference, or correction of the original evidence is applied.

---

## Outputs

### 1) `clean_messages.csv` (message-level)

One row per message, including:

- **Stable conversation identifiers**
  - `conversation_block_id`: internal technical identifier
  - `conversation_uid`: readable and unique identifier
- **Preserved source identifiers**
  - `conversation_id` (as provided in the extract)
  - `conversation_id_is_uuid`: quality flag only
- **Investigation-relevant signals**
  - `message_status` (`normal` / `deleted`)
  - `has_deleted_in_conversation`
  - `message_len`
- **Traceability fields**
  - `row_num`: reference to the raw extract row
  - `conv_seq`: block sequence in the export

Deleted messages are kept and explicitly flagged.

---

### 2) `conversation_summary.csv` (conversation-level)

One row per reconstructed conversation, including:

- Message count
- List of participants
- Number of deleted messages
- Boolean flag indicating presence of deletions

This dataset is intended for triage, scoping, or high-level review.

---

## Key forensic principles applied

This project follows standard forensic and eDiscovery principles:

- **Evidence preservation**  
  No source identifiers or content are altered or “fixed”.

- **Deterministic processing**  
  Same input always produces the same output.

- **Traceability**  
  Every output row can be traced back to its origin in the raw extract.

- **Explicit assumptions**  
  All structural assumptions are documented (see `reports/methodology.md`).

---

## Project structure

The repository follows a clear separation between transformation logic, analytics, documentation, and quality controls.

```text
deloitte-forensic-ediscovery/
├── src/
│   ├── deloitte_forensic/
│   │   ├── io.py                # Data loading utilities
│   │   ├── transform.py         # Core transformation logic
│   │   └── validate.py          # Data quality and consistency checks
│   └── cli.py                   # Command-line interface
│
├── analysis/
│   ├── investigation_analysis.py    # Investigation-ready analytical outputs
│   ├── forensic_features.py         # Temporal and behavioral forensic features
│   └── outputs/
│       ├── investigation/            # Analyst-facing investigation datasets
│       └── features/                 # Engineered forensic features
│
├── tests/
│   └── test_transform.py         # Minimal unit tests for transformation logic
│
├── reports/
│   └── methodology.md            # Methodology, assumptions, and design choices
│
├── data/
│   └── raw/                      # Raw conversation export 
│   └── processed/
│
├── requirements.txt
├── pytest.ini
├── README.md
└── .gitignore
```


## How to run the pipeline

This project follows a forensic-style, reproducible pipeline.  
Raw data is never modified and all outputs are derived artefacts.

All commands must be run from the project root.

### Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Run the transformation pipeline**
```bash
export PYTHONPATH=src

python src/cli.py \
  --input-path data/raw/conversation_data.csv \
  --out-dir data/processed
```

This generates:
- data/processed/clean_messages.csv
- data/processed/conversation_summary.csv

Identifiers are preserved as provided, deleted messages are explicitly flagged, and no records are silently altered or deleted.

**Run analyses and forensic features**

```bash
python analysis/investigation_analysis.py
python analysis/forensic_features.py
```

Outputs are written to:
- analysis/outputs/investigation/
- analysis/outputs/features/


**Data handling notes**
- Raw data is read-only 
- All outputs are deterministic and reproducible 
- No synthetic data is generated (dataset already anonymised)
- Emphasis is placed on traceability and analytical defensibility