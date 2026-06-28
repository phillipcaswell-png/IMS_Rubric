import json
from datetime import date, datetime

from evidence_discovery import discover_candidate_documents
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

ENGINE_REVIEWER = "Operational Evaluation Engine"


def prepare_evaluation(ticker, observation_date, company_name=None, reviewer=ENGINE_REVIEWER, discovery_providers=None):
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
            warnings_json,
            errors_json,
            status_json,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
        "preparation_action": preparation_action,
        "thesis_action": thesis_action,
        "warnings": list(warnings),
        "errors": list(errors),
        "step_status": {
            "preparation_record": preparation_action,
            "thesis": thesis_action if thesis_id is not None else "pending",
            "workspace": "complete" if workspace_ready else ("failed" if errors else "pending"),
            "evidence_discovery": evidence_discovery_status,
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
        "preparation_action": "unknown",
        "thesis_action": "unknown",
        "warnings": _load_json_list(preparation.get("warnings_json")),
        "errors": _load_json_list(preparation.get("errors_json")),
        "step_status": {
            "preparation_record": "complete",
            "thesis": "complete" if _coerce_int(preparation.get("thesis_id")) is not None else "pending",
            "workspace": "complete" if bool(preparation["workspace_ready"]) else "pending",
            "evidence_discovery": str(preparation.get("evidence_discovery_status", DISCOVERY_STATUS_PENDING)).strip(),
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
        "preparation_action": "failed",
        "thesis_action": "failed",
        "warnings": [],
        "errors": ["ticker and observation_date are required."],
        "step_status": {
            "preparation_record": "failed",
            "thesis": "pending",
            "workspace": "pending",
            "evidence_discovery": DISCOVERY_STATUS_FAILED,
        },
        "updated_at": None,
        "created_at": None,
    }