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
