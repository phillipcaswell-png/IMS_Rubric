import json
import os
import threading
from datetime import datetime

_ENV_ENABLED = "ATHENA_INSTRUMENTATION_ENABLED"
_ENV_MAX_EVENTS = "ATHENA_INSTRUMENTATION_MAX_EVENTS"
_DEFAULT_MAX_EVENTS = 5000

_ALLOWED_STATUSES = {"success", "failure", "observed"}
_ALLOWED_CATEGORIES = {
    "ui_navigation",
    "view_model",
    "service_call",
    "export",
    "audit_occurrence",
    "exception",
}

_lock = threading.Lock()
_events = []
_runtime_enabled_override = None


def _utc_now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


def _max_events() -> int:
    raw_value = os.getenv(_ENV_MAX_EVENTS, str(_DEFAULT_MAX_EVENTS)).strip()
    try:
        parsed = int(raw_value)
    except ValueError:
        return _DEFAULT_MAX_EVENTS
    return max(1, parsed)


def _sanitize(value):
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(k): _sanitize(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_sanitize(item) for item in value]
    return str(value)


def _is_truthy(raw_value: str) -> bool:
    normalized = raw_value.strip().lower()
    return normalized not in {"0", "false", "no", "off", "disabled"}


def is_enabled() -> bool:
    if _runtime_enabled_override is not None:
        return bool(_runtime_enabled_override)
    return _is_truthy(os.getenv(_ENV_ENABLED, "1"))


def set_enabled(enabled: bool) -> None:
    global _runtime_enabled_override
    _runtime_enabled_override = bool(enabled)


def clear_events() -> None:
    with _lock:
        _events.clear()


def get_event_count() -> int:
    with _lock:
        return len(_events)


def get_events_snapshot() -> list:
    with _lock:
        return list(_events)


def record_event(
    category: str,
    operation: str,
    duration_ms=None,
    status: str = "observed",
    metadata: dict = None,
) -> bool:
    if not is_enabled():
        return False

    try:
        event_category = str(category)
        event_status = str(status)
        if event_category not in _ALLOWED_CATEGORIES:
            return False
        if event_status not in _ALLOWED_STATUSES:
            return False

        normalized_duration = None
        if duration_ms is not None:
            try:
                normalized_duration = float(duration_ms)
            except (TypeError, ValueError):
                normalized_duration = None

        payload = {
            "timestamp": _utc_now_iso(),
            "category": event_category,
            "operation": str(operation),
            "duration_ms": normalized_duration,
            "status": event_status,
            "metadata": _sanitize(metadata or {}),
        }

        with _lock:
            _events.append(payload)
            cap = _max_events()
            if len(_events) > cap:
                del _events[0 : len(_events) - cap]
        return True
    except Exception:
        return False


def observe_ui_navigation(current_view: str, previous_view: str = None, thesis_id=None) -> bool:
    return record_event(
        category="ui_navigation",
        operation="view_transition",
        status="observed",
        metadata={
            "current_view": current_view,
            "previous_view": previous_view,
            "thesis_id": thesis_id,
        },
    )


def observe_view_model(
    view_model_name: str,
    phase: str,
    thesis_id=None,
    duration_ms=None,
    status: str = "observed",
) -> bool:
    return record_event(
        category="view_model",
        operation=str(view_model_name),
        duration_ms=duration_ms,
        status=status,
        metadata={
            "phase": phase,
            "thesis_id": thesis_id,
        },
    )


def observe_service_call(
    service_name: str,
    phase: str,
    status: str = "observed",
    duration_ms=None,
    context: dict = None,
) -> bool:
    return record_event(
        category="service_call",
        operation=str(service_name),
        duration_ms=duration_ms,
        status=status,
        metadata={
            "phase": phase,
            "context": context or {},
        },
    )


def observe_export(export_type: str, trigger: str, thesis_id=None, record_count=None) -> bool:
    return record_event(
        category="export",
        operation=str(export_type),
        status="observed",
        metadata={
            "trigger": trigger,
            "thesis_id": thesis_id,
            "record_count": record_count,
        },
    )


def observe_audit_occurrence(event_type: str, thesis_id=None, created_by: str = None, version: str = None) -> bool:
    return record_event(
        category="audit_occurrence",
        operation=str(event_type),
        status="observed",
        metadata={
            "thesis_id": thesis_id,
            "created_by": created_by,
            "version": version,
        },
    )


def observe_exception(operation: str, exception: Exception, metadata: dict = None) -> bool:
    observed_metadata = dict(metadata or {})
    observed_metadata["exception_type"] = type(exception).__name__
    return record_event(
        category="exception",
        operation=str(operation),
        status="observed",
        metadata=observed_metadata,
    )


def export_events_json(indent: int = 2) -> str:
    try:
        payload = {
            "instrumentation_enabled": is_enabled(),
            "generated_at": _utc_now_iso(),
            "event_count": get_event_count(),
            "events": get_events_snapshot(),
        }
        return json.dumps(payload, indent=indent)
    except Exception:
        # Export must remain non-fatal to governed workflows.
        return json.dumps(
            {
                "instrumentation_enabled": False,
                "generated_at": _utc_now_iso(),
                "event_count": 0,
                "events": [],
            },
            indent=indent,
        )
