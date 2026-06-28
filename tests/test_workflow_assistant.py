from workflow_assistant import (
    build_decision_prep_summary,
    build_rationale_draft,
    normalize_promotion_candidates,
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
