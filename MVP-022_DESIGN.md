# MVP-022 — Governed Evidence Extraction

## Status
Design frozen. Not yet implemented.

## Constitutional Boundaries (frozen)
- Theia stages evidence
- Analysts record governed observations
- Themis governs decisions
- No AI-generated content written into governed records
- No constitutional authority changes
- Observation informs assessment — it does not replace it

## Problem Statement
Validation Case 002 revealed that evidence_items captures provenance
but not analytical substance. Business Quality scoring requires
analysts to return to source documents rather than governed records.

## Constitutional Sequence Being Completed
Evidence → Observation → Assessment → Decision

Currently only Evidence → [gap] → Assessment → Decision exists.

## Schema Addition

```sql
CREATE TABLE IF NOT EXISTS evidence_observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    evidence_item_id INTEGER NOT NULL,
    pillar_id TEXT,
    observation_category TEXT NOT NULL,
    observation_text TEXT NOT NULL,
    evidence_quote TEXT,
    source_location TEXT,
    analyst_confidence TEXT,
    created_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    status TEXT DEFAULT 'Active',
    FOREIGN KEY (evidence_item_id) REFERENCES evidence_items(id)
);
```