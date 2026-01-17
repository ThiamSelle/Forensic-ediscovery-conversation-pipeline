# Methodology – Conversation Export Transformation

## 1. Purpose of this document

This document describes the **methodological choices**, **assumptions**, and **constraints** applied when transforming the raw conversation export into structured, analysis-ready datasets.

The objective is not to optimise for data science performance, but to ensure that the transformation process is:
- defensible in a forensic or regulatory context,
- traceable to the original evidence,
- deterministic and reproducible,
- aligned with common eDiscovery and investigation standards.

All decisions described below were made with **evidence preservation and auditability** as primary design principles.

---

## 2. Nature of the source data

The source file is a CSV export representing conversations extracted from a communication platform.

Key observed characteristics:
- The export is **block-structured**, not relational.
- Conversation blocks are delimited by an extraction marker (`APDxxxxx`).
- Metadata rows and message rows are interleaved.
- Messages are not explicitly labelled as such.
- Identifiers (conversation IDs) are non-standard and inconsistent.
- Deleted messages appear as explicit markers (`[Deleted Message]`).

The export appears to be the result of an **automated extraction process**, not a dataset designed for analytical use.

---

## 3. Core forensic assumptions

The following assumptions are applied consistently throughout the pipeline:

### 3.1 Evidence preservation

- All identifiers, message content and timestamps are preserved **exactly as provided**.
- No attempt is made to “fix”, normalise or replace source identifiers.
- Deleted messages are retained and flagged; they are never removed.

This aligns with the forensic principle that **evidence should not be altered**, even if it appears malformed or incomplete.

---

### 3.2 Determinism

- The transformation logic is fully deterministic.
- Given the same input file, the outputs will always be identical.
- No randomness or heuristic inference is used.

This ensures reproducibility and supports audit or peer review.

---

### 3.3 Explicit documentation of assumptions

Where the export structure requires interpretation (e.g. how to detect message rows), assumptions are:
- minimal,
- based on observable patterns,
- documented explicitly in this file.

---

## 4. Conversation boundary reconstruction

### 4.1 Extraction markers (`extraction_group_id`)

Values such as `APD93824` are treated as **extraction markers**, not unique conversation identifiers.

Observations:
- The same `APDxxxxx` value can appear across multiple conversation blocks.
- This suggests it represents a batch or grouping artifact from the extraction process.

Decision:
- `extraction_group_id` is preserved as-is.
- It is **not** treated as a primary key.

---

### 4.2 Conversation block sequencing (`conv_seq`)

Each occurrence of an extraction marker starts a new conversation block.

- A sequential counter (`conv_seq`) is incremented each time a new block starts.
- `conv_seq` is unique within the export.

Derived identifiers:
- `conversation_block_id = conv_seq`
- `conversation_uid = <extraction_group_id>-<conv_seq>`

This provides:
- a stable, unique internal identifier,
- a readable identifier suitable for review or discussion.

---

## 5. Identification of message rows

Message rows are detected using the following rule:

- A row is considered a message if the first column matches an **email-like pattern**.

Rationale:
- This pattern is consistent across the export.
- It avoids reliance on positional assumptions or row counts.
- It is deterministic and easily auditable.

Rows not matching this pattern are treated as metadata rows.

---

## 6. Handling of deleted messages

Deleted messages appear in the export as the literal string: [Deleted Message]


Methodology:
- These rows are retained as messages.
- `message_status` is set to `deleted`.
- The message text is preserved exactly as provided.

Additionally:
- A conversation-level flag (`has_deleted_in_conversation`) is computed.
- This flag is propagated to each message row for analytical convenience.

Rationale:
- Deleted messages are often a **key investigative signal**.
- Their presence may be more important than their content.

---

## 7. Identifier quality assessment (non-invasive)

Conversation identifiers (`conversation_id`) resemble truncated or non-standard UUIDs.

Decision:
- Identifiers are preserved without modification.
- A boolean quality flag (`conversation_id_is_uuid`) is added to indicate whether the value matches a strict UUID pattern.

This approach:
- avoids altering evidence,
- documents data quality transparently,
- allows downstream users to filter or flag records if required.

---

## 8. Feature engineering rationale

Only **lightweight, non-inferential features** are added.

### 8.1 `message_len`
- Character length of the message text.
- Useful for detecting empty, truncated or anomalous messages.
- Does not modify content.

### 8.2 `message_sequence`
- Deterministic ordering of messages within a conversation block.
- Derived from row order in the export.

No semantic interpretation or sentiment analysis is applied at this stage.

---

## 9. Output datasets

### 9.1 Message-level dataset (`clean_messages.csv`)

Purpose:
- Detailed review
- Timeline reconstruction
- Participant-level analysis
- Feeding downstream forensic or eDiscovery tools

### 9.2 Conversation-level dataset (`conversation_summary.csv`)

Purpose:
- High-level triage
- Scoping and prioritisation
- Management or legal review

Both datasets are fully traceable to the raw extract.

---

## 10. What this pipeline deliberately does NOT do

To avoid overreach in a forensic context, the pipeline does not:
- infer intent, sentiment or topic,
- merge or deduplicate conversations,
- normalise or “repair” identifiers,
- discard any rows from the original extract,
- apply machine learning or GenAI.

These steps may be appropriate later in an investigation, but only after legal and methodological validation.

---

## 11. Limitations

- The logic assumes the export follows the same structural pattern throughout.
- Message detection relies on email-pattern consistency.
- The pipeline is designed for **one export at a time**, not streaming ingestion.

These limitations are acceptable given the scope and objectives of the project.

---

## 12. Intended usage

This transformation pipeline is intended to serve as:
- a defensible preprocessing step in forensic investigations,
- a foundation for eDiscovery review workflows,
- a clean input for further analytics or AI-enabled investigation tools,
- a demonstrator of forensic data handling best practices.

---

## 13. Conclusion

This methodology prioritises **defensibility, traceability and clarity** over complexity.

It reflects the type of foundational data engineering work that underpins credible forensic analysis and ensures that any downstream insights remain anchored to preserved, auditable evidence.




