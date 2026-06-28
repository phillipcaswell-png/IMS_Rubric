import json
from datetime import date, datetime

from evidence_acquisition import (
    ACQUISITION_STATUS_ACQUIRED,
    ACQUISITION_STATUS_FAILED,
    ACQUISITION_STATUS_NOT_ATTEMPTED,
    ACQUISITION_STATUS_UNAVAILABLE,
    acquire_supported_candidates,
)
from evidence_discovery import discover_candidate_documents
from extraction_coordinator import (
    DEFAULT_EXTRACTOR_VERSION,
    EXTRACTION_STATUS_FAILED,
    EXTRACTION_STATUS_NOT_ATTEMPTED,
    EXTRACTION_STATUS_PENDING,
    coordinate_extraction,
)
from services import create_thesis, fetch_dataframe, get_overview_metrics, init_db, insert_query, run_query


LIFECYCLE_REQUESTED = "requested"
LIFECYCLE_PREPARING = "preparing"
LIFECYCLE_THESIS_READY = "thesis_ready"
LIFECYCLE_WORKSPACE_READY = "workspace_ready"
LIFECYCLE_READY_FOR_ANALYST = "ready_for_analyst"
LIFECYCLE_PARTIAL = "partial"
LIFECYCLE_FAILED = "failed"

READINESS_PENDING = "pending"
READINESS_PARTIAL = "partial"
READINESS_READY_FOR_ANALYST = "ready_for_analyst"
READINESS_FAILED = "failed"

DISCOVERY_STATUS_PENDING = "pending"
DISCOVERY_STATUS_DISCOVERED = "discovered"
DISCOVERY_STATUS_UNAVAILABLE = "unavailable"
DISCOVERY_STATUS_FAILED = "failed"

ACQUISITION_STATUS_PENDING = "pending"

EXTRACTION_STATUS_UNSUPPORTED = "unsupported"
EXTRACTION_STATUS_COMPLETED = "completed"

ENGINE_REVIEWER = "Operational Evaluation Engine"


def prepare_evaluation(
    ticker,
    observation_date,
    company_name=None,
    reviewer=ENGINE_REVIEWER,
    discovery_providers=None,
    acquisition_providers=None,
    extraction_refresh=False,
    extractor_version=DEFAULT_EXTRACTOR_VERSION,
):
    """Prepare or resume an evaluation shell for analyst review."""
    normalized_ticker = _normalize_ticker(ticker)
    normalized_observation_date = _normalize_observation_date(observation_date)

    if not normalized_ticker or not normalized_observation_date:
        return _build_ephemeral_failure(normalized_ticker, normalized_observation_date)

    init_db()
    preparation, preparation_action = _get_or_create_preparation(normalized_ticker, normalized_observation_date)
    warnings = []
    errors = []
    discovery_warnings = []
    discovery_status = DISCOVERY_STATUS_PENDING
    candidate_documents = []
    acquisition_warnings = []
    acquisition_status = ACQUISITION_STATUS_PENDING
    acquired_documents = []
    extraction_warnings = []
    extraction_status = EXTRACTION_STATUS_PENDING
    extracted_observation_count = 0
    extraction_timestamp = None
    extraction_results = []
    extraction_reused = False

    try:
        _persist_state(
            preparation["id"],
            LIFECYCLE_PREPARING,
            False,
            READINESS_PENDING,
            warnings,
            errors,
            discovery_status,
            candidate_documents,
            discovery_warnings,
            acquisition_status,
            acquired_documents,
            acquisition_warnings,
            extraction_status,
            extracted_observation_count,
            extraction_timestamp,
            extraction_results,
            extraction_warnings,
            extraction_reused,
            extractor_version,
            preparation.get("thesis_id"),
            preparation_action,
            "pending",
        )

        thesis_id, thesis_action = _resolve_or_create_thesis(
            preparation,
            normalized_ticker,
            normalized_observation_date,
            company_name,
            reviewer,
            warnings,
        )

        _persist_state(
            preparation["id"],
            LIFECYCLE_THESIS_READY,
            False,
            READINESS_PENDING,
            warnings,
            errors,
            discovery_status,
            candidate_documents,
            discovery_warnings,
            acquisition_status,
            acquired_documents,
            acquisition_warnings,
            extraction_status,
            extracted_observation_count,
            extraction_timestamp,
            extraction_results,
            extraction_warnings,
            extraction_reused,
            extractor_version,
            thesis_id,
            preparation_action,
            thesis_action,
        )

        discovery_status, candidate_documents, discovery_warnings = _resolve_candidate_discovery(
            preparation_id=preparation["id"],
            thesis_id=thesis_id,
            ticker=normalized_ticker,
            observation_date=normalized_observation_date,
            providers=discovery_providers,
        )

        acquisition_status, acquired_documents, acquisition_warnings = _resolve_source_acquisition(
            preparation_id=preparation["id"],
            thesis_id=thesis_id,
            discovery_status=discovery_status,
            candidate_documents=candidate_documents,
            providers=acquisition_providers,
        )

        (
            extraction_status,
            extracted_observation_count,
            extraction_timestamp,
            extraction_results,
            extraction_warnings,
            extraction_reused,
        ) = _resolve_automatic_extraction(
            preparation_id=preparation["id"],
            thesis_id=thesis_id,
            acquired_documents=acquired_documents,
            extractor_version=extractor_version,
            refresh=extraction_refresh,
        )

        workspace_ready = _verify_workspace_ready(thesis_id, errors)
        if workspace_ready:
            _persist_state(
                preparation["id"],
                LIFECYCLE_WORKSPACE_READY,
                True,
                READINESS_PENDING,
                warnings,
                errors,
                discovery_status,
                candidate_documents,
                discovery_warnings,
                acquisition_status,
                acquired_documents,
                acquisition_warnings,
                extraction_status,
                extracted_observation_count,
                extraction_timestamp,
                extraction_results,
                extraction_warnings,
                extraction_reused,
                extractor_version,
                thesis_id,
                preparation_action,
                thesis_action,
            )
            _persist_state(
                preparation["id"],
                LIFECYCLE_READY_FOR_ANALYST,
                True,
                READINESS_READY_FOR_ANALYST,
                warnings,
                errors,
                discovery_status,
                candidate_documents,
                discovery_warnings,
                acquisition_status,
                acquired_documents,
                acquisition_warnings,
                extraction_status,
                extracted_observation_count,
                extraction_timestamp,
                extraction_results,
                extraction_warnings,
                extraction_reused,
                extractor_version,
                thesis_id,
                preparation_action,
                thesis_action,
            )
        else:
            _persist_state(
                preparation["id"],
                LIFECYCLE_PARTIAL,
                False,
                READINESS_PARTIAL,
                warnings,
                errors,
                discovery_status,
                candidate_documents,
                discovery_warnings,
                acquisition_status,
                acquired_documents,
                acquisition_warnings,
                extraction_status,
                extracted_observation_count,
                extraction_timestamp,
                extraction_results,
                extraction_warnings,
                extraction_reused,
                extractor_version,
                thesis_id,
                preparation_action,
                thesis_action,
            )
    except Exception as exc:
        errors.append(f"Preparation failed: {type(exc).__name__}: {str(exc)}")
        _persist_state(
            preparation["id"],
            LIFECYCLE_FAILED,
            False,
            READINESS_FAILED,
            warnings,
            errors,
            DISCOVERY_STATUS_FAILED,
            [],
            [],
            ACQUISITION_STATUS_FAILED,
            [],
            [],
            EXTRACTION_STATUS_FAILED,
            0,
            None,
            [],
            [],
            False,
            extractor_version,
            preparation.get("thesis_id"),
            preparation_action,
            "failed",
        )

    return _load_preparation_object(preparation["id"])


def _normalize_ticker(ticker):
    if ticker is None:
        return ""
    return str(ticker).strip().upper()


def _normalize_observation_date(observation_date):
    if isinstance(observation_date, datetime):
        return observation_date.date().isoformat()
    if isinstance(observation_date, date):
        return observation_date.isoformat()
    if observation_date is None:
        return ""

    raw_value = str(observation_date).strip()
    if not raw_value:
        return ""
    return datetime.fromisoformat(raw_value).date().isoformat()


def _get_or_create_preparation(ticker, observation_date):
    existing_df = fetch_dataframe(
        """
        SELECT *
        FROM evaluation_preparations
        WHERE ticker = ? AND observation_date = ?
        LIMIT 1
        """,
        (ticker, observation_date),
    )
    if not existing_df.empty:
        return existing_df.iloc[0].to_dict(), "reused"

    created_at = datetime.now().isoformat()
    preparation_id = insert_query(
        """
        INSERT INTO evaluation_preparations
        (
            ticker,
            observation_date,
            thesis_id,
            lifecycle_state,
            workspace_ready,
            readiness_status,
            evidence_discovery_status,
            candidate_count,
            discovery_warnings_json,
            evidence_acquisition_status,
            acquired_document_count,
            acquisition_warnings_json,
            extraction_status,
            extracted_observation_count,
            extraction_timestamp,
            extraction_warnings_json,
            extraction_reused,
            extractor_version,
            warnings_json,
            errors_json,
            status_json,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            ticker,
            observation_date,
            None,
            LIFECYCLE_REQUESTED,
            0,
            READINESS_PENDING,
            DISCOVERY_STATUS_PENDING,
            0,
            json.dumps([]),
            ACQUISITION_STATUS_PENDING,
            0,
            json.dumps([]),
            EXTRACTION_STATUS_PENDING,
            0,
            None,
            json.dumps([]),
            0,
            DEFAULT_EXTRACTOR_VERSION,
            json.dumps([]),
            json.dumps([]),
            json.dumps({}),
            created_at,
            created_at,
        ),
    )
    return _fetch_preparation_row(preparation_id), "created"


def _resolve_or_create_thesis(preparation, ticker, observation_date, company_name, reviewer, warnings):
    existing_thesis_id = _coerce_int(preparation.get("thesis_id"))
    if existing_thesis_id is not None:
        if _thesis_exists(existing_thesis_id):
            return existing_thesis_id, "reused"
        warnings.append("Linked thesis was missing and was recreated.")

    display_name = str(company_name).strip() if company_name is not None and str(company_name).strip() else ticker
    decision_question = f"Can Athena prepare this evaluation for analyst review as of {observation_date}?"
    thesis_id = create_thesis(
        company_name=display_name,
        ticker=ticker,
        decision_question=decision_question,
        account_type=None,
        portfolio_role=None,
        primary_horizon=None,
        regime_state=None,
        reviewer=reviewer,
        status="Draft",
        drl=0,
        validation_mode_enabled=False,
        evidence_cutoff_date=None,
    )
    return thesis_id, "created"


def _verify_workspace_ready(thesis_id, errors):
    try:
        get_overview_metrics(thesis_id)
        return True
    except Exception as exc:
        errors.append(f"Workspace verification failed: {type(exc).__name__}: {str(exc)}")
        return False


def _resolve_candidate_discovery(preparation_id, thesis_id, ticker, observation_date, providers):
    preparation_row = _fetch_preparation_row(preparation_id)
    persisted_status = str(preparation_row.get("evidence_discovery_status", DISCOVERY_STATUS_PENDING)).strip()
    if persisted_status in [DISCOVERY_STATUS_UNAVAILABLE, DISCOVERY_STATUS_FAILED]:
        existing_warnings = _load_persisted_discovery_warnings(preparation_id)
        return persisted_status, [], existing_warnings

    existing_candidates = _load_persisted_candidates(preparation_id)
    if existing_candidates:
        existing_warnings = _load_persisted_discovery_warnings(preparation_id)
        return DISCOVERY_STATUS_DISCOVERED, existing_candidates, existing_warnings

    discovery_result = discover_candidate_documents(
        ticker=ticker,
        observation_date=observation_date,
        providers=providers,
    )
    discovery_status = str(discovery_result.get("evidence_discovery_status", DISCOVERY_STATUS_UNAVAILABLE)).strip()
    candidate_documents = discovery_result.get("candidate_documents", []) or []
    discovery_warnings = discovery_result.get("discovery_warnings", []) or []

    _persist_candidate_documents(preparation_id=preparation_id, thesis_id=thesis_id, candidate_documents=candidate_documents)

    return discovery_status, candidate_documents, discovery_warnings


def _resolve_source_acquisition(preparation_id, thesis_id, discovery_status, candidate_documents, providers):
    preparation_row = _fetch_preparation_row(preparation_id)
    persisted_status = str(preparation_row.get("evidence_acquisition_status", ACQUISITION_STATUS_PENDING)).strip()

    existing_documents = _load_persisted_acquired_documents(preparation_id)
    if existing_documents:
        existing_warnings = _load_persisted_acquisition_warnings(preparation_id)
        return persisted_status if persisted_status else ACQUISITION_STATUS_ACQUIRED, existing_documents, existing_warnings

    if discovery_status != DISCOVERY_STATUS_DISCOVERED or not candidate_documents:
        return ACQUISITION_STATUS_NOT_ATTEMPTED, [], []

    acquisition_result = acquire_supported_candidates(
        candidate_documents=candidate_documents,
        providers=providers,
    )
    acquisition_status = str(acquisition_result.get("acquisition_status", ACQUISITION_STATUS_UNAVAILABLE)).strip()
    acquired_documents = acquisition_result.get("acquired_documents", []) or []
    acquisition_warnings = acquisition_result.get("acquisition_warnings", []) or []

    _persist_acquired_documents(
        preparation_id=preparation_id,
        thesis_id=thesis_id,
        acquired_documents=acquired_documents,
    )

    persisted_documents = _load_persisted_acquired_documents(preparation_id)
    return acquisition_status, persisted_documents, acquisition_warnings


def _resolve_automatic_extraction(preparation_id, thesis_id, acquired_documents, extractor_version, refresh):
    extraction_result = coordinate_extraction(
        preparation_id=preparation_id,
        thesis_id=thesis_id,
        acquired_documents=acquired_documents,
        extractor_version=extractor_version,
        refresh=bool(refresh),
    )
    return (
        str(extraction_result.get("extraction_status", EXTRACTION_STATUS_NOT_ATTEMPTED)).strip(),
        int(extraction_result.get("extracted_observation_count") or 0),
        extraction_result.get("extraction_timestamp"),
        extraction_result.get("extraction_results", []) or [],
        extraction_result.get("extraction_warnings", []) or [],
        bool(extraction_result.get("extraction_reused", False)),
    )


def _persist_state(
    preparation_id,
    lifecycle_state,
    workspace_ready,
    readiness_status,
    warnings,
    errors,
    evidence_discovery_status,
    candidate_documents,
    discovery_warnings,
    evidence_acquisition_status,
    acquired_documents,
    acquisition_warnings,
    extraction_status,
    extracted_observation_count,
    extraction_timestamp,
    extraction_results,
    extraction_warnings,
    extraction_reused,
    extractor_version,
    thesis_id,
    preparation_action,
    thesis_action,
):
    preparation = _fetch_preparation_row(preparation_id)
    created_at = preparation["created_at"]
    updated_at = datetime.now().isoformat()
    status_object = {
        "ticker": preparation["ticker"],
        "observation_date": preparation["observation_date"],
        "lifecycle_state": lifecycle_state,
        "thesis_id": thesis_id,
        "preparation_id": preparation_id,
        "workspace_ready": bool(workspace_ready),
        "readiness_status": readiness_status,
        "evidence_discovery_status": evidence_discovery_status,
        "candidate_count": len(candidate_documents),
        "candidate_documents": list(candidate_documents),
        "discovery_warnings": list(discovery_warnings),
        "acquisition_status": evidence_acquisition_status,
        "acquired_document_count": len(
            [item for item in acquired_documents if str(item.get("acquisition_status", "")).strip() == ACQUISITION_STATUS_ACQUIRED]
        ),
        "acquired_documents": list(acquired_documents),
        "acquisition_warnings": list(acquisition_warnings),
        "extraction_status": extraction_status,
        "extracted_observation_count": int(extracted_observation_count),
        "extraction_timestamp": extraction_timestamp,
        "extraction_results": list(extraction_results),
        "extraction_warnings": list(extraction_warnings),
        "extraction_reused": bool(extraction_reused),
        "extractor_version": str(extractor_version).strip() if extractor_version else DEFAULT_EXTRACTOR_VERSION,
        "preparation_action": preparation_action,
        "thesis_action": thesis_action,
        "warnings": list(warnings),
        "errors": list(errors),
        "step_status": {
            "preparation_record": preparation_action,
            "thesis": thesis_action if thesis_id is not None else "pending",
            "workspace": "complete" if workspace_ready else ("failed" if errors else "pending"),
            "evidence_discovery": evidence_discovery_status,
            "evidence_acquisition": evidence_acquisition_status,
            "extraction": extraction_status,
        },
        "updated_at": updated_at,
        "created_at": created_at,
    }

    run_query(
        """
        UPDATE evaluation_preparations
        SET thesis_id = ?,
            lifecycle_state = ?,
            workspace_ready = ?,
            readiness_status = ?,
            evidence_discovery_status = ?,
            candidate_count = ?,
            discovery_warnings_json = ?,
            evidence_acquisition_status = ?,
            acquired_document_count = ?,
            acquisition_warnings_json = ?,
            extraction_status = ?,
            extracted_observation_count = ?,
            extraction_timestamp = ?,
            extraction_warnings_json = ?,
            extraction_reused = ?,
            extractor_version = ?,
            warnings_json = ?,
            errors_json = ?,
            status_json = ?,
            updated_at = ?
        WHERE id = ?
        """,
        (
            thesis_id,
            lifecycle_state,
            1 if workspace_ready else 0,
            readiness_status,
            evidence_discovery_status,
            len(candidate_documents),
            json.dumps(list(discovery_warnings)),
            evidence_acquisition_status,
            len([item for item in acquired_documents if str(item.get("acquisition_status", "")).strip() == ACQUISITION_STATUS_ACQUIRED]),
            json.dumps(list(acquisition_warnings)),
            extraction_status,
            int(extracted_observation_count),
            extraction_timestamp,
            json.dumps(list(extraction_warnings)),
            1 if extraction_reused else 0,
            str(extractor_version).strip() if extractor_version else DEFAULT_EXTRACTOR_VERSION,
            json.dumps(list(warnings)),
            json.dumps(list(errors)),
            json.dumps(status_object),
            updated_at,
            preparation_id,
        ),
    )


def _load_preparation_object(preparation_id):
    preparation = _fetch_preparation_row(preparation_id)
    stored_status = preparation.get("status_json")
    if stored_status:
        parsed_status = json.loads(stored_status)
        if isinstance(parsed_status, dict) and parsed_status:
            return parsed_status

    return {
        "ticker": preparation["ticker"],
        "observation_date": preparation["observation_date"],
        "lifecycle_state": preparation["lifecycle_state"],
        "thesis_id": _coerce_int(preparation.get("thesis_id")),
        "preparation_id": preparation["id"],
        "workspace_ready": bool(preparation["workspace_ready"]),
        "readiness_status": preparation["readiness_status"],
        "evidence_discovery_status": str(preparation.get("evidence_discovery_status", DISCOVERY_STATUS_PENDING)).strip(),
        "candidate_count": int(preparation.get("candidate_count") or 0),
        "candidate_documents": _load_persisted_candidates(preparation["id"]),
        "discovery_warnings": _load_json_list(preparation.get("discovery_warnings_json")),
        "acquisition_status": str(preparation.get("evidence_acquisition_status", ACQUISITION_STATUS_PENDING)).strip(),
        "acquired_document_count": int(preparation.get("acquired_document_count") or 0),
        "acquired_documents": _load_persisted_acquired_documents(preparation["id"]),
        "acquisition_warnings": _load_json_list(preparation.get("acquisition_warnings_json")),
        "extraction_status": str(preparation.get("extraction_status", EXTRACTION_STATUS_PENDING)).strip(),
        "extracted_observation_count": int(preparation.get("extracted_observation_count") or 0),
        "extraction_timestamp": str(preparation.get("extraction_timestamp", "")).strip() if preparation.get("extraction_timestamp") is not None else None,
        "extraction_results": _load_persisted_extraction_results(preparation["id"]),
        "extraction_warnings": _load_json_list(preparation.get("extraction_warnings_json")),
        "extraction_reused": bool(int(preparation.get("extraction_reused") or 0)),
        "extractor_version": str(preparation.get("extractor_version", DEFAULT_EXTRACTOR_VERSION)).strip() if preparation.get("extractor_version") is not None else DEFAULT_EXTRACTOR_VERSION,
        "preparation_action": "unknown",
        "thesis_action": "unknown",
        "warnings": _load_json_list(preparation.get("warnings_json")),
        "errors": _load_json_list(preparation.get("errors_json")),
        "step_status": {
            "preparation_record": "complete",
            "thesis": "complete" if _coerce_int(preparation.get("thesis_id")) is not None else "pending",
            "workspace": "complete" if bool(preparation["workspace_ready"]) else "pending",
            "evidence_discovery": str(preparation.get("evidence_discovery_status", DISCOVERY_STATUS_PENDING)).strip(),
            "evidence_acquisition": str(preparation.get("evidence_acquisition_status", ACQUISITION_STATUS_PENDING)).strip(),
            "extraction": str(preparation.get("extraction_status", EXTRACTION_STATUS_PENDING)).strip(),
        },
        "updated_at": preparation["updated_at"],
        "created_at": preparation["created_at"],
    }


def _persist_candidate_documents(preparation_id, thesis_id, candidate_documents):
    if not candidate_documents:
        return

    run_query(
        "DELETE FROM evaluation_candidate_documents WHERE preparation_id = ?",
        (int(preparation_id),),
    )

    now_value = datetime.now().isoformat()
    for candidate in candidate_documents:
        insert_query(
            """
            INSERT OR IGNORE INTO evaluation_candidate_documents
            (
                preparation_id,
                thesis_id,
                title,
                source,
                document_type,
                publication_date,
                reference_url,
                reference_id,
                discovery_status,
                provider_name,
                warnings_json,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                int(preparation_id),
                int(thesis_id) if thesis_id is not None else None,
                str(candidate.get("title", "")).strip() or None,
                str(candidate.get("source", "")).strip() or None,
                str(candidate.get("document_type", "")).strip() or None,
                str(candidate.get("publication_date", "")).strip() or None,
                str(candidate.get("reference_url", "")).strip() or None,
                str(candidate.get("reference_id", "")).strip() or None,
                str(candidate.get("discovery_status", "candidate")).strip() or "candidate",
                str(candidate.get("provider_name", "Unknown Provider")).strip(),
                json.dumps(candidate.get("warnings", [])),
                now_value,
            ),
        )


def _load_persisted_candidates(preparation_id):
    candidate_df = fetch_dataframe(
        """
        SELECT
            title,
            source,
            document_type,
            publication_date,
            reference_url,
            reference_id,
            discovery_status,
            provider_name,
            warnings_json
        FROM evaluation_candidate_documents
        WHERE preparation_id = ?
        ORDER BY id ASC
        """,
        (int(preparation_id),),
    )
    if candidate_df.empty:
        return []

    records = []
    for _, row in candidate_df.iterrows():
        records.append(
            {
                "title": str(row["title"]).strip() if row["title"] is not None else "",
                "source": str(row["source"]).strip() if row["source"] is not None else "",
                "document_type": str(row["document_type"]).strip() if row["document_type"] is not None else "",
                "publication_date": str(row["publication_date"]).strip() if row["publication_date"] is not None else "",
                "reference_url": str(row["reference_url"]).strip() if row["reference_url"] is not None else "",
                "reference_id": str(row["reference_id"]).strip() if row["reference_id"] is not None else "",
                "discovery_status": str(row["discovery_status"]).strip() if row["discovery_status"] is not None else "candidate",
                "provider_name": str(row["provider_name"]).strip() if row["provider_name"] is not None else "Unknown Provider",
                "warnings": _load_json_list(row["warnings_json"]),
                "candidate_evidence": True,
            }
        )
    return records


def _load_persisted_discovery_warnings(preparation_id):
    prep_df = fetch_dataframe(
        "SELECT discovery_warnings_json FROM evaluation_preparations WHERE id = ? LIMIT 1",
        (int(preparation_id),),
    )
    if prep_df.empty:
        return []
    return _load_json_list(prep_df.iloc[0]["discovery_warnings_json"])


def _persist_acquired_documents(preparation_id, thesis_id, acquired_documents):
    if not acquired_documents:
        return

    run_query(
        "DELETE FROM evaluation_acquired_documents WHERE preparation_id = ?",
        (int(preparation_id),),
    )

    now_value = datetime.now().isoformat()
    for document in acquired_documents:
        insert_query(
            """
            INSERT OR IGNORE INTO evaluation_acquired_documents
            (
                preparation_id,
                thesis_id,
                title,
                source,
                document_type,
                publication_date,
                reference_url,
                reference_id,
                provider_name,
                discovery_provider,
                discovery_source,
                original_candidate_identifier,
                acquisition_status,
                retrieval_timestamp,
                source_reference,
                content_type,
                source_content,
                source_content_hash,
                acquisition_error,
                warnings_json,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                int(preparation_id),
                int(thesis_id) if thesis_id is not None else None,
                str(document.get("title", "")).strip() or None,
                str(document.get("source", "")).strip() or None,
                str(document.get("document_type", "")).strip() or None,
                str(document.get("publication_date", "")).strip() or None,
                str(document.get("reference_url", "")).strip() or None,
                str(document.get("reference_id", "")).strip() or None,
                str(document.get("provider_name", "Unknown Acquisition Provider")).strip(),
                str(document.get("discovery_provider", "Unknown Discovery Provider")).strip(),
                str(document.get("discovery_source", "")).strip() or None,
                str(document.get("original_candidate_identifier", "")).strip() or None,
                str(document.get("acquisition_status", ACQUISITION_STATUS_UNAVAILABLE)).strip() or ACQUISITION_STATUS_UNAVAILABLE,
                str(document.get("retrieval_timestamp", "")).strip() or None,
                str(document.get("source_reference", "")).strip() or None,
                str(document.get("content_type", "")).strip() or None,
                str(document.get("source_content", "")).strip() or None,
                str(document.get("source_content_hash", "")).strip() or None,
                str(document.get("acquisition_error", "")).strip() or None,
                json.dumps(document.get("warnings", [])),
                now_value,
            ),
        )


def _load_persisted_acquired_documents(preparation_id):
    acquired_df = fetch_dataframe(
        """
        SELECT
            id,
            title,
            source,
            document_type,
            publication_date,
            reference_url,
            reference_id,
            provider_name,
            discovery_provider,
            discovery_source,
            original_candidate_identifier,
            acquisition_status,
            retrieval_timestamp,
            source_reference,
            content_type,
            source_content,
            source_content_hash,
            acquisition_error,
            warnings_json
        FROM evaluation_acquired_documents
        WHERE preparation_id = ?
        ORDER BY id ASC
        """,
        (int(preparation_id),),
    )
    if acquired_df.empty:
        return []

    records = []
    for _, row in acquired_df.iterrows():
        records.append(
            {
                "id": _coerce_int(row["id"]),
                "title": str(row["title"]).strip() if row["title"] is not None else "",
                "source": str(row["source"]).strip() if row["source"] is not None else "",
                "document_type": str(row["document_type"]).strip() if row["document_type"] is not None else "",
                "publication_date": str(row["publication_date"]).strip() if row["publication_date"] is not None else "",
                "reference_url": str(row["reference_url"]).strip() if row["reference_url"] is not None else "",
                "reference_id": str(row["reference_id"]).strip() if row["reference_id"] is not None else "",
                "provider_name": str(row["provider_name"]).strip() if row["provider_name"] is not None else "Unknown Acquisition Provider",
                "discovery_provider": str(row["discovery_provider"]).strip() if row["discovery_provider"] is not None else "Unknown Discovery Provider",
                "discovery_source": str(row["discovery_source"]).strip() if row["discovery_source"] is not None else "",
                "original_candidate_identifier": str(row["original_candidate_identifier"]).strip() if row["original_candidate_identifier"] is not None else "",
                "acquisition_status": str(row["acquisition_status"]).strip() if row["acquisition_status"] is not None else ACQUISITION_STATUS_UNAVAILABLE,
                "retrieval_timestamp": str(row["retrieval_timestamp"]).strip() if row["retrieval_timestamp"] is not None else "",
                "source_reference": str(row["source_reference"]).strip() if row["source_reference"] is not None else "",
                "content_type": str(row["content_type"]).strip() if row["content_type"] is not None else "",
                "source_content": str(row["source_content"]).strip() if row["source_content"] is not None else "",
                "source_content_hash": str(row["source_content_hash"]).strip() if row["source_content_hash"] is not None else "",
                "acquisition_error": str(row["acquisition_error"]).strip() if row["acquisition_error"] is not None else "",
                "warnings": _load_json_list(row["warnings_json"]),
                "acquired_source_material": True,
            }
        )
    return records


def _load_persisted_acquisition_warnings(preparation_id):
    prep_df = fetch_dataframe(
        "SELECT acquisition_warnings_json FROM evaluation_preparations WHERE id = ? LIMIT 1",
        (int(preparation_id),),
    )
    if prep_df.empty:
        return []
    return _load_json_list(prep_df.iloc[0]["acquisition_warnings_json"])


def _load_persisted_extraction_results(preparation_id):
    extraction_df = fetch_dataframe(
        """
        SELECT
            id,
            acquired_document_id,
            extraction_status,
            extraction_timestamp,
            extractor_version,
            reused,
            observation_count,
            warning_message,
            error_message
        FROM evaluation_extraction_runs
        WHERE preparation_id = ?
        ORDER BY id ASC
        """,
        (int(preparation_id),),
    )
    if extraction_df.empty:
        return []

    records = []
    for _, row in extraction_df.iterrows():
        records.append(
            {
                "run_id": _coerce_int(row["id"]),
                "acquired_document_id": _coerce_int(row["acquired_document_id"]),
                "extraction_status": str(row["extraction_status"]).strip() if row["extraction_status"] is not None else EXTRACTION_STATUS_NOT_ATTEMPTED,
                "extraction_timestamp": str(row["extraction_timestamp"]).strip() if row["extraction_timestamp"] is not None else None,
                "extractor_version": str(row["extractor_version"]).strip() if row["extractor_version"] is not None else DEFAULT_EXTRACTOR_VERSION,
                "reused": bool(int(row["reused"])) if row["reused"] is not None else False,
                "observation_count": int(row["observation_count"] or 0),
                "warning": str(row["warning_message"]).strip() if row["warning_message"] is not None else "",
                "error": str(row["error_message"]).strip() if row["error_message"] is not None else "",
            }
        )
    return records


def _fetch_preparation_row(preparation_id):
    preparation_df = fetch_dataframe(
        "SELECT * FROM evaluation_preparations WHERE id = ? LIMIT 1",
        (preparation_id,),
    )
    if preparation_df.empty:
        raise ValueError(f"Preparation record {preparation_id} not found.")
    return preparation_df.iloc[0].to_dict()


def _thesis_exists(thesis_id):
    thesis_df = fetch_dataframe(
        "SELECT id FROM theses WHERE id = ? LIMIT 1",
        (int(thesis_id),),
    )
    return not thesis_df.empty


def _load_json_list(raw_value):
    if raw_value is None:
        return []
    try:
        parsed = json.loads(raw_value)
    except (TypeError, ValueError, json.JSONDecodeError):
        return []
    return parsed if isinstance(parsed, list) else []


def _coerce_int(value):
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _build_ephemeral_failure(ticker, observation_date):
    normalized_ticker = ticker if ticker else ""
    normalized_observation_date = observation_date if observation_date else ""
    return {
        "ticker": normalized_ticker,
        "observation_date": normalized_observation_date,
        "lifecycle_state": LIFECYCLE_FAILED,
        "thesis_id": None,
        "preparation_id": None,
        "workspace_ready": False,
        "readiness_status": READINESS_FAILED,
        "evidence_discovery_status": DISCOVERY_STATUS_FAILED,
        "candidate_count": 0,
        "candidate_documents": [],
        "discovery_warnings": [],
        "acquisition_status": ACQUISITION_STATUS_FAILED,
        "acquired_document_count": 0,
        "acquired_documents": [],
        "acquisition_warnings": [],
        "extraction_status": EXTRACTION_STATUS_FAILED,
        "extracted_observation_count": 0,
        "extraction_timestamp": None,
        "extraction_results": [],
        "extraction_warnings": [],
        "extraction_reused": False,
        "extractor_version": DEFAULT_EXTRACTOR_VERSION,
        "preparation_action": "failed",
        "thesis_action": "failed",
        "warnings": [],
        "errors": ["ticker and observation_date are required."],
        "step_status": {
            "preparation_record": "failed",
            "thesis": "pending",
            "workspace": "pending",
            "evidence_discovery": DISCOVERY_STATUS_FAILED,
            "evidence_acquisition": ACQUISITION_STATUS_FAILED,
            "extraction": EXTRACTION_STATUS_FAILED,
        },
        "updated_at": None,
        "created_at": None,
    }