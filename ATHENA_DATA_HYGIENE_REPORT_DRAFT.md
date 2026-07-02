# ATHENA Data Hygiene Report Draft

Generated: 2026-07-02T02:13:09.874881Z

## A. Runtime DB Authority

- ATHENA_DB_PATH set: no
- Authoritative DB path selected: /Users/phillipcaswell/ims_mvp.db
- Authoritative DB exists: yes
- Repo-local ./ims_mvp.db exists: yes
- Authoritative DB size/mtime: 8957952 bytes, 2026-06-29 19:31:36 -0600
- Repo-local DB size/mtime: 32768 bytes, 2026-06-26 16:10:32 -0600
- DB path ambiguity exists: yes (both files exist; authoritative path selected by policy)
- Inspection connection mode: read-only (`file:/Users/phillipcaswell/ims_mvp.db?mode=ro`)
- Data Explorer cross-check snapshot: Runtime DB Path shows `/Users/phillipcaswell/ims_mvp.db`; Data Explorer page marked read-only; Microsoft thesis_id=14 visible as source-context selector option.

## B. Schema Discovery Summary

### Discovered relevant tables

- theses
- decision_logs
- thesis_reviews
- evidence_staging
- evidence_items
- evidence_observations
- pillar_scores
- pillar_evidence_links
- thesis_events
- evaluation_preparations
- evaluation_candidate_documents
- evaluation_acquired_documents
- evaluation_extracted_observations
- evaluation_extraction_runs

### Missing expected tables

- none

### Naming differences from expected terminology

- Evaluation preparation table name present as `evaluation_preparations`.
- Candidate documents table name present as `evaluation_candidate_documents`.
- Acquired documents table name present as `evaluation_acquired_documents`.
- Extracted observations table name present as `evaluation_extracted_observations`.
- Pillar evidence links table name present as `pillar_evidence_links`.

### Key columns used for joins/counts/classification

- `theses.id`
- `decision_logs.thesis_id`
- `thesis_reviews.thesis_id`, `thesis_reviews.decision_log_id`
- `evidence_staging.thesis_id`, `evidence_staging.review_date`, `evidence_staging.promoted_at`, `evidence_staging.intake_status`
- `evidence_items.id`, `evidence_items.thesis_id`, `evidence_items.publication_date`, `evidence_items.status`
- `evidence_observations.evidence_item_id`
- `pillar_scores.id`, `pillar_scores.thesis_id`, `pillar_scores.pillar_id`, `pillar_scores.judgment`
- `pillar_evidence_links.pillar_score_id`, `pillar_evidence_links.evidence_item_id`
- `thesis_events.thesis_id`, `thesis_events.event_type`
- `evaluation_preparations.id`, `evaluation_preparations.thesis_id`
- `evaluation_candidate_documents.preparation_id`, `evaluation_candidate_documents.thesis_id`
- `evaluation_acquired_documents.preparation_id`, `evaluation_acquired_documents.thesis_id`
- `evaluation_extracted_observations.preparation_id`, `evaluation_extracted_observations.thesis_id`, `evaluation_extracted_observations.acquired_document_id`

### Schema limitations affecting interpretation

- No explicit lifecycle closure flag found in `theses`.
- No canonical governance identity authority field found in inspected runtime schema.
- `thesis_events` can contain rows for thesis IDs not present in `theses` (observed for thesis_id=2).
- Evidence-to-pillar linkage quality depends on `pillar_evidence_links`; `evidence_items.related_pillar` alone is non-authoritative for linkage.

## C. Thesis Inventory

| thesis_id | company_name | ticker | status | created_at | validation_mode | decision_logs | reviews | staged | evidence_items | observations | pillar_scores | pillar_links | events | preps | candidates | acquired | extracted |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 14 | Microsoft | MSFT | Draft | 2026-06-29T18:23:51.730872 | 0 | 1 | 0 | 12 | 3 | 2 | 11 | 0 | 58 | 1 | 8 | 8 | 55 |
| 1 | NVIDIA Investment Thesis | NVDA | None | 2026-06-26T16:28:49.958696 | 0 | 1 | 2 | 3 | 3 | 0 | 11 | 1 | 64 | 0 | 0 | 0 | 0 |
| 3 | Meta Platforms Manual 1782571511797 | META | None | 2026-06-27T08:45:13.253287 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 |
| 4 | Meta Platforms Manual Cutoff 1782571531729 | META | None | 2026-06-27T08:45:33.306930 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 |
| 5 | Meta Platforms Manual Cutoff Exact 1782571549083 | META | None | 2026-06-27T08:45:50.679721 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 |
| 6 | Meta Platforms | META | None | 2026-06-27T08:55:42.351201 | 1 | 1 | 3 | 5 | 3 | 0 | 11 | 0 | 30 | 0 | 0 | 0 | 0 |
| 7 | Eastman Kodak Company | EK | None | 2026-06-27T15:24:24.590404 | 1 | 1 | 1 | 6 | 6 | 2 | 11 | 0 | 59 | 0 | 0 | 0 | 0 |
| 8 | NVIDIA NoTouch Validation | NVDA | Draft | 2026-06-28T13:42:12.359214 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 9 | 1 | 8 | 8 | 40 |
| 9 | Microsoft OVC-004 | MSFT | Draft | 2026-06-28T14:16:51.442780 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 9 | 1 | 8 | 8 | 35 |
| 10 | Oracle OVC-004 PostFix | ORCL | Draft | 2026-06-28T14:27:15.386487 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 9 | 1 | 8 | 8 | 15 |
| 11 | Intel OVC-004 INT-001 | INTC | Draft | 2026-06-28T14:35:22.665810 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 9 | 1 | 8 | 8 | 20 |
| 12 | Qualcomm OVC-004 INT-001 | QCOM | Draft | 2026-06-28T14:40:14.523852 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 9 | 1 | 8 | 8 | 21 |
| 13 | Temporary FRICTION-003 Validation | TMPFRIC003 | Draft | 2026-06-29T18:02:50.367885 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 0 | 0 |

## D. Record Classification Proposal

| thesis_id | classification | rationale |
|---|---|---|
| 14 | Source-Context Record | Known constraint: Microsoft thesis_id=14 is historical artifact / HRV-002 source context only. |
| 1 | Preserve — Substantive, Unsigned | Substantive record but unsigned; explicit governance sign-off absent. |
| 3 | Test / Junk / Manual Scratch Candidate | Manual-generated naming pattern; no substantive linked data. |
| 4 | Test / Junk / Manual Scratch Candidate | Manual-generated naming pattern; no substantive linked data. |
| 5 | Test / Junk / Manual Scratch Candidate | Manual-generated naming pattern; no substantive linked data. |
| 6 | Preserve — Substantive, Unsigned | Likely historical regression baseline candidate pending explicit sign-off. |
| 7 | Archived Constitutional Asset | Known constraint: Kodak roadmap-archived / Type A review established. |
| 8 | Archived Constitutional Asset / No-Touch Regression Reference | NVIDIA NoTouch Validation is already governed as a no-touch archived constitutional reference; preserve unchanged. |
| 9 | Evaluation-Pipeline Residue / Workflow-Discovery Evidence Pending Authority | Microsoft OVC-004 draft with evaluation pipeline artifacts (prep/candidate/acquired/extracted) but no governed evidence-item/pillar-link mapping; preserve pending explicit authority. |
| 10 | Evaluation-Pipeline Residue / Workflow-Discovery Evidence Pending Authority | Oracle OVC-004 PostFix draft with evaluation pipeline artifacts (prep/candidate/acquired/extracted) but no governed evidence-item/pillar-link mapping; preserve pending explicit authority. |
| 11 | Evaluation-Pipeline Residue / Workflow-Discovery Evidence Pending Authority | Intel OVC-004 INT-001 draft remains grouped with 9/10/12 unless external governance authority proves otherwise; preserve pending explicit authority. |
| 12 | Evaluation-Pipeline Residue / Workflow-Discovery Evidence Pending Authority | Qualcomm OVC-004 INT-001 draft with evaluation pipeline artifacts (prep/candidate/acquired/extracted) but no governed evidence-item/pillar-link mapping; preserve pending explicit authority. |
| 13 | Test / Junk / Manual Scratch Candidate | Temporary validation naming pattern; no substantive linked data. |

## E. Evidence Staging Summary

| thesis_id | staged | reviewed_staged | promoted_staged | unreviewed_staged | unclear_intake_status |
|---|---|---|---|---|---|
| 14 | 12 | 1 | 1 | 11 | 0 |
| 1 | 3 | 2 | 1 | 1 | 0 |
| 3 | 0 | 0 | 0 | 0 | 0 |
| 4 | 0 | 0 | 0 | 0 | 0 |
| 5 | 0 | 0 | 0 | 0 | 0 |
| 6 | 5 | 5 | 3 | 0 | 0 |
| 7 | 6 | 6 | 6 | 0 | 0 |
| 8 | 0 | 0 | 0 | 0 | 0 |
| 9 | 0 | 0 | 0 | 0 | 0 |
| 10 | 0 | 0 | 0 | 0 | 0 |
| 11 | 0 | 0 | 0 | 0 | 0 |
| 12 | 0 | 0 | 0 | 0 | 0 |
| 13 | 0 | 0 | 0 | 0 | 0 |

Additional staging state findings:

- Promoted but unreviewed staging rows: none
- Reviewed but unpromoted staging rows found: thesis_id 1 (1 row), thesis_id 2 (1 orphaned-row thesis reference), thesis_id 6 (2 rows)
- Microsoft thesis_id=14 staging profile: 12 staged, 1 reviewed, 1 promoted, 11 unreviewed

## F. Evidence Item Summary

| thesis_id | evidence_items | without_pillar_link | missing_publication_date | promoted_but_unmapped_inferred |
|---|---|---|---|---|
| 14 | 3 | 3 | 0 | 3 |
| 1 | 3 | 2 | 0 | 2 |
| 3 | 0 | 0 | 0 | 0 |
| 4 | 0 | 0 | 0 | 0 |
| 5 | 0 | 0 | 0 | 0 |
| 6 | 3 | 3 | 0 | 3 |
| 7 | 6 | 6 | 1 | 6 |
| 8 | 0 | 0 | 0 | 0 |
| 9 | 0 | 0 | 0 | 0 |
| 10 | 0 | 0 | 0 | 0 |
| 11 | 0 | 0 | 0 | 0 |
| 12 | 0 | 0 | 0 | 0 |
| 13 | 0 | 0 | 0 | 0 |

Notes:

- Evidence items without pillar links total: 14 rows (thesis_id 14:3, 1:2, 6:3, 7:6).
- All evidence item rows observed in this check carry `status='Promoted'`.

## G. Observation Summary

| thesis_id | evidence_observations | extracted_observations | orphan_observations |
|---|---|---|---|
| 14 | 2 | 55 | 0 |
| 1 | 0 | 0 | 0 |
| 3 | 0 | 0 | 0 |
| 4 | 0 | 0 | 0 |
| 5 | 0 | 0 | 0 |
| 6 | 0 | 0 | 0 |
| 7 | 2 | 0 | 0 |
| 8 | 0 | 40 | 0 |
| 9 | 0 | 35 | 0 |
| 10 | 0 | 15 | 0 |
| 11 | 0 | 20 | 0 |
| 12 | 0 | 21 | 0 |
| 13 | 0 | 0 | 0 |

Notes:

- Orphan evidence observations (missing evidence item): 0

## H. Pillar Score / Pillar Link Summary

| thesis_id | pillar_scores | covered_pillars | assessment_only_pillar_scores | pillar_links | scores_without_links | links_without_scores |
|---|---|---|---|---|---|---|
| 14 | 11 | B1,B2,B3,B4,B5,B6,B7,I1,I2,I3,I4 | 11 | 0 | 11 | 0 |
| 1 | 11 | B1,B2,B3,B4,B5,B6,B7,I1,I2,I3,I4 | 11 | 1 | 10 | 0 |
| 3 | 0 | none | 0 | 0 | 0 | 0 |
| 4 | 0 | none | 0 | 0 | 0 | 0 |
| 5 | 0 | none | 0 | 0 | 0 | 0 |
| 6 | 11 | B1,B2,B3,B4,B5,B6,B7,I1,I2,I3,I4 | 11 | 0 | 11 | 0 |
| 7 | 11 | B1,B2,B3,B4,B5,B6,B7,I1,I2,I3,I4 | 11 | 0 | 11 | 0 |
| 8 | 0 | none | 0 | 0 | 0 | 0 |
| 9 | 0 | none | 0 | 0 | 0 | 0 |
| 10 | 0 | none | 0 | 0 | 0 | 0 |
| 11 | 0 | none | 0 | 0 | 0 | 0 |
| 12 | 0 | none | 0 | 0 | 0 | 0 |
| 13 | 0 | none | 0 | 0 | 0 | 0 |

Notes:

- `links_without_scores` check returned 0.
- For thesis_id 14, 1, 6, 7: B1-B7 and I1-I4 score rows exist.
- For thesis_id 14/6/7: all score rows are currently without direct pillar links.

## I. Event History Summary

| thesis_id | thesis_events | decision_logs | thesis_reviews | lifecycle_gap_note |
|---|---|---|---|---|
| 14 | 58 | 1 | 0 | No explicit closure/freeze marker discovered in inspected fields. |
| 1 | 64 | 1 | 2 | No explicit closure/freeze marker discovered in inspected fields. |
| 3 | 1 | 0 | 0 | No explicit closure/freeze marker discovered in inspected fields. |
| 4 | 1 | 0 | 0 | No explicit closure/freeze marker discovered in inspected fields. |
| 5 | 1 | 0 | 0 | No explicit closure/freeze marker discovered in inspected fields. |
| 6 | 30 | 1 | 3 | No explicit closure/freeze marker discovered in inspected fields. |
| 7 | 59 | 1 | 1 | No explicit closure/freeze marker discovered in inspected fields. |
| 8 | 9 | 0 | 0 | No explicit closure/freeze marker discovered in inspected fields. |
| 9 | 9 | 0 | 0 | No explicit closure/freeze marker discovered in inspected fields. |
| 10 | 9 | 0 | 0 | No explicit closure/freeze marker discovered in inspected fields. |
| 11 | 9 | 0 | 0 | No explicit closure/freeze marker discovered in inspected fields. |
| 12 | 9 | 0 | 0 | No explicit closure/freeze marker discovered in inspected fields. |
| 13 | 1 | 0 | 0 | No explicit closure/freeze marker discovered in inspected fields. |

Additional lifecycle signals:

- `thesis_events` contains orphan thesis reference: thesis_id=2 (1 row).
- Decision action snapshot shows recommendations populated for thesis_id 14, 6, 7; thesis_id 1 has null action/recommendation.

## J. Evaluation Preparation / Document Pipeline Summary

| thesis_id | preparations | candidate_docs | acquired_docs | extracted_observations |
|---|---|---|---|---|
| 14 | 1 | 8 | 8 | 55 |
| 1 | 0 | 0 | 0 | 0 |
| 3 | 0 | 0 | 0 | 0 |
| 4 | 0 | 0 | 0 | 0 |
| 5 | 0 | 0 | 0 | 0 |
| 6 | 0 | 0 | 0 | 0 |
| 7 | 0 | 0 | 0 | 0 |
| 8 | 1 | 8 | 8 | 40 |
| 9 | 1 | 8 | 8 | 35 |
| 10 | 1 | 8 | 8 | 15 |
| 11 | 1 | 8 | 8 | 20 |
| 12 | 1 | 8 | 8 | 21 |
| 13 | 1 | 0 | 0 | 0 |

Pipeline orphan checks:

| check_name | row_count |
|---|---|
| candidate_missing_prep | 0 |
| acquired_missing_prep | 0 |
| extracted_missing_prep | 0 |
| extracted_missing_acquired_doc | 0 |
| prep_missing_thesis_link | 0 |

Linkage quality note:

- Orphan check categories above all returned 0; pipeline foreign-key style linkage appears internally consistent for inspected tables.
- Odd OVC/evaluation pipeline pattern preserved (thesis_id 8, 9, 10, 11, 12): each has evaluation pipeline rows (`evaluation_preparations`, `evaluation_candidate_documents`, `evaluation_acquired_documents`, `evaluation_extracted_observations`) while showing zero governed `evidence_items`, zero `pillar_scores`, and zero `pillar_evidence_links`.
- This pattern is classified as evaluation-pipeline residue / workflow-discovery evidence pending explicit identity authority for thesis_id 9/10/11/12.
- thesis_id 8 remains an Archived Constitutional Asset / No-Touch Regression Reference and is not grouped with pending-authority pipeline residue.
- No deletion, repair, migration, or normalization is authorized for these rows in this sprint.

## K. Data Quality Issues

- Ambiguous identity records pending authority: thesis_id 9, 10, 11, 12.
- Substantive unsigned records preserved pending sign-off disposition: thesis_id 1, 6.
- Manual/test-like records present: thesis_id 3, 4, 5, 13.
- Orphan thesis references in non-thesis tables: thesis_id 2 in `thesis_events` and `evidence_staging`.
- Evidence without pillar links: 14 promoted evidence items across thesis_id 14/1/6/7.
- Reviewed but unpromoted staging records exist (thesis_id 1/2/6).
- Assessment-only pillar score pattern appears for thesis_id 14/1/6/7.
- Period semantics ambiguity exists where `publication_date` missing (observed for thesis_id 7).
- Records that should not appear as active governed work without authority: thesis_id 14 remains source-context only; thesis_id 9/10/11/12 remain evaluation-pipeline residue pending authority.
- OVC/evaluation pipeline residue pattern observed for thesis_id 8/9/10/11/12: extraction-heavy pipeline artifacts exist without governed evidence-item/pillar-score/pillar-link materialization.
- OVC/pipeline residue records thesis_id 9/10/11/12 are preserved as workflow-discovery evidence pending explicit identity review authority (not auto-junk).
- thesis_id 8 is preserved as an Archived Constitutional Asset / No-Touch Regression Reference (not pending-authority residue).

## L. Records That Must Remain Untouched

- thesis_id=14 (Microsoft source-context historical artifact)
- thesis_id=7 (Kodak archived constitutional asset)
- thesis_id=8 (NVIDIA NoTouch Archived Constitutional Asset / No-Touch Regression Reference)
- thesis_id=9 (Microsoft OVC-004 evaluation-pipeline residue / workflow-discovery evidence pending authority)
- thesis_id=10 (Oracle OVC-004 PostFix evaluation-pipeline residue / workflow-discovery evidence pending authority)
- thesis_id=11 (Intel OVC-004 INT-001 evaluation-pipeline residue / workflow-discovery evidence pending authority; grouped with 9/10/12 absent external authority)
- thesis_id=12 (Qualcomm OVC-004 INT-001 evaluation-pipeline residue / workflow-discovery evidence pending authority)
- thesis_id=1 (historical substantive record; pending governance sign-off)
- thesis_id=6 (historical baseline candidate pending explicit authority)

## M. Records Requiring Future Cleanup Authority

| thesis_id | issue | why cleanup may be needed | required authority before action | pending recommendation |
|---|---|---|---|---|
| 2 (not in theses table) | orphan references in thesis_events/evidence_staging | referential drift; ambiguous provenance | explicit data-hygiene repair authority with archival policy | untouched pending authority |
| 3 | manual scratch-like thesis record | no substantive linked runtime data | explicit cleanup authorization | hide/archive candidate pending authority |
| 4 | manual scratch-like thesis record | no substantive linked runtime data | explicit cleanup authorization | hide/archive candidate pending authority |
| 5 | manual scratch-like thesis record | no substantive linked runtime data | explicit cleanup authorization | hide/archive candidate pending authority |
| 8 | NoTouch archived constitutional reference preservation controls | ensure no-touch archived constitutional handling remains explicit and unchanged | explicit archival governance policy confirmation | remain untouched as archived constitutional no-touch reference |
| 9 | OVC evaluation-pipeline residue pattern | pipeline artifacts exist without governed evidence/pillar materialization | explicit identity + workflow residue authority | remain visible as workflow-discovery evidence pending review |
| 10 | OVC evaluation-pipeline residue pattern | pipeline artifacts exist without governed evidence/pillar materialization | explicit identity + workflow residue authority | remain visible as workflow-discovery evidence pending review |
| 11 | OVC evaluation-pipeline residue pattern | pipeline artifacts exist without governed evidence/pillar materialization | explicit identity + workflow residue authority | remain grouped with 9/10/12 pending review |
| 12 | OVC evaluation-pipeline residue pattern | pipeline artifacts exist without governed evidence/pillar materialization | explicit identity + workflow residue authority | remain visible as workflow-discovery evidence pending review |
| 13 | temporary validation record | likely non-governed validation artifact | explicit cleanup authorization | hide/archive candidate pending authority |

## N. Recommended Next Action

1. Complete governance review of this hygiene report and ratify data-hygiene authority boundaries.
2. Resolve orphan references (thesis_id=2) under explicit repair authority only.
3. Decide sign-off disposition for thesis_id 1/6 and identity disposition for thesis_id 9/10/11/12, while preserving thesis_id 8 as an archived constitutional no-touch reference.
4. After authority decisions, define cleanup execution plan (visibility/hide/archive/retain), then reassess Microsoft Option A/B/C.
5. Defer Hermes/SpaceX setup until identity and hygiene authority decisions are finalized.

## O. No-Mutation Guarantee

- Exact DB path inspected: `/Users/phillipcaswell/ims_mvp.db`
- No application code files were changed.
- No DB writes were performed.
- No rows were inserted, updated, deleted, migrated, or repaired.
- No files were staged.
- No commits were made.

## P. Full Command and SQL Appendix

### Shell commands used

```bash
git status --short

echo "ATHENA_DB_PATH=${ATHENA_DB_PATH}"
# authoritative path resolution / stat checks / ambiguity checks

sqlite3 "file:/Users/phillipcaswell/ims_mvp.db?mode=ro" ".tables"

for t in theses decision_logs thesis_reviews evidence_staging evidence_items evidence_observations pillar_scores pillar_evidence_links thesis_events evaluation_preparations evaluation_candidate_documents evaluation_acquired_documents evaluation_extracted_observations evaluation_extraction_runs; do
  sqlite3 "file:/Users/phillipcaswell/ims_mvp.db?mode=ro" ".schema $t"
  sqlite3 "file:/Users/phillipcaswell/ims_mvp.db?mode=ro" "PRAGMA table_info($t);"
done
```

### Data Explorer cross-check interaction

- Opened Athena UI at `http://localhost:8503/`
- Navigated to Data Explorer
- Observed runtime DB path text: `/Users/phillipcaswell/ims_mvp.db`
- Observed Data Explorer read-only warning and thesis selector including thesis_id=14

### SQLite queries used (read-only)

```sql
SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;

SELECT sql FROM sqlite_master WHERE type='table' AND name=?;

PRAGMA table_info(theses);
PRAGMA table_info(decision_logs);
PRAGMA table_info(thesis_reviews);
PRAGMA table_info(evidence_staging);
PRAGMA table_info(evidence_items);
PRAGMA table_info(evidence_observations);
PRAGMA table_info(pillar_scores);
PRAGMA table_info(pillar_evidence_links);
PRAGMA table_info(thesis_events);
PRAGMA table_info(evaluation_preparations);
PRAGMA table_info(evaluation_candidate_documents);
PRAGMA table_info(evaluation_acquired_documents);
PRAGMA table_info(evaluation_extracted_observations);
PRAGMA table_info(evaluation_extraction_runs);

SELECT id AS thesis_id, company_name, ticker, status, created_at, validation_mode, evidence_cutoff_date
FROM theses
ORDER BY CASE WHEN id=14 THEN 0 ELSE 1 END, id;

WITH thesis_base AS (
  SELECT id AS thesis_id, company_name, ticker, status, created_at FROM theses
),
decision_counts AS (SELECT thesis_id, COUNT(*) AS decision_logs_count FROM decision_logs GROUP BY thesis_id),
review_counts AS (SELECT thesis_id, COUNT(*) AS thesis_reviews_count FROM thesis_reviews GROUP BY thesis_id),
staging_counts AS (
  SELECT thesis_id,
         COUNT(*) AS staged_count,
         SUM(CASE WHEN review_date IS NOT NULL AND TRIM(review_date)<>'' THEN 1 ELSE 0 END) AS reviewed_staged_count,
         SUM(CASE WHEN promoted_at IS NOT NULL AND TRIM(promoted_at)<>'' THEN 1 ELSE 0 END) AS promoted_staged_count,
         SUM(CASE WHEN review_date IS NULL OR TRIM(review_date)='' THEN 1 ELSE 0 END) AS unreviewed_staged_count,
         SUM(CASE WHEN intake_status IS NULL OR TRIM(intake_status)='' THEN 1 ELSE 0 END) AS unclear_intake_status_count
  FROM evidence_staging
  GROUP BY thesis_id
),
evidence_counts AS (SELECT thesis_id, COUNT(*) AS evidence_items_count FROM evidence_items GROUP BY thesis_id),
unmapped_evidence_counts AS (
  SELECT ei.thesis_id, COUNT(*) AS evidence_items_without_pillar_link_count
  FROM evidence_items ei
  LEFT JOIN pillar_evidence_links pel ON pel.evidence_item_id = ei.id
  WHERE pel.id IS NULL
  GROUP BY ei.thesis_id
),
period_ambiguity_counts AS (
  SELECT thesis_id, COUNT(*) AS evidence_items_missing_publication_date_count
  FROM evidence_items
  WHERE publication_date IS NULL OR TRIM(publication_date)=''
  GROUP BY thesis_id
),
observation_counts AS (
  SELECT ei.thesis_id, COUNT(*) AS evidence_observations_count
  FROM evidence_observations eo
  JOIN evidence_items ei ON ei.id = eo.evidence_item_id
  GROUP BY ei.thesis_id
),
pillar_score_counts AS (SELECT thesis_id, COUNT(*) AS pillar_scores_count FROM pillar_scores GROUP BY thesis_id),
pillar_scores_without_link_counts AS (
  SELECT ps.thesis_id, COUNT(*) AS pillar_scores_without_link_count
  FROM pillar_scores ps
  LEFT JOIN pillar_evidence_links pel ON pel.pillar_score_id = ps.id
  WHERE pel.id IS NULL
  GROUP BY ps.thesis_id
),
assessment_only_counts AS (
  SELECT thesis_id, COUNT(*) AS assessment_only_pillar_scores_count
  FROM pillar_scores
  WHERE COALESCE(TRIM(judgment), '') <> ''
    AND (evidence_items IS NULL OR TRIM(evidence_items) = '')
  GROUP BY thesis_id
),
pillar_link_counts AS (
  SELECT ps.thesis_id, COUNT(*) AS pillar_evidence_links_count
  FROM pillar_evidence_links pel
  JOIN pillar_scores ps ON ps.id = pel.pillar_score_id
  GROUP BY ps.thesis_id
),
event_counts AS (SELECT thesis_id, COUNT(*) AS thesis_events_count FROM thesis_events GROUP BY thesis_id),
prep_counts AS (SELECT thesis_id, COUNT(*) AS evaluation_preparations_count FROM evaluation_preparations GROUP BY thesis_id),
candidate_counts AS (SELECT thesis_id, COUNT(*) AS evaluation_candidate_documents_count FROM evaluation_candidate_documents GROUP BY thesis_id),
acquired_counts AS (SELECT thesis_id, COUNT(*) AS evaluation_acquired_documents_count FROM evaluation_acquired_documents GROUP BY thesis_id),
extracted_counts AS (SELECT thesis_id, COUNT(*) AS evaluation_extracted_observations_count FROM evaluation_extracted_observations GROUP BY thesis_id)
SELECT b.thesis_id, b.company_name, b.ticker, b.status, b.created_at,
       COALESCE(d.decision_logs_count,0) AS decision_logs_count,
       COALESCE(r.thesis_reviews_count,0) AS thesis_reviews_count,
       COALESCE(s.staged_count,0) AS staged_count,
       COALESCE(s.reviewed_staged_count,0) AS reviewed_staged_count,
       COALESCE(s.promoted_staged_count,0) AS promoted_staged_count,
       COALESCE(s.unreviewed_staged_count,0) AS unreviewed_staged_count,
       COALESCE(s.unclear_intake_status_count,0) AS unclear_intake_status_count,
       COALESCE(e.evidence_items_count,0) AS evidence_items_count,
       COALESCE(u.evidence_items_without_pillar_link_count,0) AS evidence_items_without_pillar_link_count,
       COALESCE(pa.evidence_items_missing_publication_date_count,0) AS evidence_items_missing_publication_date_count,
       COALESCE(o.evidence_observations_count,0) AS evidence_observations_count,
       COALESCE(psc.pillar_scores_count,0) AS pillar_scores_count,
       COALESCE(pw.pillar_scores_without_link_count,0) AS pillar_scores_without_link_count,
       COALESCE(ac.assessment_only_pillar_scores_count,0) AS assessment_only_pillar_scores_count,
       COALESCE(plc.pillar_evidence_links_count,0) AS pillar_evidence_links_count,
       COALESCE(ev.thesis_events_count,0) AS thesis_events_count,
       COALESCE(pr.evaluation_preparations_count,0) AS evaluation_preparations_count,
       COALESCE(cd.evaluation_candidate_documents_count,0) AS evaluation_candidate_documents_count,
       COALESCE(ad.evaluation_acquired_documents_count,0) AS evaluation_acquired_documents_count,
       COALESCE(xo.evaluation_extracted_observations_count,0) AS evaluation_extracted_observations_count
FROM thesis_base b
LEFT JOIN decision_counts d ON d.thesis_id=b.thesis_id
LEFT JOIN review_counts r ON r.thesis_id=b.thesis_id
LEFT JOIN staging_counts s ON s.thesis_id=b.thesis_id
LEFT JOIN evidence_counts e ON e.thesis_id=b.thesis_id
LEFT JOIN unmapped_evidence_counts u ON u.thesis_id=b.thesis_id
LEFT JOIN period_ambiguity_counts pa ON pa.thesis_id=b.thesis_id
LEFT JOIN observation_counts o ON o.thesis_id=b.thesis_id
LEFT JOIN pillar_score_counts psc ON psc.thesis_id=b.thesis_id
LEFT JOIN pillar_scores_without_link_counts pw ON pw.thesis_id=b.thesis_id
LEFT JOIN assessment_only_counts ac ON ac.thesis_id=b.thesis_id
LEFT JOIN pillar_link_counts plc ON plc.thesis_id=b.thesis_id
LEFT JOIN event_counts ev ON ev.thesis_id=b.thesis_id
LEFT JOIN prep_counts pr ON pr.thesis_id=b.thesis_id
LEFT JOIN candidate_counts cd ON cd.thesis_id=b.thesis_id
LEFT JOIN acquired_counts ad ON ad.thesis_id=b.thesis_id
LEFT JOIN extracted_counts xo ON xo.thesis_id=b.thesis_id
ORDER BY CASE WHEN b.thesis_id=14 THEN 0 ELSE 1 END, b.thesis_id;

SELECT thesis_id, pillar_id, COUNT(*) AS score_rows
FROM pillar_scores
GROUP BY thesis_id, pillar_id
ORDER BY CASE WHEN thesis_id=14 THEN 0 ELSE 1 END, thesis_id, pillar_id;

SELECT 'candidate_missing_prep' AS check_name, COUNT(*) AS row_count
FROM evaluation_candidate_documents ecd
LEFT JOIN evaluation_preparations ep ON ep.id = ecd.preparation_id
WHERE ep.id IS NULL
UNION ALL
SELECT 'acquired_missing_prep', COUNT(*)
FROM evaluation_acquired_documents ead
LEFT JOIN evaluation_preparations ep ON ep.id = ead.preparation_id
WHERE ep.id IS NULL
UNION ALL
SELECT 'extracted_missing_prep', COUNT(*)
FROM evaluation_extracted_observations eeo
LEFT JOIN evaluation_preparations ep ON ep.id = eeo.preparation_id
WHERE ep.id IS NULL
UNION ALL
SELECT 'extracted_missing_acquired_doc', COUNT(*)
FROM evaluation_extracted_observations eeo
LEFT JOIN evaluation_acquired_documents ead ON ead.id = eeo.acquired_document_id
WHERE eeo.acquired_document_id IS NOT NULL AND ead.id IS NULL
UNION ALL
SELECT 'prep_missing_thesis_link', COUNT(*)
FROM evaluation_preparations ep
LEFT JOIN theses t ON t.id = ep.thesis_id
WHERE ep.thesis_id IS NOT NULL AND t.id IS NULL;

SELECT ei.thesis_id, ei.id AS evidence_item_id, ei.related_pillar, ei.status
FROM evidence_items ei
LEFT JOIN pillar_evidence_links pel ON pel.evidence_item_id = ei.id
WHERE pel.id IS NULL
ORDER BY CASE WHEN ei.thesis_id=14 THEN 0 ELSE 1 END, ei.thesis_id, ei.id;

SELECT ps.thesis_id, ps.id AS pillar_score_id, ps.pillar_id, ps.pillar_name
FROM pillar_scores ps
LEFT JOIN pillar_evidence_links pel ON pel.pillar_score_id = ps.id
WHERE pel.id IS NULL
ORDER BY CASE WHEN ps.thesis_id=14 THEN 0 ELSE 1 END, ps.thesis_id, ps.id;

SELECT eo.id AS observation_id, eo.evidence_item_id
FROM evidence_observations eo
LEFT JOIN evidence_items ei ON ei.id = eo.evidence_item_id
WHERE ei.id IS NULL
ORDER BY eo.id;

SELECT thesis_id, event_type, COUNT(*) AS event_count
FROM thesis_events
GROUP BY thesis_id, event_type
ORDER BY CASE WHEN thesis_id=14 THEN 0 ELSE 1 END, thesis_id, event_type;

SELECT thesis_id, action, recommendation, COUNT(*) AS row_count
FROM decision_logs
GROUP BY thesis_id, action, recommendation
ORDER BY CASE WHEN thesis_id=14 THEN 0 ELSE 1 END, thesis_id, action, recommendation;

SELECT thesis_id, COUNT(*) c
FROM thesis_events te
LEFT JOIN theses t ON t.id=te.thesis_id
WHERE te.thesis_id IS NOT NULL AND t.id IS NULL
GROUP BY thesis_id
ORDER BY thesis_id;

SELECT thesis_id, COUNT(*) c
FROM evidence_staging es
LEFT JOIN theses t ON t.id=es.thesis_id
WHERE es.thesis_id IS NOT NULL AND t.id IS NULL
GROUP BY thesis_id
ORDER BY thesis_id;

SELECT thesis_id, id, intake_status, review_date, promoted_at, rejection_reason
FROM evidence_staging
WHERE review_date IS NOT NULL AND TRIM(review_date)<>''
  AND (promoted_at IS NULL OR TRIM(promoted_at)='')
ORDER BY thesis_id,id;
```

### Final verification commands

```bash
git status --short
```
