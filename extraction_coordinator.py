from datetime import datetime

from services import fetch_dataframe, insert_query, extract_observation_suggestions_from_text


EXTRACTION_STATUS_PENDING = "pending"
EXTRACTION_STATUS_NOT_ATTEMPTED = "not_attempted"
EXTRACTION_STATUS_UNSUPPORTED = "unsupported"
EXTRACTION_STATUS_FAILED = "failed"
EXTRACTION_STATUS_COMPLETED = "completed"

DEFAULT_EXTRACTOR_VERSION = "theia-sonnet-4-6-v1"


def coordinate_extraction(
    preparation_id,
    thesis_id,
    acquired_documents,
    extractor_version=DEFAULT_EXTRACTOR_VERSION,
    refresh=False,
):
    """Coordinate extraction for acquired materials while preserving reuse and provenance."""
    docs = acquired_documents if isinstance(acquired_documents, list) else []
    if not docs:
        return {
            "extraction_status": EXTRACTION_STATUS_NOT_ATTEMPTED,
            "extracted_observation_count": 0,
            "extraction_timestamp": None,
            "extraction_results": [],
            "extraction_warnings": [],
            "extraction_reused": False,
            "extractor_version": extractor_version,
        }

    results = []
    warnings = []
    extraction_reused = True
    total_observations = 0
    status_bucket = []
    last_timestamp = None

    for acquired in docs:
        doc_id = _coerce_int(acquired.get("id"))
        source_content = str(acquired.get("source_content", "")).strip()
        source_hash = str(acquired.get("source_content_hash", "")).strip()
        acquisition_status = str(acquired.get("acquisition_status", "")).strip()

        if acquisition_status != "acquired":
            run_payload = _upsert_run_without_extraction(
                preparation_id=preparation_id,
                thesis_id=thesis_id,
                acquired_document=acquired,
                extractor_version=extractor_version,
                status=EXTRACTION_STATUS_UNSUPPORTED,
                warning_message="Acquisition did not produce retrievable source material.",
                refresh=refresh,
            )
            results.append(run_payload)
            warnings.extend(run_payload.get("warnings", []))
            status_bucket.append(run_payload["extraction_status"])
            extraction_reused = extraction_reused and bool(run_payload.get("reused", False))
            continue

        if not source_content:
            run_payload = _upsert_run_without_extraction(
                preparation_id=preparation_id,
                thesis_id=thesis_id,
                acquired_document=acquired,
                extractor_version=extractor_version,
                status=EXTRACTION_STATUS_UNSUPPORTED,
                warning_message="No source text available for extraction; source reference preserved.",
                refresh=refresh,
            )
            results.append(run_payload)
            warnings.extend(run_payload.get("warnings", []))
            status_bucket.append(run_payload["extraction_status"])
            extraction_reused = extraction_reused and bool(run_payload.get("reused", False))
            continue

        reusable_run = None if refresh else _find_reusable_run(
            preparation_id=preparation_id,
            acquired_document_id=doc_id,
            extractor_version=extractor_version,
            source_content_hash=source_hash,
        )
        if reusable_run is not None:
            observation_rows = _load_observations_for_run(reusable_run["id"])
            observation_count = len(observation_rows)
            run_payload = {
                "acquired_document_id": doc_id,
                "originating_document": str(acquired.get("title", "")).strip(),
                "extraction_status": str(reusable_run.get("extraction_status", EXTRACTION_STATUS_COMPLETED)).strip(),
                "observation_count": observation_count,
                "extraction_timestamp": str(reusable_run.get("extraction_timestamp", "")).strip() or None,
                "reused": True,
                "extractor_version": str(reusable_run.get("extractor_version", extractor_version)).strip(),
                "warnings": [],
                "error": str(reusable_run.get("error_message", "")).strip(),
                "preview": observation_rows[:3],
            }
            results.append(run_payload)
            status_bucket.append(run_payload["extraction_status"])
            total_observations += observation_count
            extraction_reused = extraction_reused and True
            if run_payload["extraction_timestamp"]:
                last_timestamp = run_payload["extraction_timestamp"]
            continue

        extraction_reused = False
        extraction_response = extract_observation_suggestions_from_text(
            thesis_id=thesis_id,
            document_text=source_content,
            title=str(acquired.get("title", "")).strip(),
            subject_id=f"acquired_document_id={doc_id if doc_id is not None else 'unknown'}",
        )

        extraction_timestamp = datetime.now().isoformat()
        if extraction_response.get("success"):
            suggestions = extraction_response.get("suggestions", []) if isinstance(extraction_response, dict) else []
            run_id = insert_query(
                """
                INSERT INTO evaluation_extraction_runs
                (
                    preparation_id,
                    thesis_id,
                    acquired_document_id,
                    original_candidate_identifier,
                    source_reference,
                    acquisition_timestamp,
                    extraction_status,
                    extraction_timestamp,
                    extractor_version,
                    source_content_hash,
                    reused,
                    observation_count,
                    warning_message,
                    error_message,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    int(preparation_id),
                    int(thesis_id) if thesis_id is not None else None,
                    doc_id,
                    str(acquired.get("original_candidate_identifier", "")).strip() or None,
                    str(acquired.get("source_reference", "")).strip() or None,
                    str(acquired.get("retrieval_timestamp", "")).strip() or None,
                    EXTRACTION_STATUS_COMPLETED,
                    extraction_timestamp,
                    extractor_version,
                    source_hash or None,
                    0,
                    len(suggestions),
                    None,
                    None,
                    extraction_timestamp,
                    extraction_timestamp,
                ),
            )

            for suggestion in suggestions:
                insert_query(
                    """
                    INSERT INTO evaluation_extracted_observations
                    (
                        extraction_run_id,
                        preparation_id,
                        thesis_id,
                        acquired_document_id,
                        original_candidate_identifier,
                        source_reference,
                        acquisition_timestamp,
                        extraction_timestamp,
                        extractor_version,
                        passage,
                        pillar_signal,
                        confidence,
                        source_location,
                        created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        int(run_id),
                        int(preparation_id),
                        int(thesis_id) if thesis_id is not None else None,
                        doc_id,
                        str(acquired.get("original_candidate_identifier", "")).strip() or None,
                        str(acquired.get("source_reference", "")).strip() or None,
                        str(acquired.get("retrieval_timestamp", "")).strip() or None,
                        extraction_timestamp,
                        extractor_version,
                        str(suggestion.get("passage", "")).strip(),
                        str(suggestion.get("pillar_signal", "")).strip() or None,
                        str(suggestion.get("confidence", "")).strip() or None,
                        str(suggestion.get("source_location", "")).strip() or None,
                        extraction_timestamp,
                    ),
                )

            run_payload = {
                "acquired_document_id": doc_id,
                "originating_document": str(acquired.get("title", "")).strip(),
                "extraction_status": EXTRACTION_STATUS_COMPLETED,
                "observation_count": len(suggestions),
                "extraction_timestamp": extraction_timestamp,
                "reused": False,
                "extractor_version": extractor_version,
                "warnings": [],
                "error": "",
                "preview": suggestions[:3],
            }
            results.append(run_payload)
            status_bucket.append(EXTRACTION_STATUS_COMPLETED)
            total_observations += len(suggestions)
            last_timestamp = extraction_timestamp
            continue

        error_message = str(extraction_response.get("message", "Extraction failed.")).strip()
        warning_message = "Automatic extraction failed for this document; analyst workflow can continue."
        run_id = insert_query(
            """
            INSERT INTO evaluation_extraction_runs
            (
                preparation_id,
                thesis_id,
                acquired_document_id,
                original_candidate_identifier,
                source_reference,
                acquisition_timestamp,
                extraction_status,
                extraction_timestamp,
                extractor_version,
                source_content_hash,
                reused,
                observation_count,
                warning_message,
                error_message,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                int(preparation_id),
                int(thesis_id) if thesis_id is not None else None,
                doc_id,
                str(acquired.get("original_candidate_identifier", "")).strip() or None,
                str(acquired.get("source_reference", "")).strip() or None,
                str(acquired.get("retrieval_timestamp", "")).strip() or None,
                EXTRACTION_STATUS_FAILED,
                extraction_timestamp,
                extractor_version,
                source_hash or None,
                0,
                0,
                warning_message,
                error_message,
                extraction_timestamp,
                extraction_timestamp,
            ),
        )

        run_payload = {
            "acquired_document_id": doc_id,
            "originating_document": str(acquired.get("title", "")).strip(),
            "extraction_status": EXTRACTION_STATUS_FAILED,
            "observation_count": 0,
            "extraction_timestamp": extraction_timestamp,
            "reused": False,
            "extractor_version": extractor_version,
            "warnings": [warning_message],
            "error": error_message,
            "preview": [],
            "run_id": run_id,
        }
        results.append(run_payload)
        warnings.extend(run_payload["warnings"])
        status_bucket.append(EXTRACTION_STATUS_FAILED)
        last_timestamp = extraction_timestamp

    aggregate_status = _aggregate_status(status_bucket)
    return {
        "extraction_status": aggregate_status,
        "extracted_observation_count": int(total_observations),
        "extraction_timestamp": last_timestamp,
        "extraction_results": results,
        "extraction_warnings": warnings,
        "extraction_reused": bool(results) and extraction_reused,
        "extractor_version": extractor_version,
    }


def _find_reusable_run(preparation_id, acquired_document_id, extractor_version, source_content_hash):
    if acquired_document_id is None:
        return None

    run_df = fetch_dataframe(
        """
        SELECT *
        FROM evaluation_extraction_runs
        WHERE preparation_id = ?
          AND acquired_document_id = ?
          AND extractor_version = ?
          AND COALESCE(source_content_hash, '') = COALESCE(?, '')
        ORDER BY id DESC
        LIMIT 1
        """,
        (
            int(preparation_id),
            int(acquired_document_id),
            str(extractor_version).strip(),
            str(source_content_hash).strip() if source_content_hash else "",
        ),
    )
    if run_df.empty:
        return None
    return run_df.iloc[0].to_dict()


def _load_observations_for_run(run_id):
    obs_df = fetch_dataframe(
        """
        SELECT passage, pillar_signal, confidence, source_location
        FROM evaluation_extracted_observations
        WHERE extraction_run_id = ?
        ORDER BY id ASC
        """,
        (int(run_id),),
    )
    if obs_df.empty:
        return []
    return obs_df.to_dict("records")


def _upsert_run_without_extraction(
    preparation_id,
    thesis_id,
    acquired_document,
    extractor_version,
    status,
    warning_message,
    refresh,
):
    doc_id = _coerce_int(acquired_document.get("id"))
    source_hash = str(acquired_document.get("source_content_hash", "")).strip()

    if not refresh:
        reusable = _find_reusable_run(
            preparation_id=preparation_id,
            acquired_document_id=doc_id,
            extractor_version=extractor_version,
            source_content_hash=source_hash,
        )
        if reusable is not None:
            return {
                "acquired_document_id": doc_id,
                "originating_document": str(acquired_document.get("title", "")).strip(),
                "extraction_status": str(reusable.get("extraction_status", status)).strip(),
                "observation_count": int(reusable.get("observation_count") or 0),
                "extraction_timestamp": str(reusable.get("extraction_timestamp", "")).strip() or None,
                "reused": True,
                "extractor_version": str(reusable.get("extractor_version", extractor_version)).strip(),
                "warnings": [str(reusable.get("warning_message", "")).strip()] if str(reusable.get("warning_message", "")).strip() else [],
                "error": str(reusable.get("error_message", "")).strip(),
                "preview": [],
            }

    now_value = datetime.now().isoformat()
    run_id = insert_query(
        """
        INSERT INTO evaluation_extraction_runs
        (
            preparation_id,
            thesis_id,
            acquired_document_id,
            original_candidate_identifier,
            source_reference,
            acquisition_timestamp,
            extraction_status,
            extraction_timestamp,
            extractor_version,
            source_content_hash,
            reused,
            observation_count,
            warning_message,
            error_message,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            int(preparation_id),
            int(thesis_id) if thesis_id is not None else None,
            doc_id,
            str(acquired_document.get("original_candidate_identifier", "")).strip() or None,
            str(acquired_document.get("source_reference", "")).strip() or None,
            str(acquired_document.get("retrieval_timestamp", "")).strip() or None,
            status,
            now_value,
            extractor_version,
            source_hash or None,
            0,
            0,
            warning_message,
            None,
            now_value,
            now_value,
        ),
    )
    return {
        "acquired_document_id": doc_id,
        "originating_document": str(acquired_document.get("title", "")).strip(),
        "extraction_status": status,
        "observation_count": 0,
        "extraction_timestamp": now_value,
        "reused": False,
        "extractor_version": extractor_version,
        "warnings": [warning_message],
        "error": "",
        "preview": [],
        "run_id": run_id,
    }


def _aggregate_status(statuses):
    if not statuses:
        return EXTRACTION_STATUS_NOT_ATTEMPTED
    if any(status == EXTRACTION_STATUS_COMPLETED for status in statuses):
        return EXTRACTION_STATUS_COMPLETED
    if any(status == EXTRACTION_STATUS_FAILED for status in statuses):
        return EXTRACTION_STATUS_FAILED
    if any(status == EXTRACTION_STATUS_UNSUPPORTED for status in statuses):
        return EXTRACTION_STATUS_UNSUPPORTED
    return EXTRACTION_STATUS_NOT_ATTEMPTED


def _coerce_int(value):
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
