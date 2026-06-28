from datetime import datetime


def normalize_promotion_candidates(extracted_rows, staged_rows, ignored_candidate_ids=None):
    """Build candidate rows with explicit non-governed state for analyst action."""
    ignored = set(str(item).strip() for item in (ignored_candidate_ids or []))
    staged_index = {}
    for row in staged_rows or []:
        marker = str(row.get("duplicate_notes", "")).strip()
        if marker.startswith("athena_candidate_id="):
            staged_index[marker.split("=", 1)[1]] = row

    candidates = []
    for row in extracted_rows or []:
        candidate_id = str(row.get("id", "")).strip()
        if not candidate_id:
            continue

        stage_row = staged_index.get(candidate_id)
        stage_status = "ignored" if candidate_id in ignored else "pending"
        if stage_row is not None:
            stage_status = str(stage_row.get("intake_status", "pending")).strip().lower() or "pending"

        candidates.append(
            {
                "candidate_id": candidate_id,
                "originating_document": str(row.get("title", "")).strip(),
                "pillar_signal": str(row.get("pillar_signal", "")).strip(),
                "confidence": str(row.get("confidence", "")).strip(),
                "source_location": str(row.get("source_location", "")).strip(),
                "source_reference": str(row.get("source_reference", "")).strip() or str(row.get("reference_url", "")).strip(),
                "passage": str(row.get("passage", "")).strip(),
                "machine_status": str(row.get("extraction_status", "")).strip() or "unknown",
                "candidate_state": stage_status,
                "staged_uuid": str(stage_row.get("staging_uuid", "")).strip() if stage_row is not None else "",
            }
        )

    return candidates


def build_rationale_draft(pillar_id, pillar_name, synthesis, extracted_candidates):
    """Create an editable Athena-prepared rationale draft from available support."""
    governed = synthesis.get("governed_observations", []) if isinstance(synthesis, dict) else []
    supporting = synthesis.get("supporting_evidence", []) if isinstance(synthesis, dict) else []
    advisory = synthesis.get("advisory_signals", []) if isinstance(synthesis, dict) else []

    lines = [
        f"Athena Draft Rationale ({pillar_id} {pillar_name})",
        "",
        "This is a machine-generated draft for analyst editing and approval.",
        "No governed judgment is recorded until you explicitly save.",
        "",
    ]

    if governed:
        lines.append("Governed observations currently linked:")
        for row in governed[:3]:
            text = str(row.get("observation_text", "")).strip()
            if text:
                lines.append(f"- {text}")
        lines.append("")

    if supporting:
        lines.append("Supporting promoted evidence:")
        for row in supporting[:3]:
            title = str(row.get("title", "")).strip() or str(row.get("source_name", "")).strip() or "Untitled source"
            lines.append(f"- {title}")
        lines.append("")

    if advisory:
        lines.append("Advisory extraction signals:")
        for row in advisory[:2]:
            passage = str(row.get("passage", "")).strip()
            if passage:
                lines.append(f"- {passage[:220]}")
        lines.append("")

    if extracted_candidates:
        lines.append("Recent extracted candidate passages:")
        for row in extracted_candidates[:2]:
            passage = str(row.get("passage", "")).strip()
            if passage:
                lines.append(f"- {passage[:220]}")
        lines.append("")

    lines.append("Analyst note: confirm support, edit language, and validate falsification logic before saving.")

    warnings = []
    if not supporting:
        warnings.append("No promoted evidence is currently linked to this pillar.")
    if not governed:
        warnings.append("No governed observations are currently linked to this pillar.")

    return {
        "draft_text": "\n".join(lines).strip(),
        "warnings": warnings,
        "generated_at": datetime.now().isoformat(),
    }


def build_decision_prep_summary(gate_result, completed_business, completed_investment):
    """Build deterministic decision-preparation guidance without selecting outcomes."""
    missing = gate_result.get("missing", []) if isinstance(gate_result, dict) else []
    eligible = bool(gate_result.get("eligible")) if isinstance(gate_result, dict) else False

    if eligible:
        next_action = "Open Decision Recording and confirm recommendation fields."
    elif missing:
        next_action = f"Complete missing governance fields ({len(missing)} blockers) before decision recording."
    else:
        next_action = "Continue assessments; decision readiness is pending."

    return {
        "decision_ready": eligible,
        "missing_count": len(missing),
        "completed_business": int(completed_business),
        "completed_investment": int(completed_investment),
        "next_action": next_action,
    }


def prioritize_active_evaluation_rows(rows, active_thesis_id):
    """Place the active evaluation first while preserving the existing row order."""
    if active_thesis_id is None:
        return list(rows or [])

    ordered_rows = list(rows or [])
    head = []
    tail = []
    for row in ordered_rows:
        thesis_id = row.get("thesis_id") if isinstance(row, dict) else None
        if thesis_id == active_thesis_id:
            head.append(row)
        else:
            tail.append(row)
    return head + tail


def summarize_preparation_failure(preparation_status):
    """Return the most useful failure explanation available from existing status fields."""
    if not isinstance(preparation_status, dict):
        return ""

    for key in ["errors", "extraction_warnings", "acquisition_warnings", "discovery_warnings", "warnings"]:
        values = preparation_status.get(key, [])
        if not isinstance(values, list):
            continue
        for value in values:
            text = str(value).strip()
            if text:
                return text
    return "Preparation stopped before Athena could complete workspace handoff."


def derive_workflow_ownership_state(preparation_status):
    """Map preparation output to the Home ownership states: Preparing, Ready, or Failed."""
    readiness_status = "pending"
    lifecycle_state = "preparing"
    if isinstance(preparation_status, dict):
        readiness_status = str(preparation_status.get("readiness_status", "pending")).strip().lower()
        lifecycle_state = str(preparation_status.get("lifecycle_state", "preparing")).strip().lower()

    if readiness_status == "ready_for_analyst":
        return {"status": "Ready", "reason": ""}

    if readiness_status in {"failed", "partial"}:
        return {
            "status": "Failed",
            "reason": summarize_preparation_failure(preparation_status),
        }

    if lifecycle_state in {"failed"}:
        return {
            "status": "Failed",
            "reason": summarize_preparation_failure(preparation_status),
        }

    return {"status": "Preparing", "reason": ""}


def resolve_active_evaluation_identity(
    current_active_thesis_id,
    available_thesis_ids,
    active_request,
    latest_preparation_by_thesis,
    engine_preparation_status,
):
    """Resolve active ownership, prioritizing the latest accepted prepare request."""
    available_ids = set()
    for thesis_id in available_thesis_ids or []:
        try:
            available_ids.add(int(thesis_id))
        except (TypeError, ValueError):
            continue

    request_ticker = ""
    if isinstance(active_request, dict):
        request_ticker = str(active_request.get("ticker", "")).strip().upper()

    if request_ticker:
        matches = []
        for thesis_id, prep_status in (latest_preparation_by_thesis or {}).items():
            try:
                normalized_id = int(thesis_id)
            except (TypeError, ValueError):
                continue
            if normalized_id not in available_ids:
                continue

            prep_ticker = str((prep_status or {}).get("ticker", "")).strip().upper()
            if prep_ticker != request_ticker:
                continue

            prep_id = 0
            try:
                prep_id = int((prep_status or {}).get("preparation_id") or 0)
            except (TypeError, ValueError):
                prep_id = 0
            matches.append((prep_id, normalized_id))

        if matches:
            matches.sort(reverse=True)
            return {
                "active_thesis_id": matches[0][1],
                "pending_request": False,
            }

        return {
            "active_thesis_id": None,
            "pending_request": True,
        }

    def _prep_id_for(thesis_id):
        if thesis_id is None:
            return -1
        prep_status = (latest_preparation_by_thesis or {}).get(int(thesis_id), {})
        try:
            return int(prep_status.get("preparation_id") or -1)
        except (TypeError, ValueError):
            return -1

    latest_prep_entry = None
    for thesis_id, prep_status in (latest_preparation_by_thesis or {}).items():
        try:
            normalized_id = int(thesis_id)
        except (TypeError, ValueError):
            continue
        if normalized_id not in available_ids:
            continue
        try:
            prep_id = int((prep_status or {}).get("preparation_id") or -1)
        except (TypeError, ValueError):
            prep_id = -1
        if latest_prep_entry is None or prep_id > latest_prep_entry[0]:
            latest_prep_entry = (prep_id, normalized_id)

    if current_active_thesis_id is not None:
        try:
            normalized_current = int(current_active_thesis_id)
        except (TypeError, ValueError):
            normalized_current = None
        if normalized_current is not None and normalized_current in available_ids:
            current_prep_id = _prep_id_for(normalized_current)
            if latest_prep_entry is not None and latest_prep_entry[0] > current_prep_id:
                return {
                    "active_thesis_id": latest_prep_entry[1],
                    "pending_request": False,
                }
            return {
                "active_thesis_id": normalized_current,
                "pending_request": False,
            }

    if latest_prep_entry is not None:
        return {
            "active_thesis_id": latest_prep_entry[1],
            "pending_request": False,
        }

    if isinstance(engine_preparation_status, dict):
        engine_thesis_id = engine_preparation_status.get("thesis_id")
        if engine_thesis_id is not None:
            try:
                normalized_engine = int(engine_thesis_id)
            except (TypeError, ValueError):
                normalized_engine = None
            if normalized_engine is not None and normalized_engine in available_ids:
                return {
                    "active_thesis_id": normalized_engine,
                    "pending_request": False,
                }

    return {
        "active_thesis_id": None,
        "pending_request": False,
    }
