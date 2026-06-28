from workflow_assistant import (
    build_decision_prep_summary,
    build_rationale_draft,
    derive_workflow_ownership_state,
    normalize_promotion_candidates,
    prioritize_active_evaluation_rows,
    resolve_active_evaluation_identity,
    summarize_preparation_failure,
)


def test_normalize_promotion_candidates_resolves_stage_status_and_ignore():
    extracted_rows = [
        {
            "id": 101,
            "title": "Q1 Letter",
            "pillar_signal": "B2",
            "confidence": "0.88",
            "source_location": "p.4",
            "reference_url": "https://example.com/q1",
            "passage": "Durable switching costs observed.",
            "extraction_status": "completed",
        },
        {
            "id": 102,
            "title": "10-K",
            "pillar_signal": "B4",
            "confidence": "0.74",
            "source_location": "sec-3",
            "source_reference": "10-k-2025",
            "passage": "Cash conversion remains high.",
            "extraction_status": "completed",
        },
    ]
    staged_rows = [
        {
            "staging_uuid": "uuid-1",
            "duplicate_notes": "athena_candidate_id=101",
            "intake_status": "Reviewed",
        }
    ]

    result = normalize_promotion_candidates(
        extracted_rows=extracted_rows,
        staged_rows=staged_rows,
        ignored_candidate_ids={"102"},
    )

    assert len(result) == 2
    assert result[0]["candidate_state"] == "reviewed"
    assert result[0]["staged_uuid"] == "uuid-1"
    assert result[1]["candidate_state"] == "ignored"


def test_build_rationale_draft_includes_guardrail_language():
    synthesis = {
        "governed_observations": [{"observation_text": "Retention held above 95%."}],
        "supporting_evidence": [{"title": "Investor Deck"}],
        "advisory_signals": [{"passage": "Margin expansion likely from mix shift."}],
    }

    result = build_rationale_draft("B1", "Business Quality", synthesis, [])

    assert "machine-generated draft" in result["draft_text"]
    assert "No governed judgment is recorded until you explicitly save." in result["draft_text"]
    assert result["warnings"] == []


def test_build_decision_prep_summary_reflects_gate_blockers():
    gate = {
        "eligible": False,
        "missing": [{"pillar_id": "I2", "field": "judgment", "label": "Judgment"}],
    }

    result = build_decision_prep_summary(gate, completed_business=7, completed_investment=3)

    assert result["decision_ready"] is False
    assert result["missing_count"] == 1
    assert "blockers" in result["next_action"].lower()


def test_prioritize_active_evaluation_rows_moves_active_to_front():
    rows = [
        {"thesis_id": 3, "Company": "Meta"},
        {"thesis_id": 8, "Company": "NVIDIA"},
        {"thesis_id": 11, "Company": "Microsoft"},
    ]

    ordered = prioritize_active_evaluation_rows(rows, active_thesis_id=11)

    assert [row["thesis_id"] for row in ordered] == [11, 3, 8]


def test_summarize_preparation_failure_uses_first_available_signal():
    status = {
        "warnings": ["generic warning"],
        "discovery_warnings": ["discovery warning"],
        "acquisition_warnings": ["acquisition warning"],
        "extraction_warnings": ["extraction warning"],
        "errors": ["hard failure"],
    }

    reason = summarize_preparation_failure(status)

    assert reason == "hard failure"


def test_derive_workflow_ownership_state_covers_preparing_ready_failed():
    assert derive_workflow_ownership_state({"readiness_status": "pending"})["status"] == "Preparing"
    assert derive_workflow_ownership_state({"readiness_status": "ready_for_analyst"})["status"] == "Ready"

    failed = derive_workflow_ownership_state(
        {"readiness_status": "failed", "errors": ["SEC blocked"]}
    )
    assert failed["status"] == "Failed"
    assert "SEC blocked" in failed["reason"]


def test_active_identity_prioritizes_new_request_before_old_engine_status():
    resolved = resolve_active_evaluation_identity(
        current_active_thesis_id=9,
        available_thesis_ids=[9, 11],
        active_request={"ticker": "INTC"},
        latest_preparation_by_thesis={
            11: {"preparation_id": 4, "ticker": "INTC"},
            9: {"preparation_id": 2, "ticker": "MSFT"},
        },
        engine_preparation_status={"thesis_id": 9},
    )

    assert resolved["active_thesis_id"] == 11
    assert resolved["pending_request"] is False


def test_active_identity_marks_pending_when_request_accepted_but_not_persisted():
    resolved = resolve_active_evaluation_identity(
        current_active_thesis_id=9,
        available_thesis_ids=[9],
        active_request={"ticker": "INTC"},
        latest_preparation_by_thesis={
            9: {"preparation_id": 2, "ticker": "MSFT"},
        },
        engine_preparation_status={"thesis_id": 9},
    )

    assert resolved["active_thesis_id"] is None
    assert resolved["pending_request"] is True


def test_active_identity_prefers_newest_persisted_preparation_when_newer_than_current():
    resolved = resolve_active_evaluation_identity(
        current_active_thesis_id=11,
        available_thesis_ids=[11, 12],
        active_request=None,
        latest_preparation_by_thesis={
            11: {"preparation_id": 4, "ticker": "INTC"},
            12: {"preparation_id": 5, "ticker": "QCOM"},
        },
        engine_preparation_status={"thesis_id": 11},
    )

    assert resolved["active_thesis_id"] == 12
    assert resolved["pending_request"] is False
