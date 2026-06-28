import json
from datetime import date, datetime

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

ENGINE_REVIEWER = "Operational Evaluation Engine"


def prepare_evaluation(ticker, observation_date, company_name=None, reviewer=ENGINE_REVIEWER):
    """Prepare or resume an evaluation shell for analyst review."""
    normalized_ticker = _normalize_ticker(ticker)
    normalized_observation_date = _normalize_observation_date(observation_date)

    if not normalized_ticker or not normalized_observation_date:
        return _build_ephemeral_failure(normalized_ticker, normalized_observation_date)

    init_db()
    preparation, preparation_action = _get_or_create_preparation(normalized_ticker, normalized_observation_date)
    warnings = []
    errors = []

    try:
        _persist_state(
            preparation["id"],
            LIFECYCLE_PREPARING,
            False,
            READINESS_PENDING,
            warnings,
            errors,
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
            thesis_id,
            preparation_action,
            thesis_action,
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
            warnings_json,
            errors_json,
            status_json,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            ticker,
            observation_date,
            None,
            LIFECYCLE_REQUESTED,
            0,
            READINESS_PENDING,
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


def _persist_state(
    preparation_id,
    lifecycle_state,
    workspace_ready,
    readiness_status,
    warnings,
    errors,
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
        "preparation_action": preparation_action,
        "thesis_action": thesis_action,
        "warnings": list(warnings),
        "errors": list(errors),
        "step_status": {
            "preparation_record": preparation_action,
            "thesis": thesis_action if thesis_id is not None else "pending",
            "workspace": "complete" if workspace_ready else ("failed" if errors else "pending"),
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
        "preparation_action": "unknown",
        "thesis_action": "unknown",
        "warnings": _load_json_list(preparation.get("warnings_json")),
        "errors": _load_json_list(preparation.get("errors_json")),
        "step_status": {
            "preparation_record": "complete",
            "thesis": "complete" if _coerce_int(preparation.get("thesis_id")) is not None else "pending",
            "workspace": "complete" if bool(preparation["workspace_ready"]) else "pending",
        },
        "updated_at": preparation["updated_at"],
        "created_at": preparation["created_at"],
    }


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
    parsed = json.loads(raw_value)
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
        "preparation_action": "failed",
        "thesis_action": "failed",
        "warnings": [],
        "errors": ["ticker and observation_date are required."],
        "step_status": {
            "preparation_record": "failed",
            "thesis": "pending",
            "workspace": "pending",
        },
        "updated_at": None,
        "created_at": None,
    }