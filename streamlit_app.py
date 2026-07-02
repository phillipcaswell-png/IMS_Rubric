import streamlit as st
import pandas as pd
import json
import time
import importlib
from datetime import datetime
from evaluation_engine import prepare_evaluation
import workflow_assistant as workflow_assistant_module

workflow_assistant_module = importlib.reload(workflow_assistant_module)
normalize_promotion_candidates = workflow_assistant_module.normalize_promotion_candidates
build_rationale_draft = workflow_assistant_module.build_rationale_draft
build_decision_prep_summary = workflow_assistant_module.build_decision_prep_summary
derive_workflow_ownership_state = workflow_assistant_module.derive_workflow_ownership_state
prioritize_active_evaluation_rows = workflow_assistant_module.prioritize_active_evaluation_rows
resolve_active_evaluation_identity = workflow_assistant_module.resolve_active_evaluation_identity
from services import (
    DATABASE_FILE,
    init_db,
    run_query,
    fetch_dataframe,
    insert_query,
    is_validation_configuration_locked,
    log_event,
    get_overview_metrics,
    get_business_evidence_coverage,
    get_candidate_evidence_for_thesis,
    get_acquired_source_material_for_thesis,
    get_extraction_runs_for_thesis,
    get_extracted_observations_for_thesis,
    get_available_evidence_items,
    get_observations_for_evidence,
    get_observations_for_pillar,
    get_linked_evidence_ids,
    sync_pillar_evidence_links,
    promote_staged_evidence,
    archive_staged_evidence,
    create_evidence_observation,
    update_evidence_observation,
    get_extraction_suggestions,
    build_thesis_json,
    validate_decision_gate,
    compute_hermes_inbox,
    get_athena_prebrief,
    get_athena_evidence_synthesis,
    OBSERVATION_CATEGORY_OPTIONS,
    OBSERVATION_STATUS_OPTIONS,
    OBSERVATION_STATUS_ACTIVE,
    INTAKE_STATUS_ARCHIVED,
    stage_evidence,
    update_evidence_item,
    update_staged_evidence_source_text,
    update_staged_evidence_status,
    save_pillar_score,
    record_decision,
    save_thesis_review,
    ensure_uswr_limited_evidence_case,
    log_friction_observation,
    FRICTION_TYPE_OPTIONS,
    FRICTION_STATUS_OPTIONS,
    HERMES_REDUCTION_OPTIONS,
)

try:
    from instrumentation import (
        export_events_json,
        get_event_count,
        observe_exception,
        observe_export,
        observe_ui_navigation,
        observe_view_model,
    )
except Exception:
    def export_events_json(indent=2):
        return "{}"

    def get_event_count():
        return 0

    def observe_export(*args, **kwargs):
        return False

    def observe_exception(*args, **kwargs):
        return False

    def observe_ui_navigation(*args, **kwargs):
        return False

    def observe_view_model(*args, **kwargs):
        return False

# =============================================================================
# IMS CONTROLLED VOCABULARY
# =============================================================================

# Event Types
EVENT_EVALUATION_CREATED = "Evaluation Created"
EVENT_EVIDENCE_ADDED = "Evidence Added"
EVENT_EVIDENCE_UPDATED = "Evidence Updated"
EVENT_EVIDENCE_DELETED = "Evidence Deleted"
EVENT_BUSINESS_ASSESSMENT_COMPLETED = "Business Assessment Completed"
EVENT_BUSINESS_ASSESSMENT_UPDATED = "Business Assessment Updated"
EVENT_EVIDENCE_LINKED = "Evidence Linked to Pillar"
EVENT_EVIDENCE_UNLINKED = "Evidence Unlinked from Pillar"
EVENT_INVESTMENT_ASSESSMENT_COMPLETED = "Investment Assessment Completed"
EVENT_INVESTMENT_ASSESSMENT_UPDATED = "Investment Assessment Updated"
EVENT_DECISION_RECORDED = "Decision Recorded"
EVENT_RECOMMENDATION_CHANGED = "Recommendation Changed"
EVENT_THESIS_REVIEW_CREATED = "Thesis Review Created"
EVENT_THESIS_REVIEW_UPDATED = "Thesis Review Updated"
EVENT_REVIEW_SCHEDULED = "Review Scheduled"
EVENT_JSON_EXPORTED = "JSON Exported"
EVENT_EVIDENCE_STAGED = "Evidence Staged"
EVENT_EVIDENCE_REVIEWED = "Evidence Reviewed"
EVENT_EVIDENCE_PROMOTED = "Evidence Promoted"
EVENT_EVIDENCE_REJECTED = "Evidence Rejected"
EVENT_EVIDENCE_PROMOTION_BLOCKED = "Evidence Promotion Blocked"

INTAKE_STATUS_PENDING = "Pending"
INTAKE_STATUS_REVIEWED = "Reviewed"
INTAKE_STATUS_CONFIRMED = "Confirmed"
INTAKE_STATUS_PROMOTED = "Promoted"
INTAKE_STATUS_REJECTED = "Rejected"

INTAKE_STATUS_OPTIONS = [
    INTAKE_STATUS_PENDING,
    INTAKE_STATUS_REVIEWED,
    INTAKE_STATUS_CONFIRMED,
    INTAKE_STATUS_PROMOTED,
    INTAKE_STATUS_REJECTED,
    INTAKE_STATUS_ARCHIVED,
]

TERMINAL_INTAKE_STATUSES = [
    INTAKE_STATUS_PROMOTED,
    INTAKE_STATUS_REJECTED,
    INTAKE_STATUS_ARCHIVED,
]

OUTCOME_TYPE_A = "Type A — Thesis Error"
OUTCOME_TYPE_B = "Type B — Execution Error"
OUTCOME_TYPE_C1 = "Type C1 — Temporary Exogenous Shock"
OUTCOME_TYPE_C2 = "Type C2 — Structural Regime Change"
OUTCOME_TYPE_D = "Type D — Random Variation"

OUTCOME_TYPE_OPTIONS = [
    OUTCOME_TYPE_A,
    OUTCOME_TYPE_B,
    OUTCOME_TYPE_C1,
    OUTCOME_TYPE_C2,
    OUTCOME_TYPE_D,
]

REVIEW_HORIZON_OPTIONS = [
    "1 Year",
    "3 Years",
    "5 Years",
    "10 Years",
    "20 Years",
]

MNEMOSYNE_MINIMUM_REVIEW_VOLUME = 10

HERMES_PRIORITY_CRITICAL = 1
HERMES_PRIORITY_HIGH = 2
HERMES_PRIORITY_MEDIUM = 3
HERMES_PRIORITY_LOW = 4

# Status Values
STATUS_DRAFT = "Draft"
STATUS_EVIDENCE_COLLECTION = "Evidence Collection"
STATUS_SCORING = "Scoring"
STATUS_DECISION_REVIEW = "Decision Review"
STATUS_ACTIVE_MONITORING = "Active Monitoring"
STATUS_CLOSED = "Closed"

# Evidence Grades
GRADE_A = "A"
GRADE_B = "B"
GRADE_C = "C"
GRADE_D = "D"

# Evidence Source Types
SOURCE_TYPE_SEC_FILING = "SEC Filing"
SOURCE_TYPE_EARNINGS_CALL = "Earnings Call"
SOURCE_TYPE_PRESS_RELEASE = "Press Release"
SOURCE_TYPE_NEWS_ARTICLE = "News Article"
SOURCE_TYPE_ANALYST_REPORT = "Analyst Report"
SOURCE_TYPE_SOCIAL_MEDIA = "Social Media"
SOURCE_TYPE_MANUAL_OBSERVATION = "Manual Observation"
SOURCE_TYPE_OTHER = "Other"
SOURCE_TYPE_OPTIONS = [
    SOURCE_TYPE_SEC_FILING,
    SOURCE_TYPE_EARNINGS_CALL,
    SOURCE_TYPE_PRESS_RELEASE,
    SOURCE_TYPE_NEWS_ARTICLE,
    SOURCE_TYPE_ANALYST_REPORT,
    SOURCE_TYPE_SOCIAL_MEDIA,
    SOURCE_TYPE_MANUAL_OBSERVATION,
    SOURCE_TYPE_OTHER,
]

# RAG States
RAG_GREEN = "Green"
RAG_YELLOW = "Yellow"
RAG_RED = "Red"
RAG_ORANGE = "Orange"

ATHENA_SIDEBAR_VERSION_TEXT = "Athena v1.8.3"
ATHENA_SIDEBAR_FOOTER_TEXT = "Constitutional • Auditable • Reproducible"
ATHENA_GOVERNED_FOOTER_TEXT = (
    "Governed by Athena Charter v1.0 • Evidence-bounded • Reproducible • Auditable"
)
GOVERNED_SAVE_CONFIRMATION_KEY = "_governed_save_confirmation"

# Page configuration
st.set_page_config(
    page_title="Athena",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
/* ============================================================
   ATHENA DESIGN SYSTEM — PHASE A
   Typography and Color System
   Version 1.0 — June 2026
   ============================================================ */

/* Main background */
.stApp {
    background-color: #0A0A0F;
}

/* Main content area */
.main .block-container {
    background-color: #0A0A0F;
    padding: 1.25rem 2rem 1.5rem;
    max-width: 1200px;
    overflow-x: hidden;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: #12121A;
    border-right: 1px solid #1E1E2E;
}

[data-testid="stSidebar"] * {
    color: #E8E6E0;
}

/* Headings */
h1, h2, h3 {
    font-family: "Cormorant Garamond", "Playfair Display", Georgia, serif;
    color: #E8E6E0;
    font-weight: 300;
    letter-spacing: 0.03em;
}

/* Body text */
p, li, label, div {
    font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    color: #E8E6E0;
}

/* Metric values */
[data-testid="stMetricValue"] {
    font-family: "JetBrains Mono", Consolas, monospace;
    color: #C5A028;
    font-size: 1.8rem;
}

/* Form inputs */
.stTextInput input,
.stTextArea textarea,
.stSelectbox select,
.stNumberInput input {
    background-color: #12121A;
    border: 1px solid #1E1E2E;
    color: #E8E6E0;
    border-radius: 4px;
    font-family: Inter, sans-serif;
}

/* Input focus */
.stTextInput input:focus,
.stTextArea textarea:focus {
    border-color: #C5A028;
    outline: none;
    box-shadow: 0 0 0 2px rgba(197, 160, 40, 0.2);
}

/* Primary buttons */
.stButton > button {
    background-color: #C5A028;
    color: #0A0A0F;
    border: none;
    border-radius: 4px;
    font-family: Inter, sans-serif;
    font-weight: 600;
    letter-spacing: 0.05em;
    padding: 0.5rem 1.5rem;
    transition: background-color 0.15s ease;
}

.stButton > button:hover {
    background-color: #D4AF37;
    color: #0A0A0F;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background-color: #12121A;
    border-bottom: 1px solid #1E1E2E;
    gap: 0;
}

.stTabs [data-baseweb="tab"] {
    background-color: transparent;
    color: #8B8B9A;
    border-bottom: 2px solid transparent;
    font-family: Inter, sans-serif;
    font-size: 0.9rem;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    padding: 0.75rem 1.25rem;
}

.stTabs [aria-selected="true"] {
    color: #C5A028;
    border-bottom-color: #C5A028;
    background-color: transparent;
}

/* Dataframes */
[data-testid="stDataFrame"] {
    background-color: #12121A;
    border: 1px solid #1E1E2E;
    border-radius: 4px;
}

/* Alerts */
.stAlert {
    border-radius: 4px;
    border-left: 3px solid #C5A028;
    background-color: #12121A;
}

/* Dividers */
hr {
    border-color: #1E1E2E;
    margin: 2rem 0;
}

/* Captions */
.stCaption, small {
    color: #8B8B9A;
    font-family: "JetBrains Mono", Consolas, monospace;
    font-size: 0.8rem;
}

/* Sidebar buttons */
[data-testid="stSidebar"] .stButton > button {
    background-color: transparent;
    color: #E8E6E0;
    border: 1px solid #1E1E2E;
    width: 100%;
    text-align: left;
    padding: 0.5rem 1rem;
}

[data-testid="stSidebar"] .stButton > button:hover {
    background-color: #1E1E2E;
    color: #C5A028;
    border-color: #C5A028;
}

/* Expanders */
.streamlit-expanderHeader {
    background-color: #12121A;
    color: #E8E6E0;
    border: 1px solid #1E1E2E;
    border-radius: 4px;
    font-family: Inter, sans-serif;
}

/* Checkboxes and radio */
.stCheckbox label, .stRadio label {
    color: #E8E6E0;
    font-family: Inter, sans-serif;
}

/* Progress bars */
.stProgress > div > div {
    background-color: #C5A028;
}

/* Scrollbar */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #0A0A0F; }
::-webkit-scrollbar-thumb {
    background: #1E1E2E;
    border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover { background: #C5A028; }

/* Select boxes dropdown */
[data-baseweb="select"] {
    background-color: #12121A;
}

[data-baseweb="select"] > div {
    background-color: #12121A;
    border-color: #1E1E2E;
    color: #E8E6E0;
}

/* Dropdown menu items */
[data-baseweb="menu"] {
    background-color: #12121A;
    border: 1px solid #1E1E2E;
}

[role="option"] {
    background-color: #12121A;
    color: #E8E6E0;
}

[role="option"]:hover {
    background-color: #1E1E2E;
    color: #C5A028;
}

.athena-page-shell {
    margin-bottom: 0.9rem;
}

.athena-page-eyebrow {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    margin-bottom: 0.5rem;
}

.athena-page-title {
    font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    font-size: 2rem;
    line-height: 1.1;
    font-weight: 700;
    color: #E8E6E0;
    margin-bottom: 0.25rem;
}

.athena-page-subtitle {
    font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    font-size: 0.98rem;
    color: #A8ACB8;
    margin-bottom: 0.1rem;
}

.athena-section-title {
    font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    font-size: 1.05rem;
    font-weight: 700;
    color: #E8E6E0;
    margin: 0.35rem 0 0.2rem 0;
}

.athena-section-subtitle {
    font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    font-size: 0.84rem;
    color: #8D95A8;
    margin-bottom: 0.75rem;
}

.athena-status-chip {
    display: inline-flex;
    align-items: center;
    border-radius: 999px;
    border: 1px solid #2A3348;
    background: rgba(16, 24, 39, 0.7);
    color: #D8DCE6;
    font-size: 0.74rem;
    font-weight: 600;
    line-height: 1;
    padding: 0.28rem 0.7rem;
    margin-right: 0.35rem;
    margin-bottom: 0.35rem;
}

.athena-status-chip.gold {
    border-color: rgba(197, 160, 40, 0.5);
    background: rgba(197, 160, 40, 0.12);
    color: #F2D06B;
}

.athena-status-chip.success {
    border-color: rgba(74, 181, 108, 0.45);
    background: rgba(74, 181, 108, 0.12);
    color: #95E0A9;
}

.athena-status-chip.warning {
    border-color: rgba(240, 193, 74, 0.45);
    background: rgba(240, 193, 74, 0.12);
    color: #F7DB8A;
}

.athena-status-chip.danger {
    border-color: rgba(255, 82, 82, 0.45);
    background: rgba(255, 82, 82, 0.12);
    color: #FF9898;
}

.athena-footer {
    color: #8D95A8;
    text-align: center;
    font-size: 0.78rem;
    margin-top: 1rem;
    padding-top: 0.45rem;
    border-top: 1px solid #1E1E2E;
}

</style>
""", unsafe_allow_html=True)

# =============================================================================
# IMS UI COMPONENT LIBRARY
# =============================================================================

def section_header(title):
    """Draw a consistent section title and divider."""
    st.subheader(title)


def metric_card(label, value):
    """Display a metric with consistent formatting."""
    st.metric(label, value)


def empty_state(message):
    """Display a standardized empty state message."""
    st.info(message)


def render_status_chip(label, tone="neutral"):
    """Render a compact status chip for page shells and summaries."""
    tone_class = {
        "neutral": "",
        "gold": "gold",
        "success": "success",
        "warning": "warning",
        "danger": "danger",
    }.get(tone, "")
    class_name = "athena-status-chip"
    if tone_class:
        class_name = f"{class_name} {tone_class}"
    st.markdown(f"<span class='{class_name}'>{label}</span>", unsafe_allow_html=True)


def render_governance_badge():
    """Render the governance badge used in compact page shells."""
    st.markdown(
        "<span class='athena-status-chip gold'>Evidence-bounded • Reproducible • Auditable</span>",
        unsafe_allow_html=True,
    )


def render_page_header(title, subtitle=None, eyebrow=None):
    """Render a compact routed-page header."""
    st.markdown("<div class='athena-page-shell'>", unsafe_allow_html=True)
    if eyebrow:
        st.markdown(f"<div class='athena-page-eyebrow'><span class='athena-status-chip gold'>{eyebrow}</span></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='athena-page-title'>{title}</div>", unsafe_allow_html=True)
    if subtitle:
        st.markdown(f"<div class='athena-page-subtitle'>{subtitle}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


def render_section_title(title, subtitle=None):
    """Render a compact section title for task-centric pages."""
    st.markdown(f"<div class='athena-section-title'>{title}</div>", unsafe_allow_html=True)
    if subtitle:
        st.markdown(f"<div class='athena-section-subtitle'>{subtitle}</div>", unsafe_allow_html=True)


def render_summary_row(title, subtitle, tiles):
    """Render a compact summary row above task tables."""
    with st.container(border=True):
        render_section_title(title, subtitle)
        if not tiles:
            return
        columns = st.columns(len(tiles))
        for col, tile in zip(columns, tiles):
            with col:
                metric_card(tile["label"], tile["value"])


def render_athena_footer():
    """Render the small governed footer used on routed pages."""
    st.markdown(f"<div class='athena-footer'>{ATHENA_GOVERNED_FOOTER_TEXT}</div>", unsafe_allow_html=True)


def render_workspace_header(analyst_name=None, primary_text="Continue where you left off."):
    """Render Workspace header copy in approved order."""
    eyebrow = f"Analyst: {analyst_name}" if analyst_name else None
    render_page_header("Active Evaluation", primary_text, eyebrow=eyebrow)


def queue_governed_save_confirmation(surface_label, detail_label=None):
    """Queue a post-rerun confirmation so save success remains visible."""
    st.session_state[GOVERNED_SAVE_CONFIRMATION_KEY] = {
        "surface_label": str(surface_label).strip(),
        "detail_label": str(detail_label).strip() if detail_label else "",
    }


def render_governed_save_confirmation():
    """Render one-time governed save confirmation after rerender."""
    payload = st.session_state.pop(GOVERNED_SAVE_CONFIRMATION_KEY, None)
    if not isinstance(payload, dict):
        return

    surface_label = str(payload.get("surface_label", "governed record")).strip() or "governed record"
    detail_label = str(payload.get("detail_label", "")).strip()
    message = f"Governed write succeeded and has been persisted for {surface_label}. You may safely continue."
    if detail_label:
        message = f"{message} ({detail_label})"
    st.success(message)


def render_kpi_tile(label, value):
    """Render a single KPI tile using existing metric behavior."""
    metric_card(label, value)


def render_metric_row(tiles, section_title=None, add_divider=False):
    """Render KPI tiles in a single horizontal row."""
    if not tiles:
        return

    if add_divider:
        st.divider()
    if section_title:
        section_header(section_title)

    columns = st.columns(len(tiles))
    for col, tile in zip(columns, tiles):
        with col:
            render_kpi_tile(tile["label"], tile["value"])


def open_thesis_workspace(thesis_id):
    """Navigate to the thesis workspace for a given thesis id."""
    st.session_state["selected_thesis_id"] = thesis_id
    st.session_state["current_view"] = "Workspace"
    st.rerun()


def render_preparation_status(status_obj):
    """Render the latest engine preparation status using the canonical object."""
    if not status_obj or not isinstance(status_obj, dict):
        return

    readiness_status = str(status_obj.get("readiness_status", "pending")).strip()
    lifecycle_state = str(status_obj.get("lifecycle_state", "preparing")).strip()
    preparation_action = str(status_obj.get("preparation_action", "unknown")).strip()
    thesis_action = str(status_obj.get("thesis_action", "unknown")).strip()
    evidence_discovery_status = str(status_obj.get("evidence_discovery_status", "pending")).strip()
    candidate_count = int(status_obj.get("candidate_count", 0) or 0)
    discovery_warnings = status_obj.get("discovery_warnings", []) or []
    acquisition_status = str(status_obj.get("acquisition_status", "pending")).strip()
    acquired_document_count = int(status_obj.get("acquired_document_count", 0) or 0)
    acquisition_warnings = status_obj.get("acquisition_warnings", []) or []
    extraction_status = str(status_obj.get("extraction_status", "pending")).strip()
    extracted_observation_count = int(status_obj.get("extracted_observation_count", 0) or 0)
    extraction_warnings = status_obj.get("extraction_warnings", []) or []
    extraction_reused = bool(status_obj.get("extraction_reused", False))
    extractor_version = str(status_obj.get("extractor_version", "")).strip()
    workspace_ready = bool(status_obj.get("workspace_ready"))
    warnings = status_obj.get("warnings", []) or []
    errors = status_obj.get("errors", []) or []

    if readiness_status == "failed":
        status_renderer = st.error
    elif readiness_status == "partial":
        status_renderer = st.warning
    else:
        status_renderer = st.success

    lines = ["Preparing Evaluation..."]
    if preparation_action == "reused":
        lines.append("✓ Existing Preparation Found")
    elif preparation_action == "created":
        lines.append("✓ New Preparation Created")

    if thesis_action == "reused":
        lines.append("✓ Existing Evaluation Found")
    elif thesis_action == "created":
        lines.append("✓ New Evaluation Created")

    if workspace_ready:
        lines.append("✓ Workspace Ready")
    elif lifecycle_state == "partial":
        lines.append("⚠ Workspace Partially Prepared")
    elif readiness_status == "failed":
        lines.append("✕ Workspace Preparation Failed")
    else:
        lines.append("… Workspace Preparation Pending")

    if evidence_discovery_status == "discovered":
        lines.append(f"✓ Candidate Evidence Discovered ({candidate_count})")
    elif evidence_discovery_status == "unavailable":
        lines.append("⚠ Candidate Evidence Discovery Unavailable")
    elif evidence_discovery_status == "failed":
        lines.append("⚠ Candidate Evidence Discovery Failed")
    else:
        lines.append("… Candidate Evidence Discovery Pending")

    if acquisition_status == "acquired":
        lines.append(f"✓ Source Material Acquired ({acquired_document_count})")
    elif acquisition_status == "unavailable":
        lines.append("⚠ Source Material Acquisition Unavailable")
    elif acquisition_status == "failed":
        lines.append("⚠ Source Material Acquisition Failed")
    elif acquisition_status == "not_attempted":
        lines.append("… Source Material Acquisition Not Attempted")
    else:
        lines.append("… Source Material Acquisition Pending")

    if extraction_status == "completed":
        reuse_text = "reused" if extraction_reused else "new"
        lines.append(f"✓ Automatic Extraction Completed ({extracted_observation_count}, {reuse_text})")
    elif extraction_status == "unsupported":
        lines.append("⚠ Automatic Extraction Unsupported")
    elif extraction_status == "failed":
        lines.append("⚠ Automatic Extraction Failed")
    elif extraction_status == "not_attempted":
        lines.append("… Automatic Extraction Not Attempted")
    else:
        lines.append("… Automatic Extraction Pending")
    if extractor_version:
        lines.append(f"Extractor Version: {extractor_version}")

    for discovery_warning in discovery_warnings:
        lines.append(f"⚠ {discovery_warning}")

    for acquisition_warning in acquisition_warnings:
        lines.append(f"⚠ {acquisition_warning}")

    for extraction_warning in extraction_warnings:
        lines.append(f"⚠ {extraction_warning}")

    for warning_text in warnings:
        lines.append(f"⚠ {warning_text}")
    for error_text in errors:
        lines.append(f"✕ {error_text}")

    if readiness_status == "ready_for_analyst":
        lines.append("Ready for Analyst")
    elif readiness_status == "partial":
        lines.append("Partial Preparation")
    elif readiness_status == "failed":
        lines.append("Preparation Failed")

    status_renderer("\n\n".join(lines))


def _load_json_list_field(raw_value):
    if raw_value is None:
        return []
    if isinstance(raw_value, list):
        return raw_value
    text = str(raw_value).strip()
    if not text:
        return []
    try:
        parsed = json.loads(text)
    except (TypeError, ValueError):
        return []
    return parsed if isinstance(parsed, list) else []


def _fetch_latest_preparation_status_by_thesis():
    latest_prep_df = fetch_dataframe(
        """
        SELECT ep.*
        FROM evaluation_preparations ep
        JOIN (
            SELECT thesis_id, MAX(id) AS max_id
            FROM evaluation_preparations
            WHERE thesis_id IS NOT NULL
            GROUP BY thesis_id
        ) latest ON latest.max_id = ep.id
        """
    )

    by_thesis_id = {}
    if latest_prep_df.empty:
        return by_thesis_id

    for _, row in latest_prep_df.iterrows():
        if pd.isna(row.get("thesis_id")):
            continue
        thesis_id = int(row["thesis_id"])
        by_thesis_id[thesis_id] = {
            "thesis_id": thesis_id,
            "preparation_id": int(row["id"]),
            "ticker": str(row.get("ticker", "")).strip(),
            "observation_date": str(row.get("observation_date", "")).strip(),
            "lifecycle_state": str(row.get("lifecycle_state", "preparing")).strip(),
            "workspace_ready": bool(int(row.get("workspace_ready") or 0)),
            "readiness_status": str(row.get("readiness_status", "pending")).strip(),
            "evidence_discovery_status": str(row.get("evidence_discovery_status", "pending")).strip(),
            "candidate_count": int(row.get("candidate_count") or 0),
            "discovery_warnings": _load_json_list_field(row.get("discovery_warnings_json")),
            "acquisition_status": str(row.get("evidence_acquisition_status", "pending")).strip(),
            "acquired_document_count": int(row.get("acquired_document_count") or 0),
            "acquisition_warnings": _load_json_list_field(row.get("acquisition_warnings_json")),
            "extraction_status": str(row.get("extraction_status", "pending")).strip(),
            "extracted_observation_count": int(row.get("extracted_observation_count") or 0),
            "extraction_timestamp": str(row.get("extraction_timestamp", "")).strip(),
            "extraction_warnings": _load_json_list_field(row.get("extraction_warnings_json")),
            "warnings": _load_json_list_field(row.get("warnings_json")),
            "errors": _load_json_list_field(row.get("errors_json")),
        }

    return by_thesis_id


def _resolve_active_evaluation_thesis_id(theses_df, latest_prep_by_thesis_id):
    resolution = resolve_active_evaluation_identity(
        current_active_thesis_id=st.session_state.get("active_evaluation_thesis_id"),
        available_thesis_ids=theses_df["id"].tolist() if "id" in theses_df else [],
        active_request=st.session_state.get("active_evaluation_request"),
        latest_preparation_by_thesis=latest_prep_by_thesis_id,
        engine_preparation_status=st.session_state.get("engine_preparation_status"),
    )

    active_thesis_id = resolution.get("active_thesis_id")
    if active_thesis_id is not None:
        st.session_state["active_evaluation_thesis_id"] = int(active_thesis_id)
        return int(active_thesis_id)

    st.session_state["active_evaluation_thesis_id"] = None
    return None


def render_card_header(title, subtitle=None):
    """Render card title and optional subtitle."""
    st.markdown(
        f"<div style='font-family:Cormorant Garamond, Playfair Display, Georgia, serif; font-size:1.6rem; color:#E8E6E0; margin-bottom:0.2rem;'>{title}</div>",
        unsafe_allow_html=True,
    )
    if subtitle:
        st.markdown(
            f"<div style='font-family:Inter, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif; color:#8B8B9A; margin-bottom:0.6rem;'>{subtitle}</div>",
            unsafe_allow_html=True,
        )


def render_recommendation_block(recommendation_text, has_decision):
    """Render recommendation text with consistent emphasis."""
    recommendation_color = "#C5A028" if has_decision else "#E8E6E0"
    st.markdown(
        f"<div style='font-family:Cormorant Garamond, Playfair Display, Georgia, serif; font-size:1.9rem; color:{recommendation_color}; margin-bottom:0.1rem;'>{recommendation_text}</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div style='font-family:Inter, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif; color:#8B8B9A; margin-bottom:0.5rem;'>Recommendation</div>",
        unsafe_allow_html=True,
    )


def render_score_summary(business_score, investment_score):
    """Render business and investment score summary lines."""
    st.markdown(
        f"<div style='font-family:JetBrains Mono, Consolas, monospace; color:#E8E6E0;'>Business Score: {business_score}</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<div style='font-family:JetBrains Mono, Consolas, monospace; color:#E8E6E0;'>Investment Score: {investment_score}</div>",
        unsafe_allow_html=True,
    )


def render_progress_row(label, value_text, pct=None):
    """Render label/value text with optional progress bar."""
    st.markdown(
        f"<div style='font-family:Inter, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif; color:#8B8B9A; margin-top:0.45rem;'>{label}</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<div style='font-family:JetBrains Mono, Consolas, monospace; color:#E8E6E0;'>{value_text}</div>",
        unsafe_allow_html=True,
    )
    if pct is not None:
        bounded_pct = min(max(float(pct), 0.0), 1.0)
        st.progress(bounded_pct)


def render_progress_summary(progress_rows):
    """Render all progress rows for the hero card."""
    for row in progress_rows:
        render_progress_row(row["label"], row["value_text"], row.get("pct"))


def render_card_footer(action_label=None):
    """Render optional card footer metadata."""
    if action_label:
        st.caption(action_label)


def render_thesis_card(thesis_data):
    """Render hero thesis card using existing dashboard data only."""
    section_header("Hero Thesis")
    if not thesis_data:
        empty_state("No active thesis.")
        return

    recommendation_exists = bool(thesis_data.get("has_decision"))
    recommendation_text = thesis_data.get("recommendation", "NO DECISION")
    progress_rows = [
        {"label": "Evidence", "value_text": "Pending", "pct": None},
        {
            "label": "Assessment Progress",
            "value_text": thesis_data["assessment_progress"],
            "pct": thesis_data.get("assessment_pct"),
        },
        {
            "label": "Decision Progress",
            "value_text": thesis_data["decision_progress"],
            "pct": thesis_data.get("decision_pct"),
        },
    ]

    with st.container(border=True):
        render_card_header(thesis_data["company_name"], thesis_data["descriptor"])
        render_recommendation_block(recommendation_text, recommendation_exists)
        render_score_summary(thesis_data["business_score"], thesis_data["investment_score"])
        render_progress_summary(progress_rows)
        render_card_footer()

    if st.button("Continue ->", key=f"workspace_hero_continue_{thesis_data['thesis_id']}"):
        open_thesis_workspace(thesis_data["thesis_id"])


def render_focus_panel(watchlist_rows):
    """Render Today's Focus using existing watchlist rows only."""
    section_header("Today's Focus")
    if not watchlist_rows:
        st.info("No immediate actions required.")
        return

    priority_styles = {
        1: {"accent": "#C5A028", "label": "NOW"},
        2: {"accent": "#8B8B9A", "label": "NEXT"},
    }

    for idx, row in enumerate(watchlist_rows[:3]):
        row_priority = int(row.get("Priority", 3))
        style = priority_styles.get(row_priority, {"accent": "#5A5A66", "label": "LATER"})
        st.markdown(
            f"<div style='background:#12121A; border:1px solid #1E1E2E; border-left:3px solid {style['accent']}; border-radius:6px; padding:0.85rem; margin-bottom:0.55rem;'>"
            f"<div style='font-family:Cormorant Garamond, Playfair Display, Georgia, serif; font-size:1.3rem; color:#E8E6E0; margin-bottom:0.2rem;'>{row['Company']}</div>"
            f"<div style='font-family:JetBrains Mono, Consolas, monospace; color:#E8E6E0; margin-bottom:0.35rem;'>{style['label']}</div>"
            "<div style='font-family:Inter, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif; color:#8B8B9A;'>Next Action</div>"
            f"<div style='font-family:JetBrains Mono, Consolas, monospace; color:#E8E6E0; margin-bottom:0.35rem;'>{row['Action Required']}</div>"
            "<div style='font-family:Inter, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif; color:#8B8B9A;'>Reason</div>"
            f"<div style='font-family:JetBrains Mono, Consolas, monospace; color:#E8E6E0;'>{row['Reason']}</div>"
            "</div>",
            unsafe_allow_html=True,
        )

        if st.button("Open ->", key=f"workspace_focus_open_{idx}_{row['thesis_id']}"):
            open_thesis_workspace(row["thesis_id"])


def render_portfolio_summary(portfolio_vm):
    """Presentation wrapper for the existing portfolio summary table."""
    st.divider()
    section_header("Portfolio Summary")

    portfolio_display_df = portfolio_vm.get("display_df")
    portfolio_rows = portfolio_vm.get("rows", [])

    if portfolio_display_df is None or portfolio_display_df.empty:
        empty_state("No theses found. Click 'Prepare Evaluation' to create or resume one.")
        return

    st.dataframe(portfolio_display_df, use_container_width=True)
    st.caption("Open Thesis")
    for row in portfolio_rows:
        thesis_id = row["thesis_id"]
        label = f"View {row['Company']}"
        if st.button(label, key=f"dashboard_open_{thesis_id}"):
            open_thesis_workspace(thesis_id)


def render_governance_health(governance_display_df):
    """Render governance health table."""
    st.divider()
    section_header("Governance Health")
    if governance_display_df is not None and not governance_display_df.empty:
        st.dataframe(governance_display_df, use_container_width=True)
    else:
        empty_state("No theses available.")


def render_historical_review_summary(outcome_distribution_df, framework_theses_df):
    """Render historical review section tables."""
    st.divider()
    section_header("Historical Review Summary")
    if outcome_distribution_df is not None and not outcome_distribution_df.empty:
        st.dataframe(outcome_distribution_df, use_container_width=True)
    else:
        empty_state("No thesis reviews recorded yet.")

    if framework_theses_df is not None and not framework_theses_df.empty:
        st.dataframe(framework_theses_df, use_container_width=True)
    else:
        empty_state("No theses currently flagged for framework review consideration.")


def render_watchlist_queue(watchlist_display_df):
    """Render watchlist and review queue table."""
    st.divider()
    section_header("Watchlist / Review Queue")
    if watchlist_display_df is not None and not watchlist_display_df.empty:
        st.dataframe(watchlist_display_df, use_container_width=True)
    else:
        st.info("No items require immediate attention.")
    st.info("Workflow coordination is available in 📬 Hermes — Workflow Inbox.")


def render_mnemosyne_section(mnemosyne_data):
    """Render precomputed Mnemosyne display data."""
    st.divider()
    section_header("Mnemosyne — Historical Observations")
    st.markdown(
        "Historical observations are advisory only.\n"
        "They do not modify decision records, thesis reviews,\n"
        "or the investment framework."
    )

    if mnemosyne_data.get("banner_mode") == "Preliminary Observation":
        st.warning(
            "Preliminary Observation\n\n"
            "Historical review volume is currently below the constitutional minimum of\n"
            "10 reviews.\n\n"
            "Trends shown below are descriptive only and should not be used to modify\n"
            "the investment framework."
        )
    else:
        st.info(
            "Observation Mode\n\n"
            "Historical review volume is sufficient for exploratory pattern analysis.\n\n"
            "Observations remain informational and do not constitute framework\n"
            "recommendations."
        )

    mnemosyne_distribution_df = mnemosyne_data.get("distribution_display_df")
    if mnemosyne_distribution_df is not None and not mnemosyne_distribution_df.empty:
        st.dataframe(mnemosyne_distribution_df, use_container_width=True)
    else:
        empty_state("No thesis reviews available for historical observation yet.")

    metric_tiles = mnemosyne_data.get("metric_tiles", [])
    render_metric_row(metric_tiles)

    st.markdown(
        "Observations derived from:\n\n"
        f"• Thesis Reviews: {mnemosyne_data.get('total_reviews', 0)}\n\n"
        f"• Distinct Theses: {mnemosyne_data.get('distinct_theses', 0)}\n\n"
        "• Generated:\n"
        f"{mnemosyne_data.get('generated_at', '—')}"
    )


def render_workspace(workspace_vm):
    """Presentation-only workspace orchestration in approved order."""
    render_workspace_header(
        workspace_vm["header"].get("analyst_name"),
        workspace_vm["header"].get("primary_text", "Continue where you left off."),
    )
    render_thesis_card(workspace_vm["hero"])
    render_focus_panel(workspace_vm["focus"])
    render_portfolio_summary(workspace_vm["portfolio"])
    render_metric_row(workspace_vm["metrics"], section_title="Executive Metrics", add_divider=True)

    render_governance_health(workspace_vm["governance"].get("display_df"))
    render_historical_review_summary(
        workspace_vm["historical"].get("outcome_distribution_df"),
        workspace_vm["historical"].get("framework_theses_df"),
    )
    render_watchlist_queue(workspace_vm["watchlist"].get("display_df"))
    render_mnemosyne_section(workspace_vm["mnemosyne"])


def timeline_table(dataframe):
    """Display a timeline table with consistent formatting."""
    if not dataframe.empty:
        st.dataframe(dataframe, use_container_width=True)
    else:
        empty_state("No events yet.")


def summary_field(label, value):
    """Display a label/value pair consistently."""
    st.write(f"**{label}:** {value}")


def _display_text(value):
    """Normalize scalar values into clean display text."""
    if value is None:
        return ""
    if isinstance(value, str):
        text = value.strip()
        if text in {"-", "—"}:
            return ""
        return text
    try:
        if pd.isna(value):
            return ""
    except TypeError:
        pass
    text = str(value).strip()
    if text in {"-", "—"}:
        return ""
    return text


def summary_field_if_present(label, value, empty_text=None, hide_if_empty=False):
    """Render summary fields without punctuation placeholders."""
    text = _display_text(value)
    if text:
        summary_field(label, text)
        return
    if hide_if_empty:
        return
    if empty_text is None:
        empty_text = "Not recorded"
    summary_field(label, empty_text)


ASSESSMENT_WORKSPACE_PILLARS = [
    {"id": "B1", "name": "Business Quality", "domain": "Business Understanding"},
    {"id": "B2", "name": "Competitive Advantage", "domain": "Business Understanding"},
    {"id": "B3", "name": "Revenue Quality", "domain": "Business Understanding"},
    {"id": "B4", "name": "Financial Resilience", "domain": "Business Understanding"},
    {"id": "B5", "name": "Execution Capability", "domain": "Business Understanding"},
    {"id": "B6", "name": "Industry Position", "domain": "Business Understanding"},
    {"id": "B7", "name": "Systems Importance", "domain": "Business Understanding"},
    {"id": "I1", "name": "Valuation", "domain": "Financial Assessment"},
    {"id": "I2", "name": "Market Structure", "domain": "Financial Assessment"},
    {"id": "I3", "name": "Market Sentiment", "domain": "Financial Assessment"},
    {"id": "I4", "name": "Portfolio Contribution", "domain": "Financial Assessment"},
]

ASSESSMENT_WORKSPACE_PILLAR_MAP = {
    pillar["id"]: pillar for pillar in ASSESSMENT_WORKSPACE_PILLARS
}

BUSINESS_PILLAR_GUIDANCE = {
    "B1": "A high gross margin score should reflect durability and trend direction, not just the current level — a declining margin at 70% may score lower than a stable margin at 45%.",
    "B2": "Score the structural barrier, not the product — ask how long a well-funded competitor would need to replicate the company's market position, not whether the product is good.",
    "B3": "Prioritize recurring, contracted, or subscription revenue over transactional revenue — evaluate what percentage of next year's revenue is already secured.",
    "B4": "Financial resilience should account for non-linearity: unusually high cash positions relative to revenue may indicate inefficient capital allocation rather than strength.",
    "B5": "Score against stated commitments, not absolute performance — a company that consistently delivers 90% of guidance scores higher than one that occasionally delivers 120% unpredictably.",
    "B6": "A dominant position in a declining industry is not the same as a strong position in a growing one — the score should reflect both current standing and structural trajectory.",
    "B7": "Systems importance should account for dependency quality: reliance on a single government program or contract should not automatically receive a high score.",
}


def _get_judgment_default(existing_record):
    """Prefer governed judgment, then fall back to legacy inference text."""
    if existing_record is None:
        return ""
    if "judgment" in existing_record.index and pd.notna(existing_record["judgment"]):
        value = str(existing_record["judgment"]).strip()
        if value:
            return value
    if "inference" in existing_record.index and pd.notna(existing_record["inference"]):
        value = str(existing_record["inference"]).strip()
        if value:
            return value
    return ""


def _get_workspace_stage(business_rows, investment_rows, gate_ready):
    """Summarize the current governed workflow stage."""
    if business_rows < 7:
        return "Business Assessment"
    if investment_rows < 4:
        return "Financial Assessment"
    if gate_ready:
        return "Decision Recording"
    return "Assessment Completion"


def _build_workspace_clarity_context(thesis_id, thesis_row):
    """Build a concise workspace state summary for analysts."""
    score_df = fetch_dataframe(
        """
        SELECT
            SUM(CASE WHEN pillar_id LIKE 'B%' THEN 1 ELSE 0 END) AS business_rows,
            SUM(CASE WHEN pillar_id LIKE 'I%' THEN 1 ELSE 0 END) AS investment_rows
        FROM pillar_scores
        WHERE thesis_id = ?
        """,
        (thesis_id,),
    )
    score_row = score_df.iloc[0] if not score_df.empty else None
    business_rows = int(score_row["business_rows"]) if score_row is not None and pd.notna(score_row["business_rows"]) else 0
    investment_rows = int(score_row["investment_rows"]) if score_row is not None and pd.notna(score_row["investment_rows"]) else 0

    gate_result = validate_decision_gate(thesis_id)
    workflow_status = _get_workspace_stage(business_rows, investment_rows, gate_result["eligible"])

    decision_df = fetch_dataframe(
        """
        SELECT recommendation, review_date, horizon_map
        FROM decision_logs
        WHERE thesis_id = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (thesis_id,),
    )
    decision_row = decision_df.iloc[0] if not decision_df.empty else None

    recommendation = _display_text(decision_row["recommendation"]) if decision_row is not None else ""
    review_date = _display_text(decision_row["review_date"]) if decision_row is not None else ""
    horizon_map = _display_text(decision_row["horizon_map"]) if decision_row is not None else ""
    ticker_text = _display_text(thesis_row.get("ticker"))
    reviewer_text = _display_text(thesis_row.get("reviewer"))
    horizon_text = _display_text(thesis_row.get("primary_horizon"))

    decision_status = "Decision Recorded" if decision_row is not None else "No Decision Recorded"
    governed_decision = recommendation if recommendation else ("Recorded without recommendation" if decision_row is not None else "No governed decision recorded")

    if decision_row is not None:
        next_action = "Review Historical Outcome"
    elif gate_result["eligible"]:
        next_action = "Record Decision"
    else:
        next_action = "Continue Assessment"

    return {
        "workflow_status": workflow_status,
        "decision_status": decision_status,
        "governed_decision": governed_decision,
        "decision_review_date": review_date,
        "decision_horizon_map": horizon_map,
        "ticker": ticker_text,
        "reviewer": reviewer_text,
        "investment_horizon": horizon_text,
        "next_action": next_action,
        "gate_status": "Decision Eligible" if gate_result["eligible"] else f"Decision Blocked ({len(gate_result['missing'])} requirements remaining)",
    }


def _build_assessment_workspace_context(thesis_id, pillar_id):
    """Assemble promoted evidence and observation context for one pillar."""
    if pillar_id.startswith("B"):
        synthesis = get_athena_evidence_synthesis(thesis_id=thesis_id, pillar_id=pillar_id)
        return {
            "governed_observations": synthesis.get("governed_observations", []),
            "advisory_signals": synthesis.get("advisory_signals", []),
            "supporting_evidence": synthesis.get("supporting_evidence", []),
            "coverage": synthesis.get("coverage", {}),
        }

    observations_df = get_observations_for_pillar(thesis_id=thesis_id, pillar_id=pillar_id)
    governed_observations = observations_df.to_dict("records") if not observations_df.empty else []
    supporting_df = fetch_dataframe(
        """
        SELECT DISTINCT
            ei.id AS evidence_item_id,
            ei.publication_date,
            ei.source_name,
            ei.title,
            ei.source_publisher,
            ei.evidence_grade,
            ei.url_or_citation
        FROM evidence_items ei
        LEFT JOIN pillar_evidence_links pel ON pel.evidence_item_id = ei.id
        LEFT JOIN pillar_scores ps ON ps.id = pel.pillar_score_id
        WHERE ei.thesis_id = ?
          AND (
              ei.related_pillar = ?
              OR (ps.thesis_id = ? AND ps.pillar_id = ?)
          )
        ORDER BY
            CASE WHEN ei.publication_date IS NULL OR TRIM(ei.publication_date) = '' THEN 1 ELSE 0 END ASC,
            ei.publication_date ASC,
            ei.id ASC
        """,
        (thesis_id, pillar_id, thesis_id, pillar_id),
    )
    supporting_evidence = supporting_df.to_dict("records") if not supporting_df.empty else []
    return {
        "governed_observations": governed_observations,
        "advisory_signals": [],
        "supporting_evidence": supporting_evidence,
        "coverage": {
            "governed_observation_count": len(governed_observations),
            "advisory_signal_count": 0,
            "evidence_item_count": len(supporting_evidence),
        },
    }


def render_assessment_workspace(thesis_id, thesis, default_validation_review_date):
    """Preferred continuous assessment workflow reusing governed persistence."""
    section_header("Assessment Workspace")

    pillar_labels = [f"{pillar['id']} {pillar['name']}" for pillar in ASSESSMENT_WORKSPACE_PILLARS]
    selected_label = st.selectbox(
        "Assessment Focus",
        options=pillar_labels,
        key=f"assessment_workspace_focus_{thesis_id}",
    )
    pillar_id, pillar_name = selected_label.split(" ", 1)
    pillar_meta = ASSESSMENT_WORKSPACE_PILLAR_MAP[pillar_id]

    existing_df = fetch_dataframe(
        "SELECT * FROM pillar_scores WHERE thesis_id = ? AND pillar_id = ?",
        (thesis_id, pillar_id),
    )
    existing_record = existing_df.iloc[0] if not existing_df.empty else None
    pillar_score_id = int(existing_record["id"]) if existing_record is not None and pd.notna(existing_record["id"]) else None
    default_review_date, validation_mode_enabled, evidence_cutoff_date = _resolve_validation_review_date(
        thesis,
        existing_record["review_date"] if existing_record is not None else None,
    )
    validation_review_date_blocked = validation_mode_enabled and evidence_cutoff_date is None
    if validation_review_date_blocked:
        st.error("Validation mode requires evidence_cutoff_date before pillar scores can be saved.")

    available_evidence_ids, available_evidence_labels = get_available_evidence_items(thesis_id)
    linked_evidence_defaults = get_linked_evidence_ids(pillar_score_id) if pillar_score_id is not None else []
    context = _build_assessment_workspace_context(thesis_id, pillar_id)
    candidate_df = get_candidate_evidence_for_thesis(thesis_id)
    acquired_df = get_acquired_source_material_for_thesis(thesis_id)
    extraction_runs_df = get_extraction_runs_for_thesis(thesis_id)
    extracted_observations_df = get_extracted_observations_for_thesis(thesis_id)
    preparation_df = fetch_dataframe(
        """
        SELECT
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
            extractor_version
        FROM evaluation_preparations
        WHERE thesis_id = ?
        ORDER BY updated_at DESC, id DESC
        LIMIT 1
        """,
        (thesis_id,),
    )
    evidence_discovery_status = "pending"
    discovery_warnings = []
    evidence_acquisition_status = "pending"
    acquisition_warnings = []
    extraction_status = "pending"
    extracted_observation_count = 0
    extraction_timestamp = None
    extraction_warnings = []
    extraction_reused = False
    extractor_version = ""
    if not preparation_df.empty:
        prep_row = preparation_df.iloc[0]
        if pd.notna(prep_row["evidence_discovery_status"]) and str(prep_row["evidence_discovery_status"]).strip():
            evidence_discovery_status = str(prep_row["evidence_discovery_status"]).strip()
        if pd.notna(prep_row["discovery_warnings_json"]) and str(prep_row["discovery_warnings_json"]).strip():
            try:
                discovery_warnings = json.loads(str(prep_row["discovery_warnings_json"]))
                if not isinstance(discovery_warnings, list):
                    discovery_warnings = []
            except (ValueError, TypeError):
                discovery_warnings = []
        if pd.notna(prep_row["evidence_acquisition_status"]) and str(prep_row["evidence_acquisition_status"]).strip():
            evidence_acquisition_status = str(prep_row["evidence_acquisition_status"]).strip()
        if pd.notna(prep_row["acquisition_warnings_json"]) and str(prep_row["acquisition_warnings_json"]).strip():
            try:
                acquisition_warnings = json.loads(str(prep_row["acquisition_warnings_json"]))
                if not isinstance(acquisition_warnings, list):
                    acquisition_warnings = []
            except (ValueError, TypeError):
                acquisition_warnings = []
        if pd.notna(prep_row["extraction_status"]) and str(prep_row["extraction_status"]).strip():
            extraction_status = str(prep_row["extraction_status"]).strip()
        if pd.notna(prep_row["extracted_observation_count"]):
            extracted_observation_count = int(prep_row["extracted_observation_count"] or 0)
        if pd.notna(prep_row["extraction_timestamp"]) and str(prep_row["extraction_timestamp"]).strip():
            extraction_timestamp = str(prep_row["extraction_timestamp"]).strip()
        if pd.notna(prep_row["extraction_warnings_json"]) and str(prep_row["extraction_warnings_json"]).strip():
            try:
                extraction_warnings = json.loads(str(prep_row["extraction_warnings_json"]))
                if not isinstance(extraction_warnings, list):
                    extraction_warnings = []
            except (ValueError, TypeError):
                extraction_warnings = []
        extraction_reused = bool(int(prep_row["extraction_reused"])) if pd.notna(prep_row["extraction_reused"]) else False
        if pd.notna(prep_row["extractor_version"]) and str(prep_row["extractor_version"]).strip():
            extractor_version = str(prep_row["extractor_version"]).strip()
    gate_result = validate_decision_gate(thesis_id)

    progress_df = fetch_dataframe(
        """
        SELECT
            SUM(CASE WHEN pillar_id LIKE 'B%' THEN 1 ELSE 0 END) AS business_rows,
            SUM(CASE WHEN pillar_id LIKE 'I%' THEN 1 ELSE 0 END) AS investment_rows
        FROM pillar_scores
        WHERE thesis_id = ?
        """,
        (thesis_id,),
    )
    progress_row = progress_df.iloc[0] if not progress_df.empty else None
    business_rows = int(progress_row["business_rows"]) if progress_row is not None and pd.notna(progress_row["business_rows"]) else 0
    investment_rows = int(progress_row["investment_rows"]) if progress_row is not None and pd.notna(progress_row["investment_rows"]) else 0

    left_col, right_col = st.columns([3, 1])

    with right_col:
        st.subheader("Progress")
        st.metric("Completed Pillars", f"{gate_result['completed']} / {gate_result['required']}")
        st.metric("Remaining Pillars", gate_result["required"] - gate_result["completed"])
        st.metric("Decision Readiness", "Ready" if gate_result["eligible"] else "Blocked")
        st.caption(f"Current Workflow Stage: {_get_workspace_stage(business_rows, investment_rows, gate_result['eligible'])}")
        if gate_result["missing"]:
            with st.expander("Remaining Requirements"):
                for item in gate_result["missing"]:
                    st.write(f"- {item['pillar_id']} — {item['label']}")

        st.markdown("**Guided Workflow (Athena Prepared -> Analyst Confirmed)**")
        staged_df = fetch_dataframe(
            """
            SELECT staging_uuid, intake_status, source_name, duplicate_notes, promoted_evidence_id
            FROM evidence_staging
            WHERE thesis_id = ?
            ORDER BY created_at DESC, id DESC
            """,
            (thesis_id,),
        )
        staged_rows = staged_df.to_dict("records") if not staged_df.empty else []
        extracted_rows = extracted_observations_df.to_dict("records") if not extracted_observations_df.empty else []
        ignored_key = f"assessment_workspace_ignored_candidates_{thesis_id}"
        ignored_candidates = st.session_state.setdefault(ignored_key, [])
        candidate_rows = normalize_promotion_candidates(
            extracted_rows=extracted_rows,
            staged_rows=staged_rows,
            ignored_candidate_ids=ignored_candidates,
        )

        prep_summary = build_decision_prep_summary(
            gate_result=gate_result,
            completed_business=business_rows,
            completed_investment=investment_rows,
        )
        st.caption(prep_summary["next_action"])
        st.caption("All actions below are analyst-triggered. Athena suggestions do not write governed records by themselves.")

        if candidate_rows:
            with st.expander("Athena Candidate Passages", expanded=False):
                candidate_df = pd.DataFrame(candidate_rows)
                st.dataframe(
                    candidate_df[
                        [
                            "candidate_id",
                            "candidate_state",
                            "originating_document",
                            "pillar_signal",
                            "confidence",
                            "source_location",
                            "machine_status",
                        ]
                    ],
                    use_container_width=True,
                )

                candidate_options = [row["candidate_id"] for row in candidate_rows]
                selected_candidate_id = st.selectbox(
                    "Candidate Passage",
                    options=candidate_options,
                    key=f"assessment_workspace_candidate_select_{thesis_id}",
                )
                selected_candidate = next(
                    (row for row in candidate_rows if row["candidate_id"] == selected_candidate_id),
                    None,
                )
                if selected_candidate is not None:
                    st.caption(selected_candidate.get("passage", ""))
                    st.caption(
                        f"Reference: {selected_candidate.get('source_reference') or '—'} | "
                        f"Current State: {selected_candidate.get('candidate_state') or 'pending'}"
                    )

                    analyst_name = thesis["reviewer"] if thesis["reviewer"] else "System"
                    col_a, col_b = st.columns(2)
                    with col_a:
                        if st.button(
                            "Promote Candidate To Intake",
                            key=f"assessment_workspace_promote_candidate_{thesis_id}",
                            use_container_width=True,
                        ):
                            if selected_candidate.get("candidate_state") in ["reviewed", "confirmed", "promoted", "archived", "rejected"]:
                                st.info("This candidate already has a staged or terminal state.")
                            else:
                                candidate_url = selected_candidate.get("source_reference") or ""
                                passage = selected_candidate.get("passage") or ""
                                staging_uuid = stage_evidence(
                                    intake_thesis_id=thesis_id,
                                    intake_source_type="Athena Extracted Passage",
                                    intake_source_name=selected_candidate.get("originating_document") or "Extracted Source",
                                    intake_source_url=candidate_url,
                                    intake_publication_date=None,
                                    intake_retrieval_date=datetime.now().date(),
                                    intake_author_publisher=None,
                                    intake_evidence_summary=passage[:1200],
                                    intake_key_takeaway=(passage[:220] if passage else "Athena extracted candidate"),
                                    intake_preliminary_grade=None,
                                    intake_source_quality_notes=f"Athena prepared candidate from extraction (id={selected_candidate_id})",
                                    intake_duplicate_flag=0,
                                    intake_duplicate_notes=f"athena_candidate_id={selected_candidate_id}",
                                    intake_created_by=analyst_name,
                                )
                                update_staged_evidence_source_text(staging_uuid=staging_uuid, source_text=passage)
                                st.success(f"Candidate staged: {staging_uuid}")
                                st.rerun()

                    with col_b:
                        if st.button(
                            "Ignore Candidate",
                            key=f"assessment_workspace_ignore_candidate_{thesis_id}",
                            use_container_width=True,
                        ):
                            ignored_set = set(st.session_state.get(ignored_key, []))
                            ignored_set.add(str(selected_candidate_id))
                            st.session_state[ignored_key] = sorted(ignored_set)
                            st.success("Candidate marked ignored for this session.")
                            st.rerun()
        else:
            st.caption("No extracted Athena candidates are available for intake promotion yet.")

        pending_staging_df = fetch_dataframe(
            """
            SELECT staging_uuid, intake_status, source_name
            FROM evidence_staging
            WHERE thesis_id = ?
              AND intake_status IN ('Reviewed', 'Confirmed')
            ORDER BY created_at DESC, id DESC
            """,
            (thesis_id,),
        )
        if not pending_staging_df.empty:
            with st.expander("Analyst Confirmation Queue", expanded=False):
                st.caption("Promotion remains explicit: confirmed intake is only promoted on analyst click.")
                st.dataframe(pending_staging_df, use_container_width=True)
                queue_options = pending_staging_df["staging_uuid"].astype(str).tolist()
                selected_queue_uuid = st.selectbox(
                    "Select Staged Evidence",
                    options=queue_options,
                    key=f"assessment_workspace_queue_uuid_{thesis_id}",
                )
                queue_status = str(
                    pending_staging_df[pending_staging_df["staging_uuid"] == selected_queue_uuid].iloc[0]["intake_status"]
                ).strip()
                reviewer_name = st.text_input(
                    "Analyst Name",
                    value=thesis["reviewer"] if thesis["reviewer"] else "System",
                    key=f"assessment_workspace_queue_reviewer_{thesis_id}",
                )
                col_a, col_b = st.columns(2)
                with col_a:
                    if queue_status == INTAKE_STATUS_REVIEWED and st.button(
                        "Confirm Staged Evidence",
                        key=f"assessment_workspace_confirm_staged_{thesis_id}",
                        use_container_width=True,
                    ):
                        status_result = update_staged_evidence_status(
                            staging_uuid=selected_queue_uuid,
                            target_status=INTAKE_STATUS_CONFIRMED,
                            reviewer_name=reviewer_name,
                            rejection_reason_input="",
                            thesis_id=thesis_id,
                        )
                        if status_result["success"]:
                            st.success(status_result["message"])
                            st.rerun()
                        st.error(status_result["message"])
                with col_b:
                    if queue_status == INTAKE_STATUS_CONFIRMED and st.button(
                        "Promote Confirmed Evidence",
                        key=f"assessment_workspace_promote_staged_{thesis_id}",
                        use_container_width=True,
                    ):
                        promotion_result = promote_staged_evidence(
                            staging_uuid=selected_queue_uuid,
                            analyst=reviewer_name.strip() if reviewer_name else "System",
                        )
                        if promotion_result["success"]:
                            st.success(
                                f"Promoted to evidence_items ID {promotion_result['promoted_evidence_id']}"
                            )
                            st.rerun()
                        st.error(promotion_result["message"])

    with left_col:
        st.subheader(pillar_meta["domain"])
        st.caption(f"Focused Pillar: {pillar_id} — {pillar_name}")
        if pillar_id in BUSINESS_PILLAR_GUIDANCE:
            st.info(BUSINESS_PILLAR_GUIDANCE[pillar_id])

        st.markdown("**Discovered Candidate Evidence**")
        st.caption("Candidate evidence only. These documents are discovery metadata and are not acquired, ingested, extracted, promoted, or governed evidence.")
        st.caption(f"Discovery Status: {evidence_discovery_status}")
        if discovery_warnings:
            for warning in discovery_warnings:
                st.warning(str(warning))

        if not candidate_df.empty:
            candidate_rows = candidate_df.copy()
            candidate_rows["candidate_evidence"] = "Candidate"
            visible_columns = [
                column for column in [
                    "candidate_evidence",
                    "title",
                    "source",
                    "document_type",
                    "publication_date",
                    "reference_url",
                    "reference_id",
                    "provider_name",
                    "discovery_status",
                ] if column in candidate_rows.columns
            ]
            st.dataframe(candidate_rows[visible_columns], use_container_width=True)
        else:
            if evidence_discovery_status == "discovered":
                st.caption("No candidate evidence metadata is currently available for this preparation.")
            elif evidence_discovery_status == "unavailable":
                st.caption("Candidate discovery is currently unavailable for this thesis.")
            elif evidence_discovery_status == "failed":
                st.caption("Candidate discovery failed during preparation. You can continue governed review.")
            else:
                st.caption("Candidate discovery has not yet produced documents for this thesis.")

        st.markdown("**Acquired Source Material**")
        st.caption("Acquired source material only. These records are retrieval-stage artifacts and are not extracted observations or governed evidence.")
        st.caption(f"Acquisition Status: {evidence_acquisition_status}")
        if acquisition_warnings:
            for warning in acquisition_warnings:
                st.warning(str(warning))

        if not acquired_df.empty:
            acquired_rows = acquired_df.copy()
            acquired_rows["stage"] = "Acquired Source"
            visible_columns = [
                column for column in [
                    "stage",
                    "title",
                    "source",
                    "document_type",
                    "acquisition_status",
                    "retrieval_timestamp",
                    "source_reference",
                    "reference_url",
                    "original_candidate_identifier",
                    "discovery_provider",
                    "provider_name",
                    "acquisition_error",
                ] if column in acquired_rows.columns
            ]
            st.dataframe(acquired_rows[visible_columns], use_container_width=True)
        else:
            if evidence_acquisition_status == "acquired":
                st.caption("Acquisition completed but no durable source records are currently available.")
            elif evidence_acquisition_status == "unavailable":
                st.caption("Candidate source acquisition is currently unavailable for this thesis.")
            elif evidence_acquisition_status == "failed":
                st.caption("Candidate source acquisition failed during preparation. You can continue governed review.")
            elif evidence_acquisition_status == "not_attempted":
                st.caption("Source acquisition did not run because discovery did not produce acquirable candidates.")
            else:
                st.caption("Source acquisition has not yet produced records for this thesis.")

        st.markdown("**Extracted Observations**")
        st.caption("Machine-generated preparation only. Extracted observations are not analyst-governed evidence.")
        st.caption(f"Extraction Status: {extraction_status}")
        st.caption(f"Extracted Observation Count: {extracted_observation_count}")
        if extraction_timestamp:
            st.caption(f"Extraction Timestamp: {extraction_timestamp}")
        if extractor_version:
            st.caption(f"Extractor Version: {extractor_version}")
        st.caption(f"Extraction Mode: {'Reused' if extraction_reused else 'New/Partial'}")
        if extraction_warnings:
            for warning in extraction_warnings:
                st.warning(str(warning))

        if not extraction_runs_df.empty:
            run_rows = extraction_runs_df.copy()
            run_rows["reuse_indicator"] = run_rows["reused"].apply(
                lambda value: "Reused" if str(value).strip() in ["1", "1.0", "True", "true"] else "New"
            )
            visible_run_columns = [
                column for column in [
                    "title",
                    "source",
                    "document_type",
                    "extraction_status",
                    "observation_count",
                    "extraction_timestamp",
                    "reuse_indicator",
                    "warning_message",
                    "error_message",
                ] if column in run_rows.columns
            ]
            st.dataframe(run_rows[visible_run_columns], use_container_width=True)
        else:
            if extraction_status == "completed":
                st.caption("Extraction completed but no run metadata is currently available.")
            elif extraction_status == "unsupported":
                st.caption("Extraction is currently unsupported for available acquired materials.")
            elif extraction_status == "failed":
                st.caption("Automatic extraction failed during preparation. You can continue governed review.")
            elif extraction_status == "not_attempted":
                st.caption("Automatic extraction did not run because there was no eligible acquired source material.")
            else:
                st.caption("Automatic extraction has not yet produced run records for this thesis.")

        if not extracted_observations_df.empty:
            preview_rows = extracted_observations_df.copy()
            preview_rows["machine_generated"] = "Machine Generated"
            visible_observation_columns = [
                column for column in [
                    "machine_generated",
                    "title",
                    "extraction_status",
                    "observation_count",
                    "extraction_timestamp",
                    "passage",
                    "pillar_signal",
                    "confidence",
                    "source_location",
                ] if column in preview_rows.columns
            ]
            st.dataframe(preview_rows[visible_observation_columns], use_container_width=True)

        st.markdown("**Evidence Context**")
        supporting_rows = context["supporting_evidence"]
        if supporting_rows:
            supporting_df = pd.DataFrame(supporting_rows)
            visible_columns = [
                column for column in [
                    "evidence_item_id",
                    "publication_date",
                    "title",
                    "source_name",
                    "source_publisher",
                    "evidence_grade",
                ] if column in supporting_df.columns
            ]
            st.dataframe(supporting_df[visible_columns], use_container_width=True)
        else:
            st.caption("No promoted evidence currently surfaced for this pillar.")

        observation_rows = context["governed_observations"]
        st.markdown("**Relevant Observations**")
        if observation_rows:
            observation_df = pd.DataFrame(observation_rows)
            visible_columns = [
                column for column in [
                    "observation_id",
                    "observation_category",
                    "observation_text",
                    "analyst_confidence",
                    "evidence_item_id",
                    "evidence_title",
                ] if column in observation_df.columns
            ]
            st.dataframe(observation_df[visible_columns], use_container_width=True)
        else:
            st.caption("No governed observations currently surfaced for this pillar.")

        advisory_rows = context["advisory_signals"]
        if advisory_rows:
            st.markdown("**Theia Context**")
            advisory_df = pd.DataFrame(advisory_rows)
            visible_columns = [
                column for column in [
                    "evidence_title",
                    "passage",
                    "pillar_signal",
                    "confidence",
                    "source_location",
                ] if column in advisory_df.columns
            ]
            st.dataframe(advisory_df[visible_columns], use_container_width=True)

        st.markdown("**Business Narrative**")
        rationale_draft = build_rationale_draft(
            pillar_id=pillar_id,
            pillar_name=pillar_name,
            synthesis=context,
            extracted_candidates=(extracted_observations_df.to_dict("records") if not extracted_observations_df.empty else []),
        )
        rationale_draft_key = f"assessment_workspace_reasoning_{thesis_id}_{pillar_id}"
        if st.button(
            "Prepare Athena Draft Rationale",
            key=f"assessment_workspace_prepare_draft_{thesis_id}_{pillar_id}",
            use_container_width=True,
        ):
            st.session_state[rationale_draft_key] = rationale_draft["draft_text"]
            st.success("Athena draft prepared. Review and edit before saving governed assessment.")
            st.rerun()
        if rationale_draft["warnings"]:
            for warning in rationale_draft["warnings"]:
                st.warning(warning)
        st.text_area(
            "Reasoning Draft",
            key=rationale_draft_key,
            placeholder="Draft your reasoning here. This remains working context until governed fields are approved.",
            height=120,
        )
        if gate_result["eligible"]:
            st.info("Decision gate is ready. Proceed to the Record Decision section for explicit decision confirmation.")
        else:
            st.caption(
                f"Decision gate blocked by {len(gate_result['missing'])} missing required fields. "
                "Complete governed fields before decision recording."
            )

        st.subheader("Governed Assessment")
        score_key = f"assessment_workspace_score_{thesis_id}_{pillar_id}"
        rag_key = f"assessment_workspace_rag_{thesis_id}_{pillar_id}"
        grade_key = f"assessment_workspace_grade_{thesis_id}_{pillar_id}"
        confidence_key = f"assessment_workspace_confidence_{thesis_id}_{pillar_id}"
        sources_key = f"assessment_workspace_sources_{thesis_id}_{pillar_id}"
        judgment_key = f"assessment_workspace_judgment_{thesis_id}_{pillar_id}"
        falsification_key = f"assessment_workspace_falsification_{thesis_id}_{pillar_id}"
        reviewer_key = f"assessment_workspace_reviewer_{thesis_id}_{pillar_id}"
        notes_key = f"assessment_workspace_notes_{thesis_id}_{pillar_id}"
        linked_key = f"assessment_workspace_links_{thesis_id}_{pillar_id}"
        drl_key = f"assessment_workspace_drl_{thesis_id}_{pillar_id}"
        review_date_key = f"assessment_workspace_review_date_{thesis_id}_{pillar_id}"

        assessment_record_signature_key = f"assessment_workspace_record_signature_{thesis_id}_{pillar_id}"
        assessment_record_signature = (
            None if existing_record is None else existing_record.get("id"),
            None if existing_record is None else existing_record.get("score"),
            None if existing_record is None else existing_record.get("rag_status"),
            None if existing_record is None else existing_record.get("evidence_grade"),
            None if existing_record is None else existing_record.get("confidence_basis"),
            None if existing_record is None else existing_record.get("primary_sources"),
            None if existing_record is None else existing_record.get("judgment"),
            None if existing_record is None else existing_record.get("inference"),
            None if existing_record is None else existing_record.get("falsification_trigger"),
            None if existing_record is None else existing_record.get("reviewer"),
            None if existing_record is None else existing_record.get("review_date"),
            None if existing_record is None else existing_record.get("drl"),
            tuple(linked_evidence_defaults),
        )

        default_score_value = int(existing_record["score"]) if existing_record is not None and pd.notna(existing_record["score"]) else 5
        default_rag_options = [RAG_GREEN, RAG_YELLOW, RAG_ORANGE, RAG_RED] if pillar_id.startswith("B") else ["", RAG_GREEN, RAG_YELLOW, RAG_ORANGE, RAG_RED]
        default_rag_value = existing_record["rag_status"] if existing_record is not None and pd.notna(existing_record["rag_status"]) else default_rag_options[0]
        if default_rag_value not in default_rag_options:
            default_rag_value = default_rag_options[0]
        default_grade_options = [GRADE_A, GRADE_B, GRADE_C, GRADE_D] if pillar_id.startswith("B") else ["", GRADE_A, GRADE_B, GRADE_C, GRADE_D]
        default_grade_value = existing_record["evidence_grade"] if existing_record is not None and pd.notna(existing_record["evidence_grade"]) else default_grade_options[0]
        if default_grade_value not in default_grade_options:
            default_grade_value = default_grade_options[0]
        drl_options = [""] + list(range(1, 10))
        default_drl = existing_record["drl"] if existing_record is not None and pd.notna(existing_record["drl"]) else ""
        if default_drl not in drl_options:
            default_drl = ""

        if st.session_state.get(assessment_record_signature_key) != assessment_record_signature:
            st.session_state[assessment_record_signature_key] = assessment_record_signature
            st.session_state[score_key] = default_score_value
            st.session_state[rag_key] = default_rag_value
            st.session_state[grade_key] = default_grade_value
            st.session_state[confidence_key] = existing_record["confidence_basis"] if existing_record is not None and pd.notna(existing_record["confidence_basis"]) else ""
            st.session_state[sources_key] = existing_record["primary_sources"] if existing_record is not None and pd.notna(existing_record["primary_sources"]) else ""
            st.session_state[judgment_key] = _get_judgment_default(existing_record)
            st.session_state[falsification_key] = existing_record["falsification_trigger"] if existing_record is not None and pd.notna(existing_record["falsification_trigger"]) else ""
            st.session_state[reviewer_key] = existing_record["reviewer"] if existing_record is not None and pd.notna(existing_record["reviewer"]) else (thesis["reviewer"] if thesis["reviewer"] else "")
            st.session_state.setdefault(notes_key, "")
            st.session_state[linked_key] = linked_evidence_defaults
            st.session_state[drl_key] = default_drl
            st.session_state[review_date_key] = default_review_date
        else:
            st.session_state.setdefault(score_key, default_score_value)
            st.session_state.setdefault(rag_key, default_rag_value)
            st.session_state.setdefault(grade_key, default_grade_value)
            st.session_state.setdefault(confidence_key, existing_record["confidence_basis"] if existing_record is not None and pd.notna(existing_record["confidence_basis"]) else "")
            st.session_state.setdefault(sources_key, existing_record["primary_sources"] if existing_record is not None and pd.notna(existing_record["primary_sources"]) else "")
            st.session_state.setdefault(judgment_key, _get_judgment_default(existing_record))
            st.session_state.setdefault(falsification_key, existing_record["falsification_trigger"] if existing_record is not None and pd.notna(existing_record["falsification_trigger"]) else "")
            st.session_state.setdefault(reviewer_key, existing_record["reviewer"] if existing_record is not None and pd.notna(existing_record["reviewer"]) else (thesis["reviewer"] if thesis["reviewer"] else ""))
            st.session_state.setdefault(notes_key, "")
            st.session_state.setdefault(linked_key, linked_evidence_defaults)
            st.session_state.setdefault(drl_key, default_drl)
            st.session_state.setdefault(review_date_key, default_review_date)

        col1, col2 = st.columns(2)
        with col1:
            score = st.number_input("Score (1-10)", min_value=1, max_value=10, key=score_key)
        with col2:
            rag_status = st.selectbox("RAG Status", default_rag_options, key=rag_key)

        col1, col2 = st.columns(2)
        with col1:
            evidence_grade = st.selectbox("Evidence Grade", default_grade_options, key=grade_key)
        with col2:
            confidence_label = "Confidence Basis (why you trust or distrust this judgment)" if pillar_id.startswith("B") else "Confidence Basis *"
            confidence_basis = st.text_input(confidence_label, key=confidence_key)

        if not pillar_id.startswith("B"):
            primary_sources = st.text_input("Primary Sources", key=sources_key)
        else:
            primary_sources = None

        selected_evidence_links = st.multiselect(
            "Linked Evidence Items",
            options=available_evidence_ids,
            format_func=lambda evidence_id: available_evidence_labels.get(evidence_id, f"#{evidence_id}"),
            key=linked_key,
            help="Link one or more evidence items to this governed pillar assessment.",
        )
        judgment = st.text_area("Judgment", key=judgment_key, height=100)
        falsification_label = "Falsification Trigger" if pillar_id.startswith("B") else "Falsification Trigger *"
        falsification_trigger = st.text_input(falsification_label, key=falsification_key)

        col1, col2 = st.columns(2)
        with col1:
            reviewer = st.text_input("Reviewer", key=reviewer_key)
        with col2:
            review_date = st.date_input("Review Date", key=review_date_key)

        if not pillar_id.startswith("B"):
            drl = st.selectbox("DRL", drl_options, key=drl_key)
        else:
            drl = None

        if st.button("Save Governed Assessment", use_container_width=True, key=f"assessment_workspace_save_{thesis_id}_{pillar_id}"):
            if validation_review_date_blocked:
                st.error("Validation mode requires evidence_cutoff_date before pillar scores can be saved.")
            if pillar_id.startswith("I") and not confidence_basis.strip():
                st.error("Confidence Basis is required.")
            elif pillar_id.startswith("I") and not judgment.strip():
                st.error("Judgment is required.")
            elif pillar_id.startswith("I") and not falsification_trigger.strip():
                st.error("Falsification Trigger is required.")
            elif not validation_review_date_blocked:
                created_by = reviewer.strip() if reviewer and reviewer.strip() else (thesis["reviewer"] if thesis["reviewer"] else "System")
                pillar_result = save_pillar_score(
                    thesis_id=thesis_id,
                    pillar_id=pillar_id,
                    pillar_name=pillar_name,
                    score=score,
                    rag_status=rag_status,
                    evidence_grade=evidence_grade,
                    judgment=judgment,
                    confidence_basis=confidence_basis,
                    falsification_trigger=falsification_trigger,
                    reviewer=reviewer,
                    review_date=review_date,
                    created_by=created_by,
                    primary_sources=primary_sources,
                    drl=drl,
                )
                resolved_pillar_score_id = pillar_result["pillar_score_id"]

                if pillar_result["is_update"]:
                    st.success(f"✓ Assessment updated for {pillar_id} {pillar_name}")
                else:
                    st.success(f"✓ Assessment saved for {pillar_id} {pillar_name}")

                st.toast("Governed assessment persisted. You may safely continue.")
                queue_governed_save_confirmation(
                    "Assessment",
                    detail_label=f"{pillar_id} {pillar_name}",
                )

                if resolved_pillar_score_id is None:
                    st.error("Unable to resolve pillar_score_id; evidence links were not synchronized.")
                else:
                    sync_pillar_evidence_links(
                        pillar_score_id=resolved_pillar_score_id,
                        selected_evidence_ids=selected_evidence_links,
                        created_by=created_by,
                    )
                st.rerun()

        st.subheader("Notes")
        st.text_area(
            "Analyst Working Notes",
            key=notes_key,
            placeholder="Draft notes remain working context until governed fields are approved.",
            height=120,
        )
        st.caption("Draft notes are session-scoped working context and do not modify governed persistence until you save the governed assessment.")


def _derive_lifecycle_status(complete_condition, current_condition):
    """Map deterministic lifecycle state to complete/current/pending."""
    if complete_condition:
        return "complete"
    if current_condition:
        return "current"
    return "pending"


def build_thesis_overview_vm(thesis_id: int) -> dict:
    """Assemble a read-only Thesis Overview View Model."""
    thesis_df = fetch_dataframe(
        "SELECT * FROM theses WHERE id = ?",
        (thesis_id,),
    )

    if thesis_df.empty:
        return {
            "header": {
                "company_name": "Unknown Thesis",
                "ticker": "—",
                "validation_mode": False,
                "cutoff_date": None,
            },
            "governance": {
                "gate_complete": 0,
                "gate_required": 11,
                "gate_pct": 0.0,
                "decision_recorded": False,
                "missing": [],
                "validation_locked": False,
            },
            "lifecycle": {
                "perception_status": "pending",
                "understanding_status": "pending",
                "judgment_status": "pending",
                "commitment_status": "pending",
                "memory_status": "pending",
            },
            "evidence": {
                "promoted_count": 0,
                "staging_count": 0,
                "staging_by_status": {},
                "latest_publication_date": None,
            },
            "observations": {
                "count": 0,
            },
            "scoring": {
                "business_avg": None,
                "investment_avg": None,
                "pillars_complete": 0,
                "pillars_required": 11,
            },
            "decision": {
                "recommendation": None,
                "conviction": None,
                "recorded_date": None,
            },
            "reviews": {
                "horizons_complete": 0,
                "horizons_required": len(REVIEW_HORIZON_OPTIONS),
                "latest_horizon": None,
                "review_count": 0,
                "framework_review_eligible_count": 0,
                "latest_review_date": None,
            },
            "attribution": {
                "type": None,
                "recorded_date": None,
            },
            "next_action": {
                "text": "No immediate governed action from Hermes.",
                "reason": None,
                "priority": None,
            },
            "assessment": None,
            "summary": {
                "reviewer": "—",
                "status": "—",
                "drl": "—",
                "primary_horizon": "—",
                "regime_state": "—",
                "created_at": None,
                "decision_question": "—",
            },
            "progress": {
                "evidence_count": 0,
                "business_pillars_completed": 0,
                "investment_pillars_completed": 0,
                "audit_event_count": 0,
            },
            "timeline": {
                "rows": pd.DataFrame(),
            },
            "prebrief": {
                "raw": {},
                "provenance": {},
                "blockers": {},
            },
            "json_export": {
                "payload": {},
                "json_string": "{}",
            },
        }

    thesis = thesis_df.iloc[0]
    validation_mode_enabled = int(thesis["validation_mode"]) == 1 if pd.notna(thesis["validation_mode"]) else False
    cutoff_date = str(thesis["evidence_cutoff_date"]).strip() if pd.notna(thesis["evidence_cutoff_date"]) and str(thesis["evidence_cutoff_date"]).strip() else None

    metrics = get_overview_metrics(thesis_id)
    validation_locked = is_validation_configuration_locked(thesis_id)
    athena_prebrief = get_athena_prebrief(thesis_id)

    lifecycle_state = athena_prebrief.get("lifecycle_state", {})
    governance_readiness = athena_prebrief.get("governance_readiness", {})
    evidence_summary_data = athena_prebrief.get("evidence_summary", {})
    historical_context_data = athena_prebrief.get("historical_context", {})

    gate_complete = int(governance_readiness.get("completed", 0))
    gate_required = int(governance_readiness.get("required", 11))
    gate_pct = 0.0 if gate_required == 0 else min(max(gate_complete / gate_required, 0.0), 1.0)
    decision_recorded = bool(lifecycle_state.get("decision_recorded"))

    observations_df = fetch_dataframe(
        """
        SELECT COUNT(*) AS observation_count
        FROM evidence_observations eo
        JOIN evidence_items ei ON ei.id = eo.evidence_item_id
        WHERE ei.thesis_id = ?
          AND eo.status = ?
        """,
        (thesis_id, OBSERVATION_STATUS_ACTIVE),
    )
    observations_count = int(observations_df.iloc[0]["observation_count"]) if not observations_df.empty else 0

    scoring_df = fetch_dataframe(
        """
        SELECT
            ROUND(AVG(CASE WHEN pillar_id LIKE 'B%' THEN score END), 1) AS business_avg,
            ROUND(AVG(CASE WHEN pillar_id LIKE 'I%' THEN score END), 1) AS investment_avg
        FROM pillar_scores
        WHERE thesis_id = ?
          AND score IS NOT NULL
        """,
        (thesis_id,),
    )
    business_avg = float(scoring_df.iloc[0]["business_avg"]) if not scoring_df.empty and pd.notna(scoring_df.iloc[0]["business_avg"]) else None
    investment_avg = float(scoring_df.iloc[0]["investment_avg"]) if not scoring_df.empty and pd.notna(scoring_df.iloc[0]["investment_avg"]) else None

    latest_decision_df = fetch_dataframe(
        """
        SELECT recommendation, created_at
        FROM decision_logs
        WHERE thesis_id = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (thesis_id,),
    )
    latest_decision_row = latest_decision_df.iloc[0] if not latest_decision_df.empty else None

    latest_review_df = fetch_dataframe(
        """
        SELECT review_horizon, outcome_attribution_type, review_date
        FROM thesis_reviews
        WHERE thesis_id = ?
        ORDER BY review_date DESC, id DESC
        LIMIT 1
        """,
        (thesis_id,),
    )
    latest_review_row = latest_review_df.iloc[0] if not latest_review_df.empty else None

    hermes_tasks = [
        task
        for task in compute_hermes_inbox()
        if task.get("thesis_id") is not None and int(task.get("thesis_id")) == int(thesis_id)
    ]
    primary_task = hermes_tasks[0] if hermes_tasks else None

    promoted_count = int(evidence_summary_data.get("repository_count", 0))
    staging_count = int(evidence_summary_data.get("staging_total", 0))
    horizons_complete = len(historical_context_data.get("horizons_present", []))

    lifecycle_perception = _derive_lifecycle_status(
        complete_condition=promoted_count > 0,
        current_condition=staging_count > 0,
    )
    lifecycle_understanding = _derive_lifecycle_status(
        complete_condition=observations_count > 0,
        current_condition=promoted_count > 0,
    )
    lifecycle_judgment = _derive_lifecycle_status(
        complete_condition=gate_complete >= gate_required and gate_required > 0,
        current_condition=gate_complete > 0,
    )
    lifecycle_commitment = _derive_lifecycle_status(
        complete_condition=decision_recorded,
        current_condition=gate_complete >= gate_required and gate_required > 0,
    )
    lifecycle_memory = _derive_lifecycle_status(
        complete_condition=int(historical_context_data.get("review_count", 0)) > 0,
        current_condition=decision_recorded,
    )

    timeline_df = fetch_dataframe(
        """
        SELECT created_at as Timestamp, event_type as 'Event Type', event_description as Description, created_by as 'Created By'
        FROM thesis_events
        WHERE thesis_id = ?
        ORDER BY created_at DESC
        LIMIT 20
        """,
        (thesis_id,),
    )

    thesis_json = build_thesis_json(thesis_id)

    return {
        "header": {
            "company_name": thesis["company_name"],
            "ticker": thesis["ticker"] if pd.notna(thesis["ticker"]) and str(thesis["ticker"]).strip() else "—",
            "validation_mode": validation_mode_enabled,
            "cutoff_date": cutoff_date,
        },
        "governance": {
            "gate_complete": gate_complete,
            "gate_required": gate_required,
            "gate_pct": gate_pct,
            "decision_recorded": decision_recorded,
            "missing": governance_readiness.get("missing", []),
            "validation_locked": validation_locked,
        },
        "lifecycle": {
            "perception_status": lifecycle_perception,
            "understanding_status": lifecycle_understanding,
            "judgment_status": lifecycle_judgment,
            "commitment_status": lifecycle_commitment,
            "memory_status": lifecycle_memory,
        },
        "evidence": {
            "promoted_count": promoted_count,
            "staging_count": staging_count,
            "staging_by_status": evidence_summary_data.get("staging_by_status", {}),
            "latest_publication_date": evidence_summary_data.get("latest_repository_publication_date"),
        },
        "observations": {
            "count": observations_count,
        },
        "scoring": {
            "business_avg": business_avg,
            "investment_avg": investment_avg,
            "pillars_complete": gate_complete,
            "pillars_required": gate_required,
        },
        "decision": {
            "recommendation": (
                str(latest_decision_row["recommendation"]).strip()
                if latest_decision_row is not None and pd.notna(latest_decision_row["recommendation"]) and str(latest_decision_row["recommendation"]).strip()
                else None
            ),
            # Future extension: no canonical conviction field exists yet.
            "conviction": None,
            "recorded_date": (
                str(latest_decision_row["created_at"]).strip()
                if latest_decision_row is not None and pd.notna(latest_decision_row["created_at"]) and str(latest_decision_row["created_at"]).strip()
                else None
            ),
        },
        "reviews": {
            "horizons_complete": horizons_complete,
            "horizons_required": len(REVIEW_HORIZON_OPTIONS),
            "latest_horizon": (
                str(latest_review_row["review_horizon"]).strip()
                if latest_review_row is not None and pd.notna(latest_review_row["review_horizon"]) and str(latest_review_row["review_horizon"]).strip()
                else None
            ),
            "review_count": int(historical_context_data.get("review_count", 0)),
            "framework_review_eligible_count": int(historical_context_data.get("framework_review_eligible_count", 0)),
            "latest_review_date": historical_context_data.get("latest_review_date"),
        },
        "attribution": {
            "type": (
                str(latest_review_row["outcome_attribution_type"]).strip()
                if latest_review_row is not None and pd.notna(latest_review_row["outcome_attribution_type"]) and str(latest_review_row["outcome_attribution_type"]).strip()
                else None
            ),
            "recorded_date": (
                str(latest_review_row["review_date"]).strip()
                if latest_review_row is not None and pd.notna(latest_review_row["review_date"]) and str(latest_review_row["review_date"]).strip()
                else None
            ),
        },
        "next_action": {
            "text": (
                primary_task.get("action")
                if primary_task is not None and primary_task.get("action")
                else athena_prebrief.get("next_action", "No immediate governed action from Hermes.")
            ),
            "reason": (
                primary_task.get("description")
                if primary_task is not None and primary_task.get("description")
                else (primary_task.get("task_type") if primary_task is not None else None)
            ),
            "priority": int(primary_task["priority"]) if primary_task is not None and primary_task.get("priority") is not None else None,
        },
        "assessment": None,
        "summary": {
            "reviewer": thesis["reviewer"] if pd.notna(thesis["reviewer"]) and str(thesis["reviewer"]).strip() else "—",
            "status": thesis["status"] if pd.notna(thesis["status"]) and str(thesis["status"]).strip() else "—",
            "drl": thesis["drl"] if pd.notna(thesis["drl"]) and str(thesis["drl"]).strip() else "—",
            "primary_horizon": thesis["primary_horizon"] if pd.notna(thesis["primary_horizon"]) and str(thesis["primary_horizon"]).strip() else "—",
            "regime_state": thesis["regime_state"] if pd.notna(thesis["regime_state"]) and str(thesis["regime_state"]).strip() else "—",
            "created_at": thesis["created_at"] if pd.notna(thesis["created_at"]) and str(thesis["created_at"]).strip() else None,
            "decision_question": thesis["decision_question"] if pd.notna(thesis["decision_question"]) and str(thesis["decision_question"]).strip() else "—",
        },
        "progress": {
            "evidence_count": int(metrics["evidence_count"]),
            "business_pillars_completed": int(metrics["business_pillars_completed"]),
            "investment_pillars_completed": int(metrics["investment_pillars_completed"]),
            "audit_event_count": int(metrics["audit_event_count"]),
        },
        "timeline": {
            "rows": timeline_df,
        },
        "prebrief": {
            "raw": athena_prebrief,
            "provenance": athena_prebrief.get("provenance", {}),
            "blockers": athena_prebrief.get("blockers", {}),
        },
        "json_export": {
            "payload": thesis_json,
            "json_string": json.dumps(thesis_json, indent=2, default=str),
        },
    }


def _display_value(value):
    """Return an em dash for missing display values."""
    if value is None:
        return "—"
    if isinstance(value, str) and not value.strip():
        return "—"
    return value


def _resolve_validation_review_date(thesis, existing_review_date=None):
    validation_mode_enabled = int(thesis["validation_mode"]) == 1 if pd.notna(thesis["validation_mode"]) else False
    evidence_cutoff_date = None
    if pd.notna(thesis["evidence_cutoff_date"]) and str(thesis["evidence_cutoff_date"]).strip():
        evidence_cutoff_date = pd.to_datetime(thesis["evidence_cutoff_date"]).date()

    if existing_review_date is not None and pd.notna(existing_review_date):
        resolved_review_date = pd.to_datetime(existing_review_date).date()
    elif validation_mode_enabled and evidence_cutoff_date is not None:
        resolved_review_date = evidence_cutoff_date
    else:
        resolved_review_date = datetime.now().date()

    return resolved_review_date, validation_mode_enabled, evidence_cutoff_date


def render_constitutional_journey(vm):
    """Render lifecycle journey using only VM lifecycle fields."""
    section_header("Constitutional Journey")
    steps = [
        ("Perception", vm["lifecycle"]["perception_status"]),
        ("Understanding", vm["lifecycle"]["understanding_status"]),
        ("Judgment", vm["lifecycle"]["judgment_status"]),
        ("Commitment", vm["lifecycle"]["commitment_status"]),
        ("Memory", vm["lifecycle"]["memory_status"]),
    ]
    status_text = {
        "complete": "Complete",
        "current": "Current",
        "pending": "Pending",
    }
    status_progress = {
        "complete": 1.0,
        "current": 0.5,
        "pending": 0.0,
    }

    columns = st.columns(5)
    for idx, (label, raw_status) in enumerate(steps):
        status = raw_status if raw_status in status_text else "pending"
        with columns[idx]:
            st.markdown(f"**{label}**")
            st.progress(status_progress[status])
            if status == "complete":
                st.success(status_text[status])
            elif status == "current":
                st.info(status_text[status])
            else:
                st.caption(status_text[status])


def render_thesis_health_summary(vm):
    """Render thesis health summary from VM header/governance/decision/review fields."""
    section_header("Thesis Health Summary")
    col1, col2, col3 = st.columns(3)

    decision_status = "Recorded" if vm["governance"]["decision_recorded"] else "Pending"

    with col1:
        summary_field("Company", _display_value(vm["header"]["company_name"]))
        summary_field("Ticker", _display_value(vm["header"]["ticker"]))
        summary_field("Validation Mode", "Enabled" if vm["header"]["validation_mode"] else "Disabled")
        summary_field("Evidence Cutoff", _display_value(vm["header"]["cutoff_date"]))

    with col2:
        summary_field("Decision Status", decision_status)
        summary_field("Recommendation", _display_value(vm["decision"]["recommendation"]))
        summary_field("Decision Recorded Date", _display_value(vm["decision"]["recorded_date"]))

    with col3:
        summary_field("Latest Review Horizon", _display_value(vm["reviews"]["latest_horizon"]))
        summary_field("Outcome Attribution", _display_value(vm["attribution"]["type"]))


def render_thesis_progress_summary(vm):
    """Render progress summary rows from VM-only evidence/observation/scoring/review fields."""
    section_header("Progress Summary")

    promoted_count = int(vm["evidence"]["promoted_count"])
    staging_count = int(vm["evidence"]["staging_count"])
    observations_count = int(vm["observations"]["count"])
    pillars_complete = int(vm["scoring"]["pillars_complete"])
    pillars_required = int(vm["scoring"]["pillars_required"])
    review_count = int(vm["reviews"]["review_count"])
    framework_count = int(vm["reviews"]["framework_review_eligible_count"])

    evidence_pct = 1.0 if promoted_count > 0 else (0.5 if staging_count > 0 else 0.0)
    observations_pct = 1.0 if observations_count > 0 else (0.5 if promoted_count > 0 else 0.0)
    thesis_pct = 0.0 if pillars_required <= 0 else min(max(pillars_complete / pillars_required, 0.0), 1.0)
    decision_pct = 1.0 if vm["governance"]["decision_recorded"] else (0.5 if pillars_complete > 0 else 0.0)
    review_pct = 1.0 if review_count > 0 else (0.5 if vm["decision"]["recorded_date"] else 0.0)
    framework_pct = 1.0 if framework_count > 0 else 0.0

    progress_rows = [
        {
            "label": "Evidence",
            "value_text": f"{promoted_count} promoted / {staging_count} staged",
            "pct": evidence_pct,
        },
        {
            "label": "Observations",
            "value_text": f"{observations_count} recorded",
            "pct": observations_pct,
        },
        {
            "label": "Thesis",
            "value_text": f"{pillars_complete} / {pillars_required} pillars complete",
            "pct": thesis_pct,
        },
        {
            "label": "Decision",
            "value_text": "Recorded" if vm["governance"]["decision_recorded"] else "Pending",
            "pct": decision_pct,
        },
        {
            "label": "Historical Review",
            "value_text": f"{review_count} reviews",
            "pct": review_pct,
        },
        {
            "label": "Framework Learning",
            "value_text": f"{framework_count} eligible",
            "pct": framework_pct,
        },
    ]

    render_progress_summary(progress_rows)


def render_constitutional_status(vm):
    """Render read-only governance status panel from VM governance/review/attribution fields."""
    section_header("Constitutional Status")

    evidence_governed_status = "Complete" if int(vm["governance"]["gate_complete"]) > 0 else "Pending"
    provenance_status = "Complete" if _display_value(vm["attribution"]["recorded_date"]) != "—" else "Unknown"
    decision_status = "Complete" if vm["governance"]["decision_recorded"] else "Pending"
    historical_status = "Active" if int(vm["reviews"]["review_count"]) > 0 else "Pending"
    attribution_status = "Complete" if _display_value(vm["attribution"]["type"]) != "—" else "Pending"
    learning_status = "Active" if int(vm["reviews"]["framework_review_eligible_count"]) > 0 else "Pending"

    status_rows = [
        ("Evidence Governed", evidence_governed_status),
        ("Provenance Complete", provenance_status),
        ("Decision Recorded", decision_status),
        ("Historical Review Active", historical_status),
        ("Attribution Complete", attribution_status),
        ("Framework Learning Pending", learning_status),
    ]

    for label, status in status_rows:
        col1, col2 = st.columns([2, 3])
        with col1:
            st.checkbox(label, value=status in {"Complete", "Active"}, disabled=True)
        with col2:
            summary_field("Status", status)


def render_hermes_next_action(vm):
    """Render Hermes next action details sourced only from VM next_action."""
    section_header("Hermes Next Action")
    next_action_text = _display_value(vm["next_action"]["text"])
    if next_action_text == "—":
        st.warning("No governed action currently queued.")
    else:
        st.info(str(next_action_text))

    summary_field("Reason", _display_value(vm["next_action"]["reason"]))
    summary_field("Priority", _display_value(vm["next_action"]["priority"]))


def render_thesis_overview(vm):
    """Render Thesis Overview using a single, pre-assembled View Model."""
    render_constitutional_journey(vm)
    st.divider()
    render_thesis_health_summary(vm)
    st.divider()
    render_thesis_progress_summary(vm)
    st.divider()
    render_constitutional_status(vm)
    st.divider()
    render_hermes_next_action(vm)
    st.divider()

    section_header("Thesis Context")
    col1, col2 = st.columns(2)
    with col1:
        summary_field("Reviewer", vm["summary"]["reviewer"])
        summary_field("DRL", vm["summary"]["drl"])
    with col2:
        summary_field("Thesis Status", vm["summary"]["status"])
        summary_field("Primary Horizon", vm["summary"]["primary_horizon"])
        summary_field("Regime State", vm["summary"]["regime_state"])
        summary_field("Created", vm["summary"]["created_at"] or "—")

    if vm["governance"]["validation_locked"]:
        st.info("Validation mode and evidence cutoff date are immutable after the first decision record. Use a new thesis for a different historical scenario.")

    summary_field("Decision Question", vm["summary"]["decision_question"])

    st.divider()
    section_header("Athena Pre-Brief")

    st.markdown("**Governance Readiness**")
    if vm["governance"]["missing"]:
        st.write("Missing Requirements:")
        for item in vm["governance"]["missing"]:
            st.write(f"- {item['pillar_id']} — {item['label']}")
    else:
        st.write("Missing Requirements: —")

    st.markdown("**Evidence Summary**")
    summary_field("Latest Repository Publication Date", vm["evidence"]["latest_publication_date"] or "—")
    if vm["evidence"]["staging_by_status"]:
        st.write("Staging by Status:")
        for status_name, status_count in vm["evidence"]["staging_by_status"].items():
            st.write(f"- {status_name}: {status_count}")
    else:
        st.write("Staging by Status: —")

    st.markdown("**Historical Context**")
    summary_field("Latest Review Date", vm["reviews"]["latest_review_date"] or "—")
    prebrief_raw = vm["prebrief"]["raw"]
    horizons_present = prebrief_raw.get("historical_context", {}).get("horizons_present", [])
    summary_field("Horizons Present", ", ".join(horizons_present) if horizons_present else "—")

    st.markdown("**Blockers**")
    blockers_data = vm["prebrief"]["blockers"]
    for subsystem_name in ["theia", "hermes", "themis", "mnemosyne"]:
        subsystem_blockers = blockers_data.get(subsystem_name, [])
        if subsystem_blockers:
            st.write(f"- {subsystem_name}:")
            for blocker_item in subsystem_blockers:
                st.write(f"  - {blocker_item}")
        else:
            st.write(f"- {subsystem_name}: none")

    st.markdown("**Provenance**")
    provenance_data = vm["prebrief"]["provenance"]
    summary_field("Lifecycle State Owner", provenance_data.get("lifecycle_state", "—"))
    summary_field("Governance Readiness Owner", provenance_data.get("governance_readiness", "—"))
    summary_field("Evidence Summary Owner", provenance_data.get("evidence_summary", "—"))
    summary_field("Historical Context Owner", provenance_data.get("historical_context", "—"))
    summary_field("Next Action Owner", provenance_data.get("next_action", "—"))

    with st.expander("Raw Pre-Brief Object"):
        st.json(vm["prebrief"]["raw"])

    st.divider()
    section_header("Timeline")
    timeline_table(vm["timeline"]["rows"])

    st.divider()
    section_header("JSON Export")
    st.json(vm["json_export"]["payload"])
    json_download_clicked = st.download_button(
        label="Download Athena Evaluation JSON",
        data=vm["json_export"]["json_string"],
        file_name=f"ims_thesis_{vm['header']['company_name']}.json",
        mime="application/json",
        key="json_download",
    )
    if json_download_clicked:
        observe_export(
            export_type="thesis_json",
            trigger="download_button",
            record_count=len(vm["json_export"].get("payload", {})),
        )

    instrumentation_json = export_events_json()
    telemetry_download_clicked = st.download_button(
        label="Download Instrumentation Telemetry JSON",
        data=instrumentation_json,
        file_name=f"ims_instrumentation_{vm['header']['company_name']}.json",
        mime="application/json",
        key="instrumentation_json_download",
    )
    if telemetry_download_clicked:
        observe_export(
            export_type="instrumentation_json",
            trigger="download_button",
            record_count=get_event_count(),
        )


# Initialize database on app start
init_db()

# Application header
st.markdown(
    '<h1 style="font-family: Cormorant Garamond, Playfair Display,'
    ' Georgia, serif; font-weight: 300; font-size: 2.8rem;'
    ' letter-spacing: 0.08em; color: #E8E6E0; margin-bottom: 0;">'
    'Athena</h1>',
    unsafe_allow_html=True
)
st.markdown("---")
st.markdown(
    '<p style="font-family: JetBrains Mono, Consolas, monospace;'
    ' font-size: 0.75rem; color: #C5A028; letter-spacing: 0.1em;'
    ' text-transform: uppercase;">⚖ Governed by Athena Charter v1.0</p>',
    unsafe_allow_html=True
)
st.markdown("---")

# Initialize session state
if 'current_view' not in st.session_state:
    st.session_state['current_view'] = 'Home'
if 'selected_thesis_id' not in st.session_state:
    st.session_state['selected_thesis_id'] = None
if 'selected_evidence_id' not in st.session_state:
    st.session_state['selected_evidence_id'] = None
if 'engine_preparation_status' not in st.session_state:
    st.session_state['engine_preparation_status'] = None
if 'active_evaluation_thesis_id' not in st.session_state:
    st.session_state['active_evaluation_thesis_id'] = None
if 'active_evaluation_request' not in st.session_state:
    st.session_state['active_evaluation_request'] = None
if 'pending_prepare_request' not in st.session_state:
    st.session_state['pending_prepare_request'] = None
if 'selected_thesis_id_explorer' not in st.session_state:
    st.session_state['selected_thesis_id_explorer'] = None


def _capture_navigation_event():
    """Capture view transitions passively without affecting navigation logic."""
    current_view = st.session_state.get("current_view", "Home")
    previous_view = st.session_state.get("_instrument_previous_view")
    thesis_id = st.session_state.get("selected_thesis_id")

    if previous_view != current_view:
        observe_ui_navigation(
            current_view=current_view,
            previous_view=previous_view,
            thesis_id=thesis_id,
        )
        st.session_state["_instrument_previous_view"] = current_view


def _render_sidebar_styles():
    """Render stable sidebar styles without positional selectors."""
    st.markdown(
        """
<style>
section[data-testid='stSidebar'] .athena-brand-title {
  font-family: Cormorant Garamond, Playfair Display, Georgia, serif;
  font-size: 1.8rem;
  letter-spacing: 0.08em;
  font-weight: 500;
  color: #E8E6E0;
  margin: 0;
}
section[data-testid='stSidebar'] .athena-brand-subtitle {
  font-family: Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  font-size: 0.68rem;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: #8B8B9A;
  margin-top: 0.35rem;
  margin-bottom: 1.1rem;
}
section[data-testid='stSidebar'] .athena-section-label {
  font-family: Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  font-size: 0.68rem;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: #8B8B9A;
  margin-top: 0.2rem;
  margin-bottom: 0.45rem;
}
section[data-testid='stSidebar'] .athena-history-map {
  font-family: JetBrains Mono, Consolas, monospace;
  font-size: 0.7rem;
  color: #8B8B9A;
  margin-left: 0.85rem;
  margin-top: -0.35rem;
  margin-bottom: 0.3rem;
}
section[data-testid='stSidebar'] .athena-active-card {
  background: #12121A;
  border: 1px solid #1E1E2E;
  border-radius: 0.55rem;
  padding: 0.8rem 0.9rem;
  margin-bottom: 0.45rem;
}
section[data-testid='stSidebar'] .athena-active-company {
  font-family: Cormorant Garamond, Playfair Display, Georgia, serif;
  font-size: 1.2rem;
  color: #E8E6E0;
  line-height: 1.25;
}
section[data-testid='stSidebar'] .athena-active-subtitle {
  font-family: JetBrains Mono, Consolas, monospace;
  font-size: 0.8rem;
  color: #8B8B9A;
  margin-top: 0.3rem;
}
section[data-testid='stSidebar'] .athena-active-status {
  font-family: Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  color: #C5A028;
  margin-top: 0.35rem;
  font-size: 0.86rem;
}
section[data-testid='stSidebar'] div[data-testid='stButton'] > button {
  width: 100%;
  border-radius: 0.5rem;
  transition: background-color 200ms ease, color 200ms ease, border-color 200ms ease;
}
</style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_brand():
    """Render sidebar brand header."""
    st.markdown("<div class='athena-brand-title'>ATHENA</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='athena-brand-subtitle'>Governed Investment Intelligence</div>",
        unsafe_allow_html=True,
    )


def _is_primary_nav_active(label, current_view):
    """Return whether a primary navigation label should appear active."""
    if label == "Home":
        return current_view in ["Home", "Dashboard", "New Thesis", "Hermes Workflow Inbox"]
    if label == "Portfolio":
        return current_view == "Portfolio"
    if label == "Workspace":
        return current_view in ["Workspace", "Thesis Workspace", "Thesis Detail"]
    if label == "History":
        return current_view in ["History", "Documentation"]
    if label == "Data Explorer":
        return current_view == "Data Explorer"
    if label == "Microsoft HRV-002 Readiness":
        return current_view == "Microsoft HRV-002 Readiness"
    if label == "Settings":
        return current_view == "Settings"
    return False


def _apply_primary_navigation(label):
    """Apply existing primary navigation mapping and lifecycle behavior."""
    if label == "Home":
        st.session_state["current_view"] = "Home"
        st.session_state["selected_thesis_id"] = None
    elif label == "Portfolio":
        st.session_state["current_view"] = "Portfolio"
        st.session_state["selected_thesis_id"] = None
    elif label == "Workspace":
        if st.session_state.get("selected_thesis_id") is not None:
            st.session_state["current_view"] = "Workspace"
        else:
            st.session_state["current_view"] = "Workspace"
    elif label == "History":
        st.session_state["current_view"] = "History"
        st.session_state["selected_thesis_id"] = None
    elif label == "Data Explorer":
        st.session_state["current_view"] = "Data Explorer"
    elif label == "Microsoft HRV-002 Readiness":
        st.session_state["current_view"] = "Microsoft HRV-002 Readiness"
        st.session_state["selected_thesis_id"] = None
    elif label == "Settings":
        st.session_state["current_view"] = "Settings"
        st.session_state["selected_thesis_id"] = None


def render_sidebar_primary_navigation(current_view):
    """Render primary navigation controls."""
    primary_nav_labels = ["Home", "Portfolio", "Workspace", "History", "Data Explorer", "Microsoft HRV-002 Readiness", "Settings"]
    for nav_label in primary_nav_labels:
        button_type = "primary" if _is_primary_nav_active(nav_label, current_view) else "secondary"
        if st.button(nav_label, key=f"nav_{nav_label}", use_container_width=True, type=button_type):
            _apply_primary_navigation(nav_label)
            st.rerun()


def _active_thesis_descriptor(thesis_row):
    """Build a neutral thesis descriptor from existing thesis metadata."""
    descriptor_fields = ["account_type", "portfolio_role", "primary_horizon"]
    for field_name in descriptor_fields:
        if field_name in thesis_row and pd.notna(thesis_row[field_name]):
            candidate = str(thesis_row[field_name]).strip()
            if candidate:
                return candidate
    return "Active Thesis"


def render_active_thesis_card(theses_df, selected_thesis_id):
    """Render the active thesis summary card when a thesis is selected."""
    if selected_thesis_id is None:
        return

    active_match = theses_df[theses_df["id"] == selected_thesis_id]
    active_company_name = "Selected Thesis"
    active_descriptor = "Active Thesis"
    if not active_match.empty:
        active_row = active_match.iloc[0]
        active_company_name = active_row["company_name"]
        active_descriptor = _active_thesis_descriptor(active_row)

    st.markdown("<div class='athena-section-label'>Active Thesis</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='athena-active-card'>"
        f"<div class='athena-active-company'>{active_company_name}</div>"
        f"<div class='athena-active-subtitle'>{active_descriptor}</div>"
        "<div class='athena-active-status'>⬤ In Progress</div>"
        "</div>",
        unsafe_allow_html=True,
    )

    if st.button("Continue →", key="nav_continue_active", use_container_width=True, type="secondary"):
        st.session_state["current_view"] = "Thesis Workspace"
        st.rerun()


def render_sidebar_portfolio(theses_df):
    """Render thesis list under Portfolio section."""
    st.markdown("<div class='athena-section-label'>Portfolio</div>", unsafe_allow_html=True)
    for _, row in theses_df.iterrows():
        is_selected = st.session_state.get("selected_thesis_id") == row["id"]
        button_type = "primary" if is_selected else "secondary"
        if st.button(
            row["company_name"],
            key=f"thesis_{row['id']}",
            use_container_width=True,
            type=button_type,
        ):
            st.session_state["current_view"] = "Thesis Workspace"
            st.session_state["selected_thesis_id"] = row["id"]
            st.rerun()


def render_sidebar_actions():
    """Render sidebar actions with existing routing behavior."""
    st.markdown("<div class='athena-section-label'>Actions</div>", unsafe_allow_html=True)

    if st.button("Prepare Evaluation", key="nav_new_thesis", use_container_width=True, type="secondary"):
        st.session_state["current_view"] = "New Thesis"
        st.session_state["selected_thesis_id"] = None
        st.rerun()

    if st.button("Workflow Inbox", key="nav_workflow_inbox", use_container_width=True, type="secondary"):
        st.session_state["current_view"] = "Hermes Workflow Inbox"
        st.session_state["selected_thesis_id"] = None
        st.rerun()


def format_display_value(value, fallback="Not available"):
    """Normalize user-facing values for Home display."""
    text = _display_text(value)
    return text if text else fallback


EXPLICIT_ARCHIVED_STATUS_LABELS = {
    7: "Roadmap-Archived / Type A Review Established",
    8: "Roadmap-Archived / No-Touch Regression Reference",
}

# Archived constitutional assets are identity-scoped by governed thesis identifiers.
# Do not infer archival identity from company name or ticker.
ARCHIVED_CONSTITUTIONAL_ASSET_THESIS_IDS = {7, 8}

# Unclassified and ambiguous records are excluded from operational work queues
# until governed identity and lifecycle authority is explicit.
UNCLASSIFIED_DATA_HYGIENE_THESIS_IDS = {1, 3, 4, 5, 6, 9, 10, 11, 12, 13}

# Explicitly allowed operational records in current runtime data.
# Future ratified identities can be added through governed process.
ALLOWED_ACTIVE_OPERATIONAL_THESIS_IDS = set()
PROGRESS_MODE_ACTIVE_TICKERS = {"USWR"}


def _load_progress_mode_active_operational_thesis_ids():
    ids = set(ALLOWED_ACTIVE_OPERATIONAL_THESIS_IDS)
    try:
        if not PROGRESS_MODE_ACTIVE_TICKERS:
            return ids
        placeholders = ",".join(["?"] * len(PROGRESS_MODE_ACTIVE_TICKERS))
        ticker_df = fetch_dataframe(
            f"SELECT id FROM theses WHERE UPPER(COALESCE(ticker, '')) IN ({placeholders})",
            tuple(sorted(PROGRESS_MODE_ACTIVE_TICKERS)),
        )
        if not ticker_df.empty:
            ids.update(ticker_df["id"].astype(int).tolist())
    except Exception:
        # Keep routing resilient if DB is unavailable during render startup.
        pass
    return ids


ACTIVE_OPERATIONAL_THESIS_IDS = _load_progress_mode_active_operational_thesis_ids()

AFFIRMATIVE_ACTIVE_STATUS_LABELS = {
    "active",
    "in progress",
    "in-progress",
    "operational",
    "pursued",
}

# thesis_id=14 remains unresolved governance identity and should not be treated
# as clean active HRV-002 execution until governance state is explicit.
GOVERNANCE_ATTENTION_ONLY_THESIS_IDS = {14}

MICROSOFT_READINESS_SOURCE_THESIS_ID = 14

MICROSOFT_BUSINESS_PILLARS = [
    ("B1", "Business Quality"),
    ("B2", "Competitive Advantage"),
    ("B3", "Revenue Quality"),
    ("B4", "Financial Resilience"),
    ("B5", "Execution Capability"),
    ("B6", "Industry Position"),
    ("B7", "Systems Importance"),
]

MICROSOFT_INVESTMENT_PILLARS = [
    ("I1", "Valuation"),
    ("I2", "Market Structure"),
    ("I3", "Market Sentiment"),
    ("I4", "Portfolio Contribution"),
]


def _to_int_thesis_id(thesis_id):
    try:
        return int(thesis_id) if thesis_id is not None else None
    except (TypeError, ValueError):
        return None


def is_archived_constitutional_asset(thesis_id):
    thesis_id_int = _to_int_thesis_id(thesis_id)
    return thesis_id_int in ARCHIVED_CONSTITUTIONAL_ASSET_THESIS_IDS


def is_governance_attention_only_asset(thesis_id):
    thesis_id_int = _to_int_thesis_id(thesis_id)
    return thesis_id_int in GOVERNANCE_ATTENTION_ONLY_THESIS_IDS


def is_unclassified_non_operational_record(row):
    thesis_id_int = _to_int_thesis_id((row or {}).get("thesis_id") if isinstance(row, dict) else None)
    if thesis_id_int is None:
        return False
    return thesis_id_int in UNCLASSIFIED_DATA_HYGIENE_THESIS_IDS


def has_affirmative_active_signal(row):
    thesis_id_int = _to_int_thesis_id((row or {}).get("thesis_id") if isinstance(row, dict) else None)
    if thesis_id_int is None:
        return False

    if bool((row or {}).get("explicit_active_program")):
        return True

    active_program_identity = _display_text((row or {}).get("active_program_identity") if isinstance(row, dict) else "")
    if active_program_identity:
        return True

    status_text = _display_text((row or {}).get("status") if isinstance(row, dict) else "").lower()
    if status_text in AFFIRMATIVE_ACTIVE_STATUS_LABELS:
        return True

    return thesis_id_int in ACTIVE_OPERATIONAL_THESIS_IDS


def is_active_operational_work(row):
    thesis_id_int = _to_int_thesis_id((row or {}).get("thesis_id") if isinstance(row, dict) else None)
    if thesis_id_int is None:
        return False
    if is_archived_constitutional_asset(thesis_id_int):
        return False
    if is_governance_attention_only_asset(thesis_id_int):
        return False
    if is_unclassified_non_operational_record(row):
        return False

    status_text = _display_text((row or {}).get("status") if isinstance(row, dict) else "")
    if status_text == STATUS_CLOSED:
        return False

    return has_affirmative_active_signal(row)


def should_show_on_home_active_work(row):
    return is_active_operational_work(row)


def should_show_governance_attention(row):
    thesis_id_int = _to_int_thesis_id((row or {}).get("thesis_id"))
    if thesis_id_int is None:
        return False

    if bool((row or {}).get("governance_unresolved")):
        return True

    if is_governance_attention_only_asset(thesis_id_int):
        return True

    if thesis_id_int == 7:
        return bool((row or {}).get("framework_review_eligible"))

    return False


def build_governance_attention_message(row):
    thesis_id_int = _to_int_thesis_id((row or {}).get("thesis_id"))
    if thesis_id_int is None:
        return ""

    if bool((row or {}).get("governance_unresolved")):
        return "Governance unresolved follow-up required"

    if thesis_id_int == 7 and bool((row or {}).get("framework_review_eligible")):
        return "Kodak archived asset — Framework Review Consideration Eligible"
    if thesis_id_int == 14:
        return "Microsoft thesis_id=14 — Closure / identity ambiguity"
    return ""


def render_friction_logger(default_thesis_id=None, default_workflow_area="Workspace"):
    """Render a minimal friction log form that writes to existing thesis/audit events."""
    with st.expander("Log Friction", expanded=False):
        thesis_options_df = fetch_dataframe(
            "SELECT id, company_name, ticker FROM theses ORDER BY company_name ASC"
        )
        thesis_options = ["None"]
        thesis_label_map = {"None": None}
        for _, thesis_row in thesis_options_df.iterrows():
            tid = int(thesis_row["id"])
            ticker = str(thesis_row["ticker"]).strip().upper() if pd.notna(thesis_row["ticker"]) else ""
            label = f"{tid} — {thesis_row['company_name']} ({ticker or 'N/A'})"
            thesis_options.append(label)
            thesis_label_map[label] = tid

        default_label = "None"
        if default_thesis_id is not None:
            for option_label, option_value in thesis_label_map.items():
                if option_value == int(default_thesis_id):
                    default_label = option_label
                    break

        with st.form(f"friction_log_form_{default_workflow_area}_{default_thesis_id}"):
            selected_label = st.selectbox(
                "Thesis Context",
                options=thesis_options,
                index=thesis_options.index(default_label) if default_label in thesis_options else 0,
                help="Optional thesis association for this friction observation.",
            )
            workflow_area = st.text_input("Workflow Area", value=default_workflow_area)
            friction_type = st.selectbox("Friction Type", options=FRICTION_TYPE_OPTIONS)
            short_description = st.text_input("Short Description")
            analyst_impact = st.text_area("Analyst Impact", height=80)
            hermes_flag = st.selectbox("Could Hermes eventually reduce this?", options=HERMES_REDUCTION_OPTIONS)
            friction_status = st.selectbox("Status", options=FRICTION_STATUS_OPTIONS, index=0)
            submitted = st.form_submit_button("Record Friction", use_container_width=True)

            if submitted:
                if not short_description.strip():
                    st.error("Short description is required.")
                elif not analyst_impact.strip():
                    st.error("Analyst impact is required.")
                else:
                    selected_thesis_id = thesis_label_map.get(selected_label)
                    payload = log_friction_observation(
                        workflow_area=workflow_area,
                        friction_type=friction_type,
                        short_description=short_description,
                        analyst_impact=analyst_impact,
                        hermes_reduction_potential=hermes_flag,
                        status=friction_status,
                        thesis_id=selected_thesis_id,
                        created_by="Phillip",
                    )
                    st.success(
                        "Friction recorded: "
                        f"{payload.get('friction_type')} ({payload.get('status')})"
                    )


def _schema_table_support(table_name, required_columns=None):
    """Return structured table/column availability for runtime schema checks."""
    required = list(required_columns or [])
    table_df = fetch_dataframe(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    )
    table_available = not table_df.empty
    if not table_available:
        return {
            "table": table_name,
            "available": False,
            "columns": [],
            "required_columns": required,
            "missing_columns": required,
            "message": "Not available from current runtime schema.",
        }

    columns_df = fetch_dataframe(f"PRAGMA table_info({table_name})")
    columns = columns_df["name"].astype(str).tolist() if not columns_df.empty and "name" in columns_df.columns else []
    missing_columns = [col for col in required if col not in columns]
    return {
        "table": table_name,
        "available": True,
        "columns": columns,
        "required_columns": required,
        "missing_columns": missing_columns,
        "message": "Available" if not missing_columns else "Not available from current runtime schema.",
    }


def _safe_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _as_year_text(value):
    text = _display_text(value)
    if not text:
        return ""
    try:
        return pd.to_datetime(text, errors="coerce").strftime("%Y")
    except Exception:
        return ""


def get_microsoft_identity_state():
    """Build static identity state panel rows for HRV-001/HRV-002 framing."""
    return pd.DataFrame(
        [
            {"Identity": "HRV-001", "State": "Preserved historical Microsoft review concept"},
            {"Identity": "thesis_id=14", "State": "Ambiguous historical Microsoft artifact (not active work)"},
            {"Identity": "HRV-002", "State": "Draft successor concept, not yet active"},
            {"Identity": "Active HRV-002 thesis_id", "State": "Not created"},
        ]
    )


def get_microsoft_runtime_snapshot(thesis_id=MICROSOFT_READINESS_SOURCE_THESIS_ID):
    """Return read-only runtime snapshot for Microsoft source thesis context."""
    unavailable_text = "Not available from current runtime schema."
    snapshot = {
        "thesis_id": _safe_int(thesis_id),
        "company_name": unavailable_text,
        "ticker": unavailable_text,
        "status": unavailable_text,
        "created_at": unavailable_text,
        "decision_log_count": unavailable_text,
        "thesis_review_count": unavailable_text,
        "thesis_event_count": unavailable_text,
        "latest_event_timestamp": unavailable_text,
        "decision_recommendation": unavailable_text,
    }

    theses_support = _schema_table_support("theses", ["id", "company_name", "ticker", "status", "created_at"])
    decision_logs_support = _schema_table_support("decision_logs", ["id", "thesis_id", "recommendation", "created_at"])
    thesis_reviews_support = _schema_table_support("thesis_reviews", ["thesis_id"])
    thesis_events_support = _schema_table_support("thesis_events", ["thesis_id", "created_at"])

    if theses_support["available"] and not theses_support["missing_columns"]:
        thesis_df = fetch_dataframe(
            "SELECT id, company_name, ticker, status, created_at FROM theses WHERE id = ?",
            (thesis_id,),
        )
        if not thesis_df.empty:
            base = thesis_df.iloc[0]
            snapshot.update(
                {
                    "thesis_id": _safe_int(base.get("id")),
                    "company_name": format_display_value(base.get("company_name"), fallback="—"),
                    "ticker": format_display_value(base.get("ticker"), fallback="—"),
                    "status": format_display_value(base.get("status"), fallback="—"),
                    "created_at": format_display_value(base.get("created_at"), fallback="—"),
                }
            )
        else:
            snapshot.update(
                {
                    "company_name": "thesis_id=14 not found in theses.",
                    "ticker": "—",
                    "status": "—",
                    "created_at": "—",
                }
            )

    if decision_logs_support["available"] and not decision_logs_support["missing_columns"]:
        decision_count_df = fetch_dataframe(
            "SELECT COUNT(*) AS decision_count FROM decision_logs WHERE thesis_id = ?",
            (thesis_id,),
        )
        decision_latest_df = fetch_dataframe(
            """
            SELECT recommendation
            FROM decision_logs
            WHERE thesis_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (thesis_id,),
        )
        snapshot["decision_log_count"] = _safe_int(decision_count_df.iloc[0]["decision_count"]) if not decision_count_df.empty else 0
        snapshot["decision_recommendation"] = (
            format_display_value(decision_latest_df.iloc[0].get("recommendation"), fallback="—")
            if not decision_latest_df.empty
            else "—"
        )

    if thesis_reviews_support["available"] and not thesis_reviews_support["missing_columns"]:
        review_count_df = fetch_dataframe(
            "SELECT COUNT(*) AS review_count FROM thesis_reviews WHERE thesis_id = ?",
            (thesis_id,),
        )
        snapshot["thesis_review_count"] = _safe_int(review_count_df.iloc[0]["review_count"]) if not review_count_df.empty else 0

    if thesis_events_support["available"] and not thesis_events_support["missing_columns"]:
        event_stats_df = fetch_dataframe(
            "SELECT COUNT(*) AS event_count, MAX(created_at) AS latest_event_at FROM thesis_events WHERE thesis_id = ?",
            (thesis_id,),
        )
        snapshot["thesis_event_count"] = _safe_int(event_stats_df.iloc[0]["event_count"]) if not event_stats_df.empty else 0
        snapshot["latest_event_timestamp"] = (
            format_display_value(event_stats_df.iloc[0].get("latest_event_at"), fallback="—")
            if not event_stats_df.empty
            else "—"
        )

    return snapshot


def get_microsoft_evidence_pipeline_status(thesis_id=MICROSOFT_READINESS_SOURCE_THESIS_ID):
    """Return schema-aware evidence pipeline counts for Microsoft readiness board."""
    support = {
        "evidence_staging": _schema_table_support("evidence_staging", ["thesis_id", "intake_status", "review_date", "promoted_at"]),
        "evidence_items": _schema_table_support("evidence_items", ["thesis_id"]),
        "evidence_observations": _schema_table_support("evidence_observations", ["id", "created_at"]),
        "thesis_events": _schema_table_support("thesis_events", ["thesis_id", "event_type"]),
    }

    rows = []

    if support["evidence_staging"]["available"] and not support["evidence_staging"]["missing_columns"]:
        staging_df = fetch_dataframe(
            """
            SELECT
                SUM(CASE WHEN intake_status = 'Pending' THEN 1 ELSE 0 END) AS staged_count,
                SUM(CASE WHEN review_date IS NOT NULL AND TRIM(review_date) <> '' THEN 1 ELSE 0 END) AS reviewed_count,
                SUM(CASE WHEN promoted_at IS NOT NULL AND TRIM(promoted_at) <> '' THEN 1 ELSE 0 END) AS promoted_count
            FROM evidence_staging
            WHERE thesis_id = ?
            """,
            (thesis_id,),
        )
        staging_row = staging_df.iloc[0] if not staging_df.empty else {}
        rows.append({"Metric": "Evidence staged", "Value": _safe_int(staging_row.get("staged_count")), "Source": "evidence_staging"})
        rows.append({"Metric": "Evidence reviewed", "Value": _safe_int(staging_row.get("reviewed_count")), "Source": "evidence_staging"})
        rows.append({"Metric": "Evidence promoted", "Value": _safe_int(staging_row.get("promoted_count")), "Source": "evidence_staging"})
    elif support["thesis_events"]["available"] and not support["thesis_events"]["missing_columns"]:
        event_df = fetch_dataframe(
            """
            SELECT
                SUM(CASE WHEN event_type = 'Evidence Staged' THEN 1 ELSE 0 END) AS staged_count,
                SUM(CASE WHEN event_type = 'Evidence Reviewed' THEN 1 ELSE 0 END) AS reviewed_count,
                SUM(CASE WHEN event_type = 'Evidence Promoted' THEN 1 ELSE 0 END) AS promoted_count
            FROM thesis_events
            WHERE thesis_id = ?
            """,
            (thesis_id,),
        )
        event_row = event_df.iloc[0] if not event_df.empty else {}
        rows.append({"Metric": "Evidence staged", "Value": _safe_int(event_row.get("staged_count")), "Source": "Derived from thesis_events"})
        rows.append({"Metric": "Evidence reviewed", "Value": _safe_int(event_row.get("reviewed_count")), "Source": "Derived from thesis_events"})
        rows.append({"Metric": "Evidence promoted", "Value": _safe_int(event_row.get("promoted_count")), "Source": "Derived from thesis_events"})
    else:
        rows.append({"Metric": "Evidence staged", "Value": "Not available from current runtime schema.", "Source": "Unavailable"})
        rows.append({"Metric": "Evidence reviewed", "Value": "Not available from current runtime schema.", "Source": "Unavailable"})
        rows.append({"Metric": "Evidence promoted", "Value": "Not available from current runtime schema.", "Source": "Unavailable"})

    if support["evidence_items"]["available"] and not support["evidence_items"]["missing_columns"]:
        evidence_items_df = fetch_dataframe(
            "SELECT COUNT(*) AS item_count FROM evidence_items WHERE thesis_id = ?",
            (thesis_id,),
        )
        rows.append({"Metric": "Evidence added/attached", "Value": _safe_int(evidence_items_df.iloc[0].get("item_count")) if not evidence_items_df.empty else 0, "Source": "evidence_items"})
    else:
        rows.append({"Metric": "Evidence added/attached", "Value": "Not available from current runtime schema.", "Source": "Unavailable"})

    if support["thesis_events"]["available"] and not support["thesis_events"]["missing_columns"]:
        observation_events_df = fetch_dataframe(
            """
            SELECT
                SUM(CASE WHEN event_type = 'Evidence Observation Created' THEN 1 ELSE 0 END) AS created_count,
                SUM(CASE WHEN event_type = 'Evidence Observation Updated' THEN 1 ELSE 0 END) AS updated_count
            FROM thesis_events
            WHERE thesis_id = ?
            """,
            (thesis_id,),
        )
        obs_row = observation_events_df.iloc[0] if not observation_events_df.empty else {}
        rows.append({"Metric": "Evidence observations created", "Value": _safe_int(obs_row.get("created_count")), "Source": "Derived from thesis_events"})
        rows.append({"Metric": "Evidence observations updated", "Value": _safe_int(obs_row.get("updated_count")), "Source": "Derived from thesis_events"})
    else:
        rows.append({"Metric": "Evidence observations created", "Value": "Not available from current runtime schema.", "Source": "Unavailable"})
        rows.append({"Metric": "Evidence observations updated", "Value": "Not available from current runtime schema.", "Source": "Unavailable"})

    return pd.DataFrame(rows), support


def get_microsoft_pillar_coverage_matrix(thesis_id=MICROSOFT_READINESS_SOURCE_THESIS_ID):
    """Return pillar-level coverage with explicit Not available markers when schema is missing."""
    score_support = _schema_table_support("pillar_scores", ["thesis_id", "pillar_id", "pillar_name", "score_rationale", "inference", "judgment"])
    obs_support = _schema_table_support("evidence_observations", ["evidence_item_id", "pillar_id", "id"])
    items_support = _schema_table_support("evidence_items", ["id", "thesis_id"])
    links_support = _schema_table_support("pillar_evidence_links", ["pillar_score_id", "evidence_item_id"])

    evidence_link_verification_available = (
        links_support["available"]
        and not links_support["missing_columns"]
        and score_support["available"]
        and not score_support["missing_columns"]
    )
    observation_verification_available = (
        obs_support["available"]
        and not obs_support["missing_columns"]
        and items_support["available"]
        and not items_support["missing_columns"]
    )
    direct_verification_available = (
        evidence_link_verification_available
        or observation_verification_available
    )

    score_df = pd.DataFrame()
    if score_support["available"] and not score_support["missing_columns"]:
        score_df = fetch_dataframe(
            """
            SELECT
                pillar_id,
                MAX(COALESCE(NULLIF(TRIM(pillar_name), ''), '')) AS pillar_name,
                COUNT(*) AS score_rows,
                MAX(CASE WHEN COALESCE(NULLIF(TRIM(score_rationale), ''), NULLIF(TRIM(inference), ''), NULLIF(TRIM(judgment), '')) IS NOT NULL THEN 1 ELSE 0 END) AS has_assessment_narrative
            FROM pillar_scores
            WHERE thesis_id = ?
            GROUP BY pillar_id
            """,
            (thesis_id,),
        )

    observation_df = pd.DataFrame()
    if observation_verification_available:
        observation_df = fetch_dataframe(
            """
            SELECT eo.pillar_id, COUNT(*) AS observation_count
            FROM evidence_observations eo
            JOIN evidence_items ei ON ei.id = eo.evidence_item_id
            WHERE ei.thesis_id = ?
            GROUP BY eo.pillar_id
            """,
            (thesis_id,),
        )

    evidence_link_df = pd.DataFrame()
    if evidence_link_verification_available:
        evidence_link_df = fetch_dataframe(
            """
            SELECT ps.pillar_id, COUNT(DISTINCT pel.evidence_item_id) AS evidence_count
            FROM pillar_evidence_links pel
            JOIN pillar_scores ps ON ps.id = pel.pillar_score_id
            WHERE ps.thesis_id = ?
            GROUP BY ps.pillar_id
            """,
            (thesis_id,),
        )

    score_map = {str(row["pillar_id"]): row for _, row in score_df.iterrows()} if not score_df.empty else {}
    obs_map = {str(row["pillar_id"]): _safe_int(row.get("observation_count")) for _, row in observation_df.iterrows()} if not observation_df.empty else {}
    evidence_map = {str(row["pillar_id"]): _safe_int(row.get("evidence_count")) for _, row in evidence_link_df.iterrows()} if not evidence_link_df.empty else {}

    matrix_rows = []
    for pillar_id, default_name in MICROSOFT_BUSINESS_PILLARS + MICROSOFT_INVESTMENT_PILLARS:
        score_row = score_map.get(pillar_id)
        score_present = bool(score_row is not None and _safe_int(score_row.get("score_rows")) > 0)
        narrative_present = bool(score_row is not None and _safe_int(score_row.get("has_assessment_narrative")) == 1)
        evidence_count = (
            evidence_map.get(pillar_id, 0)
            if evidence_link_verification_available
            else None
        )
        observation_count = (
            obs_map.get(pillar_id, 0)
            if observation_verification_available
            else None
        )

        direct_support_count = (evidence_count or 0) + (observation_count or 0)

        if not direct_verification_available:
            basis = "Unavailable due to schema"
        elif direct_support_count > 0:
            basis = "Direct evidence metadata"
        elif score_present or narrative_present:
            basis = "Assessment data only"
        else:
            basis = "No verifiable runtime support"

        if not direct_verification_available:
            status = "Needs Review"
        elif direct_support_count > 0 and score_present and narrative_present:
            status = "Covered"
        elif direct_support_count > 0:
            status = "Partial"
        elif score_present or narrative_present:
            status = "Needs Review"
        else:
            status = "Missing"

        matrix_rows.append(
            {
                "pillar_id": pillar_id,
                "pillar_name": format_display_value(score_row.get("pillar_name"), fallback=default_name) if score_row is not None else default_name,
                "evidence_count": evidence_count if evidence_count is not None else "Not available",
                "observation_count": observation_count if observation_count is not None else "Not available",
                "pillar_score_present": "Yes" if score_present else "No",
                "assessment_narrative_present": "Yes" if narrative_present else "No" if score_present else "Not available",
                "basis": basis,
                "status": status,
            }
        )

    support = {
        "pillar_scores": score_support,
        "evidence_observations": obs_support,
        "evidence_items": items_support,
        "pillar_evidence_links": links_support,
    }
    return pd.DataFrame(matrix_rows), support


def get_microsoft_period_coverage(thesis_id=MICROSOFT_READINESS_SOURCE_THESIS_ID):
    """Return year/period coverage with explicit distinction of metadata types."""
    evidence_support = _schema_table_support("evidence_items", ["thesis_id", "publication_date", "created_at"])
    decision_support = _schema_table_support("decision_logs", ["thesis_id", "review_date", "created_at"])

    evidence_period_years = []
    ingestion_years = []
    if evidence_support["available"] and not evidence_support["missing_columns"]:
        evidence_period_df = fetch_dataframe(
            "SELECT publication_date, created_at FROM evidence_items WHERE thesis_id = ?",
            (thesis_id,),
        )
        if not evidence_period_df.empty:
            evidence_period_years = sorted({year for year in evidence_period_df["publication_date"].apply(_as_year_text).tolist() if year})
            ingestion_years = sorted({year for year in evidence_period_df["created_at"].apply(_as_year_text).tolist() if year})

    review_years = []
    decision_years = []
    if decision_support["available"] and not decision_support["missing_columns"]:
        decision_df = fetch_dataframe(
            "SELECT review_date, created_at FROM decision_logs WHERE thesis_id = ?",
            (thesis_id,),
        )
        if not decision_df.empty:
            review_years = sorted({year for year in decision_df["review_date"].apply(_as_year_text).tolist() if year})
            decision_years = sorted({year for year in decision_df["created_at"].apply(_as_year_text).tolist() if year})

    can_verify_year_coverage = bool(evidence_period_years)
    period_rows = [
        {
            "Category": "Evidence period / filing period",
            "Years": ", ".join(evidence_period_years) if evidence_period_years else "Year coverage cannot be verified from current runtime metadata.",
            "Notes": "Derived from evidence_items.publication_date when available.",
        },
        {
            "Category": "Athena ingestion timestamp",
            "Years": ", ".join(ingestion_years) if ingestion_years else "Not available from current runtime schema.",
            "Notes": "Derived from evidence_items.created_at; ingestion time only.",
        },
        {
            "Category": "Review date",
            "Years": ", ".join(review_years) if review_years else "Not available from current runtime schema.",
            "Notes": "Derived from decision_logs.review_date.",
        },
        {
            "Category": "Decision date",
            "Years": ", ".join(decision_years) if decision_years else "Not available from current runtime schema.",
            "Notes": "Derived from decision_logs.created_at.",
        },
    ]

    return pd.DataFrame(period_rows), can_verify_year_coverage, {"evidence_items": evidence_support, "decision_logs": decision_support}


def _explorer_available_columns(table_name, preferred_columns):
    """Return available columns for a table from an ordered preferred list."""
    support = _schema_table_support(table_name)
    if not support["available"]:
        return [], support
    available = [column for column in preferred_columns if column in support["columns"]]
    return available, support


def _explorer_count_value(query, params=()):
    """Return integer count from a SELECT count query."""
    df = fetch_dataframe(query, params)
    if df.empty:
        return 0
    column_name = df.columns[0]
    return _safe_int(df.iloc[0].get(column_name))


def _render_explorer_dataset(
    section_label,
    description,
    dataframe,
    unavailable=False,
    empty_message="No rows found for this thesis.",
):
    """Render one read-only dataset expander for Data Explorer."""
    with st.expander(section_label, expanded=False):
        st.caption(description)
        if unavailable:
            st.info("Unavailable in schema.")
            return
        row_count = len(dataframe.index)
        st.caption(f"Row count: {row_count}")
        if dataframe.empty:
            st.info(empty_message)
            return
        st.dataframe(dataframe, use_container_width=True, hide_index=True)


def derive_asset_status_label(company_name, ticker, persisted_status, thesis_id=None, fallback="—"):
    """Map archived constitutional asset labels using explicit governed identity only."""
    persisted_text = _display_text(persisted_status)
    thesis_id_int = _to_int_thesis_id(thesis_id)

    if thesis_id_int in EXPLICIT_ARCHIVED_STATUS_LABELS:
        return EXPLICIT_ARCHIVED_STATUS_LABELS[thesis_id_int]

    return persisted_text if persisted_text else fallback


def derive_decision_label(row):
    """Return governed decision label without creating new governed outcomes."""
    recommendation = _display_text((row or {}).get("recommendation"))
    if not recommendation:
        return "NO DECISION"
    return recommendation.upper()


def derive_confidence_display(row):
    """Return confidence from existing persisted fields only."""
    candidate_keys = [
        "decision_confidence",
        "confidence",
        "confidence_percent",
        "confidence_pct",
        "confidence_label",
        "inference_confidence",
    ]
    for key in candidate_keys:
        raw_value = (row or {}).get(key)
        if raw_value is None:
            continue
        if isinstance(raw_value, (int, float)):
            numeric_value = float(raw_value)
            if numeric_value <= 1.0:
                numeric_value *= 100.0
            if 0.0 <= numeric_value <= 100.0:
                return f"{numeric_value:.0f}%"
            continue

        text = str(raw_value).strip()
        if not text:
            continue
        try:
            numeric_value = float(text)
            if numeric_value <= 1.0:
                numeric_value *= 100.0
            if 0.0 <= numeric_value <= 100.0:
                return f"{numeric_value:.0f}%"
        except ValueError:
            return text
    return "Not available"


def derive_home_health(row):
    """Build a Home-only health summary without modifying governed state."""
    recommendation = _display_text((row or {}).get("recommendation")).lower()
    avg_score = (row or {}).get("avg_score")
    completed_ratio = float((row or {}).get("completion_ratio") or 0.0)

    risky_terms = {"avoid", "sell", "reduce", "high risk"}
    mixed_terms = {"observe", "hold", "watch"}
    strong_terms = {"buy", "ready", "high conviction", "ready with conditions", "buy with conditions"}

    if not recommendation:
        if completed_ratio < 0.25:
            return "No Decision"
        return "Mixed"

    if recommendation in risky_terms:
        if recommendation in {"avoid", "sell", "high risk"}:
            return "High Risk"
        return "Weak Candidate"

    if recommendation in mixed_terms:
        return "Mixed"

    if recommendation in strong_terms:
        if isinstance(avg_score, (int, float)) and float(avg_score) >= 7.0 and completed_ratio >= 0.7:
            return "Strong Candidate"
        return "Mixed"

    return "Mixed"


def derive_health_bucket(row):
    """Alias for portfolio summary bucketing."""
    return derive_home_health(row)


def derive_lifecycle_display(row):
    """Derive lifecycle from existing workflow and governed readiness state."""
    if bool((row or {}).get("framework_review_eligible")):
        return "Framework Review"

    has_decision = bool((row or {}).get("has_decision"))
    if has_decision and bool((row or {}).get("has_review_record")):
        return "Historical Review"

    prep_readiness = _display_text((row or {}).get("prep_readiness")).lower()
    prep_lifecycle = _display_text((row or {}).get("prep_lifecycle")).lower()
    if prep_readiness in {"pending", "preparing"} or prep_lifecycle in {"preparing", "thesis_ready"}:
        return "Preparation"

    if bool((row or {}).get("decision_eligible")) or has_decision:
        return "Decision"

    return "Assessment"


def derive_next_action_display(row):
    """Provide one clear analyst next action from existing persisted state."""
    if bool((row or {}).get("framework_review_eligible")):
        return "Framework Review Consideration Eligible"

    if bool((row or {}).get("has_decision")) and bool((row or {}).get("review_due")):
        return "Review Historical Outcome"

    if bool((row or {}).get("decision_eligible")) and not bool((row or {}).get("has_decision")):
        return "Record Decision"

    prep_readiness = _display_text((row or {}).get("prep_readiness")).lower()
    discovery_status = _display_text((row or {}).get("evidence_discovery_status")).lower()
    acquisition_status = _display_text((row or {}).get("evidence_acquisition_status")).lower()
    extraction_status = _display_text((row or {}).get("extraction_status")).lower()

    if prep_readiness in {"pending", "preparing"}:
        if discovery_status in {"pending", "preparing"}:
            return "Evidence Discovery"
        if acquisition_status in {"pending", "preparing"}:
            return "Evidence Acquisition"
        if extraction_status in {"pending", "preparing"}:
            return "Continue Evaluation"

    business_completed = int((row or {}).get("business_completed") or 0)
    investment_completed = int((row or {}).get("investment_completed") or 0)
    if business_completed < 7:
        return "Complete Business Assessment"
    if investment_completed < 4:
        return "Continue Evaluation"

    return "Continue Evaluation"


def render_company_logo_placeholder(company_name, ticker=None, thesis_id=None):
    """Render internal placeholder identifier blocks for Home cards."""
    ticker_text = _display_text(ticker).upper()
    company_text = _display_text(company_name)
    initials = "".join(word[0] for word in company_text.split()[:4] if word)[:4].upper()
    label = ticker_text if ticker_text else (initials if initials else "ATH")

    thesis_id_int = _to_int_thesis_id(thesis_id)

    # Archived visual styling requires explicit governed identity.
    # Do not infer archival status from company name or ticker alone.
    archived_visual_thesis_ids = set(EXPLICIT_ARCHIVED_STATUS_LABELS.keys())

    palette_class = "home-logo-generic"
    if thesis_id_int in archived_visual_thesis_ids:
        palette_class = "home-logo-archived"
    elif ticker_text == "QCOM" or "qualcomm" in company_text.lower():
        palette_class = "home-logo-qcom"

    st.markdown(
        f"<div class='home-logo-block {palette_class}'>{label}</div>",
        unsafe_allow_html=True,
    )


def render_home_evaluation_card(row, button_key):
    """Render one Needs Attention card and return True if Continue clicked."""
    health_value = derive_health_bucket(row)
    health_class = {
        "Strong Candidate": "health-strong",
        "Mixed": "health-mixed",
        "Weak Candidate": "health-weak",
        "High Risk": "health-risk",
        "No Decision": "health-none",
    }.get(health_value, "health-none")

    decision_label = derive_decision_label(row)
    confidence_text = derive_confidence_display(row)
    lifecycle_text = derive_lifecycle_display(row)
    next_action_text = derive_next_action_display(row)
    recommendation_text = format_display_value((row or {}).get("recommendation"), fallback="Not available")
    health_score = (row or {}).get("avg_score")
    health_score_text = f"{float(health_score):.1f} / 10" if isinstance(health_score, (int, float)) else "Not available"

    with st.container(border=True):
        c_logo, c_body, c_cta = st.columns([1.1, 5.2, 1.4])
        with c_logo:
            render_company_logo_placeholder(
                (row or {}).get("company_name"),
                (row or {}).get("ticker"),
                thesis_id=(row or {}).get("thesis_id"),
            )
        with c_body:
            st.markdown(
                f"<div class='home-card-company'>{format_display_value((row or {}).get('company_name'))}</div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"<div class='home-card-ticker'>{format_display_value((row or {}).get('ticker'))}</div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"<span class='home-chip {health_class}'>Investment Health: {health_value}</span> "
                f"<span class='home-chip home-chip-muted'>Health Score: {health_score_text}</span>",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"<div class='home-card-primary-decision'>{decision_label}</div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"<div class='home-card-detail'>Recommendation Status: {recommendation_text}</div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"<div class='home-card-detail'>Confidence: {confidence_text} | Lifecycle: {lifecycle_text}</div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"<div class='home-card-next-action'>Next action: {next_action_text}</div>",
                unsafe_allow_html=True,
            )
        with c_cta:
            return st.button("Continue", key=button_key, use_container_width=True)
    return False


def render_current_evaluation_panel(row):
    """Render focused panel for one active/current evaluation."""
    if not isinstance(row, dict):
        empty_state("No current evaluation selected.")
        return False

    decision_recorded = "Decision Recorded" if bool(row.get("has_decision")) else "Decision Not Recorded"
    review_status = "Ready for Historical Review" if bool(row.get("has_decision")) else "Assessment In Progress"
    lifecycle_text = derive_lifecycle_display(row)
    next_action_text = derive_next_action_display(row)

    with st.container(border=True):
        col_logo, col_info, col_action = st.columns([1.1, 5.4, 1.5])
        with col_logo:
            render_company_logo_placeholder(
                row.get("company_name"),
                row.get("ticker"),
                thesis_id=row.get("thesis_id"),
            )
        with col_info:
            st.markdown(
                f"<div class='home-card-company'>{format_display_value(row.get('company_name'))}</div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"<span class='home-chip home-chip-muted'>{decision_recorded}</span> "
                f"<span class='home-chip home-chip-muted'>{review_status}</span>",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"<div class='home-card-detail'>Decision: {derive_decision_label(row)} | Confidence: {derive_confidence_display(row)}</div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"<div class='home-card-detail'>Lifecycle: {lifecycle_text}</div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"<div class='home-card-next-action'>Next action: {next_action_text}</div>",
                unsafe_allow_html=True,
            )
        with col_action:
            return st.button("Continue Evaluation", key=f"current_eval_continue_{int(row.get('thesis_id'))}", use_container_width=True)
    return False


def render_home_sidebar_panels(rows):
    """Render Home right-rail summary panels."""
    rows = rows or []
    health_counts = {
        "Strong Candidate": 0,
        "Mixed": 0,
        "Weak Candidate": 0,
        "High Risk": 0,
        "No Decision": 0,
    }
    lifecycle_counts = {
        "Preparation": 0,
        "Assessment": 0,
        "Decision": 0,
        "Historical Review": 0,
        "Framework Review": 0,
    }

    for row in rows:
        health_counts[derive_health_bucket(row)] = health_counts.get(derive_health_bucket(row), 0) + 1
        lifecycle_name = derive_lifecycle_display(row)
        lifecycle_counts[lifecycle_name] = lifecycle_counts.get(lifecycle_name, 0) + 1

    def _render_summary_card(title, total_label, total_value, segments):
        total_value = int(total_value)
        if total_value <= 0:
            total_value = 0

        start_angle = 0.0
        gradient_parts = []
        for segment in segments:
            value = int(segment["value"])
            if total_value > 0 and value > 0:
                span = 360.0 * (value / total_value)
                end_angle = start_angle + span
                gradient_parts.append(f"{segment['color']} {start_angle:.2f}deg {end_angle:.2f}deg")
                start_angle = end_angle
        if not gradient_parts:
            gradient_parts = ["#2A3348 0deg 360deg"]

        legend_html = "".join(
            f"<div class='home-summary-legend-row'><span class='home-summary-swatch' style='background:{segment['color']};'></span><span>{segment['label']}</span><span>{segment['value']}</span><span>{segment['pct']}</span></div>"
            for segment in segments
        )

        st.markdown(
            f"""
            <div class='home-summary-card'>
              <div class='home-summary-title'>{title}</div>
              <div class='home-summary-body'>
                <div class='home-summary-donut' style='background: conic-gradient({', '.join(gradient_parts)});'>
                  <div class='home-summary-donut-inner'>
                    <div class='home-summary-donut-value'>{total_value}</div>
                    <div class='home-summary-donut-label'>{total_label}</div>
                  </div>
                </div>
                <div class='home-summary-legend'>
                  {legend_html}
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with st.container(border=True):
        _render_summary_card(
            "Portfolio Health (Summary)",
            "Evaluations",
            len(rows),
            [
                {"label": "Strong", "value": health_counts.get("Strong Candidate", 0), "pct": f"{(health_counts.get('Strong Candidate', 0) / len(rows) * 100):.0f}%" if rows else "0%", "color": "#56C267"},
                {"label": "Mixed", "value": health_counts.get("Mixed", 0), "pct": f"{(health_counts.get('Mixed', 0) / len(rows) * 100):.0f}%" if rows else "0%", "color": "#F0C14A"},
                {"label": "Weak", "value": health_counts.get("Weak Candidate", 0), "pct": f"{(health_counts.get('Weak Candidate', 0) / len(rows) * 100):.0f}%" if rows else "0%", "color": "#FF7272"},
                {"label": "High Risk", "value": health_counts.get("High Risk", 0), "pct": f"{(health_counts.get('High Risk', 0) / len(rows) * 100):.0f}%" if rows else "0%", "color": "#FF4F4F"},
                {"label": "No Decision", "value": health_counts.get("No Decision", 0), "pct": f"{(health_counts.get('No Decision', 0) / len(rows) * 100):.0f}%" if rows else "0%", "color": "#6B7280"},
            ],
        )

    with st.container(border=True):
        _render_summary_card(
            "Pipeline by Lifecycle",
            "Evaluations",
            len(rows),
            [
                {"label": "Preparation", "value": lifecycle_counts.get("Preparation", 0), "pct": f"{(lifecycle_counts.get('Preparation', 0) / len(rows) * 100):.0f}%" if rows else "0%", "color": "#6B7280"},
                {"label": "Assessment", "value": lifecycle_counts.get("Assessment", 0), "pct": f"{(lifecycle_counts.get('Assessment', 0) / len(rows) * 100):.0f}%" if rows else "0%", "color": "#56C267"},
                {"label": "Decision", "value": lifecycle_counts.get("Decision", 0), "pct": f"{(lifecycle_counts.get('Decision', 0) / len(rows) * 100):.0f}%" if rows else "0%", "color": "#F0C14A"},
                {"label": "Historical Review", "value": lifecycle_counts.get("Historical Review", 0), "pct": f"{(lifecycle_counts.get('Historical Review', 0) / len(rows) * 100):.0f}%" if rows else "0%", "color": "#8B5CF6"},
                {"label": "Framework Review", "value": lifecycle_counts.get("Framework Review", 0), "pct": f"{(lifecycle_counts.get('Framework Review', 0) / len(rows) * 100):.0f}%" if rows else "0%", "color": "#FF4F4F"},
            ],
        )


# Sidebar navigation
with st.sidebar:
    current_view = st.session_state.get("current_view", "Home")

    _render_sidebar_styles()
    render_sidebar_brand()
    st.divider()
    render_sidebar_primary_navigation(current_view)
    st.divider()
    if st.button("New Evaluation", key="sidebar_new_evaluation", use_container_width=True):
        st.session_state["current_view"] = "New Thesis"
        st.session_state["selected_thesis_id"] = None
        st.rerun()
    st.caption(f"Runtime DB Path: {DATABASE_FILE}")
    st.markdown(
        f"<div style='margin-top:0.8rem; color:#8D95A8; font-size:0.78rem; line-height:1.4;'>{ATHENA_SIDEBAR_VERSION_TEXT}<br/>{ATHENA_SIDEBAR_FOOTER_TEXT}</div>",
        unsafe_allow_html=True,
    )

_capture_navigation_event()

review_presence_df = fetch_dataframe("SELECT DISTINCT thesis_id FROM thesis_reviews")
reviewed_ids = set(review_presence_df["thesis_id"].astype(int).tolist()) if not review_presence_df.empty else set()

framework_eligible_df = fetch_dataframe(
    """
    SELECT DISTINCT thesis_id
    FROM thesis_reviews
    WHERE framework_review_eligible = 1
    """
)
framework_eligible_ids = set(framework_eligible_df["thesis_id"].astype(int).tolist()) if not framework_eligible_df.empty else set()

# Main content area
if st.session_state['current_view'] in ['Home', 'Dashboard']:

    theses_df = fetch_dataframe(
        """
        SELECT id, company_name, ticker, status
        FROM theses
        ORDER BY company_name ASC
        """
    )

    latest_decision_df = fetch_dataframe(
        """
        SELECT d1.*
        FROM decision_logs d1
        JOIN (
            SELECT thesis_id, MAX(id) AS max_id
            FROM decision_logs
            GROUP BY thesis_id
        ) latest
            ON latest.thesis_id = d1.thesis_id
           AND latest.max_id = d1.id
        """
    )

    if latest_decision_df.empty:
        latest_decision_by_thesis_id = {}
    else:
        latest_decision_by_thesis_id = {
            int(row["thesis_id"]): row
            for _, row in latest_decision_df.iterrows()
        }

    business_score_df = fetch_dataframe(
        """
        SELECT thesis_id, ROUND(AVG(score), 1) AS avg_business_score
        FROM pillar_scores
        WHERE pillar_id LIKE 'B%' AND score IS NOT NULL
        GROUP BY thesis_id
        """
    )
    business_score_by_thesis_id = {
        int(row["thesis_id"]): float(row["avg_business_score"])
        for _, row in business_score_df.iterrows()
    }

    investment_score_df = fetch_dataframe(
        """
        SELECT thesis_id, ROUND(AVG(score), 1) AS avg_investment_score
        FROM pillar_scores
        WHERE pillar_id LIKE 'I%' AND score IS NOT NULL
        GROUP BY thesis_id
        """
    )
    investment_score_by_thesis_id = {
        int(row["thesis_id"]): float(row["avg_investment_score"])
        for _, row in investment_score_df.iterrows()
    }

    framework_eligible_df = fetch_dataframe(
        """
        SELECT DISTINCT thesis_id
        FROM thesis_reviews
        WHERE framework_review_eligible = 1
        """
    )
    framework_eligible_ids = set(framework_eligible_df["thesis_id"].astype(int).tolist()) if not framework_eligible_df.empty else set()

    # Build once and reuse across sections.
    gate_results_by_thesis_id = {}
    for _, thesis_row in theses_df.iterrows():
        tid = int(thesis_row["id"])
        gate_results_by_thesis_id[tid] = validate_decision_gate(tid)

    latest_prep_by_thesis_id = _fetch_latest_preparation_status_by_thesis()
    latest_engine_status = st.session_state.get("engine_preparation_status")
    if isinstance(latest_engine_status, dict) and latest_engine_status.get("thesis_id") is not None:
        latest_prep_by_thesis_id[int(latest_engine_status["thesis_id"])] = latest_engine_status

    readiness_by_thesis_id = {}
    for thesis_id, prep_status in latest_prep_by_thesis_id.items():
        readiness_by_thesis_id[int(thesis_id)] = str(prep_status.get("readiness_status", "pending")).strip()

    today_date = datetime.now().date()

    def get_priority_and_reason(thesis_id):
        latest_decision_row = latest_decision_by_thesis_id.get(thesis_id)
        gate_result = gate_results_by_thesis_id[thesis_id]

        if thesis_id in framework_eligible_ids:
            return 1, "Framework Review Consideration Eligible"

        if latest_decision_row is not None and pd.notna(latest_decision_row["next_review_date"]):
            next_review_date = pd.to_datetime(latest_decision_row["next_review_date"]).date()
            if next_review_date < today_date:
                return 2, "Next review date past due"

        if latest_decision_row is None:
            return 3, "No decision recorded"

        if not gate_result["eligible"]:
            return 4, "Governance gate incomplete"

        return None, "—"

    active_theses_count = int(
        theses_df[theses_df["status"].fillna("") != STATUS_CLOSED]["id"].count()
    )
    decision_eligible_count = sum(
        1 for gate_result in gate_results_by_thesis_id.values() if gate_result["eligible"]
    )

    needs_review_count = 0
    for _, decision_row in latest_decision_df.iterrows():
        if pd.notna(decision_row["next_review_date"]):
            if pd.to_datetime(decision_row["next_review_date"]).date() < today_date:
                needs_review_count += 1

    framework_review_eligible_count = len(framework_eligible_ids)

    portfolio_rows = []
    for _, thesis_row in theses_df.iterrows():
        tid = int(thesis_row["id"])
        latest_decision_row = latest_decision_by_thesis_id.get(tid)
        priority_value, reason_text = get_priority_and_reason(tid)
        action_required = reason_text if priority_value is not None else "—"

        recommendation_value = "—"
        next_review_value = "—"
        if latest_decision_row is not None:
            recommendation_value = latest_decision_row["recommendation"] if pd.notna(latest_decision_row["recommendation"]) and str(latest_decision_row["recommendation"]).strip() else "—"
            next_review_value = latest_decision_row["next_review_date"] if pd.notna(latest_decision_row["next_review_date"]) and str(latest_decision_row["next_review_date"]).strip() else "—"

        business_score_value = "—"
        if tid in business_score_by_thesis_id:
            business_score_value = f"{business_score_by_thesis_id[tid]:.1f}"

        investment_score_value = "—"
        if tid in investment_score_by_thesis_id:
            investment_score_value = f"{investment_score_by_thesis_id[tid]:.1f}"

        portfolio_rows.append(
            {
                "thesis_id": tid,
                "Company": thesis_row["company_name"],
                "Ticker": thesis_row["ticker"] if pd.notna(thesis_row["ticker"]) and str(thesis_row["ticker"]).strip() else "—",
                "Status": derive_asset_status_label(
                    thesis_row["company_name"],
                    thesis_row["ticker"],
                    thesis_row["status"],
                    thesis_id=tid,
                    fallback="—",
                ),
                "Recommendation": recommendation_value,
                "Business Score": business_score_value,
                "Investment Score": investment_score_value,
                "Next Review": next_review_value,
                "Action Required": action_required,
            }
        )

    watchlist_rows = []
    for _, thesis_row in theses_df.iterrows():
        tid = int(thesis_row["id"])
        priority_value, reason_text = get_priority_and_reason(tid)
        if priority_value is None:
            continue

        watchlist_rows.append(
            {
                "thesis_id": tid,
                "Priority": priority_value,
                "Company": thesis_row["company_name"],
                "Ticker": thesis_row["ticker"] if pd.notna(thesis_row["ticker"]) and str(thesis_row["ticker"]).strip() else "—",
                "Action Required": reason_text,
                "Reason": reason_text,
            }
        )

    hero_thesis_id = st.session_state.get("selected_thesis_id")
    if hero_thesis_id is None:
        if portfolio_rows:
            hero_thesis_id = int(portfolio_rows[0]["thesis_id"])
        elif watchlist_rows:
            hero_thesis_id = int(watchlist_rows[0]["thesis_id"])

    hero_thesis_data = None
    if hero_thesis_id is not None:
        hero_match = theses_df[theses_df["id"] == hero_thesis_id]
        if not hero_match.empty:
            hero_row = hero_match.iloc[0]
            hero_latest_decision = latest_decision_by_thesis_id.get(int(hero_thesis_id))
            hero_gate = gate_results_by_thesis_id.get(int(hero_thesis_id), {"completed": 0, "required": 11})
            hero_descriptor = "—"
            if pd.notna(hero_row["status"]) and str(hero_row["status"]).strip():
                hero_descriptor = str(hero_row["status"]).strip()
            else:
                hero_descriptor = _active_thesis_descriptor(hero_row)

            hero_business_score = "—"
            if int(hero_thesis_id) in business_score_by_thesis_id:
                hero_business_score = f"{business_score_by_thesis_id[int(hero_thesis_id)]:.1f}"

            hero_investment_score = "—"
            if int(hero_thesis_id) in investment_score_by_thesis_id:
                hero_investment_score = f"{investment_score_by_thesis_id[int(hero_thesis_id)]:.1f}"

            hero_recommendation = "NO DECISION"
            has_hero_decision = hero_latest_decision is not None
            if has_hero_decision and pd.notna(hero_latest_decision["recommendation"]) and str(hero_latest_decision["recommendation"]).strip():
                hero_recommendation = str(hero_latest_decision["recommendation"]).strip()

            assessment_completed = int(hero_gate.get("completed", 0))
            assessment_required = int(hero_gate.get("required", 11))
            assessment_pct = 0.0 if assessment_required == 0 else min(max(assessment_completed / assessment_required, 0.0), 1.0)

            hero_thesis_data = {
                "thesis_id": int(hero_thesis_id),
                "company_name": hero_row["company_name"],
                "descriptor": hero_descriptor,
                "recommendation": hero_recommendation,
                "has_decision": has_hero_decision,
                "business_score": hero_business_score,
                "investment_score": hero_investment_score,
                "assessment_progress": f"{assessment_completed} / {assessment_required}",
                "assessment_pct": assessment_pct,
                "decision_progress": "Recorded" if has_hero_decision else "Not Recorded",
                "decision_pct": 1.0 if has_hero_decision else 0.0,
            }

    watchlist_rows_sorted = sorted(
        watchlist_rows,
        key=lambda row: (row["Priority"], row["Company"]),
    )

    governance_rows = []
    for _, thesis_row in theses_df.iterrows():
        tid = int(thesis_row["id"])
        gate_result = gate_results_by_thesis_id[tid]
        latest_decision_row = latest_decision_by_thesis_id.get(tid)

        if gate_result["eligible"]:
            gate_status = "🟢 Eligible"
            gate_sort = 1
        else:
            gate_status = "🔴 Blocked"
            gate_sort = 0

        last_decision_date = "—"
        next_review_date = "—"
        if latest_decision_row is not None:
            if pd.notna(latest_decision_row["created_at"]) and str(latest_decision_row["created_at"]).strip():
                last_decision_date = str(latest_decision_row["created_at"])
            if pd.notna(latest_decision_row["next_review_date"]) and str(latest_decision_row["next_review_date"]).strip():
                next_review_date = str(latest_decision_row["next_review_date"])

        governance_rows.append(
            {
                "Company": thesis_row["company_name"],
                "Gate Status": gate_status,
                "Completed": f"{gate_result['completed']} / 11",
                "Last Decision Date": last_decision_date,
                "Next Review Date": next_review_date,
                "_gate_sort": gate_sort,
            }
        )

    governance_display_df = pd.DataFrame()
    if governance_rows:
        governance_df = pd.DataFrame(governance_rows).sort_values(
            by=["_gate_sort", "Company"],
            ascending=[True, True]
        )
        governance_display_df = governance_df[
            ["Company", "Gate Status", "Completed", "Last Decision Date", "Next Review Date"]
        ]

    outcome_distribution_df = fetch_dataframe(
        """
        SELECT outcome_attribution_type AS 'Outcome Type', COUNT(*) AS Count
        FROM thesis_reviews
        GROUP BY outcome_attribution_type
        ORDER BY outcome_attribution_type
        """
    )

    framework_theses_df = fetch_dataframe(
        """
        SELECT t.company_name AS Company, tr.review_horizon AS 'Review Horizon', tr.review_date AS 'Review Date'
        FROM thesis_reviews tr
        JOIN theses t ON t.id = tr.thesis_id
        WHERE tr.framework_review_eligible = 1
        ORDER BY t.company_name ASC, tr.review_date DESC
        """
    )

    watchlist_display_df = pd.DataFrame()
    if watchlist_rows_sorted:
        watchlist_df = pd.DataFrame(watchlist_rows_sorted).sort_values(
            by=["Priority", "Company"],
            ascending=[True, True]
        )
        watchlist_display_df = watchlist_df[["Priority", "Company", "Ticker", "Reason"]]

    total_reviews_df = fetch_dataframe(
        "SELECT COUNT(*) AS total_reviews FROM thesis_reviews"
    )
    total_reviews = int(total_reviews_df.iloc[0]["total_reviews"]) if not total_reviews_df.empty else 0

    if total_reviews < MNEMOSYNE_MINIMUM_REVIEW_VOLUME:
        mnemosyne_banner_mode = "Preliminary Observation"
    else:
        mnemosyne_banner_mode = "Observation Mode"

    mnemosyne_outcome_distribution_df = fetch_dataframe(
        """
        SELECT outcome_attribution_type,
               COUNT(*) AS review_count
        FROM thesis_reviews
        GROUP BY outcome_attribution_type
        ORDER BY outcome_attribution_type
        """
    )

    distribution_display_df = pd.DataFrame()
    if not mnemosyne_outcome_distribution_df.empty:
        distribution_display_rows = []
        for _, row in mnemosyne_outcome_distribution_df.iterrows():
            review_count = int(row["review_count"])
            percentage = 0.0 if total_reviews == 0 else (review_count / total_reviews) * 100.0
            distribution_display_rows.append(
                {
                    "Outcome Type": row["outcome_attribution_type"],
                    "Count": review_count,
                    "Percentage": f"{percentage:.1f}%",
                }
            )
        distribution_display_df = pd.DataFrame(distribution_display_rows)

    distinct_theses_df = fetch_dataframe(
        "SELECT COUNT(DISTINCT thesis_id) AS distinct_theses FROM thesis_reviews"
    )
    review_horizons_completed_df = fetch_dataframe(
        "SELECT COUNT(DISTINCT review_horizon) AS review_horizons_completed FROM thesis_reviews WHERE review_horizon IS NOT NULL"
    )
    framework_review_consideration_count_df = fetch_dataframe(
        "SELECT COUNT(*) AS framework_review_consideration_count FROM thesis_reviews WHERE framework_review_eligible = 1"
    )

    distinct_theses = int(distinct_theses_df.iloc[0]["distinct_theses"]) if not distinct_theses_df.empty else 0
    review_horizons_completed = int(review_horizons_completed_df.iloc[0]["review_horizons_completed"]) if not review_horizons_completed_df.empty else 0
    framework_review_consideration_count = int(framework_review_consideration_count_df.iloc[0]["framework_review_consideration_count"]) if not framework_review_consideration_count_df.empty else 0

    metric_tiles = [
        {"label": "Active Theses", "value": active_theses_count},
        {"label": "Decision Eligible", "value": decision_eligible_count},
        {"label": "Needs Review", "value": needs_review_count},
        {"label": "Framework Review", "value": framework_review_eligible_count},
    ]

    mnemosyne_data = {
        "banner_mode": mnemosyne_banner_mode,
        "distribution_display_df": distribution_display_df,
        "metric_tiles": [
            {"label": "Total Thesis Reviews", "value": total_reviews},
            {"label": "Distinct Theses Reviewed", "value": distinct_theses},
            {"label": "Review Horizons Completed", "value": review_horizons_completed},
            {"label": "Framework Review Consideration Count", "value": framework_review_consideration_count},
        ],
        "total_reviews": total_reviews,
        "distinct_theses": distinct_theses,
        "generated_at": datetime.now().strftime('%Y-%m-%d %H:%M'),
    }

    portfolio_display_df = pd.DataFrame()
    if portfolio_rows:
        portfolio_display_df = pd.DataFrame(portfolio_rows)[
            [
                "Company",
                "Ticker",
                "Status",
                "Recommendation",
                "Business Score",
                "Investment Score",
                "Next Review",
                "Action Required",
            ]
        ]

    st.markdown(
        """
        <style>
        .home-root {
            padding-top: 0.25rem;
        }
        .home-greeting {
            font-family: Inter, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif;
            font-size: 2.2rem;
            font-weight: 700;
            color: #E8E6E0;
            margin-bottom: 0.2rem;
        }
        .home-subtitle {
            font-family: Inter, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif;
            font-size: 1.0rem;
            color: #A8ACB8;
            margin-bottom: 0.9rem;
        }
        .home-date {
            text-align: right;
            color: #A8ACB8;
            font-size: 0.88rem;
            padding-top: 0.7rem;
        }
        .home-section-title {
            font-family: Inter, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif;
            font-weight: 700;
            font-size: 1.05rem;
            color: #E8E6E0;
            margin: 0.3rem 0 0.75rem 0;
        }
        .home-logo-block {
            width: 52px;
            height: 52px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: Inter, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif;
            font-size: 0.82rem;
            font-weight: 700;
            color: #FFFFFF;
            border: 1px solid rgba(255,255,255,0.15);
            margin-top: 0.15rem;
        }
        .home-logo-kodak { background: linear-gradient(135deg, #586274 0%, #313848 100%); }
        .home-logo-nvda { background: linear-gradient(135deg, #586274 0%, #313848 100%); }
        .home-logo-qcom { background: linear-gradient(135deg, #2B7DFF 0%, #103B7A 100%); }
        .home-logo-meta { background: linear-gradient(135deg, #586274 0%, #313848 100%); }
        .home-logo-archived { background: linear-gradient(135deg, #586274 0%, #313848 100%); }
        .home-logo-generic { background: linear-gradient(135deg, #586274 0%, #313848 100%); }
        .home-card-company {
            font-family: Inter, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif;
            font-size: 1.35rem;
            font-weight: 700;
            color: #E8E6E0;
            margin-bottom: 0.15rem;
        }
        .home-card-ticker {
            font-family: Inter, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif;
            font-size: 0.9rem;
            color: #8E95A5;
            margin-bottom: 0.55rem;
        }
        .home-chip {
            display: inline-block;
            border-radius: 999px;
            padding: 0.2rem 0.65rem;
            font-size: 0.75rem;
            font-weight: 600;
            margin-right: 0.35rem;
            margin-bottom: 0.35rem;
        }
        .home-chip-muted {
            color: #B8BDCA;
            border: 1px solid #2A3348;
            background: rgba(16, 24, 39, 0.7);
        }
        .health-strong { color: #56C267; border: 1px solid #245A32; background: rgba(23, 85, 37, 0.22); }
        .health-mixed { color: #F0C14A; border: 1px solid #6A531D; background: rgba(109, 77, 22, 0.22); }
        .health-weak { color: #FF7272; border: 1px solid #6E2B2B; background: rgba(102, 27, 27, 0.22); }
        .health-risk { color: #FF4F4F; border: 1px solid #7A2323; background: rgba(126, 26, 26, 0.24); }
        .health-none { color: #A8ACB8; border: 1px solid #394154; background: rgba(49, 57, 74, 0.22); }
        .home-card-primary-decision {
            font-family: Inter, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif;
            font-size: 1.02rem;
            font-weight: 700;
            color: #E6B12D;
            margin-top: 0.2rem;
        }
        .home-card-detail {
            font-family: Inter, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif;
            color: #B9BFCD;
            font-size: 0.86rem;
            margin-top: 0.15rem;
        }
        .home-card-next-action {
            font-family: Inter, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif;
            color: #E8E6E0;
            font-size: 0.9rem;
            font-weight: 600;
            margin-top: 0.45rem;
        }
        .home-summary-card {
            background: #0F1118;
            border: 1px solid #1E2331;
            border-radius: 14px;
            padding: 1rem;
            margin-bottom: 0.8rem;
        }
        .home-summary-title {
            font-family: Inter, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif;
            font-size: 1.05rem;
            font-weight: 700;
            color: #E8E6E0;
            margin-bottom: 0.8rem;
        }
        .home-summary-body {
            display: flex;
            gap: 0.9rem;
            align-items: center;
        }
        .home-summary-donut {
            width: 110px;
            height: 110px;
            border-radius: 50%;
            position: relative;
            flex: 0 0 110px;
        }
        .home-summary-donut::after {
            content: '';
            position: absolute;
            inset: 22px;
            background: #0A0A0F;
            border-radius: 50%;
            border: 1px solid #1E2331;
        }
        .home-summary-donut-inner {
            position: absolute;
            inset: 0;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            z-index: 1;
            text-align: center;
        }
        .home-summary-donut-value {
            font-family: Inter, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif;
            font-size: 2rem;
            font-weight: 700;
            line-height: 1;
            color: #E8E6E0;
        }
        .home-summary-donut-label {
            font-family: Inter, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif;
            font-size: 0.68rem;
            color: #A8ACB8;
            margin-top: 0.2rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }
        .home-summary-legend {
            flex: 1;
            display: flex;
            flex-direction: column;
            gap: 0.45rem;
        }
        .home-summary-legend-row {
            display: grid;
            grid-template-columns: 10px 1fr auto auto;
            align-items: center;
            gap: 0.45rem;
            font-family: Inter, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif;
            font-size: 0.82rem;
            color: #D8DCE6;
        }
        .home-summary-swatch {
            width: 10px;
            height: 10px;
            border-radius: 999px;
            display: inline-block;
        }
        .home-summary-legend-row span:nth-child(2) {
            color: #E8E6E0;
        }
        .home-summary-legend-row span:nth-child(3),
        .home-summary-legend-row span:nth-child(4) {
            color: #A8ACB8;
        }
        .home-footer-note {
            color: #8D95A8;
            text-align: center;
            font-size: 0.8rem;
            margin-top: 0.9rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Keep existing preparation flow behavior unchanged.
    pending_prepare_request = st.session_state.get("pending_prepare_request")
    if isinstance(pending_prepare_request, dict):
        with st.status("Preparing evaluation...", expanded=False):
            preparation_status = prepare_evaluation(
                ticker=pending_prepare_request.get("ticker", ""),
                observation_date=pending_prepare_request.get("observation_date", datetime.now().date()),
                company_name=pending_prepare_request.get("company_name", ""),
                reviewer=pending_prepare_request.get("reviewer", ""),
            )
        st.session_state["engine_preparation_status"] = preparation_status
        thesis_id = preparation_status.get("thesis_id")
        if thesis_id is not None:
            st.session_state["active_evaluation_thesis_id"] = int(thesis_id)
            st.session_state["selected_thesis_id"] = int(thesis_id)
        st.session_state["pending_prepare_request"] = None
        st.session_state["current_view"] = "Home"
        st.rerun()

    score_rollup_df = fetch_dataframe(
        """
        SELECT
            thesis_id,
            SUM(CASE WHEN pillar_id LIKE 'B%' THEN 1 ELSE 0 END) AS business_completed,
            SUM(CASE WHEN pillar_id LIKE 'I%' THEN 1 ELSE 0 END) AS investment_completed,
            ROUND(AVG(CASE WHEN score IS NOT NULL THEN score END), 1) AS avg_score,
            MAX(COALESCE(inference_confidence, '')) AS inference_confidence
        FROM pillar_scores
        GROUP BY thesis_id
        """
    )
    score_rollup_by_thesis = {
        int(row["thesis_id"]): {
            "business_completed": int(row["business_completed"]) if pd.notna(row["business_completed"]) else 0,
            "investment_completed": int(row["investment_completed"]) if pd.notna(row["investment_completed"]) else 0,
            "avg_score": float(row["avg_score"]) if pd.notna(row["avg_score"]) else None,
            "inference_confidence": _display_text(row.get("inference_confidence")),
        }
        for _, row in score_rollup_df.iterrows()
    } if not score_rollup_df.empty else {}

    active_evaluation_thesis_id = _resolve_active_evaluation_thesis_id(theses_df, latest_prep_by_thesis_id)

    home_rows = []
    for _, thesis_row in theses_df.iterrows():
        tid = int(thesis_row["id"])
        gate = gate_results_by_thesis_id.get(tid, {"completed": 0, "required": 11, "eligible": False})
        latest_decision_row = latest_decision_by_thesis_id.get(tid)
        prep_status = latest_prep_by_thesis_id.get(tid, {})
        score_rollup = score_rollup_by_thesis.get(tid, {})

        recommendation = ""
        if latest_decision_row is not None and pd.notna(latest_decision_row.get("recommendation")):
            recommendation = str(latest_decision_row.get("recommendation")).strip()

        next_review_date = None
        review_due = False
        if latest_decision_row is not None and pd.notna(latest_decision_row.get("next_review_date")):
            next_review_date = pd.to_datetime(latest_decision_row.get("next_review_date")).date()
            review_due = next_review_date < today_date

        business_completed = int(score_rollup.get("business_completed") or 0)
        investment_completed = int(score_rollup.get("investment_completed") or 0)
        completion_ratio = min(max((business_completed + investment_completed) / 11.0, 0.0), 1.0)
        workflow_state = derive_workflow_ownership_state(prep_status)

        row = {
            "thesis_id": tid,
            "company_name": thesis_row.get("company_name"),
            "ticker": thesis_row.get("ticker"),
            "status": thesis_row.get("status"),
            "recommendation": recommendation,
            "has_decision": latest_decision_row is not None,
            "decision_eligible": bool(gate.get("eligible")),
            "framework_review_eligible": tid in framework_eligible_ids,
            "has_review_record": tid in reviewed_ids,
            "review_due": review_due,
            "next_review_date": next_review_date.isoformat() if next_review_date is not None else "",
            "business_completed": business_completed,
            "investment_completed": investment_completed,
            "completion_ratio": completion_ratio,
            "avg_score": score_rollup.get("avg_score"),
            "inference_confidence": score_rollup.get("inference_confidence", ""),
            "prep_readiness": prep_status.get("readiness_status", ""),
            "prep_lifecycle": prep_status.get("lifecycle_state", ""),
            "evidence_discovery_status": prep_status.get("evidence_discovery_status", ""),
            "evidence_acquisition_status": prep_status.get("acquisition_status", ""),
            "extraction_status": prep_status.get("extraction_status", ""),
            "workflow_status": workflow_state.get("status", "Preparing"),
            "workflow_reason": workflow_state.get("reason", ""),
            "is_active": active_evaluation_thesis_id is not None and int(active_evaluation_thesis_id) == tid,
        }

        lifecycle = derive_lifecycle_display(row)
        lifecycle_rank = {
            "Preparation": 0,
            "Assessment": 1,
            "Decision": 2,
            "Historical Review": 3,
            "Framework Review": 4,
        }.get(lifecycle, 5)

        urgency_rank = 4
        if row["is_active"]:
            urgency_rank = 0
        elif row["framework_review_eligible"]:
            urgency_rank = 1
        elif row["review_due"]:
            urgency_rank = 2
        elif row["decision_eligible"] and not row["has_decision"]:
            urgency_rank = 3

        row["priority_key"] = (urgency_rank, lifecycle_rank, format_display_value(row.get("company_name")))
        home_rows.append(row)

    home_rows = sorted(home_rows, key=lambda row: row["priority_key"])
    active_home_rows = [row for row in home_rows if should_show_on_home_active_work(row)]
    needs_attention_rows = active_home_rows[:5]

    governance_attention_rows = []
    for row in home_rows:
        if not should_show_governance_attention(row):
            continue
        governance_message = build_governance_attention_message(row)
        if not governance_message:
            continue
        governance_attention_rows.append(
            {
                "thesis_id": int(row["thesis_id"]),
                "company_name": row.get("company_name"),
                "message": governance_message,
                "next_action": derive_next_action_display(row),
            }
        )

    current_eval_row = None
    for row in active_home_rows:
        if row.get("is_active"):
            current_eval_row = row
            break
    if current_eval_row is None and active_home_rows:
        current_eval_row = active_home_rows[0]

    hour = datetime.now().hour
    greeting = "Good morning" if hour < 12 else ("Good afternoon" if hour < 18 else "Good evening")

    st.markdown("<div class='home-root'></div>", unsafe_allow_html=True)
    hdr_left, hdr_right = st.columns([4.8, 1.2])
    with hdr_left:
        st.markdown(f"<div class='home-greeting'>{greeting}, Phillip</div>", unsafe_allow_html=True)
        st.markdown("<div class='home-subtitle'>Here's what needs your attention.</div>", unsafe_allow_html=True)
    with hdr_right:
        st.markdown(
            f"<div class='home-date'>{datetime.now().strftime('%B %d, %Y • %I:%M %p')}</div>",
            unsafe_allow_html=True,
        )

    main_col, right_col = st.columns([3.9, 1.35], gap="large")
    with main_col:
        st.markdown(
            f"<div class='home-section-title'>Needs Attention ({len(needs_attention_rows)})</div>",
            unsafe_allow_html=True,
        )
        if not needs_attention_rows:
            empty_state("No active evaluations currently need attention.")
        else:
            for idx, row in enumerate(needs_attention_rows):
                continue_clicked = render_home_evaluation_card(row, button_key=f"home_cmd_continue_{idx}_{int(row['thesis_id'])}")
                if continue_clicked:
                    st.session_state["selected_thesis_id"] = int(row["thesis_id"])
                    st.session_state["current_view"] = "Workspace"
                    st.rerun()

        if governance_attention_rows:
            st.markdown("<div class='home-section-title' style='margin-top:0.95rem;'>Governance Attention</div>", unsafe_allow_html=True)
            for governance_item in governance_attention_rows:
                st.markdown(
                    f"<div class='home-card-detail'><strong>{format_display_value(governance_item['company_name'])}</strong> — {format_display_value(governance_item['message'])}</div>",
                    unsafe_allow_html=True,
                )

        st.markdown("<div class='home-section-title' style='margin-top:0.95rem;'>Current Evaluation</div>", unsafe_allow_html=True)
        if current_eval_row is not None and render_current_evaluation_panel(current_eval_row):
            st.session_state["selected_thesis_id"] = int(current_eval_row["thesis_id"])
            st.session_state["current_view"] = "Workspace"
            st.rerun()
        elif current_eval_row is None:
            empty_state("No active evaluation selected.")

        st.markdown("<div class='home-section-title' style='margin-top:0.95rem;'>Quick Actions</div>", unsafe_allow_html=True)
        q1, q2, q3, q4 = st.columns(4)
        with q1:
            if st.button("New Evaluation", key="home_quick_new_eval", use_container_width=True):
                st.session_state["current_view"] = "New Thesis"
                st.session_state["selected_thesis_id"] = None
                st.rerun()
        with q2:
            st.button("Upload Evidence", key="home_quick_upload_evidence", use_container_width=True, disabled=True)
        with q3:
            if st.button("Evidence Discovery", key="home_quick_evidence_discovery", use_container_width=True):
                if current_eval_row is not None:
                    st.session_state["selected_thesis_id"] = int(current_eval_row["thesis_id"])
                    st.session_state["current_view"] = "Workspace"
                    st.rerun()
        with q4:
            if st.button("Review Queue", key="home_quick_review_queue", use_container_width=True):
                st.session_state["current_view"] = "Hermes Workflow Inbox"
                st.session_state["selected_thesis_id"] = None
                st.rerun()

        st.markdown(
            "<div class='home-footer-note'>Governed by Athena Charter v1.0 • Every decision is evidence-bounded, reproducible, and auditable.</div>",
            unsafe_allow_html=True,
        )

    with right_col:
        render_home_sidebar_panels(active_home_rows)

        recent_activity_df = fetch_dataframe(
            """
            SELECT created_at, event_type, event_description
            FROM thesis_events
            ORDER BY created_at DESC
            LIMIT 5
            """
        )
        if not recent_activity_df.empty:
            with st.container(border=True):
                st.markdown("### Recent Activity")
                for _, event_row in recent_activity_df.iterrows():
                    event_type = format_display_value(event_row.get("event_type"))
                    event_desc = format_display_value(event_row.get("event_description"))
                    event_time = format_display_value(event_row.get("created_at"))
                    st.write(f"{event_type}")
                    st.caption(f"{event_desc} • {event_time}")

    render_athena_footer()

elif st.session_state['current_view'] == 'Portfolio':
    render_page_header("Portfolio", "What companies am I responsible for?", eyebrow="Portfolio")

    portfolio_df = fetch_dataframe(
        """
        SELECT
            t.id,
            t.company_name,
            t.ticker,
            t.status,
            COALESCE(MAX(te.created_at), t.created_at) AS last_updated
        FROM theses t
        LEFT JOIN thesis_events te ON te.thesis_id = t.id
        GROUP BY t.id, t.company_name, t.ticker, t.status, t.created_at
        ORDER BY t.company_name ASC
        """
    )

    latest_decision_df = fetch_dataframe(
        """
        SELECT d1.*
        FROM decision_logs d1
        JOIN (
            SELECT thesis_id, MAX(id) AS max_id
            FROM decision_logs
            GROUP BY thesis_id
        ) latest ON latest.thesis_id = d1.thesis_id AND latest.max_id = d1.id
        """
    )
    latest_decision_by_thesis_id = {
        int(row["thesis_id"]): row for _, row in latest_decision_df.iterrows()
    } if not latest_decision_df.empty else {}

    rows = []
    for _, row in portfolio_df.iterrows():
        thesis_id = int(row["id"])
        if not is_active_operational_work({"thesis_id": thesis_id, "status": row.get("status")}):
            continue

        gate = validate_decision_gate(thesis_id)
        score_progress_df = fetch_dataframe(
            """
            SELECT
                SUM(CASE WHEN pillar_id LIKE 'B%' THEN 1 ELSE 0 END) AS business_rows,
                SUM(CASE WHEN pillar_id LIKE 'I%' THEN 1 ELSE 0 END) AS investment_rows
            FROM pillar_scores
            WHERE thesis_id = ?
            """,
            (thesis_id,),
        )
        progress_row = score_progress_df.iloc[0] if not score_progress_df.empty else None
        business_rows = int(progress_row["business_rows"]) if progress_row is not None and pd.notna(progress_row["business_rows"]) else 0
        investment_rows = int(progress_row["investment_rows"]) if progress_row is not None and pd.notna(progress_row["investment_rows"]) else 0
        lifecycle_stage = _get_workspace_stage(business_rows, investment_rows, gate["eligible"])

        latest_decision = latest_decision_by_thesis_id.get(thesis_id)
        recommendation = "—"
        if latest_decision is not None and pd.notna(latest_decision.get("recommendation")) and str(latest_decision.get("recommendation")).strip():
            recommendation = str(latest_decision.get("recommendation")).strip()

        next_action = "Complete constitutional assessment fields"
        if gate["eligible"]:
            next_action = "Record or update decision"
        elif gate["missing"]:
            next_action = f"Resolve {len(gate['missing'])} gate blockers"

        rows.append(
            {
                "thesis_id": thesis_id,
                "Company": row["company_name"],
                "Ticker": row["ticker"] if pd.notna(row["ticker"]) and str(row["ticker"]).strip() else "—",
                "Current Status": derive_asset_status_label(
                    row["company_name"],
                    row["ticker"],
                    row["status"],
                    thesis_id=thesis_id,
                    fallback="—",
                ),
                "Lifecycle Stage": lifecycle_stage,
                "Recommendation": recommendation,
                "Last Updated": row["last_updated"] if pd.notna(row["last_updated"]) else "—",
                "Next Action": next_action,
            }
        )

    inventory_df = pd.DataFrame(rows)
    if inventory_df.empty:
        empty_state("No active pursued evaluations found.")
    else:
        decision_ready_count = int((inventory_df["Next Action"] == "Record or update decision").sum())
        historical_reviews_count = int((inventory_df["Lifecycle Stage"] == "Historical Review").sum())
        framework_eligible_count = int((inventory_df["Lifecycle Stage"] == "Framework Review").sum())
        render_summary_row(
            "Portfolio Overview",
            "A compact view of the portfolio register and its current workload.",
            [
                {"label": "Total Evaluations", "value": len(inventory_df)},
                {"label": "Decision-Ready", "value": decision_ready_count},
                {"label": "Historical Reviews", "value": historical_reviews_count},
                {"label": "Framework Eligible", "value": framework_eligible_count},
            ],
        )
        st.caption("Archived constitutional assets are excluded from active portfolio views and remain available through History records.")
        search_query = st.text_input("Search", placeholder="Company, ticker, or status")
        status_options = ["All"] + sorted(inventory_df["Current Status"].dropna().astype(str).unique().tolist())
        selected_status = st.selectbox("Filter", options=status_options)
        sort_options = ["Company", "Lifecycle Stage", "Current Status", "Last Updated", "Next Action"]
        selected_sort = st.selectbox("Sort", options=sort_options, index=0)

        filtered_df = inventory_df.copy()
        if search_query.strip():
            query = search_query.strip().lower()
            filtered_df = filtered_df[
                filtered_df.apply(
                    lambda r: query in str(r["Company"]).lower()
                    or query in str(r["Ticker"]).lower()
                    or query in str(r["Current Status"]).lower(),
                    axis=1,
                )
            ]
        if selected_status != "All":
            filtered_df = filtered_df[filtered_df["Current Status"] == selected_status]

        filtered_df = filtered_df.sort_values(by=[selected_sort, "Company"], ascending=[True, True])
        render_section_title("Evaluation Register", "Search, filter, and sort the current portfolio queue.")
        st.dataframe(filtered_df[["Company", "Ticker", "Current Status", "Lifecycle Stage", "Recommendation", "Last Updated", "Next Action"]], use_container_width=True)

        open_options = filtered_df["thesis_id"].astype(int).tolist()
        if open_options:
            selected_open_thesis = st.selectbox(
                "Open Workspace",
                options=open_options,
                format_func=lambda tid: f"{int(tid)} — {filtered_df[filtered_df['thesis_id'] == tid].iloc[0]['Company']}",
            )
            if st.button("Continue In Workspace", use_container_width=True):
                st.session_state["selected_thesis_id"] = int(selected_open_thesis)
                st.session_state["current_view"] = "Workspace"
                st.rerun()

elif st.session_state['current_view'] == 'History':
    render_page_header("Validation History", "What decisions have already been made?", eyebrow="History")

    completed_df = fetch_dataframe(
        """
        SELECT id, company_name, ticker, status, created_at
        FROM theses
        WHERE status = ?
        ORDER BY created_at DESC
        """,
        (STATUS_CLOSED,),
    )
    render_section_title("Completed Evaluations")
    if completed_df.empty:
        st.info("No completed evaluations yet.")
    else:
        st.dataframe(completed_df, use_container_width=True)

    recommendation_df = fetch_dataframe(
        """
        SELECT t.company_name, t.ticker, d.recommendation, d.review_date, d.next_review_date, d.created_at
        FROM decision_logs d
        JOIN theses t ON t.id = d.thesis_id
        ORDER BY d.created_at DESC
        """
    )
    render_section_title("Historical Recommendations")
    if recommendation_df.empty:
        st.info("No decision records yet.")
    else:
        st.dataframe(recommendation_df, use_container_width=True)

    outcome_df = fetch_dataframe(
        """
        SELECT t.company_name, tr.review_horizon, tr.outcome_attribution_type, tr.review_date, tr.framework_review_eligible
        FROM thesis_reviews tr
        JOIN theses t ON t.id = tr.thesis_id
        ORDER BY tr.review_date DESC, tr.created_at DESC
        """
    )
    render_section_title("Outcome Attribution")
    if outcome_df.empty:
        st.info("No outcome attribution records yet.")
    else:
        st.dataframe(outcome_df, use_container_width=True)

    audit_df = fetch_dataframe(
        """
        SELECT te.created_at, t.company_name, te.event_type, te.event_description, te.created_by
        FROM thesis_events te
        JOIN theses t ON t.id = te.thesis_id
        ORDER BY te.created_at DESC
        LIMIT 250
        """
    )
    render_section_title("Audit Trail")
    if audit_df.empty:
        st.info("No audit events recorded.")
    else:
        st.dataframe(audit_df, use_container_width=True)

    lessons_df = fetch_dataframe(
        """
        SELECT t.company_name, tr.review_horizon, tr.outcome_summary, tr.thesis_quality_assessment, tr.framework_notes, tr.review_date
        FROM thesis_reviews tr
        JOIN theses t ON t.id = tr.thesis_id
        ORDER BY tr.review_date DESC, tr.created_at DESC
        """
    )

    render_summary_row(
        "History Overview",
        "A validation-first view of completed work and post-decision records.",
        [
            {"label": "Completed Evaluations", "value": len(completed_df)},
            {"label": "Historical Recommendations", "value": len(recommendation_df)},
            {"label": "Outcome Reviews", "value": len(outcome_df)},
            {"label": "Framework Eligible", "value": int(outcome_df["framework_review_eligible"].fillna(0).astype(int).sum()) if not outcome_df.empty and "framework_review_eligible" in outcome_df.columns else 0},
        ],
    )
    render_section_title("Lessons Learned")
    if lessons_df.empty:
        st.info("No lessons learned captured yet.")
    else:
        st.dataframe(lessons_df, use_container_width=True)

elif st.session_state['current_view'] == 'Microsoft HRV-002 Readiness':
    render_page_header(
        "Microsoft HRV-002 Readiness Board",
        "Read-only verification board for Microsoft longitudinal validation readiness.",
        eyebrow="Governance",
    )

    st.warning(
        "HRV-002 successor identity is drafted but not ratified. "
        "thesis_id=14 remains preserved as an ambiguous historical artifact and is not active work."
    )
    st.error(
        "HRV-002 replay is blocked and not authorized. HRV-001 remains closed and may not be reused. "
        "No replay execution may begin until a governed HRV-002 successor identity package is implemented."
    )

    st.markdown(
        """
        - **Blocked state:** Microsoft HRV-002 is blocked.
        - **Source-context protection:** thesis_id=14 remains historical/source-context only.
        - **HRV-001 protection:** HRV-001 stays closed and is never reused.
        - **Missing blockers:** explicit HRV-002 runtime identity; pillar-to-evidence linkage; outcome attribution readiness (`thesis_reviews`); replay freeze authority.
        - **Next governance step:** implement the HRV-002 successor identity package before replay.
        """
    )

    render_section_title("Identity State Panel")
    identity_state_df = get_microsoft_identity_state()
    st.dataframe(identity_state_df, use_container_width=True, hide_index=True)

    render_section_title("Runtime DB Snapshot")
    snapshot = get_microsoft_runtime_snapshot()
    snapshot_df = pd.DataFrame(
        [
            {"Field": "company_name", "Value": snapshot["company_name"]},
            {"Field": "ticker", "Value": snapshot["ticker"]},
            {"Field": "status", "Value": snapshot["status"]},
            {"Field": "created_at", "Value": snapshot["created_at"]},
            {"Field": "decision log count", "Value": snapshot["decision_log_count"]},
            {"Field": "thesis review count", "Value": snapshot["thesis_review_count"]},
            {"Field": "thesis event count", "Value": snapshot["thesis_event_count"]},
            {"Field": "latest event timestamp", "Value": snapshot["latest_event_timestamp"]},
            {"Field": "decision recommendation", "Value": snapshot["decision_recommendation"]},
        ]
    )
    st.dataframe(snapshot_df, use_container_width=True, hide_index=True)

    render_section_title("Evidence Pipeline Status")
    pipeline_df, pipeline_support = get_microsoft_evidence_pipeline_status()
    st.dataframe(pipeline_df, use_container_width=True, hide_index=True)
    with st.expander("Schema support details", expanded=False):
        support_rows = []
        for table_name, support_payload in pipeline_support.items():
            support_rows.append(
                {
                    "Table": table_name,
                    "Available": "Yes" if support_payload.get("available") else "No",
                    "Missing Columns": ", ".join(support_payload.get("missing_columns", [])) if support_payload.get("missing_columns") else "—",
                    "Message": support_payload.get("message"),
                }
            )
        st.dataframe(pd.DataFrame(support_rows), use_container_width=True, hide_index=True)

    render_section_title("Pillar Coverage Matrix")
    pillar_matrix_df, pillar_support = get_microsoft_pillar_coverage_matrix()
    st.dataframe(pillar_matrix_df, use_container_width=True, hide_index=True)
    with st.expander("Pillar schema support details", expanded=False):
        support_rows = []
        for table_name, support_payload in pillar_support.items():
            support_rows.append(
                {
                    "Table": table_name,
                    "Available": "Yes" if support_payload.get("available") else "No",
                    "Missing Columns": ", ".join(support_payload.get("missing_columns", [])) if support_payload.get("missing_columns") else "—",
                    "Message": support_payload.get("message"),
                }
            )
        st.dataframe(pd.DataFrame(support_rows), use_container_width=True, hide_index=True)

    render_section_title("Year / Period Coverage")
    period_df, can_verify_period_years, period_support = get_microsoft_period_coverage()
    st.dataframe(period_df, use_container_width=True, hide_index=True)
    if not can_verify_period_years:
        st.info("Year coverage cannot be verified from current runtime metadata.")
    with st.expander("Period schema support details", expanded=False):
        support_rows = []
        for table_name, support_payload in period_support.items():
            support_rows.append(
                {
                    "Table": table_name,
                    "Available": "Yes" if support_payload.get("available") else "No",
                    "Missing Columns": ", ".join(support_payload.get("missing_columns", [])) if support_payload.get("missing_columns") else "—",
                    "Message": support_payload.get("message"),
                }
            )
        st.dataframe(pd.DataFrame(support_rows), use_container_width=True, hide_index=True)

    render_section_title("Readiness Summary")
    covered_count = int((pillar_matrix_df["status"] == "Covered").sum()) if not pillar_matrix_df.empty else 0
    partial_count = int((pillar_matrix_df["status"] == "Partial").sum()) if not pillar_matrix_df.empty else 0
    missing_count = int((pillar_matrix_df["status"] == "Missing").sum()) if not pillar_matrix_df.empty else 0
    needs_review_count = int((pillar_matrix_df["status"] == "Needs Review").sum()) if not pillar_matrix_df.empty else 0

    render_summary_row(
        "Readiness Overview",
        "Microsoft source-context readiness indicators (read-only).",
        [
            {"label": "Ready for successor creation", "value": "Blocked"},
            {"label": "Covered Pillars", "value": covered_count},
            {"label": "Partial Pillars", "value": partial_count},
            {"label": "Missing/Needs Review", "value": missing_count + needs_review_count},
        ],
    )

    st.markdown(
        """
        - **Blocker:** HRV-002 successor identity not ratified and no active successor thesis exists.
        - **Data readiness:** Evidence and pillar coverage are summarized above for source-context verification only.
        - **Replay authority:** Replay remains blocked/not authorized in this board.
        - **Next action:** Ratify/create HRV-002 successor identity, then map verified Microsoft evidence into successor workflow.
        """
    )

    render_section_title("No Mutation Guarantee")
    st.markdown(
        """
        - This board is read-only.
        - No inserts.
        - No updates.
        - No deletes.
        - No automatic status changes.
        - No automatic promotion.
        - No automatic scoring.
        """
    )

    render_athena_footer()

elif st.session_state['current_view'] == 'Data Explorer':
    render_page_header(
        "Data Explorer",
        "Inspect thesis-linked runtime data directly with read-only queries.",
        eyebrow="Explorer",
    )
    st.caption(f"Runtime DB Path: {DATABASE_FILE}")
    render_status_chip("Read-only", tone="gold")
    st.warning(
        "This page is read-only. It does not create, edit, promote, attach, migrate, score, or route evidence."
    )

    theses_selector_support = _schema_table_support("theses", ["id", "company_name", "ticker", "status", "created_at"])
    if not theses_selector_support["available"] or "id" in theses_selector_support["missing_columns"]:
        render_section_title("Thesis Selector")
        st.info("Unavailable in schema.")
        render_athena_footer()
    else:
        selector_columns = [
            column
            for column in ["id", "company_name", "ticker", "status", "created_at"]
            if column in theses_selector_support["columns"]
        ]
        theses_selector_df = fetch_dataframe(
            f"SELECT {', '.join(selector_columns)} FROM theses ORDER BY id ASC"
        )

        render_section_title("Thesis Selector")
        if theses_selector_df.empty:
            empty_state("No thesis records found in runtime data.")
            render_athena_footer()
        else:
            st.dataframe(theses_selector_df, use_container_width=True, hide_index=True)

            available_thesis_ids = sorted(theses_selector_df["id"].astype(int).tolist())
            selected_explorer_id = st.session_state.get("selected_thesis_id_explorer")
            if selected_explorer_id not in available_thesis_ids:
                st.session_state["selected_thesis_id_explorer"] = int(available_thesis_ids[0])
                st.session_state["data_explorer_thesis_selector"] = int(available_thesis_ids[0])

            if 14 in available_thesis_ids:
                if st.button(
                    "Open Microsoft thesis_id=14 — historical artifact / HRV-002 source context",
                    key="data_explorer_open_msft_14",
                    use_container_width=False,
                ):
                    st.session_state["selected_thesis_id_explorer"] = 14
                    st.session_state["data_explorer_thesis_selector"] = 14
                    st.rerun()

            selector_lookup = theses_selector_df.set_index("id", drop=False)

            selected_thesis_id_explorer = st.selectbox(
                "Select thesis",
                options=available_thesis_ids,
                index=available_thesis_ids.index(int(st.session_state["selected_thesis_id_explorer"])),
                format_func=lambda thesis_id: (
                    f"{int(thesis_id)} | "
                    f"{format_display_value(selector_lookup.loc[thesis_id].get('company_name'), fallback='—')} | "
                    f"{format_display_value(selector_lookup.loc[thesis_id].get('ticker'), fallback='—')} | "
                    f"{format_display_value(selector_lookup.loc[thesis_id].get('status'), fallback='—')} | "
                    f"{format_display_value(selector_lookup.loc[thesis_id].get('created_at'), fallback='—')}"
                ),
                key="data_explorer_thesis_selector",
            )
            st.session_state["selected_thesis_id_explorer"] = int(selected_thesis_id_explorer)
            selected_thesis_id = int(selected_thesis_id_explorer)

            selected_thesis_full_df = fetch_dataframe("SELECT * FROM theses WHERE id = ?", (selected_thesis_id,))
            selected_thesis_row = selected_thesis_full_df.iloc[0].to_dict() if not selected_thesis_full_df.empty else {}

            render_section_title("Selected Thesis Identity")
            identity_fields = [
                "id",
                "company_name",
                "ticker",
                "status",
                "decision_question",
                "account_type",
                "portfolio_role",
                "primary_horizon",
                "regime_state",
                "reviewer",
                "drl",
                "validation_mode",
                "evidence_cutoff_date",
                "created_at",
            ]
            identity_rows = []
            thesis_columns_present = set(selected_thesis_full_df.columns.tolist()) if not selected_thesis_full_df.empty else set()
            for field_name in identity_fields:
                if field_name == "id":
                    display_field = "thesis_id"
                else:
                    display_field = field_name
                if field_name in thesis_columns_present:
                    identity_rows.append(
                        {
                            "Field": display_field,
                            "Value": format_display_value(selected_thesis_row.get(field_name), fallback="—"),
                        }
                    )
                else:
                    identity_rows.append({"Field": display_field, "Value": "Unavailable in schema."})
            st.dataframe(pd.DataFrame(identity_rows), use_container_width=True, hide_index=True)

            render_section_title("Summary Counts")
            count_rows = []

            decision_logs_support = _schema_table_support("decision_logs", ["thesis_id"])
            if decision_logs_support["available"] and not decision_logs_support["missing_columns"]:
                decision_log_count = _explorer_count_value(
                    "SELECT COUNT(*) AS value_count FROM decision_logs WHERE thesis_id = ?",
                    (selected_thesis_id,),
                )
            else:
                decision_log_count = "Unavailable in schema."
            count_rows.append({"Metric": "decision log count", "Value": decision_log_count})

            thesis_reviews_support = _schema_table_support("thesis_reviews", ["thesis_id"])
            if thesis_reviews_support["available"] and not thesis_reviews_support["missing_columns"]:
                thesis_review_count = _explorer_count_value(
                    "SELECT COUNT(*) AS value_count FROM thesis_reviews WHERE thesis_id = ?",
                    (selected_thesis_id,),
                )
            else:
                thesis_review_count = "Unavailable in schema."
            count_rows.append({"Metric": "thesis review count", "Value": thesis_review_count})

            thesis_events_support = _schema_table_support("thesis_events", ["thesis_id"])
            if thesis_events_support["available"] and not thesis_events_support["missing_columns"]:
                thesis_event_count = _explorer_count_value(
                    "SELECT COUNT(*) AS value_count FROM thesis_events WHERE thesis_id = ?",
                    (selected_thesis_id,),
                )
            else:
                thesis_event_count = "Unavailable in schema."
            count_rows.append({"Metric": "thesis event count", "Value": thesis_event_count})

            evidence_staging_support = _schema_table_support(
                "evidence_staging", ["thesis_id", "intake_status", "review_date", "promoted_at"]
            )
            if evidence_staging_support["available"] and not evidence_staging_support["missing_columns"]:
                staged_count = _explorer_count_value(
                    "SELECT COUNT(*) AS value_count FROM evidence_staging WHERE thesis_id = ? AND intake_status = 'Pending'",
                    (selected_thesis_id,),
                )
                reviewed_staged_count = _explorer_count_value(
                    "SELECT COUNT(*) AS value_count FROM evidence_staging WHERE thesis_id = ? AND review_date IS NOT NULL AND TRIM(review_date) <> ''",
                    (selected_thesis_id,),
                )
                promoted_staged_count = _explorer_count_value(
                    "SELECT COUNT(*) AS value_count FROM evidence_staging WHERE thesis_id = ? AND promoted_at IS NOT NULL AND TRIM(promoted_at) <> ''",
                    (selected_thesis_id,),
                )
            else:
                staged_count = "Unavailable in schema."
                reviewed_staged_count = "Unavailable in schema."
                promoted_staged_count = "Unavailable in schema."
            count_rows.append({"Metric": "staged evidence count", "Value": staged_count})
            count_rows.append({"Metric": "reviewed staged evidence count", "Value": reviewed_staged_count})
            count_rows.append({"Metric": "promoted staged evidence count", "Value": promoted_staged_count})

            evidence_items_support = _schema_table_support("evidence_items", ["id", "thesis_id"])
            if evidence_items_support["available"] and not evidence_items_support["missing_columns"]:
                attached_count = _explorer_count_value(
                    "SELECT COUNT(*) AS value_count FROM evidence_items WHERE thesis_id = ?",
                    (selected_thesis_id,),
                )
            else:
                attached_count = "Unavailable in schema."
            count_rows.append({"Metric": "attached evidence item count", "Value": attached_count})

            evidence_observations_support = _schema_table_support("evidence_observations", ["evidence_item_id"])
            if (
                evidence_observations_support["available"]
                and not evidence_observations_support["missing_columns"]
                and evidence_items_support["available"]
                and not evidence_items_support["missing_columns"]
            ):
                observation_count = _explorer_count_value(
                    """
                    SELECT COUNT(*) AS value_count
                    FROM evidence_observations eo
                    JOIN evidence_items ei ON ei.id = eo.evidence_item_id
                    WHERE ei.thesis_id = ?
                    """,
                    (selected_thesis_id,),
                )
            else:
                observation_count = "Unavailable in schema."
            count_rows.append({"Metric": "evidence observation count", "Value": observation_count})

            pillar_scores_support = _schema_table_support("pillar_scores", ["id", "thesis_id"])
            if pillar_scores_support["available"] and not pillar_scores_support["missing_columns"]:
                pillar_score_count = _explorer_count_value(
                    "SELECT COUNT(*) AS value_count FROM pillar_scores WHERE thesis_id = ?",
                    (selected_thesis_id,),
                )
            else:
                pillar_score_count = "Unavailable in schema."
            count_rows.append({"Metric": "pillar score count", "Value": pillar_score_count})

            pillar_links_support = _schema_table_support("pillar_evidence_links", ["pillar_score_id", "evidence_item_id"])
            if (
                pillar_links_support["available"]
                and not pillar_links_support["missing_columns"]
                and pillar_scores_support["available"]
                and not pillar_scores_support["missing_columns"]
            ):
                pillar_link_count = _explorer_count_value(
                    """
                    SELECT COUNT(*) AS value_count
                    FROM pillar_evidence_links pel
                    JOIN pillar_scores ps ON ps.id = pel.pillar_score_id
                    WHERE ps.thesis_id = ?
                    """,
                    (selected_thesis_id,),
                )
            else:
                pillar_link_count = "Unavailable in schema."
            count_rows.append({"Metric": "pillar evidence link count", "Value": pillar_link_count})

            eval_prep_support = _schema_table_support("evaluation_preparations", ["thesis_id"])
            if eval_prep_support["available"] and not eval_prep_support["missing_columns"]:
                prep_count = _explorer_count_value(
                    "SELECT COUNT(*) AS value_count FROM evaluation_preparations WHERE thesis_id = ?",
                    (selected_thesis_id,),
                )
            else:
                prep_count = "Unavailable in schema."
            count_rows.append({"Metric": "evaluation preparation count", "Value": prep_count})

            eval_candidate_support = _schema_table_support("evaluation_candidate_documents", ["thesis_id"])
            if eval_candidate_support["available"] and not eval_candidate_support["missing_columns"]:
                candidate_count = _explorer_count_value(
                    "SELECT COUNT(*) AS value_count FROM evaluation_candidate_documents WHERE thesis_id = ?",
                    (selected_thesis_id,),
                )
            else:
                candidate_count = "Unavailable in schema."
            count_rows.append({"Metric": "evaluation candidate document count", "Value": candidate_count})

            eval_acquired_support = _schema_table_support("evaluation_acquired_documents", ["thesis_id"])
            if eval_acquired_support["available"] and not eval_acquired_support["missing_columns"]:
                acquired_count = _explorer_count_value(
                    "SELECT COUNT(*) AS value_count FROM evaluation_acquired_documents WHERE thesis_id = ?",
                    (selected_thesis_id,),
                )
            else:
                acquired_count = "Unavailable in schema."
            count_rows.append({"Metric": "evaluation acquired document count", "Value": acquired_count})

            eval_extracted_support = _schema_table_support("evaluation_extracted_observations", ["thesis_id"])
            if eval_extracted_support["available"] and not eval_extracted_support["missing_columns"]:
                extracted_count = _explorer_count_value(
                    "SELECT COUNT(*) AS value_count FROM evaluation_extracted_observations WHERE thesis_id = ?",
                    (selected_thesis_id,),
                )
            else:
                extracted_count = "Unavailable in schema."
            count_rows.append({"Metric": "evaluation extracted observation count", "Value": extracted_count})

            st.dataframe(pd.DataFrame(count_rows), use_container_width=True, hide_index=True)

            thesis_row_support = _schema_table_support("theses", ["id"])
            thesis_full_df = pd.DataFrame()
            thesis_unavailable = not thesis_row_support["available"] or bool(thesis_row_support["missing_columns"])
            if not thesis_unavailable:
                thesis_full_df = fetch_dataframe("SELECT * FROM theses WHERE id = ?", (selected_thesis_id,))
            _render_explorer_dataset(
                "A. Full Thesis Row",
                "Full thesis record from the theses table for the selected thesis_id.",
                thesis_full_df,
                unavailable=thesis_unavailable,
            )

            decision_log_columns = [
                "id",
                "thesis_id",
                "recommendation",
                "horizon_map",
                "action",
                "review_date",
                "decision_rationale",
                "key_risks",
                "falsification_summary",
                "next_review_date",
                "created_at",
            ]
            decision_columns, decision_support = _explorer_available_columns("decision_logs", decision_log_columns)
            decision_df = pd.DataFrame()
            decision_unavailable = (not decision_support["available"]) or ("thesis_id" not in decision_support["columns"]) or (len(decision_columns) == 0)
            if not decision_unavailable:
                decision_df = fetch_dataframe(
                    f"SELECT {', '.join(decision_columns)} FROM decision_logs WHERE thesis_id = ? ORDER BY id DESC",
                    (selected_thesis_id,),
                )
            _render_explorer_dataset(
                "B. Decision Logs",
                "Decision history and recommendation metadata for the selected thesis.",
                decision_df,
                unavailable=decision_unavailable,
            )

            review_columns = [
                "id",
                "thesis_id",
                "decision_log_id",
                "review_date",
                "review_horizon",
                "outcome_summary",
                "outcome_attribution_type",
                "outcome_evidence",
                "thesis_quality_assessment",
                "decision_quality_preserved",
                "framework_review_eligible",
                "reviewer",
                "created_at",
            ]
            review_available_columns, review_support = _explorer_available_columns("thesis_reviews", review_columns)
            review_df = pd.DataFrame()
            review_unavailable = (not review_support["available"]) or ("thesis_id" not in review_support["columns"]) or (len(review_available_columns) == 0)
            if not review_unavailable:
                review_df = fetch_dataframe(
                    f"SELECT {', '.join(review_available_columns)} FROM thesis_reviews WHERE thesis_id = ? ORDER BY id DESC",
                    (selected_thesis_id,),
                )
            _render_explorer_dataset(
                "C. Thesis Reviews",
                "Post-decision review records and outcome attribution fields.",
                review_df,
                unavailable=review_unavailable,
            )

            staging_columns = [
                "id",
                "staging_uuid",
                "thesis_id",
                "source_type",
                "source_name",
                "source_url",
                "publication_date",
                "retrieval_date",
                "author_publisher",
                "evidence_summary",
                "key_takeaway",
                "preliminary_grade",
                "intake_status",
                "rejection_reason",
                "reviewed_by",
                "review_date",
                "promoted_evidence_id",
                "promoted_at",
                "created_by",
                "created_at",
                "archive_reason",
            ]
            staging_available_columns, staging_support = _explorer_available_columns("evidence_staging", staging_columns)
            staging_df = pd.DataFrame()
            staging_unavailable = (not staging_support["available"]) or ("thesis_id" not in staging_support["columns"]) or (len(staging_available_columns) == 0)
            if not staging_unavailable:
                staging_df = fetch_dataframe(
                    f"SELECT {', '.join(staging_available_columns)} FROM evidence_staging WHERE thesis_id = ? ORDER BY id ASC",
                    (selected_thesis_id,),
                )
            _render_explorer_dataset(
                "D. Evidence Staging",
                "Staged evidence intake records before and after review/promotion steps.",
                staging_df,
                unavailable=staging_unavailable,
            )

            evidence_item_columns = [
                "id",
                "thesis_id",
                "source_name",
                "source_type",
                "publication_date",
                "evidence_grade",
                "confidence_basis",
                "url_or_citation",
                "related_pillar",
                "evidence_summary",
                "title",
                "source_publisher",
                "key_takeaway",
                "tags",
                "credibility_score",
                "materiality_score",
                "thesis_alignment",
                "status",
                "created_at",
            ]
            evidence_item_available_columns, evidence_item_support = _explorer_available_columns("evidence_items", evidence_item_columns)
            evidence_items_df = pd.DataFrame()
            evidence_items_unavailable = (not evidence_item_support["available"]) or ("thesis_id" not in evidence_item_support["columns"]) or (len(evidence_item_available_columns) == 0)
            if not evidence_items_unavailable:
                evidence_items_df = fetch_dataframe(
                    f"SELECT {', '.join(evidence_item_available_columns)} FROM evidence_items WHERE thesis_id = ? ORDER BY id ASC",
                    (selected_thesis_id,),
                )
            _render_explorer_dataset(
                "E. Evidence Items",
                "Promoted or attached evidence records currently linked to the selected thesis.",
                evidence_items_df,
                unavailable=evidence_items_unavailable,
            )

            observation_df = pd.DataFrame()
            observation_unavailable = False
            eo_support = _schema_table_support("evidence_observations", ["evidence_item_id"])
            ei_support = _schema_table_support("evidence_items", ["id", "thesis_id"])
            if (
                (not eo_support["available"])
                or (not ei_support["available"])
                or ("evidence_item_id" not in eo_support["columns"])
                or ("id" not in ei_support["columns"])
                or ("thesis_id" not in ei_support["columns"])
            ):
                observation_unavailable = True
            else:
                observation_select_expressions = []
                if "id" in eo_support["columns"]:
                    observation_select_expressions.append("eo.id AS observation_id")
                if "evidence_item_id" in eo_support["columns"]:
                    observation_select_expressions.append("eo.evidence_item_id")
                if "source_name" in ei_support["columns"]:
                    observation_select_expressions.append("ei.source_name AS evidence_source_name")
                if "source_type" in ei_support["columns"]:
                    observation_select_expressions.append("ei.source_type AS evidence_source_type")
                if "publication_date" in ei_support["columns"]:
                    observation_select_expressions.append("ei.publication_date AS evidence_publication_date")
                if "pillar_id" in eo_support["columns"]:
                    observation_select_expressions.append("eo.pillar_id")
                if "observation_category" in eo_support["columns"]:
                    observation_select_expressions.append("eo.observation_category")
                if "observation_text" in eo_support["columns"]:
                    observation_select_expressions.append("eo.observation_text")
                if "evidence_quote" in eo_support["columns"]:
                    observation_select_expressions.append("eo.evidence_quote")
                if "source_location" in eo_support["columns"]:
                    observation_select_expressions.append("eo.source_location")
                if "analyst_confidence" in eo_support["columns"]:
                    observation_select_expressions.append("eo.analyst_confidence")
                if "status" in eo_support["columns"]:
                    observation_select_expressions.append("eo.status AS observation_status")
                if "created_by" in eo_support["columns"]:
                    observation_select_expressions.append("eo.created_by AS observation_created_by")
                if "created_at" in eo_support["columns"]:
                    observation_select_expressions.append("eo.created_at AS observation_created_at")

                if len(observation_select_expressions) == 0:
                    observation_unavailable = True
                else:
                    observation_order_clause = "ORDER BY eo.id DESC"
                    if "created_at" in eo_support["columns"]:
                        observation_order_clause = "ORDER BY eo.created_at DESC"
                    observation_df = fetch_dataframe(
                        f"""
                        SELECT {', '.join(observation_select_expressions)}
                        FROM evidence_observations eo
                        JOIN evidence_items ei ON ei.id = eo.evidence_item_id
                        WHERE ei.thesis_id = ?
                        {observation_order_clause}
                        """,
                        (selected_thesis_id,),
                    )
            _render_explorer_dataset(
                "F. Evidence Observations",
                "Observation records joined to their evidence items for contextual traceability.",
                observation_df,
                unavailable=observation_unavailable,
            )

            pillar_score_columns = [
                "id",
                "thesis_id",
                "pillar_id",
                "pillar_name",
                "score",
                "rag_status",
                "evidence_grade",
                "confidence_basis",
                "primary_sources",
                "evidence_items",
                "inference",
                "inference_confidence",
                "falsification_trigger",
                "score_rationale",
                "judgment",
                "reviewer",
                "review_date",
                "drl",
                "created_at",
            ]
            pillar_score_available_columns, pillar_score_support = _explorer_available_columns("pillar_scores", pillar_score_columns)
            pillar_score_df = pd.DataFrame()
            pillar_score_unavailable = (not pillar_score_support["available"]) or ("thesis_id" not in pillar_score_support["columns"]) or (len(pillar_score_available_columns) == 0)
            if not pillar_score_unavailable:
                pillar_score_df = fetch_dataframe(
                    f"SELECT {', '.join(pillar_score_available_columns)} FROM pillar_scores WHERE thesis_id = ? ORDER BY pillar_id ASC, id ASC",
                    (selected_thesis_id,),
                )
            _render_explorer_dataset(
                "G. Pillar Scores",
                "Business and investment pillar assessments recorded for the selected thesis.",
                pillar_score_df,
                unavailable=pillar_score_unavailable,
            )

            pillar_link_df = pd.DataFrame()
            pillar_link_unavailable = False
            pel_support = _schema_table_support("pillar_evidence_links", ["pillar_score_id", "evidence_item_id"])
            ps_support = _schema_table_support("pillar_scores", ["id", "thesis_id"])
            ei_link_support = _schema_table_support("evidence_items", ["id"])
            if (
                (not pel_support["available"])
                or (not ps_support["available"])
                or (not ei_link_support["available"])
                or ("pillar_score_id" not in pel_support["columns"])
                or ("evidence_item_id" not in pel_support["columns"])
                or ("id" not in ps_support["columns"])
                or ("thesis_id" not in ps_support["columns"])
                or ("id" not in ei_link_support["columns"])
            ):
                pillar_link_unavailable = True
            else:
                link_select_expressions = []
                if "id" in pel_support["columns"]:
                    link_select_expressions.append("pel.id AS link_id")
                if "pillar_score_id" in pel_support["columns"]:
                    link_select_expressions.append("pel.pillar_score_id")
                if "pillar_id" in ps_support["columns"]:
                    link_select_expressions.append("ps.pillar_id")
                if "pillar_name" in ps_support["columns"]:
                    link_select_expressions.append("ps.pillar_name")
                if "evidence_item_id" in pel_support["columns"]:
                    link_select_expressions.append("pel.evidence_item_id")
                if "source_name" in ei_link_support["columns"]:
                    link_select_expressions.append("ei.source_name AS evidence_source_name")
                if "source_type" in ei_link_support["columns"]:
                    link_select_expressions.append("ei.source_type AS evidence_source_type")
                if "publication_date" in ei_link_support["columns"]:
                    link_select_expressions.append("ei.publication_date AS evidence_publication_date")
                if "status" in ei_link_support["columns"]:
                    link_select_expressions.append("ei.status AS evidence_status")
                if "created_by" in pel_support["columns"]:
                    link_select_expressions.append("pel.created_by AS link_created_by")
                if "created_at" in pel_support["columns"]:
                    link_select_expressions.append("pel.created_at AS link_created_at")

                if len(link_select_expressions) == 0:
                    pillar_link_unavailable = True
                else:
                    link_order_clause = "ORDER BY pel.id DESC"
                    if "created_at" in pel_support["columns"]:
                        link_order_clause = "ORDER BY pel.created_at DESC"
                    pillar_link_df = fetch_dataframe(
                        f"""
                        SELECT {', '.join(link_select_expressions)}
                        FROM pillar_evidence_links pel
                        JOIN pillar_scores ps ON ps.id = pel.pillar_score_id
                        JOIN evidence_items ei ON ei.id = pel.evidence_item_id
                        WHERE ps.thesis_id = ?
                        {link_order_clause}
                        """,
                        (selected_thesis_id,),
                    )
            _render_explorer_dataset(
                "H. Pillar Evidence Links",
                "Direct links between pillar score records and evidence items.",
                pillar_link_df,
                unavailable=pillar_link_unavailable,
                empty_message="No direct pillar evidence links found for this thesis.",
            )

            thesis_event_columns = ["id", "thesis_id", "event_type", "event_description", "created_by", "created_at", "version"]
            thesis_event_available_columns, thesis_event_support = _explorer_available_columns("thesis_events", thesis_event_columns)
            thesis_event_df = pd.DataFrame()
            thesis_event_unavailable = (not thesis_event_support["available"]) or ("thesis_id" not in thesis_event_support["columns"]) or (len(thesis_event_available_columns) == 0)
            if not thesis_event_unavailable:
                event_order_clause = "ORDER BY id DESC"
                if "created_at" in thesis_event_support["columns"]:
                    event_order_clause = "ORDER BY created_at DESC"
                thesis_event_df = fetch_dataframe(
                    f"SELECT {', '.join(thesis_event_available_columns)} FROM thesis_events WHERE thesis_id = ? {event_order_clause}",
                    (selected_thesis_id,),
                )
            _render_explorer_dataset(
                "I. Thesis Events",
                "Audit and workflow event timeline for the selected thesis.",
                thesis_event_df,
                unavailable=thesis_event_unavailable,
            )

            eval_prep_columns = [
                "id",
                "ticker",
                "observation_date",
                "thesis_id",
                "lifecycle_state",
                "workspace_ready",
                "readiness_status",
                "evidence_discovery_status",
                "candidate_count",
                "evidence_acquisition_status",
                "acquired_document_count",
                "extraction_status",
                "extracted_observation_count",
                "extraction_timestamp",
                "extractor_version",
                "created_at",
                "updated_at",
            ]
            eval_prep_available_columns, eval_prep_table_support = _explorer_available_columns("evaluation_preparations", eval_prep_columns)
            eval_prep_df = pd.DataFrame()
            eval_prep_unavailable = (not eval_prep_table_support["available"]) or ("thesis_id" not in eval_prep_table_support["columns"]) or (len(eval_prep_available_columns) == 0)
            if not eval_prep_unavailable:
                eval_prep_df = fetch_dataframe(
                    f"SELECT {', '.join(eval_prep_available_columns)} FROM evaluation_preparations WHERE thesis_id = ? ORDER BY id DESC",
                    (selected_thesis_id,),
                )
            _render_explorer_dataset(
                "J. Evaluation Preparation Data",
                "Preparation-state records used by discovery, acquisition, and extraction workflows.",
                eval_prep_df,
                unavailable=eval_prep_unavailable,
            )

            candidate_columns = [
                "id",
                "preparation_id",
                "thesis_id",
                "title",
                "source",
                "document_type",
                "publication_date",
                "reference_url",
                "reference_id",
                "discovery_status",
                "provider_name",
                "created_at",
            ]
            candidate_available_columns, candidate_table_support = _explorer_available_columns("evaluation_candidate_documents", candidate_columns)
            candidate_df = pd.DataFrame()
            candidate_unavailable = (not candidate_table_support["available"]) or ("thesis_id" not in candidate_table_support["columns"]) or (len(candidate_available_columns) == 0)
            if not candidate_unavailable:
                candidate_df = fetch_dataframe(
                    f"SELECT {', '.join(candidate_available_columns)} FROM evaluation_candidate_documents WHERE thesis_id = ? ORDER BY id DESC",
                    (selected_thesis_id,),
                )
            _render_explorer_dataset(
                "K. Evaluation Candidate Documents",
                "Candidate documents discovered before acquisition for this thesis.",
                candidate_df,
                unavailable=candidate_unavailable,
            )

            acquired_df = pd.DataFrame()
            acquired_unavailable = False
            acquired_support = _schema_table_support("evaluation_acquired_documents", ["thesis_id"])
            if not acquired_support["available"] or "thesis_id" not in acquired_support["columns"]:
                acquired_unavailable = True
            else:
                acquired_select_expressions = []
                for column_name in [
                    "id",
                    "preparation_id",
                    "thesis_id",
                    "title",
                    "source",
                    "document_type",
                    "publication_date",
                    "reference_url",
                    "reference_id",
                    "provider_name",
                    "acquisition_status",
                    "retrieval_timestamp",
                    "source_reference",
                    "content_type",
                    "acquisition_error",
                    "created_at",
                ]:
                    if column_name in acquired_support["columns"]:
                        acquired_select_expressions.append(column_name)

                if "source_content" in acquired_support["columns"]:
                    acquired_select_expressions.append(
                        "CASE WHEN source_content IS NOT NULL AND TRIM(source_content) <> '' THEN 'Yes' ELSE 'No' END AS source_content_exists"
                    )
                    acquired_select_expressions.append("LENGTH(source_content) AS source_content_character_count")
                else:
                    acquired_select_expressions.append("'Unavailable in schema.' AS source_content_exists")
                    acquired_select_expressions.append("NULL AS source_content_character_count")

                if len(acquired_select_expressions) == 0:
                    acquired_unavailable = True
                else:
                    acquired_df = fetch_dataframe(
                        f"SELECT {', '.join(acquired_select_expressions)} FROM evaluation_acquired_documents WHERE thesis_id = ? ORDER BY id DESC",
                        (selected_thesis_id,),
                    )
            _render_explorer_dataset(
                "L. Evaluation Acquired Documents",
                "Acquired document records; source content is represented only by existence and character count fields.",
                acquired_df,
                unavailable=acquired_unavailable,
            )

            extracted_columns = [
                "id",
                "extraction_run_id",
                "preparation_id",
                "thesis_id",
                "acquired_document_id",
                "original_candidate_identifier",
                "source_reference",
                "acquisition_timestamp",
                "extraction_timestamp",
                "extractor_version",
                "passage",
                "pillar_signal",
                "confidence",
                "source_location",
                "created_at",
            ]
            extracted_available_columns, extracted_table_support = _explorer_available_columns("evaluation_extracted_observations", extracted_columns)
            extracted_df = pd.DataFrame()
            extracted_unavailable = (not extracted_table_support["available"]) or ("thesis_id" not in extracted_table_support["columns"]) or (len(extracted_available_columns) == 0)
            if not extracted_unavailable:
                extracted_df = fetch_dataframe(
                    f"SELECT {', '.join(extracted_available_columns)} FROM evaluation_extracted_observations WHERE thesis_id = ? ORDER BY id DESC",
                    (selected_thesis_id,),
                )
            _render_explorer_dataset(
                "M. Evaluation Extracted Observations",
                "Extraction outputs linked to the selected thesis for evidence synthesis review.",
                extracted_df,
                unavailable=extracted_unavailable,
            )

            render_athena_footer()

elif st.session_state['current_view'] == 'Hermes Workflow Inbox':
    st.header("📬 Hermes — Workflow Inbox")

    inbox_tasks = compute_hermes_inbox()
    priority_one_count = sum(1 for task in inbox_tasks if task["priority"] == HERMES_PRIORITY_CRITICAL)
    priority_two_count = sum(1 for task in inbox_tasks if task["priority"] == HERMES_PRIORITY_HIGH)
    priority_three_count = sum(1 for task in inbox_tasks if task["priority"] == HERMES_PRIORITY_MEDIUM)
    priority_four_count = sum(1 for task in inbox_tasks if task["priority"] == HERMES_PRIORITY_LOW)

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        metric_card("Total Tasks", len(inbox_tasks))
    with col2:
        metric_card("Priority 1", priority_one_count)
    with col3:
        metric_card("Priority 2", priority_two_count)
    with col4:
        metric_card("Priority 3", priority_three_count)
    with col5:
        metric_card("Priority 4", priority_four_count)

    if inbox_tasks:
        inbox_rows = []
        for task in inbox_tasks:
            inbox_rows.append(
                {
                    "Priority": int(task["priority"]),
                    "Source": task["source"],
                    "Company": task["company_name"],
                    "Task": task["task_type"],
                    "Due Date": task["due_date"] if task["due_date"] else "—",
                    "Action": task["action"],
                }
            )

        inbox_display_df = pd.DataFrame(inbox_rows).sort_values(
            by=["Priority", "Due Date", "Company"],
            ascending=[True, True, True],
        )
        st.dataframe(inbox_display_df, use_container_width=True)
    else:
        st.info("No workflow items currently require analyst attention.")

elif st.session_state['current_view'] == 'New Thesis':
    st.header("Prepare Evaluation")
    st.caption("Enter a ticker and observation date. Athena will create or resume the evaluation shell and open the Assessment Workspace.")

    with st.container(border=True):
        st.subheader("Generation III Progress Mode")
        st.caption(
            "Create/enable the USWR limited-evidence case for operational observation while HRV-002 remains blocked."
        )
        if st.button("Ensure USWR Limited-Evidence Case", key="ensure_uswr_progress_mode", use_container_width=True):
            uswr_result = ensure_uswr_limited_evidence_case(created_by="Phillip")
            st.session_state["selected_thesis_id"] = int(uswr_result["thesis_id"])
            st.session_state["current_view"] = "Workspace"
            st.success(
                "USWR limited-evidence scaffold is ready. "
                f"thesis_id={int(uswr_result['thesis_id'])}, created={bool(uswr_result['created'])}."
            )
            st.rerun()

    with st.form("prepare_evaluation_form"):
        col1, col2 = st.columns(2)

        with col1:
            ticker = st.text_input("Ticker *", placeholder="e.g., AAPL")

        with col2:
            observation_date = st.date_input(
                "Observation Date *",
                value=datetime.now().date(),
                min_value=datetime(1900, 1, 1).date(),
                help="The engine uses ticker + observation date as the idempotent preparation key.",
            )

        col1, col2 = st.columns(2)

        with col1:
            company_name = st.text_input("Company Name (optional)", placeholder="Optional display name")

        with col2:
            reviewer = st.text_input("Reviewer (optional)", placeholder="Name of reviewer")

        submitted = st.form_submit_button("Prepare Evaluation", use_container_width=True)

        if submitted:
            if not ticker.strip():
                st.error("Ticker is required.")
            else:
                normalized_ticker = ticker.strip().upper()
                st.session_state["active_evaluation_request"] = {
                    "ticker": normalized_ticker,
                    "observation_date": observation_date.isoformat(),
                    "company_name": company_name.strip() if company_name else "",
                    "reviewer": reviewer.strip() if reviewer else "",
                }
                st.session_state["active_evaluation_thesis_id"] = None
                st.session_state["engine_preparation_status"] = None
                st.session_state["pending_prepare_request"] = {
                    "ticker": normalized_ticker,
                    "observation_date": observation_date,
                    "company_name": company_name,
                    "reviewer": reviewer,
                }

                st.session_state["current_view"] = "Home"
                st.rerun()

elif st.session_state['current_view'] in ['Workspace', 'Thesis Detail', 'Thesis Workspace']:
    # Get thesis data
    thesis_id = st.session_state['selected_thesis_id']
    if thesis_id is None:
        render_page_header("Active Evaluation", "What needs judgment now?", eyebrow="Workspace")
        render_friction_logger(default_thesis_id=None, default_workflow_area="Workspace Queue")

        workspace_rows = []
        workspace_theses_df = fetch_dataframe(
            "SELECT id, company_name, ticker, status FROM theses ORDER BY company_name ASC"
        )
        for _, workspace_row in workspace_theses_df.iterrows():
            workspace_tid = int(workspace_row["id"])
            if not is_active_operational_work({"thesis_id": workspace_tid, "status": workspace_row.get("status")}):
                continue

            gate = validate_decision_gate(workspace_tid)
            score_df = fetch_dataframe(
                """
                SELECT
                    SUM(CASE WHEN pillar_id LIKE 'B%' THEN 1 ELSE 0 END) AS business_rows,
                    SUM(CASE WHEN pillar_id LIKE 'I%' THEN 1 ELSE 0 END) AS investment_rows
                FROM pillar_scores
                WHERE thesis_id = ?
                """,
                (workspace_tid,),
            )
            score_row = score_df.iloc[0] if not score_df.empty else None
            business_rows = int(score_row["business_rows"]) if score_row is not None and pd.notna(score_row["business_rows"]) else 0
            investment_rows = int(score_row["investment_rows"]) if score_row is not None and pd.notna(score_row["investment_rows"]) else 0
            stage = _get_workspace_stage(business_rows, investment_rows, gate["eligible"])
            next_action = "Complete governed assessment fields"
            if gate["eligible"]:
                next_action = "Record decision"
            elif gate["missing"]:
                next_action = f"Resolve {len(gate['missing'])} gate blockers"

            workspace_rows.append(
                {
                    "thesis_id": workspace_tid,
                    "Company": workspace_row["company_name"],
                    "Ticker": workspace_row["ticker"] if pd.notna(workspace_row["ticker"]) and str(workspace_row["ticker"]).strip() else "Ticker not assigned",
                    "Current Stage": stage,
                    "Next Recommended Action": next_action,
                    "Current Status": derive_asset_status_label(
                        workspace_row["company_name"],
                        workspace_row["ticker"],
                        workspace_row["status"],
                        thesis_id=workspace_tid,
                        fallback="Status not set",
                    ),
                }
            )

        if not workspace_rows:
            empty_state("No evaluations available. Start from Home using Prepare Evaluation.")
        else:
            gate_ready_count = 0
            framework_review_count = 0
            gate_blocker_count = 0
            for workspace_row in workspace_rows:
                workspace_gate = validate_decision_gate(int(workspace_row["thesis_id"]))
                if workspace_gate.get("eligible"):
                    gate_ready_count += 1
                if int(workspace_row["thesis_id"]) in framework_eligible_ids:
                    framework_review_count += 1
                if workspace_gate.get("missing"):
                    gate_blocker_count += 1

            render_summary_row(
                "Evaluation Queue",
                "Queue first, table second. Open the next evaluation directly from here.",
                [
                    {"label": "Requiring Action", "value": len(workspace_rows)},
                    {"label": "Decision-Ready", "value": gate_ready_count},
                    {"label": "Gate Blockers", "value": gate_blocker_count},
                    {"label": "Framework Eligible", "value": framework_review_count},
                ],
            )
            workspace_df = pd.DataFrame(workspace_rows)
            st.dataframe(
                workspace_df[["Company", "Ticker", "Current Stage", "Next Recommended Action", "Current Status"]],
                use_container_width=True,
            )
            selected_workspace_thesis = st.selectbox(
                "Select Evaluation",
                options=workspace_df["thesis_id"].astype(int).tolist(),
                format_func=lambda tid: f"{int(tid)} — {workspace_df[workspace_df['thesis_id'] == tid].iloc[0]['Company']}",
            )
            if st.button("Open Workspace", use_container_width=True):
                st.session_state['selected_thesis_id'] = int(selected_workspace_thesis)
                st.session_state['current_view'] = 'Workspace'
                st.rerun()
        st.stop()

    thesis_df = fetch_dataframe(
        "SELECT * FROM theses WHERE id = ?",
        (thesis_id,)
    )
    
    if not thesis_df.empty:
        thesis = thesis_df.iloc[0]
        default_validation_review_date, thesis_validation_mode_enabled, thesis_cutoff_date = _resolve_validation_review_date(thesis)
        validation_review_date_blocked = thesis_validation_mode_enabled and thesis_cutoff_date is None
        
        render_page_header(
            "Active Evaluation",
            "What needs judgment now?",
            eyebrow=f"{thesis['company_name']}" if pd.notna(thesis['company_name']) and str(thesis['company_name']).strip() else "Workspace",
        )
        render_governed_save_confirmation()

        workspace_clarity = _build_workspace_clarity_context(thesis_id, thesis)

        engine_preparation_status = st.session_state.get("engine_preparation_status")
        if (
            isinstance(engine_preparation_status, dict)
            and engine_preparation_status.get("thesis_id") == thesis_id
        ):
            render_preparation_status(engine_preparation_status)
        
        # Analyst-first workspace summary
        header_metrics = [
            ("Ticker", workspace_clarity["ticker"] if workspace_clarity["ticker"] else "Ticker not assigned"),
            ("Workflow Status", workspace_clarity["workflow_status"]),
            ("Governed Decision", workspace_clarity["governed_decision"]),
            (
                "Investment Horizon",
                workspace_clarity["investment_horizon"] if workspace_clarity["investment_horizon"] else "Not set",
            ),
        ]
        if workspace_clarity["reviewer"]:
            header_metrics.append(("Reviewer", workspace_clarity["reviewer"]))

        header_columns = st.columns(len(header_metrics))
        for idx, (label, value) in enumerate(header_metrics):
            with header_columns[idx]:
                st.metric(label, value)

        st.info(f"Next action: {workspace_clarity['next_action']}")
        render_friction_logger(default_thesis_id=int(thesis_id), default_workflow_area="Workspace Detail")
        
        st.divider()
        
        # Keep all workspace sections reachable without horizontal scrolling.
        st.markdown(
            """
            <style>
            div[data-baseweb="tab-list"] {
                flex-wrap: wrap;
                row-gap: 0.35rem;
            }
            div[data-baseweb="tab-list"] button {
                height: auto;
                padding-top: 0.25rem;
                padding-bottom: 0.25rem;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

        # Tabs
        tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11 = st.tabs(
            [
                "Assessment",
                "Overview",
                "Evidence",
                "Business",
                "Industry",
                "Financials",
                "Management",
                "Valuation",
                "History",
                "Decision",
                "Audit"
            ]
        )
        
        with tab1:
            render_assessment_workspace(thesis_id, thesis, default_validation_review_date)

        with tab2:
            vm_started = time.perf_counter()
            observe_view_model(
                view_model_name="thesis_overview_vm",
                phase="entry",
                thesis_id=int(thesis_id),
            )
            try:
                thesis_overview_vm = build_thesis_overview_vm(int(thesis_id))
                vm_duration_ms = round((time.perf_counter() - vm_started) * 1000.0, 3)
                observe_view_model(
                    view_model_name="thesis_overview_vm",
                    phase="exit",
                    thesis_id=int(thesis_id),
                    duration_ms=vm_duration_ms,
                    status="success",
                )
            except Exception as exc:
                observe_exception(
                    operation="thesis_overview_view_model",
                    exception=exc,
                    metadata={"thesis_id": int(thesis_id)},
                )
                vm_duration_ms = round((time.perf_counter() - vm_started) * 1000.0, 3)
                observe_view_model(
                    view_model_name="thesis_overview_vm",
                    phase="exit",
                    thesis_id=int(thesis_id),
                    duration_ms=vm_duration_ms,
                    status="failure",
                )
                raise
            render_thesis_overview(thesis_overview_vm)
        
        with tab3:
            # Add Evidence Item Form
            section_header("Add Evidence Item")
            
            with st.form("add_evidence_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    evidence_title = st.text_input("Title *", placeholder="e.g., Archived regression filing (historical)")
                
                with col2:
                    source_type = st.selectbox(
                        "Source Type *",
                        [""] + SOURCE_TYPE_OPTIONS
                    )
                
                col1, col2 = st.columns(2)
                
                with col1:
                    source_publisher = st.text_input("Source / Publisher *", placeholder="e.g., SEC, Bloomberg, Reuters")
                
                with col2:
                    publication_date = st.date_input("Publication Date")

                col1, col2 = st.columns(2)

                with col1:
                    related_pillar = st.selectbox(
                        "Related Business Pillar (Optional)",
                        ["", "B1", "B2", "B3", "B4", "B5", "B6", "B7"]
                    )

                with col2:
                    evidence_grade = st.selectbox(
                        "Evidence Grade (Optional)",
                        ["", GRADE_A, GRADE_B, GRADE_C, GRADE_D]
                    )

                url_or_citation = st.text_input("URL (Optional)", placeholder="https://...")

                summary = st.text_area("Summary *", placeholder="Summarize the evidence", height=100)

                key_takeaway = st.text_area("Key Takeaway *", placeholder="What is the key actionable takeaway?", height=80)

                tags = st.text_input("Tags", placeholder="ai, datacenter, margins")

                col1, col2 = st.columns(2)

                with col1:
                    credibility_score = st.number_input(
                        "Credibility Score (1-10)",
                        min_value=1,
                        max_value=10,
                        value=5
                    )

                with col2:
                    materiality_score = st.number_input(
                        "Materiality Score (1-10)",
                        min_value=1,
                        max_value=10,
                        value=5
                    )

                thesis_alignment = st.selectbox(
                    "Thesis Alignment",
                    ["Bull", "Bear", "Neutral"]
                )
                
                submitted = st.form_submit_button("Add Evidence", use_container_width=True)
                
                if submitted:
                    # Validation
                    if not evidence_title.strip():
                        st.error("Title is required.")
                    elif not source_type:
                        st.error("Source Type is required.")
                    elif not source_publisher.strip():
                        st.error("Source / Publisher is required.")
                    elif not summary.strip():
                        st.error("Summary is required.")
                    elif not key_takeaway.strip():
                        st.error("Key Takeaway is required.")
                    else:
                        # Insert into database
                        insert_query(
                            """
                            INSERT INTO evidence_items
                            (thesis_id, source_name, source_type, publication_date,
                             evidence_grade, url_or_citation, related_pillar, evidence_summary, created_at,
                             title, source_publisher, key_takeaway, tags,
                             credibility_score, materiality_score, thesis_alignment)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                thesis_id,
                                evidence_title.strip(),
                                source_type,
                                publication_date.isoformat() if publication_date else None,
                                evidence_grade if evidence_grade else None,
                                url_or_citation.strip() if url_or_citation else None,
                                related_pillar if related_pillar else None,
                                summary.strip(),
                                datetime.now().isoformat(),
                                evidence_title.strip(),
                                source_publisher.strip(),
                                key_takeaway.strip(),
                                tags.strip() if tags else None,
                                int(credibility_score),
                                int(materiality_score),
                                thesis_alignment
                            )
                        )
                        
                        # Log event
                        event_created_by = thesis['reviewer'] if thesis['reviewer'] else "System"
                        log_event(
                            thesis_id=thesis_id,
                            event_type=EVENT_EVIDENCE_ADDED,
                            description=f"Evidence item added: {evidence_title.strip()}",
                            created_by=event_created_by,
                            version="1.0"
                        )
                        
                        st.success(f"✓ Evidence added: {evidence_title.strip()}")
                        st.rerun()
            
            st.divider()
            
            # Display Evidence Items
            section_header("Evidence Items")
            evidence_df = fetch_dataframe(
                """
                SELECT 
                    id,
                    COALESCE(title, source_name) AS title,
                    source_type,
                    source_publisher,
                    url_or_citation,
                    publication_date,
                    COALESCE(evidence_summary, '') AS summary,
                    key_takeaway,
                    source_text,
                    tags,
                    credibility_score,
                    materiality_score,
                    thesis_alignment,
                    created_at
                FROM evidence_items
                WHERE thesis_id = ?
                ORDER BY created_at DESC
                """,
                (thesis_id,)
            )
            
            if not evidence_df.empty:
                st.dataframe(evidence_df, use_container_width=True)
            else:
                empty_state("No evidence items have been added for this thesis yet.")

            if not evidence_df.empty:
                st.divider()
                section_header("Edit or Delete Evidence")

                evidence_options_df = fetch_dataframe(
                    """
                    SELECT
                        id,
                        COALESCE(title, source_name) AS title,
                        source_type,
                        source_publisher,
                        url_or_citation,
                        publication_date,
                        COALESCE(evidence_summary, '') AS summary,
                        key_takeaway,
                        source_text,
                        tags,
                        credibility_score,
                        materiality_score,
                        thesis_alignment,
                        created_at
                    FROM evidence_items
                    WHERE thesis_id = ?
                    ORDER BY created_at DESC
                    """,
                    (thesis_id,)
                )

                evidence_ids = evidence_options_df["id"].tolist()
                if st.session_state['selected_evidence_id'] not in evidence_ids:
                    st.session_state['selected_evidence_id'] = evidence_ids[0] if evidence_ids else None

                selected_evidence_id = st.selectbox(
                    "Select Evidence Item",
                    evidence_ids,
                    index=evidence_ids.index(st.session_state['selected_evidence_id']) if st.session_state['selected_evidence_id'] in evidence_ids else 0,
                    format_func=lambda ev_id: (
                        f"#{ev_id} - {evidence_options_df[evidence_options_df['id'] == ev_id].iloc[0]['title']}"
                    ),
                    key="evidence_selector"
                )
                st.session_state['selected_evidence_id'] = selected_evidence_id

                selected_df = evidence_options_df[evidence_options_df["id"] == st.session_state['selected_evidence_id']]

                if not selected_df.empty:
                    selected_evidence = selected_df.iloc[0]

                    source_type_options = [""] + SOURCE_TYPE_OPTIONS
                    source_type_default = selected_evidence['source_type'] if pd.notna(selected_evidence['source_type']) else ""
                    source_type_index = source_type_options.index(source_type_default) if source_type_default in source_type_options else 0

                    alignment_options = ["Bull", "Bear", "Neutral"]
                    alignment_default = selected_evidence['thesis_alignment'] if pd.notna(selected_evidence['thesis_alignment']) else "Bull"
                    alignment_index = alignment_options.index(alignment_default) if alignment_default in alignment_options else 0

                    publication_date_default = datetime.now().date()
                    if pd.notna(selected_evidence['publication_date']) and str(selected_evidence['publication_date']).strip() != "":
                        publication_date_default = pd.to_datetime(selected_evidence['publication_date']).date()

                    with st.form("edit_evidence_form"):
                        col1, col2 = st.columns(2)

                        with col1:
                            edit_title = st.text_input(
                                "Title *",
                                value=selected_evidence['title'] if pd.notna(selected_evidence['title']) else ""
                            )

                        with col2:
                            edit_source_type = st.selectbox(
                                "Source Type *",
                                source_type_options,
                                index=source_type_index
                            )

                        col1, col2 = st.columns(2)

                        with col1:
                            edit_source_publisher = st.text_input(
                                "Source / Publisher *",
                                value=selected_evidence['source_publisher'] if pd.notna(selected_evidence['source_publisher']) else ""
                            )

                        with col2:
                            edit_publication_date = st.date_input(
                                "Publication Date",
                                value=publication_date_default
                            )

                        edit_url = st.text_input(
                            "URL (Optional)",
                            value=selected_evidence['url_or_citation'] if pd.notna(selected_evidence['url_or_citation']) else ""
                        )

                        edit_summary = st.text_area(
                            "Summary *",
                            value=selected_evidence['summary'] if pd.notna(selected_evidence['summary']) else "",
                            height=100
                        )

                        edit_key_takeaway = st.text_area(
                            "Key Takeaway *",
                            value=selected_evidence['key_takeaway'] if pd.notna(selected_evidence['key_takeaway']) else "",
                            height=80
                        )

                        edit_source_text = st.text_area(
                            "Relevant Source Text (Optional)",
                            value=selected_evidence['source_text'] if pd.notna(selected_evidence['source_text']) else "",
                            height=160,
                            help="Paste the sections of the document most relevant to your assessment. Full documents are accepted, but focused excerpts produce better extraction results."
                        )

                        edit_tags = st.text_input(
                            "Tags",
                            value=selected_evidence['tags'] if pd.notna(selected_evidence['tags']) else ""
                        )

                        col1, col2 = st.columns(2)

                        with col1:
                            edit_credibility_score = st.number_input(
                                "Credibility Score (1-10)",
                                min_value=1,
                                max_value=10,
                                value=int(selected_evidence['credibility_score']) if pd.notna(selected_evidence['credibility_score']) else 5
                            )

                        with col2:
                            edit_materiality_score = st.number_input(
                                "Materiality Score (1-10)",
                                min_value=1,
                                max_value=10,
                                value=int(selected_evidence['materiality_score']) if pd.notna(selected_evidence['materiality_score']) else 5
                            )

                        edit_thesis_alignment = st.selectbox(
                            "Thesis Alignment",
                            alignment_options,
                            index=alignment_index
                        )

                        edit_submitted = st.form_submit_button("Save Evidence Changes", use_container_width=True)

                        if edit_submitted:
                            if not edit_title.strip():
                                st.error("Title is required.")
                            elif not edit_source_type:
                                st.error("Source Type is required.")
                            elif not edit_source_publisher.strip():
                                st.error("Source / Publisher is required.")
                            elif not edit_summary.strip():
                                st.error("Summary is required.")
                            elif not edit_key_takeaway.strip():
                                st.error("Key Takeaway is required.")
                            else:
                                updated = update_evidence_item(
                                    evidence_item_id=st.session_state['selected_evidence_id'],
                                    source_name=edit_title.strip(),
                                    title=edit_title.strip(),
                                    source_type=edit_source_type,
                                    source_publisher=edit_source_publisher.strip(),
                                    url_or_citation=edit_url.strip() if edit_url else None,
                                    publication_date=edit_publication_date.isoformat() if edit_publication_date else None,
                                    evidence_summary=edit_summary.strip(),
                                    key_takeaway=edit_key_takeaway.strip(),
                                    source_text=edit_source_text,
                                    tags=edit_tags.strip() if edit_tags else None,
                                    credibility_score=int(edit_credibility_score),
                                    materiality_score=int(edit_materiality_score),
                                    thesis_alignment=edit_thesis_alignment,
                                    thesis_id=thesis_id,
                                    updated_by=thesis['reviewer'] if thesis['reviewer'] else "System",
                                )

                                if not updated:
                                    st.error("Evidence item update failed.")
                                else:
                                    st.success("✓ Evidence item updated")
                                    st.session_state['selected_evidence_id'] = None
                                    st.rerun()

                    st.write("")
                    confirm = st.checkbox("Confirm deletion of this evidence item")
                    if confirm:
                        if st.button("Delete"):
                            delete_title = selected_evidence['title'] if pd.notna(selected_evidence['title']) else f"Evidence #{st.session_state['selected_evidence_id']}"
                            run_query(
                                "DELETE FROM evidence_items WHERE id = ? AND thesis_id = ?",
                                (st.session_state['selected_evidence_id'], thesis_id)
                            )

                            event_created_by = thesis['reviewer'] if thesis['reviewer'] else "System"
                            log_event(
                                thesis_id=thesis_id,
                                event_type=EVENT_EVIDENCE_DELETED,
                                description=f"Evidence item deleted: {delete_title}",
                                created_by=event_created_by,
                                version="1.0"
                            )

                            st.success("✓ Evidence item deleted")
                            st.session_state['selected_evidence_id'] = None
                            st.rerun()

            st.divider()
            section_header("Theia v1 — Governed Evidence Staging")

            all_thesis_options_df = fetch_dataframe(
                "SELECT id, company_name FROM theses ORDER BY company_name ASC"
            )
            all_thesis_ids = all_thesis_options_df["id"].astype(int).tolist() if not all_thesis_options_df.empty else []
            thesis_option_values = [None] + all_thesis_ids
            default_thesis_index = 0
            if thesis_id in thesis_option_values:
                default_thesis_index = thesis_option_values.index(thesis_id)

            with st.form("theia_intake_form"):
                intake_thesis_id = st.selectbox(
                    "Thesis",
                    options=thesis_option_values,
                    index=default_thesis_index,
                    format_func=lambda tid: (
                        "— Unassigned —"
                        if tid is None
                        else f"{int(tid)} — {all_thesis_options_df[all_thesis_options_df['id'] == int(tid)].iloc[0]['company_name']}"
                    ),
                    key="theia_intake_thesis_id"
                )

                col1, col2 = st.columns(2)
                with col1:
                    intake_source_type = st.selectbox(
                        "Source Type",
                        options=[""] + SOURCE_TYPE_OPTIONS,
                        key="theia_intake_source_type"
                    )
                with col2:
                    intake_preliminary_grade = st.selectbox(
                        "Preliminary Grade",
                        options=[""] + [GRADE_A, GRADE_B, GRADE_C, GRADE_D],
                        key="theia_intake_preliminary_grade"
                    )

                intake_source_name = st.text_input("Source Name", key="theia_intake_source_name")
                intake_source_url = st.text_input("Source URL", key="theia_intake_source_url")

                col1, col2 = st.columns(2)
                with col1:
                    intake_publication_date = st.date_input(
                        "Publication Date",
                        value=datetime.now().date(),
                        min_value=datetime(1900, 1, 1).date(),
                        key="theia_intake_publication_date"
                    )
                with col2:
                    intake_retrieval_date = st.date_input(
                        "Retrieval Date",
                        value=datetime.now().date(),
                        min_value=datetime(1900, 1, 1).date(),
                        key="theia_intake_retrieval_date"
                    )

                intake_author_publisher = st.text_input("Author / Publisher", key="theia_intake_author_publisher")
                intake_evidence_summary = st.text_area("Evidence Summary", height=90, key="theia_intake_summary")
                intake_key_takeaway = st.text_area("Key Takeaway", height=90, key="theia_intake_key_takeaway")
                intake_source_text = st.text_area(
                    "Relevant Source Text",
                    height=180,
                    key="theia_intake_source_text",
                    help="Paste the sections of the document most relevant to your assessment. Full documents are accepted, but focused excerpts produce better extraction results."
                )
                intake_source_quality_notes = st.text_area("Source Quality Notes", height=90, key="theia_intake_quality_notes")

                intake_duplicate_flag = st.checkbox("Duplicate Flag", value=False, key="theia_intake_duplicate_flag")
                intake_duplicate_notes = st.text_area("Duplicate Notes", height=70, key="theia_intake_duplicate_notes")
                intake_created_by = st.text_input(
                    "Created By",
                    value=thesis['reviewer'] if thesis['reviewer'] else "System",
                    key="theia_intake_created_by"
                )
                intake_cutoff_acknowledged = st.checkbox(
                    "I understand this evidence will remain in staging until it satisfies the constitutional promotion rules.",
                    value=False,
                    key="theia_intake_cutoff_ack"
                )

                intake_submitted = st.form_submit_button("Stage Evidence", use_container_width=True)

                if intake_submitted:
                    requires_cutoff_advisory = False
                    advisory_cutoff_date = None

                    if intake_thesis_id is not None:
                        intake_thesis_df = fetch_dataframe(
                            "SELECT validation_mode, evidence_cutoff_date FROM theses WHERE id = ? LIMIT 1",
                            (int(intake_thesis_id),)
                        )
                        if not intake_thesis_df.empty:
                            intake_thesis_row = intake_thesis_df.iloc[0]
                            intake_validation_mode = int(intake_thesis_row["validation_mode"]) == 1 if pd.notna(intake_thesis_row["validation_mode"]) else False
                            if intake_validation_mode and pd.notna(intake_thesis_row["evidence_cutoff_date"]) and str(intake_thesis_row["evidence_cutoff_date"]).strip():
                                advisory_cutoff_date = pd.to_datetime(intake_thesis_row["evidence_cutoff_date"]).date()
                                if intake_publication_date and intake_publication_date > advisory_cutoff_date:
                                    requires_cutoff_advisory = True

                    if requires_cutoff_advisory:
                        st.warning(
                            "Historical Validation Notice\n\n"
                            f"This evidence was published after the historical evidence cutoff ({advisory_cutoff_date.isoformat()}). The evidence may still be staged for review, but it cannot be promoted into the thesis while historical validation mode remains active."
                        )
                        if not intake_cutoff_acknowledged:
                            st.warning("Acknowledgment is required before staging this post-cutoff evidence.")
                        else:
                            staging_uuid = stage_evidence(
                                intake_thesis_id=intake_thesis_id,
                                intake_source_type=intake_source_type,
                                intake_source_name=intake_source_name,
                                intake_source_url=intake_source_url,
                                intake_publication_date=intake_publication_date,
                                intake_retrieval_date=intake_retrieval_date,
                                intake_author_publisher=intake_author_publisher,
                                intake_evidence_summary=intake_evidence_summary,
                                intake_key_takeaway=intake_key_takeaway,
                                intake_preliminary_grade=intake_preliminary_grade,
                                intake_source_quality_notes=intake_source_quality_notes,
                                intake_duplicate_flag=intake_duplicate_flag,
                                intake_duplicate_notes=intake_duplicate_notes,
                                intake_created_by=intake_created_by,
                            )

                            update_staged_evidence_source_text(
                                staging_uuid=staging_uuid,
                                source_text=intake_source_text,
                            )

                            st.success(f"✓ Evidence staged with UUID: {staging_uuid}")
                            st.rerun()
                    else:
                        staging_uuid = stage_evidence(
                            intake_thesis_id=intake_thesis_id,
                            intake_source_type=intake_source_type,
                            intake_source_name=intake_source_name,
                            intake_source_url=intake_source_url,
                            intake_publication_date=intake_publication_date,
                            intake_retrieval_date=intake_retrieval_date,
                            intake_author_publisher=intake_author_publisher,
                            intake_evidence_summary=intake_evidence_summary,
                            intake_key_takeaway=intake_key_takeaway,
                            intake_preliminary_grade=intake_preliminary_grade,
                            intake_source_quality_notes=intake_source_quality_notes,
                            intake_duplicate_flag=intake_duplicate_flag,
                            intake_duplicate_notes=intake_duplicate_notes,
                            intake_created_by=intake_created_by,
                        )

                        update_staged_evidence_source_text(
                            staging_uuid=staging_uuid,
                            source_text=intake_source_text,
                        )

                        st.success(f"✓ Evidence staged with UUID: {staging_uuid}")
                        st.rerun()

            st.divider()
            section_header("Theia Intake Review Queue")

            status_filter_options = ["All"] + INTAKE_STATUS_OPTIONS
            selected_status_filter = st.selectbox(
                "Filter by Intake Status",
                options=status_filter_options,
                key="theia_status_filter"
            )

            staging_query = "SELECT * FROM evidence_staging WHERE thesis_id = ?"
            staging_params = (thesis_id,)
            if selected_status_filter != "All":
                staging_query += " AND intake_status = ?"
                staging_params = (thesis_id, selected_status_filter)
            staging_query += " ORDER BY created_at DESC"

            staging_df = fetch_dataframe(staging_query, staging_params)

            if staging_df.empty:
                empty_state("No staged evidence records found for this filter.")
            else:
                queue_display_df = staging_df[
                    [
                        "staging_uuid",
                        "intake_status",
                        "source_name",
                        "source_type",
                        "preliminary_grade",
                        "duplicate_flag",
                        "archive_reason",
                        "reviewed_by",
                        "review_date",
                        "promoted_evidence_id",
                        "created_at",
                    ]
                ].copy()
                queue_display_df = queue_display_df.rename(
                    columns={
                        "staging_uuid": "Staging UUID",
                        "intake_status": "Status",
                        "source_name": "Source Name",
                        "source_type": "Source Type",
                        "preliminary_grade": "Prelim Grade",
                        "duplicate_flag": "Duplicate",
                        "archive_reason": "Archive Reason",
                        "reviewed_by": "Reviewed By",
                        "review_date": "Review Date",
                        "promoted_evidence_id": "Promoted Evidence ID",
                        "created_at": "Created At",
                    }
                )
                st.dataframe(queue_display_df, use_container_width=True)

                staging_uuid_options = staging_df["staging_uuid"].astype(str).tolist()
                selected_staging_uuid = st.selectbox(
                    "Select Staged Evidence",
                    options=staging_uuid_options,
                    key="theia_selected_staging_uuid"
                )

                selected_staging_df = staging_df[staging_df["staging_uuid"] == selected_staging_uuid]
                selected_staging = selected_staging_df.iloc[0] if not selected_staging_df.empty else None

                if selected_staging is not None:
                    current_status = str(selected_staging["intake_status"]).strip() if pd.notna(selected_staging["intake_status"]) else INTAKE_STATUS_PENDING
                    summary_field("Current Status", current_status)
                    summary_field("Source Name", selected_staging["source_name"] if pd.notna(selected_staging["source_name"]) else "—")
                    summary_field("Summary", selected_staging["evidence_summary"] if pd.notna(selected_staging["evidence_summary"]) else "—")
                    summary_field("Duplicate Notes", selected_staging["duplicate_notes"] if pd.notna(selected_staging["duplicate_notes"]) else "—")

                    reviewer_name = st.text_input(
                        "Analyst",
                        value=thesis['reviewer'] if thesis['reviewer'] else "System",
                        key="theia_reviewer_name"
                    )

                    rejection_reason_input = st.text_area(
                        "Rejection Reason (required for rejection)",
                        value="",
                        key="theia_rejection_reason"
                    )

                    archive_reason_input = st.text_area(
                        "Archive Reason (required for archive)",
                        value="",
                        key="theia_archive_reason"
                    )

                    if current_status in TERMINAL_INTAKE_STATUSES:
                        st.info(f"Status is terminal ({current_status}). No further status transitions are allowed.")
                    else:
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            if current_status == INTAKE_STATUS_PENDING and st.button("Mark as Reviewed", key="theia_mark_reviewed"):
                                result = update_staged_evidence_status(
                                    staging_uuid=selected_staging_uuid,
                                    target_status=INTAKE_STATUS_REVIEWED,
                                    reviewer_name=reviewer_name,
                                    rejection_reason_input=rejection_reason_input,
                                    thesis_id=int(selected_staging["thesis_id"]) if pd.notna(selected_staging["thesis_id"]) else None,
                                )
                                if result["success"]:
                                    st.success(result["message"])
                                    st.rerun()
                                st.error(result["message"])

                        with col2:
                            if current_status == INTAKE_STATUS_REVIEWED and st.button("Mark as Confirmed", key="theia_mark_confirmed"):
                                result = update_staged_evidence_status(
                                    staging_uuid=selected_staging_uuid,
                                    target_status=INTAKE_STATUS_CONFIRMED,
                                    reviewer_name=reviewer_name,
                                    rejection_reason_input=rejection_reason_input,
                                    thesis_id=int(selected_staging["thesis_id"]) if pd.notna(selected_staging["thesis_id"]) else None,
                                )
                                if result["success"]:
                                    st.success(result["message"])
                                    st.rerun()
                                st.error(result["message"])

                        with col3:
                            if current_status == INTAKE_STATUS_REVIEWED and st.button("Mark as Rejected", key="theia_mark_rejected"):
                                result = update_staged_evidence_status(
                                    staging_uuid=selected_staging_uuid,
                                    target_status=INTAKE_STATUS_REJECTED,
                                    reviewer_name=reviewer_name,
                                    rejection_reason_input=rejection_reason_input,
                                    thesis_id=int(selected_staging["thesis_id"]) if pd.notna(selected_staging["thesis_id"]) else None,
                                )
                                if result["success"]:
                                    st.success(result["message"])
                                    st.rerun()
                                st.error(result["message"])

                        with col4:
                            if st.button("Archive Staged Evidence", key="theia_archive_staged"):
                                archive_result = archive_staged_evidence(
                                    staging_uuid=selected_staging_uuid,
                                    analyst=reviewer_name,
                                    archive_reason=archive_reason_input,
                                )
                                if archive_result["success"]:
                                    st.success(archive_result["message"])
                                    st.rerun()
                                st.error(archive_result["message"])

                        if current_status == INTAKE_STATUS_CONFIRMED:
                            if st.button("Promote to Evidence Repository", key="theia_promote_confirmed"):
                                promotion_result = promote_staged_evidence(
                                    staging_uuid=selected_staging_uuid,
                                    analyst=reviewer_name.strip() if reviewer_name else "System"
                                )
                                if promotion_result["success"]:
                                    st.success(f"✓ Promoted to evidence_items ID {promotion_result['promoted_evidence_id']}")
                                    st.rerun()
                                else:
                                    st.error(promotion_result["message"])

            st.divider()
            section_header("Governed Evidence Observations (MVP-022)")

            promoted_evidence_df = fetch_dataframe(
                """
                SELECT id, title, source_name, publication_date, evidence_grade
                FROM evidence_items
                WHERE thesis_id = ? AND COALESCE(status, 'Promoted') = 'Promoted'
                ORDER BY publication_date DESC, id DESC
                """,
                (thesis_id,),
            )

            if promoted_evidence_df.empty:
                empty_state("No promoted evidence items available for governed observations.")
            else:
                promoted_ids = promoted_evidence_df["id"].astype(int).tolist()
                promoted_labels = {}
                for _, row in promoted_evidence_df.iterrows():
                    evidence_id = int(row["id"])
                    title = str(row["title"]).strip() if pd.notna(row["title"]) and str(row["title"]).strip() else "—"
                    source_name = str(row["source_name"]).strip() if pd.notna(row["source_name"]) and str(row["source_name"]).strip() else "—"
                    publication_date = str(row["publication_date"]).strip() if pd.notna(row["publication_date"]) and str(row["publication_date"]).strip() else "—"
                    evidence_grade = str(row["evidence_grade"]).strip() if pd.notna(row["evidence_grade"]) and str(row["evidence_grade"]).strip() else "—"
                    promoted_labels[evidence_id] = (
                        f"#{evidence_id} | {title} | Source: {source_name} | Date: {publication_date} | Grade: {evidence_grade}"
                    )

                selected_observation_evidence_id = st.selectbox(
                    "Select Promoted Evidence Item",
                    options=promoted_ids,
                    format_func=lambda evidence_id: promoted_labels.get(evidence_id, f"#{evidence_id}"),
                    key="observation_selected_evidence_id",
                )

                st.caption("Theia Extraction (Ephemeral)")
                extraction_suggestions = []
                if st.button("Extract Passages", key="theia_extract_passages_button", use_container_width=True):
                    extraction_result = get_extraction_suggestions(
                        evidence_item_id=selected_observation_evidence_id,
                    )
                    extraction_suggestions = extraction_result.get("suggestions", [])

                    if extraction_result.get("success"):
                        st.success(extraction_result.get("message", "Extraction completed."))
                    else:
                        st.error(extraction_result.get("message", "Extraction failed."))

                if extraction_suggestions:
                    st.write("Suggested Passages (Ephemeral)")
                    for idx, suggestion in enumerate(extraction_suggestions, start=1):
                        with st.expander(f"Suggestion {idx}", expanded=False):
                            st.write(suggestion.get("passage", ""))
                            st.caption(
                                f"Pillar Signal: {suggestion.get('pillar_signal') or '—'} | "
                                f"Confidence: {suggestion.get('confidence') or '—'} | "
                                f"Source Location: {suggestion.get('source_location') or '—'}"
                            )

                            if st.button("Use Pillar In Observation Form", key=f"theia_use_suggestion_{idx}"):
                                if suggestion.get("pillar_signal"):
                                    st.session_state["observation_pillar_id"] = suggestion.get("pillar_signal")
                                st.session_state["observation_text"] = ""
                                st.success("Pillar pre-populated. Observation text remains blank.")

                with st.form("observation_create_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        observation_pillar_id = st.selectbox(
                            "Pillar ID",
                            options=["B1", "B2", "B3", "B4", "B5", "B6", "B7", "I1", "I2", "I3", "I4"],
                            key="observation_pillar_id",
                        )
                    with col2:
                        observation_category = st.selectbox(
                            "Observation Category",
                            options=OBSERVATION_CATEGORY_OPTIONS,
                            key="observation_category",
                        )

                    observation_text = st.text_area(
                        "Observation Text",
                        height=100,
                        key="observation_text",
                    )
                    evidence_quote = st.text_area(
                        "Evidence Quote",
                        height=80,
                        key="observation_evidence_quote",
                    )
                    source_location = st.text_input(
                        "Source Location",
                        key="observation_source_location",
                    )

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        analyst_confidence = st.selectbox(
                            "Analyst Confidence",
                            options=["Low", "Medium", "High"],
                            index=2,
                            key="observation_analyst_confidence",
                        )
                    with col2:
                        created_by = st.text_input(
                            "Created By",
                            value=thesis['reviewer'] if thesis['reviewer'] else "System",
                            key="observation_created_by",
                        )
                    with col3:
                        observation_status = st.selectbox(
                            "Status",
                            options=OBSERVATION_STATUS_OPTIONS,
                            index=OBSERVATION_STATUS_OPTIONS.index(OBSERVATION_STATUS_ACTIVE),
                            key="observation_status",
                        )

                    create_observation_submitted = st.form_submit_button("Create Observation", use_container_width=True)

                    if create_observation_submitted:
                        try:
                            creation_result = create_evidence_observation(
                                evidence_item_id=selected_observation_evidence_id,
                                pillar_id=observation_pillar_id,
                                observation_category=observation_category,
                                observation_text=observation_text,
                                evidence_quote=evidence_quote,
                                source_location=source_location,
                                analyst_confidence=analyst_confidence,
                                created_by=created_by,
                                status=observation_status,
                            )
                            if creation_result["success"]:
                                st.success(f"✓ Observation created (ID {creation_result['observation_id']})")
                                st.toast("Governed observation persisted. You may safely continue.")
                                queue_governed_save_confirmation(
                                    "Governed Observation",
                                    detail_label=f"ID {creation_result['observation_id']}",
                                )
                                st.rerun()
                            else:
                                st.error(creation_result["message"])
                        except ValueError as exc:
                            st.error(str(exc))

                observations_for_evidence_df = get_observations_for_evidence(selected_observation_evidence_id)
                st.caption("Observations for Selected Evidence Item")
                if observations_for_evidence_df.empty:
                    st.info("No observations recorded for this evidence item.")
                else:
                    st.dataframe(observations_for_evidence_df, use_container_width=True)

                    observation_id_options = observations_for_evidence_df["id"].astype(int).tolist()
                    selected_observation_id = st.selectbox(
                        "Select Observation to Update",
                        options=observation_id_options,
                        key="observation_selected_update_id",
                    )
                    selected_observation_df = observations_for_evidence_df[
                        observations_for_evidence_df["id"] == selected_observation_id
                    ]
                    selected_observation = selected_observation_df.iloc[0] if not selected_observation_df.empty else None

                    if selected_observation is not None:
                        observation_update_signature = (
                            selected_observation_evidence_id,
                            selected_observation_id,
                            selected_observation.get("pillar_id"),
                            selected_observation.get("observation_category"),
                            selected_observation.get("observation_text"),
                            selected_observation.get("evidence_quote"),
                            selected_observation.get("source_location"),
                            selected_observation.get("analyst_confidence"),
                            selected_observation.get("status"),
                        )
                        if st.session_state.get("observation_update_signature") != observation_update_signature:
                            st.session_state["observation_update_signature"] = observation_update_signature
                            st.session_state["observation_update_pillar_id"] = str(selected_observation["pillar_id"]) if pd.notna(selected_observation["pillar_id"]) else ""
                            current_category = str(selected_observation["observation_category"]).strip() if pd.notna(selected_observation["observation_category"]) else OBSERVATION_CATEGORY_OPTIONS[0]
                            st.session_state["observation_update_category"] = current_category if current_category in OBSERVATION_CATEGORY_OPTIONS else OBSERVATION_CATEGORY_OPTIONS[0]
                            st.session_state["observation_update_text"] = str(selected_observation["observation_text"]) if pd.notna(selected_observation["observation_text"]) else ""
                            st.session_state["observation_update_quote"] = str(selected_observation["evidence_quote"]) if pd.notna(selected_observation["evidence_quote"]) else ""
                            st.session_state["observation_update_source_location"] = str(selected_observation["source_location"]) if pd.notna(selected_observation["source_location"]) else ""
                            current_confidence = str(selected_observation["analyst_confidence"]).strip() if pd.notna(selected_observation["analyst_confidence"]) else "Medium"
                            st.session_state["observation_update_confidence"] = current_confidence if current_confidence in ["Low", "Medium", "High"] else "Medium"
                            current_status = str(selected_observation["status"]).strip() if pd.notna(selected_observation["status"]) else OBSERVATION_STATUS_ACTIVE
                            st.session_state["observation_update_status"] = current_status if current_status in OBSERVATION_STATUS_OPTIONS else OBSERVATION_STATUS_ACTIVE
                            st.session_state["observation_updated_by"] = thesis['reviewer'] if thesis['reviewer'] else "System"

                        with st.form("observation_update_form"):
                            col1, col2 = st.columns(2)
                            with col1:
                                update_pillar_id = st.text_input(
                                    "Update Pillar ID",
                                    key="observation_update_pillar_id",
                                )
                            with col2:
                                update_observation_category = st.selectbox(
                                    "Update Category",
                                    options=OBSERVATION_CATEGORY_OPTIONS,
                                    key="observation_update_category",
                                )

                            update_observation_text = st.text_area(
                                "Update Observation Text",
                                height=100,
                                key="observation_update_text",
                            )
                            update_evidence_quote = st.text_area(
                                "Update Evidence Quote",
                                height=80,
                                key="observation_update_quote",
                            )
                            update_source_location = st.text_input(
                                "Update Source Location",
                                key="observation_update_source_location",
                            )

                            col1, col2, col3 = st.columns(3)
                            with col1:
                                update_analyst_confidence = st.selectbox(
                                    "Update Analyst Confidence",
                                    options=["Low", "Medium", "High"],
                                    key="observation_update_confidence",
                                )
                            with col2:
                                update_status = st.selectbox(
                                    "Update Status",
                                    options=OBSERVATION_STATUS_OPTIONS,
                                    key="observation_update_status",
                                )
                            with col3:
                                update_by = st.text_input(
                                    "Updated By",
                                    key="observation_updated_by",
                                )

                            update_submitted = st.form_submit_button("Update Observation", use_container_width=True)
                            if update_submitted:
                                try:
                                    update_result = update_evidence_observation(
                                        observation_id=selected_observation_id,
                                        pillar_id=update_pillar_id,
                                        observation_category=update_observation_category,
                                        observation_text=update_observation_text,
                                        evidence_quote=update_evidence_quote,
                                        source_location=update_source_location,
                                        analyst_confidence=update_analyst_confidence,
                                        status=update_status,
                                        updated_by=update_by,
                                    )
                                    if update_result["success"]:
                                        st.success("✓ Observation updated")
                                        st.toast("Governed observation persisted. You may safely continue.")
                                        queue_governed_save_confirmation(
                                            "Governed Observation",
                                            detail_label=f"ID {selected_observation_id}",
                                        )
                                        st.rerun()
                                    else:
                                        st.error(update_result["message"])
                                except ValueError as exc:
                                    st.error(str(exc))

                pillar_filter = st.selectbox(
                    "View Observations by Pillar",
                    options=["B1", "B2", "B3", "B4", "B5", "B6", "B7", "I1", "I2", "I3", "I4"],
                    key="observation_pillar_filter",
                )
                observations_for_pillar_df = get_observations_for_pillar(thesis_id=thesis_id, pillar_id=pillar_filter)
                st.caption(f"Observations for Thesis {thesis_id} / Pillar {pillar_filter}")
                if observations_for_pillar_df.empty:
                    st.info("No observations found for the selected pillar.")
                else:
                    st.dataframe(observations_for_pillar_df, use_container_width=True)
        
        with tab4:
            section_header("Business Quality Scoring")

            coverage = get_business_evidence_coverage(thesis_id)
            st.caption("Evidence Coverage")
            st.dataframe(
                pd.DataFrame(coverage),
                use_container_width=True,
            )

            pillar_options = [
                "B1 Business Quality",
                "B2 Competitive Advantage",
                "B3 Revenue Quality",
                "B4 Financial Resilience",
                "B5 Execution Capability",
                "B6 Industry Position",
                "B7 Systems Importance"
            ]
            selected_pillar = st.selectbox("Select Pillar to Score", pillar_options, key="business_pillar")

            pillar_id = selected_pillar.split(" ", 1)[0]
            pillar_name = selected_pillar.split(" ", 1)[1]

            synthesis = get_athena_evidence_synthesis(thesis_id=thesis_id, pillar_id=pillar_id)

            st.subheader("Athena Evidence Synthesis")

            st.markdown("**1. Governed Observations**")
            governed_rows = synthesis.get("governed_observations", [])
            if not governed_rows:
                st.caption("No governed observations currently mapped to this pillar.")
            else:
                governed_df = pd.DataFrame(governed_rows)
                governed_view = governed_df[
                    [
                        "label",
                        "observation_id",
                        "observation_text",
                        "observation_category",
                        "evidence_item_id",
                        "evidence_title",
                        "analyst_confidence",
                    ]
                ]
                st.dataframe(governed_view, use_container_width=True)

            st.markdown("**2. Advisory Extraction Signals**")
            advisory_rows = synthesis.get("advisory_signals", [])
            if not advisory_rows:
                st.caption("No advisory extraction signals available for this pillar.")
            else:
                advisory_df = pd.DataFrame(advisory_rows)
                advisory_view = advisory_df[
                    [
                        "label",
                        "evidence_item_id",
                        "evidence_title",
                        "passage",
                        "pillar_signal",
                        "confidence",
                        "source_location",
                    ]
                ]
                st.dataframe(advisory_view, use_container_width=True)

            st.markdown("**3. Supporting Evidence**")
            supporting_rows = synthesis.get("supporting_evidence", [])
            if not supporting_rows:
                st.caption("No promoted evidence currently linked to this pillar.")
            else:
                supporting_df = pd.DataFrame(supporting_rows)
                supporting_view = supporting_df[
                    [
                        "evidence_item_id",
                        "publication_date",
                        "source_name",
                        "title",
                        "source_publisher",
                        "evidence_grade",
                    ]
                ]
                st.dataframe(supporting_view, use_container_width=True)

            st.markdown("**4. Coverage Summary**")
            coverage = synthesis.get("coverage", {})
            coverage_df = pd.DataFrame(
                [
                    {
                        "Governed Observations": int(coverage.get("governed_observation_count", 0)),
                        "Advisory Signals": int(coverage.get("advisory_signal_count", 0)),
                        "Evidence Items": int(coverage.get("evidence_item_count", 0)),
                    }
                ]
            )
            st.dataframe(coverage_df, use_container_width=True)

            st.divider()

            existing_df = fetch_dataframe(
                "SELECT * FROM pillar_scores WHERE thesis_id = ? AND pillar_id = ?",
                (thesis_id, pillar_id)
            )
            existing_record = existing_df.iloc[0] if not existing_df.empty else None

            available_evidence_ids, available_evidence_labels = get_available_evidence_items(thesis_id)
            linked_evidence_defaults = []
            if existing_record is not None and pd.notna(existing_record['id']):
                linked_evidence_defaults = get_linked_evidence_ids(int(existing_record['id']))

            judgment_default = ""
            if existing_record is not None:
                if 'judgment' in existing_record.index and pd.notna(existing_record['judgment']) and str(existing_record['judgment']).strip() != "":
                    judgment_default = str(existing_record['judgment'])
                elif pd.notna(existing_record['inference']) and str(existing_record['inference']).strip() != "":
                    judgment_default = str(existing_record['inference'])

            with st.form("business_quality_scoring_form"):
                if pillar_id == "B1":
                    st.info("A high gross margin score should reflect durability and trend direction, not just the current level — a declining margin at 70% may score lower than a stable margin at 45%.")
                elif pillar_id == "B2":
                    st.info("Score the structural barrier, not the product — ask how long a well-funded competitor would need to replicate the company's market position, not whether the product is good.")
                elif pillar_id == "B3":
                    st.info("Prioritize recurring, contracted, or subscription revenue over transactional revenue — evaluate what percentage of next year's revenue is already secured.")
                elif pillar_id == "B4":
                    st.info("Financial resilience should account for non-linearity: unusually high cash positions relative to revenue may indicate inefficient capital allocation rather than strength.")
                elif pillar_id == "B5":
                    st.info("Score against stated commitments, not absolute performance — a company that consistently delivers 90% of guidance scores higher than one that occasionally delivers 120% unpredictably.")
                elif pillar_id == "B6":
                    st.info("A dominant position in a declining industry is not the same as a strong position in a growing one — the score should reflect both current standing and structural trajectory.")
                elif pillar_id == "B7":
                    st.info("Systems importance should account for dependency quality: reliance on a single government program or contract should not automatically receive a high score.")

                selected_evidence_links = st.multiselect(
                    "Linked Evidence Items",
                    options=available_evidence_ids,
                    default=linked_evidence_defaults,
                    format_func=lambda evidence_id: available_evidence_labels.get(evidence_id, f"#{evidence_id}"),
                    help="Link one or more evidence items to this pillar score."
                )

                col1, col2 = st.columns(2)

                with col1:
                    score = st.number_input(
                        "Score (1-10)",
                        min_value=1,
                        max_value=10,
                        value=int(existing_record['score']) if existing_record is not None and pd.notna(existing_record['score']) else 5
                    )

                with col2:
                    rag_options = [RAG_GREEN, RAG_YELLOW, RAG_ORANGE, RAG_RED]
                    rag_default_idx = 0
                    if existing_record is not None and pd.notna(existing_record['rag_status']):
                        try:
                            rag_default_idx = rag_options.index(existing_record['rag_status'])
                        except ValueError:
                            rag_default_idx = 0
                    rag_status = st.selectbox("RAG Status", rag_options, index=rag_default_idx)

                col1, col2 = st.columns(2)

                with col1:
                    grade_options = [GRADE_A, GRADE_B, GRADE_C, GRADE_D]
                    grade_default_idx = 0
                    if existing_record is not None and pd.notna(existing_record['evidence_grade']):
                        try:
                            grade_default_idx = grade_options.index(existing_record['evidence_grade'])
                        except ValueError:
                            grade_default_idx = 0
                    evidence_grade = st.selectbox("Evidence Grade", grade_options, index=grade_default_idx)

                with col2:
                    confidence_basis = st.text_input(
                        "Confidence Basis (why you trust or distrust this judgment)",
                        value=existing_record['confidence_basis'] if existing_record is not None and pd.notna(existing_record['confidence_basis']) else ""
                    )

                judgment = st.text_area(
                    "Judgment",
                    value=judgment_default,
                    height=80
                )

                falsification_trigger = st.text_input(
                    "Falsification Trigger",
                    value=existing_record['falsification_trigger'] if existing_record is not None and pd.notna(existing_record['falsification_trigger']) else ""
                )

                col1, col2 = st.columns(2)

                with col1:
                    reviewer = st.text_input(
                        "Reviewer",
                        value=existing_record['reviewer'] if existing_record is not None and pd.notna(existing_record['reviewer']) else ""
                    )

                with col2:
                    review_date = st.date_input(
                        "Review Date",
                        value=pd.to_datetime(existing_record['review_date']).date() if existing_record is not None and pd.notna(existing_record['review_date']) else default_validation_review_date
                    )

                submitted = st.form_submit_button("Save Business Quality Score", use_container_width=True)

                if submitted:
                    if validation_review_date_blocked:
                        st.error("Validation mode requires evidence_cutoff_date before pillar scores can be saved.")
                    else:
                        created_by = reviewer.strip() if reviewer and reviewer.strip() else (thesis['reviewer'] if thesis['reviewer'] else "System")
                        pillar_result = save_pillar_score(
                            thesis_id=thesis_id,
                            pillar_id=pillar_id,
                            pillar_name=pillar_name,
                            score=score,
                            rag_status=rag_status,
                            evidence_grade=evidence_grade,
                            judgment=judgment,
                            confidence_basis=confidence_basis,
                            falsification_trigger=falsification_trigger,
                            reviewer=reviewer,
                            review_date=review_date,
                            created_by=created_by,
                        )
                        pillar_score_id = pillar_result["pillar_score_id"]

                        if pillar_result["is_update"]:
                            st.success(f"✓ Business assessment updated for {pillar_id} {pillar_name}")
                        else:
                            st.success(f"✓ Business assessment saved for {pillar_id} {pillar_name}")

                        st.toast("Business assessment persisted. You may safely continue.")
                        queue_governed_save_confirmation(
                            "Business Assessment",
                            detail_label=f"{pillar_id} {pillar_name}",
                        )

                        if pillar_score_id is None:
                            st.error("Unable to resolve pillar_score_id; evidence links were not synchronized.")
                        else:
                            sync_pillar_evidence_links(
                                pillar_score_id=pillar_score_id,
                                selected_evidence_ids=selected_evidence_links,
                                created_by=created_by
                            )

                        st.rerun()
            
            st.divider()
            
            # Display Business Assessment Scores
            section_header("Business Assessment Scores")
            business_df = fetch_dataframe(
                """
                SELECT 
                    pillar_id, pillar_name, score, rag_status, evidence_grade,
                    judgment, inference_confidence
                FROM pillar_scores
                WHERE thesis_id = ? AND pillar_id LIKE 'B%'
                ORDER BY pillar_id ASC
                """,
                (st.session_state['selected_thesis_id'],)
            )
            
            if not business_df.empty:
                rag_map = {
                    RAG_GREEN: "🟢 Green",
                    RAG_YELLOW: "🟡 Yellow",
                    RAG_ORANGE: "🟠 Orange",
                    RAG_RED: "🔴 Red"
                }

                business_df["Pillar"] = business_df.apply(
                    lambda row: f"{row['pillar_id']} — {row['pillar_name']}" if isinstance(row['pillar_name'], str) and row['pillar_name'].strip() else str(row['pillar_id']),
                    axis=1
                )
                business_df["RAG Status"] = business_df["rag_status"].apply(
                    lambda x: rag_map.get(x, "— Unknown")
                )
                business_df["Evidence Grade"] = business_df["evidence_grade"].apply(
                    lambda x: x if isinstance(x, str) and x.strip() else "—"
                )
                business_df["Judgment"] = business_df["judgment"].apply(
                    lambda x: (x[:60] + "...") if isinstance(x, str) and len(x) > 60 else (x or "—")
                )
                business_df["Confidence"] = business_df["inference_confidence"].apply(
                    lambda x: x if isinstance(x, str) and x.strip() else "—"
                )

                summary_df = business_df[["Pillar", "score", "RAG Status", "Evidence Grade", "Judgment", "Confidence"]].rename(
                    columns={"score": "Score"}
                )

                st.dataframe(summary_df, use_container_width=True)
            else:
                empty_state("No business assessment scores have been added for this thesis yet.")
        
        with tab5:
            empty_state("Industry Module Coming Next")

        with tab6:
            # Add Investment Assessment Form
            section_header("Add Investment Assessment")

            # Pillar selection (outside form to enable preloading)
            pillar_options = [
                "",
                "I1 Valuation",
                "I2 Market Structure",
                "I3 Market Sentiment",
                "I4 Portfolio Contribution"
            ]
            selected_pillar = st.selectbox("Select Pillar to Edit *", pillar_options, key="invest_pillar")

            # Check for existing record
            existing_record = None
            existing_pillar_score_id = None
            if selected_pillar and selected_pillar != "":
                pillar_id_check = selected_pillar.split(" ", 1)[0]
                existing_df = fetch_dataframe(
                    "SELECT * FROM pillar_scores WHERE thesis_id = ? AND pillar_id = ?",
                    (thesis_id, pillar_id_check)
                )
                if not existing_df.empty:
                    existing_record = existing_df.iloc[0]
                    existing_pillar_score_id = int(existing_record['id']) if pd.notna(existing_record['id']) else None

            investment_judgment_default = ""
            if existing_record is not None:
                if 'judgment' in existing_record.index and pd.notna(existing_record['judgment']) and str(existing_record['judgment']).strip() != "":
                    investment_judgment_default = str(existing_record['judgment'])
                elif pd.notna(existing_record['inference']) and str(existing_record['inference']).strip() != "":
                    investment_judgment_default = str(existing_record['inference'])

            record_signature = (
                selected_pillar,
                None if existing_record is None else existing_record.get('confidence_basis'),
                None if existing_record is None else existing_record.get('primary_sources'),
                None if existing_record is None else existing_record.get('judgment'),
                None if existing_record is None else existing_record.get('inference'),
                None if existing_record is None else existing_record.get('falsification_trigger'),
                None if existing_record is None else existing_record.get('reviewer'),
                None if existing_record is None else existing_record.get('review_date'),
                None if existing_record is None else existing_record.get('drl'),
                None if existing_record is None else existing_record.get('score'),
                None if existing_record is None else existing_record.get('rag_status'),
                None if existing_record is None else existing_record.get('evidence_grade'),
            )
            if st.session_state.get("invest_record_signature") != record_signature:
                st.session_state["invest_record_signature"] = record_signature
                st.session_state["invest_score"] = int(existing_record['score']) if existing_record is not None and pd.notna(existing_record['score']) else 5
                st.session_state["invest_rag"] = existing_record['rag_status'] if existing_record is not None and pd.notna(existing_record['rag_status']) else ""
                st.session_state["invest_grade"] = existing_record['evidence_grade'] if existing_record is not None and pd.notna(existing_record['evidence_grade']) else ""
                st.session_state["invest_conf_basis"] = existing_record['confidence_basis'] if existing_record is not None and pd.notna(existing_record['confidence_basis']) else ""
                st.session_state["invest_sources"] = existing_record['primary_sources'] if existing_record is not None and pd.notna(existing_record['primary_sources']) else ""
                st.session_state["invest_judgment"] = investment_judgment_default
                st.session_state["invest_fals"] = existing_record['falsification_trigger'] if existing_record is not None and pd.notna(existing_record['falsification_trigger']) else ""
                st.session_state["invest_reviewer"] = existing_record['reviewer'] if existing_record is not None and pd.notna(existing_record['reviewer']) else ""
                st.session_state["invest_date"] = pd.to_datetime(existing_record['review_date']).date() if existing_record is not None and pd.notna(existing_record['review_date']) else default_validation_review_date
                st.session_state["invest_drl"] = existing_record['drl'] if existing_record is not None and pd.notna(existing_record['drl']) else ""
                st.session_state["invest_links"] = linked_evidence_defaults
            else:
                st.session_state.setdefault("invest_links", linked_evidence_defaults)

            available_evidence_ids, available_evidence_labels = get_available_evidence_items(thesis_id)
            linked_evidence_defaults = []
            if existing_pillar_score_id is not None:
                linked_evidence_defaults = get_linked_evidence_ids(existing_pillar_score_id)

            with st.form("investment_assessment_form"):
                col1, col2 = st.columns(2)

                with col1:
                    score = st.number_input(
                        "Score (1-10)",
                        min_value=1,
                        max_value=10,
                        value=int(existing_record['score']) if existing_record is not None and pd.notna(existing_record['score']) else 5,
                        key="invest_score"
                    )

                with col2:
                    rag_options = ["", RAG_GREEN, RAG_YELLOW, RAG_ORANGE, RAG_RED]
                    rag_default_idx = 0
                    if existing_record is not None and pd.notna(existing_record['rag_status']):
                        try:
                            rag_default_idx = rag_options.index(existing_record['rag_status'])
                        except ValueError:
                            rag_default_idx = 0
                    rag_status = st.selectbox(
                        "RAG Status",
                        rag_options,
                        index=rag_default_idx,
                        key="invest_rag"
                    )

                col1, col2 = st.columns(2)

                with col1:
                    grade_options = ["", GRADE_A, GRADE_B, GRADE_C, GRADE_D]
                    grade_default_idx = 0
                    if existing_record is not None and pd.notna(existing_record['evidence_grade']):
                        try:
                            grade_default_idx = grade_options.index(existing_record['evidence_grade'])
                        except ValueError:
                            grade_default_idx = 0
                    evidence_grade = st.selectbox(
                        "Evidence Grade",
                        grade_options,
                        index=grade_default_idx,
                        key="invest_grade"
                    )

                with col2:
                    confidence_basis = st.text_input(
                        "Confidence Basis *",
                        value=existing_record['confidence_basis'] if existing_record is not None and pd.notna(existing_record['confidence_basis']) else "",
                        placeholder="e.g., Expert Opinion, Statistical Analysis",
                        key="invest_conf_basis"
                    )

                col1, col2 = st.columns(2)

                with col1:
                    primary_sources = st.text_input(
                        "Primary Sources",
                        value=existing_record['primary_sources'] if existing_record is not None and pd.notna(existing_record['primary_sources']) else "",
                        placeholder="List of primary sources",
                        key="invest_sources"
                    )

                with col2:
                    selected_evidence_links = st.multiselect(
                        "Linked Evidence Items",
                        options=available_evidence_ids,
                        key="invest_links",
                        format_func=lambda evidence_id: available_evidence_labels.get(evidence_id, f"#{evidence_id}"),
                        help="Link one or more evidence items to this investment pillar score."
                    )

                judgment = st.text_area(
                    "Judgment",
                    value=investment_judgment_default,
                    placeholder="What is your judgment from this assessment?",
                    height=80,
                    key="invest_judgment"
                )

                col1, col2 = st.columns(2)

                with col1:
                    st.write("")

                with col2:
                    falsification_trigger = st.text_input(
                        "Falsification Trigger *",
                        value=existing_record['falsification_trigger'] if existing_record is not None and pd.notna(existing_record['falsification_trigger']) else "",
                        placeholder="What would prove this wrong?",
                        key="invest_fals"
                    )

                col1, col2 = st.columns(2)

                with col1:
                    reviewer = st.text_input(
                        "Reviewer",
                        value=existing_record['reviewer'] if existing_record is not None and pd.notna(existing_record['reviewer']) else "",
                        placeholder="Name of reviewer",
                        key="invest_reviewer"
                    )

                with col2:
                    review_date = st.date_input(
                        "Review Date",
                        value=pd.to_datetime(existing_record['review_date']).date() if existing_record is not None and pd.notna(existing_record['review_date']) else default_validation_review_date,
                        key="invest_date"
                    )

                col1, col2 = st.columns(2)

                with col1:
                    drl_options = [""] + list(range(1, 10))
                    drl_default_idx = 0
                    if existing_record is not None and pd.notna(existing_record['drl']):
                        try:
                            drl_default_idx = drl_options.index(existing_record['drl'])
                        except ValueError:
                            drl_default_idx = 0
                    drl = st.selectbox("DRL", drl_options, index=drl_default_idx, key="invest_drl")

                with col2:
                    st.write("")  # Spacer

                submitted = st.form_submit_button("Save Assessment", use_container_width=True, key="invest_submit")

                if submitted:
                    # Validation
                    if validation_review_date_blocked:
                        st.error("Validation mode requires evidence_cutoff_date before pillar scores can be saved.")
                    if not selected_pillar or selected_pillar == "":
                        st.error("Pillar is required.")
                    elif not confidence_basis.strip():
                        st.error("Confidence Basis is required.")
                    elif not judgment.strip():
                        st.error("Judgment is required.")
                    elif not falsification_trigger.strip():
                        st.error("Falsification Trigger is required.")
                    elif not validation_review_date_blocked:
                        # Split pillar into ID and name
                        pillar_parts = selected_pillar.split(" ", 1)
                        pillar_id = pillar_parts[0]
                        pillar_name = pillar_parts[1] if len(pillar_parts) > 1 else ""

                        # Determine created_by
                        if reviewer.strip():
                            created_by = reviewer.strip()
                        elif thesis['reviewer']:
                            created_by = thesis['reviewer']
                        else:
                            created_by = "System"

                        pillar_result = save_pillar_score(
                            thesis_id=thesis_id,
                            pillar_id=pillar_id,
                            pillar_name=pillar_name,
                            score=score,
                            rag_status=rag_status,
                            evidence_grade=evidence_grade,
                            judgment=judgment,
                            confidence_basis=confidence_basis,
                            falsification_trigger=falsification_trigger,
                            reviewer=reviewer,
                            review_date=review_date,
                            created_by=created_by,
                            primary_sources=primary_sources,
                            drl=drl,
                        )
                        pillar_score_id = pillar_result["pillar_score_id"]

                        if pillar_result["is_update"]:
                            st.success(f"✓ Investment assessment updated for {pillar_id} {pillar_name}")
                        else:
                            st.success(f"✓ Investment assessment saved for {pillar_id} {pillar_name}")

                        st.toast("Investment assessment persisted. You may safely continue.")
                        queue_governed_save_confirmation(
                            "Investment Assessment",
                            detail_label=f"{pillar_id} {pillar_name}",
                        )

                        if pillar_score_id is None:
                            st.error("Unable to resolve pillar_score_id; evidence links were not synchronized.")
                        else:
                            sync_pillar_evidence_links(
                                pillar_score_id=pillar_score_id,
                                selected_evidence_ids=selected_evidence_links,
                                created_by=created_by
                            )

                        st.rerun()

            st.divider()

            # Display Investment Assessment Scores
            section_header("Investment Assessment Scores")
            investment_df = fetch_dataframe(
                """
                SELECT
                    pillar_id, pillar_name, score, rag_status, evidence_grade,
                    confidence_basis, primary_sources, evidence_items, inference,
                    inference_confidence, falsification_trigger, score_rationale,
                    reviewer, review_date, drl, created_at
                FROM pillar_scores
                WHERE thesis_id = ? AND pillar_id LIKE 'I%'
                ORDER BY pillar_id
                """,
                (thesis_id,)
            )

            if not investment_df.empty:
                st.dataframe(investment_df, use_container_width=True)
            else:
                empty_state("No investment assessment scores have been added for this thesis yet.")

        with tab7:
            empty_state("Management Module Coming Next")

        with tab8:
            empty_state("Valuation Module Coming Next")
        
        with tab9:
            section_header("Historical Validation / Thesis Review")

            decision_context_df = fetch_dataframe(
                """
                SELECT *
                FROM decision_logs
                WHERE thesis_id = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (thesis_id,)
            )

            if decision_context_df.empty:
                st.info("No recorded decision exists yet. A thesis review cannot be created until a governed decision has been recorded.")
            else:
                decision_context = decision_context_df.iloc[0]
                decision_log_id = int(decision_context["id"])

                st.caption("Decision Record (Read-Only Context)")
                summary_field("Decision Log ID", decision_context["id"])
                summary_field_if_present("Recommendation", decision_context["recommendation"])
                summary_field_if_present("Review Date", decision_context["review_date"])
                summary_field_if_present("Horizon Map", decision_context["horizon_map"])
                summary_field_if_present("Action", decision_context["action"])
                summary_field_if_present("Decision Rationale", decision_context["decision_rationale"])
                summary_field_if_present("Key Risks", decision_context["key_risks"])
                summary_field_if_present("Falsification Summary", decision_context["falsification_summary"])
                summary_field_if_present("Next Review Date", decision_context["next_review_date"])
                summary_field_if_present("Created At", decision_context["created_at"])

                st.divider()

                review_horizon = st.selectbox(
                    "Review Horizon",
                    REVIEW_HORIZON_OPTIONS,
                    key="thesis_review_horizon"
                )

                existing_review_df = fetch_dataframe(
                    """
                    SELECT *
                    FROM thesis_reviews
                    WHERE thesis_id = ? AND decision_log_id = ? AND review_horizon = ?
                    LIMIT 1
                    """,
                    (thesis_id, decision_log_id, review_horizon)
                )
                existing_review = existing_review_df.iloc[0] if not existing_review_df.empty else None

                default_review_date = default_validation_review_date
                if existing_review is not None and pd.notna(existing_review["review_date"]):
                    default_review_date = pd.to_datetime(existing_review["review_date"]).date()

                default_outcome_type_idx = 0
                if existing_review is not None and pd.notna(existing_review["outcome_attribution_type"]):
                    existing_outcome_type = str(existing_review["outcome_attribution_type"])
                    if existing_outcome_type in OUTCOME_TYPE_OPTIONS:
                        default_outcome_type_idx = OUTCOME_TYPE_OPTIONS.index(existing_outcome_type)

                with st.form("thesis_review_form"):
                    review_date = st.date_input(
                        "Review Date",
                        value=default_review_date,
                        key="thesis_review_date"
                    )

                    outcome_attribution_type = st.selectbox(
                        "Outcome Attribution Type",
                        OUTCOME_TYPE_OPTIONS,
                        index=default_outcome_type_idx,
                        key="thesis_review_outcome_type"
                    )

                    outcome_summary = st.text_area(
                        "Outcome Summary",
                        value=existing_review["outcome_summary"] if existing_review is not None and pd.notna(existing_review["outcome_summary"]) else "",
                        height=90,
                        key="thesis_review_outcome_summary"
                    )

                    outcome_evidence = st.text_area(
                        "Outcome Evidence",
                        value=existing_review["outcome_evidence"] if existing_review is not None and pd.notna(existing_review["outcome_evidence"]) else "",
                        height=90,
                        key="thesis_review_outcome_evidence"
                    )

                    thesis_quality_assessment = st.text_area(
                        "Thesis Quality Assessment",
                        value=existing_review["thesis_quality_assessment"] if existing_review is not None and pd.notna(existing_review["thesis_quality_assessment"]) else "",
                        height=90,
                        key="thesis_review_quality_assessment"
                    )

                    decision_quality_preserved = st.checkbox(
                        "Decision Quality Preserved",
                        value=bool(existing_review["decision_quality_preserved"]) if existing_review is not None and pd.notna(existing_review["decision_quality_preserved"]) else True,
                        key="thesis_review_decision_quality_preserved"
                    )

                    decision_quality_notes = st.text_area(
                        "Decision Quality Notes",
                        value=existing_review["decision_quality_notes"] if existing_review is not None and pd.notna(existing_review["decision_quality_notes"]) else "",
                        height=90,
                        key="thesis_review_decision_quality_notes"
                    )

                    framework_review_eligible = 1 if outcome_attribution_type == OUTCOME_TYPE_A else 0
                    st.write(
                        f"Framework Review Consideration Eligible: {'Yes' if framework_review_eligible == 1 else 'No'}"
                    )

                    framework_notes = st.text_area(
                        "Framework Notes",
                        value=existing_review["framework_notes"] if existing_review is not None and pd.notna(existing_review["framework_notes"]) else "",
                        height=90,
                        key="thesis_review_framework_notes"
                    )

                    reviewer = st.text_input(
                        "Reviewer",
                        value=existing_review["reviewer"] if existing_review is not None and pd.notna(existing_review["reviewer"]) else (thesis["reviewer"] if thesis["reviewer"] else ""),
                        key="thesis_review_reviewer"
                    )

                    review_submitted = st.form_submit_button("Save Thesis Review", use_container_width=True)

                    if review_submitted:
                        if not review_horizon:
                            st.error("Review Horizon is required.")
                        elif not outcome_attribution_type:
                            st.error("Outcome Attribution Type is required.")
                        elif not reviewer.strip():
                            st.error("Reviewer is required.")
                        else:
                            review_result = save_thesis_review(
                                thesis_id=thesis_id,
                                decision_log_id=decision_log_id,
                                review_date=review_date,
                                review_horizon=review_horizon,
                                outcome_summary=outcome_summary,
                                outcome_attribution_type=outcome_attribution_type,
                                outcome_evidence=outcome_evidence,
                                thesis_quality_assessment=thesis_quality_assessment,
                                decision_quality_preserved=decision_quality_preserved,
                                decision_quality_notes=decision_quality_notes,
                                framework_notes=framework_notes,
                                reviewer=reviewer,
                            )

                            if review_result["is_update"]:
                                st.success("✓ Thesis review updated")
                            else:
                                st.success("✓ Thesis review created")

                            st.rerun()

                st.divider()
                section_header("Existing Thesis Reviews")
                reviews_df = fetch_dataframe(
                    """
                    SELECT
                        review_horizon,
                        review_date,
                        outcome_attribution_type,
                        framework_review_eligible,
                        reviewer,
                        created_at
                    FROM thesis_reviews
                    WHERE thesis_id = ?
                    ORDER BY review_date DESC
                    """,
                    (thesis_id,)
                )

                if not reviews_df.empty:
                    st.dataframe(reviews_df, use_container_width=True)
                else:
                    empty_state("No thesis reviews have been recorded for this thesis yet.")

        with tab10:
            gate_result = validate_decision_gate(thesis_id)

            existing_decision_df = fetch_dataframe(
                "SELECT * FROM decision_logs WHERE thesis_id = ? ORDER BY id DESC LIMIT 1",
                (thesis_id,)
            )
            existing_decision = existing_decision_df.iloc[0] if not existing_decision_df.empty else None

            section_header("Governed Decision Summary")
            summary_field(
                "Recommendation",
                _display_text(existing_decision["recommendation"]) if existing_decision is not None and _display_text(existing_decision["recommendation"]) else "Not recorded",
            )
            summary_field(
                "Decision Status",
                "Recorded" if existing_decision is not None else "Not Recorded",
            )
            summary_field(
                "Review Date",
                _display_text(existing_decision["review_date"]) if existing_decision is not None and _display_text(existing_decision["review_date"]) else "Not recorded",
            )
            summary_field(
                "Investment Horizon",
                _display_text(existing_decision["horizon_map"]) if existing_decision is not None and _display_text(existing_decision["horizon_map"]) else "Not recorded",
            )
            summary_field(
                "Decision Gate Status",
                "Decision Eligible" if gate_result["eligible"] else f"Decision Blocked ({len(gate_result['missing'])} requirements remaining)",
            )
            st.info(
                "Next action: "
                + (
                    "Decision Recorded"
                    if existing_decision is not None
                    else ("Record Decision" if gate_result["eligible"] else "Continue Assessment")
                )
            )
            st.divider()

            section_header("Themis Constitutional Validation")
            if gate_result["eligible"]:
                st.success("🟢 Decision Eligible")
            else:
                st.error("🔴 Decision Blocked")

            st.write(f"Completed: {gate_result['completed']} / {gate_result['required']}")
            if gate_result["missing"]:
                st.write("Missing Requirements:")
                for item in gate_result["missing"]:
                    st.write(f"- {item['pillar_id']} — {item['label']}")
            st.caption(f"Validated at: {gate_result['validated_at']}")
            st.divider()

            # Decision Form
            section_header("Record Decision")

            if is_validation_configuration_locked(thesis_id):
                st.caption("Validation configuration is locked for this thesis because a decision record exists.")

            decision_form_signature = (
                None if existing_decision is None else existing_decision.get("id"),
                None if existing_decision is None else existing_decision.get("recommendation"),
                None if existing_decision is None else existing_decision.get("review_date"),
                None if existing_decision is None else existing_decision.get("horizon_map"),
                None if existing_decision is None else existing_decision.get("action"),
                None if existing_decision is None else existing_decision.get("decision_rationale"),
                None if existing_decision is None else existing_decision.get("key_risks"),
                None if existing_decision is None else existing_decision.get("falsification_summary"),
                None if existing_decision is None else existing_decision.get("next_review_date"),
            )
            if st.session_state.get("decision_form_signature") != decision_form_signature:
                st.session_state["decision_form_signature"] = decision_form_signature
                st.session_state["decision_rec"] = existing_decision['recommendation'] if existing_decision is not None and pd.notna(existing_decision['recommendation']) else ""
                st.session_state["decision_date"] = pd.to_datetime(existing_decision['review_date']).date() if existing_decision is not None and pd.notna(existing_decision['review_date']) else datetime.now().date()
                st.session_state["decision_horizon"] = existing_decision['horizon_map'] if existing_decision is not None and pd.notna(existing_decision['horizon_map']) else ""
                st.session_state["decision_action"] = existing_decision['action'] if existing_decision is not None and pd.notna(existing_decision['action']) else ""
                st.session_state["decision_rationale"] = existing_decision['decision_rationale'] if existing_decision is not None and pd.notna(existing_decision['decision_rationale']) else ""
                st.session_state["decision_risks"] = existing_decision['key_risks'] if existing_decision is not None and pd.notna(existing_decision['key_risks']) else ""
                st.session_state["decision_false"] = existing_decision['falsification_summary'] if existing_decision is not None and pd.notna(existing_decision['falsification_summary']) else ""
                st.session_state["decision_next_review"] = pd.to_datetime(existing_decision['next_review_date']).date() if existing_decision is not None and pd.notna(existing_decision['next_review_date']) else datetime.now().date()
            
            with st.form("decision_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    recommendation_options = ["", "Observe", "Ready with Conditions", "Ready", "High Conviction", "Avoid", "Hold", "Sell"]
                    current_recommendation = st.session_state.get("decision_rec", "")
                    if current_recommendation not in recommendation_options:
                        st.session_state["decision_rec"] = ""
                    recommendation = st.selectbox(
                        "Recommendation",
                        recommendation_options,
                        key="decision_rec"
                    )
                
                with col2:
                    review_date = st.date_input(
                        "Review Date",
                        key="decision_date"
                    )
                
                horizon_map = st.text_area(
                    "Horizon Map",
                    placeholder="e.g., 1-Year: Observe | 3-Year: Ready with Conditions | 10-Year: High Conviction",
                    height=80,
                    key="decision_horizon"
                )
                
                action = st.text_area(
                    "Action",
                    placeholder="What action should be taken?",
                    height=80,
                    key="decision_action"
                )
                
                decision_rationale = st.text_area(
                    "Decision Rationale",
                    placeholder="Explain the reasoning behind this decision",
                    height=80,
                    key="decision_rationale"
                )
                
                key_risks = st.text_area(
                    "Key Risks",
                    placeholder="What are the key risks?",
                    height=80,
                    key="decision_risks"
                )
                
                falsification_summary = st.text_area(
                    "Falsification Summary",
                    placeholder="Summary of falsification criteria",
                    height=80,
                    key="decision_false"
                )
                
                next_review_date = st.date_input(
                    "Next Review Date",
                    key="decision_next_review"
                )
                
                submitted = st.form_submit_button("Save Decision", use_container_width=True, key="decision_submit")
                
                if submitted:
                    gate_result = validate_decision_gate(thesis_id)
                    if not gate_result["eligible"]:
                        st.error("Decision blocked by Themis Constitutional Validation.")
                        for item in gate_result["missing"]:
                            st.write(f"- {item['pillar_id']} — {item['label']}")
                    else:
                        record_decision(
                            thesis_id=thesis_id,
                            recommendation=recommendation,
                            horizon_map=horizon_map,
                            action=action,
                            review_date=review_date,
                            decision_rationale=decision_rationale,
                            key_risks=key_risks,
                            falsification_summary=falsification_summary,
                            next_review_date=next_review_date,
                            existing_decision=existing_decision,
                            validated_at=gate_result["validated_at"],
                            created_by=thesis['reviewer'] if thesis['reviewer'] else "System",
                        )

                        st.success("✓ Decision saved")
                        st.toast("Decision persisted. You may safely continue.")
                        queue_governed_save_confirmation("Decision Gate")
                        st.rerun()
            
            st.divider()
            
            # Display existing decision
            section_header("Current Decision")
            if existing_decision is not None:
                summary_field_if_present("Recommendation", existing_decision['recommendation'])
                summary_field_if_present("Review Date", existing_decision['review_date'])
                summary_field_if_present("Horizon Map", existing_decision['horizon_map'])
                summary_field_if_present("Action", existing_decision['action'])
            else:
                empty_state("No decision has been recorded for this thesis yet.")
        
        with tab11:
            # Audit Trail
            section_header("Audit Trail")
            
            events_df = fetch_dataframe(
                "SELECT created_at, event_type, event_description, created_by FROM thesis_events WHERE thesis_id = ? ORDER BY created_at DESC",
                (thesis_id,)
            )
            
            if not events_df.empty:
                metric_card("Total Events", len(events_df))
                
                # Format timestamp to be human-readable
                events_df['Timestamp'] = pd.to_datetime(events_df['created_at']).dt.strftime('%Y-%m-%d %H:%M:%S')
                display_df = events_df[['Timestamp', 'event_type', 'event_description', 'created_by']].copy()
                display_df.columns = ['Timestamp', 'Event Type', 'Description', 'Created By']
                
                st.divider()
                st.dataframe(display_df, use_container_width=True)
            else:
                metric_card("Total Events", 0)
                st.divider()
                empty_state("No audit events have been recorded for this thesis yet.")
        
    else:
        st.error("Selected thesis could not be found.")

elif st.session_state['current_view'] == 'Settings':
    render_page_header("Settings", "How is Athena configured?", eyebrow="Settings")
    render_governance_badge()

    render_section_title("Documentation")
    st.info("Operational guides, governance references, and workflow notes are centralized here.")
    st.markdown(
        "- Workflow: Prepare -> Review -> Decide\n"
        "- Governance: Themis constitutional validation remains authoritative\n"
        "- Review: Historical attribution captured in History"
    )

    render_section_title("Governance")
    governance_theses_df = fetch_dataframe("SELECT id FROM theses ORDER BY id ASC")
    if governance_theses_df.empty:
        st.info("No theses available for governance reporting.")
    else:
        governance_ids = governance_theses_df["id"].astype(int).tolist()
        governance_ready = 0
        for governance_tid in governance_ids:
            if validate_decision_gate(governance_tid)["eligible"]:
                governance_ready += 1
        st.write(f"Decision-ready evaluations: {governance_ready} / {len(governance_ids)}")

    render_section_title("System Information")
    system_counts_df = fetch_dataframe(
        """
        SELECT
            (SELECT COUNT(*) FROM theses) AS thesis_count,
            (SELECT COUNT(*) FROM evidence_items) AS evidence_count,
            (SELECT COUNT(*) FROM decision_logs) AS decision_count,
            (SELECT COUNT(*) FROM thesis_reviews) AS review_count
        """
    )
    if not system_counts_df.empty:
        system_row = system_counts_df.iloc[0]
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            metric_card("Theses", int(system_row["thesis_count"]))
        with col2:
            metric_card("Evidence Items", int(system_row["evidence_count"]))
        with col3:
            metric_card("Decisions", int(system_row["decision_count"]))
        with col4:
            metric_card("Reviews", int(system_row["review_count"]))

    render_section_title("Developer Tools")
    metric_card("Instrumentation Events", get_event_count())
    export_payload = export_events_json(indent=2)
    st.download_button(
        "Download Instrumentation JSON",
        data=export_payload,
        file_name="athena_instrumentation.json",
        mime="application/json",
        use_container_width=True,
    )

    render_section_title("Preferences")
    st.session_state.setdefault("athena_pref_compact_tables", False)
    st.session_state.setdefault("athena_pref_show_workflow_hints", True)
    st.checkbox("Compact table view", key="athena_pref_compact_tables")
    st.checkbox("Show workflow hints", key="athena_pref_show_workflow_hints")
    st.caption("Preferences are session-scoped for this runtime.")

    render_section_title("About Athena")
    st.markdown("Athena is the analyst operating system for governed investment workflow.")
    st.caption("Doctrine: Does this help the analyst know what to do next within five seconds?")

elif st.session_state['current_view'] == 'Documentation':
    st.session_state['current_view'] = 'History'
    st.rerun()

