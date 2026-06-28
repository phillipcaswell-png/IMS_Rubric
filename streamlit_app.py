import streamlit as st
import pandas as pd
import json
import time
from datetime import datetime
from evaluation_engine import prepare_evaluation
from services import (
    init_db,
    run_query,
    fetch_dataframe,
    insert_query,
    is_validation_configuration_locked,
    log_event,
    get_overview_metrics,
    get_business_evidence_coverage,
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
    padding: 2rem 3rem;
    max-width: 1100px;
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


def render_workspace_header(analyst_name=None, primary_text="Continue where you left off."):
    """Render Workspace header copy in approved order."""
    st.markdown("## Athena")
    if analyst_name:
        st.markdown(f"Good morning, {analyst_name}.")
    st.caption(primary_text)


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
    st.session_state["current_view"] = "Thesis Workspace"
    st.rerun()


def render_preparation_status(status_obj):
    """Render the latest engine preparation status using the canonical object."""
    if not status_obj or not isinstance(status_obj, dict):
        return

    readiness_status = str(status_obj.get("readiness_status", "pending")).strip()
    lifecycle_state = str(status_obj.get("lifecycle_state", "preparing")).strip()
    preparation_action = str(status_obj.get("preparation_action", "unknown")).strip()
    thesis_action = str(status_obj.get("thesis_action", "unknown")).strip()
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

    available_evidence_ids, available_evidence_labels = get_available_evidence_items(thesis_id)
    linked_evidence_defaults = get_linked_evidence_ids(pillar_score_id) if pillar_score_id is not None else []
    context = _build_assessment_workspace_context(thesis_id, pillar_id)
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

    with left_col:
        st.subheader(pillar_meta["domain"])
        st.caption(f"Focused Pillar: {pillar_id} — {pillar_name}")
        if pillar_id in BUSINESS_PILLAR_GUIDANCE:
            st.info(BUSINESS_PILLAR_GUIDANCE[pillar_id])

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
        st.text_area(
            "Reasoning Draft",
            key=f"assessment_workspace_reasoning_{thesis_id}_{pillar_id}",
            placeholder="Draft your reasoning here. This remains working context until governed fields are approved.",
            height=120,
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

        st.session_state.setdefault(score_key, int(existing_record["score"]) if existing_record is not None and pd.notna(existing_record["score"]) else 5)
        default_rag_options = [RAG_GREEN, RAG_YELLOW, RAG_ORANGE, RAG_RED] if pillar_id.startswith("B") else ["", RAG_GREEN, RAG_YELLOW, RAG_ORANGE, RAG_RED]
        default_rag_value = existing_record["rag_status"] if existing_record is not None and pd.notna(existing_record["rag_status"]) else default_rag_options[0]
        if default_rag_value not in default_rag_options:
            default_rag_value = default_rag_options[0]
        st.session_state.setdefault(rag_key, default_rag_value)
        default_grade_options = [GRADE_A, GRADE_B, GRADE_C, GRADE_D] if pillar_id.startswith("B") else ["", GRADE_A, GRADE_B, GRADE_C, GRADE_D]
        default_grade_value = existing_record["evidence_grade"] if existing_record is not None and pd.notna(existing_record["evidence_grade"]) else default_grade_options[0]
        if default_grade_value not in default_grade_options:
            default_grade_value = default_grade_options[0]
        st.session_state.setdefault(grade_key, default_grade_value)
        st.session_state.setdefault(confidence_key, existing_record["confidence_basis"] if existing_record is not None and pd.notna(existing_record["confidence_basis"]) else "")
        st.session_state.setdefault(sources_key, existing_record["primary_sources"] if existing_record is not None and pd.notna(existing_record["primary_sources"]) else "")
        st.session_state.setdefault(judgment_key, _get_judgment_default(existing_record))
        st.session_state.setdefault(falsification_key, existing_record["falsification_trigger"] if existing_record is not None and pd.notna(existing_record["falsification_trigger"]) else "")
        st.session_state.setdefault(reviewer_key, existing_record["reviewer"] if existing_record is not None and pd.notna(existing_record["reviewer"]) else (thesis["reviewer"] if thesis["reviewer"] else ""))
        st.session_state.setdefault(notes_key, "")
        st.session_state.setdefault(linked_key, linked_evidence_defaults)
        drl_options = [""] + list(range(1, 10))
        default_drl = existing_record["drl"] if existing_record is not None and pd.notna(existing_record["drl"]) else ""
        if default_drl not in drl_options:
            default_drl = ""
        st.session_state.setdefault(drl_key, default_drl)
        st.session_state.setdefault(review_date_key, pd.to_datetime(existing_record["review_date"]).date() if existing_record is not None and pd.notna(existing_record["review_date"]) else default_validation_review_date)

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
            if pillar_id.startswith("I") and not confidence_basis.strip():
                st.error("Confidence Basis is required.")
            elif pillar_id.startswith("I") and not judgment.strip():
                st.error("Judgment is required.")
            elif pillar_id.startswith("I") and not falsification_trigger.strip():
                st.error("Falsification Trigger is required.")
            else:
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
    st.session_state['current_view'] = 'Dashboard'
if 'selected_thesis_id' not in st.session_state:
    st.session_state['selected_thesis_id'] = None
if 'selected_evidence_id' not in st.session_state:
    st.session_state['selected_evidence_id'] = None
if 'engine_preparation_status' not in st.session_state:
    st.session_state['engine_preparation_status'] = None


def _capture_navigation_event():
    """Capture view transitions passively without affecting navigation logic."""
    current_view = st.session_state.get("current_view", "Dashboard")
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
    if label == "Workspace":
        return current_view in ["Dashboard", "New Thesis", "Hermes Workflow Inbox"]
    if label == "Theses":
        return current_view in ["Thesis Workspace", "Thesis Detail"]
    if label == "History":
        return current_view == "Documentation"
    if label == "Settings":
        return current_view == "Settings"
    return False


def _apply_primary_navigation(label):
    """Apply existing primary navigation mapping and lifecycle behavior."""
    if label == "Workspace":
        st.session_state["current_view"] = "Dashboard"
        st.session_state["selected_thesis_id"] = None
    elif label == "Theses":
        if st.session_state.get("selected_thesis_id") is not None:
            st.session_state["current_view"] = "Thesis Workspace"
        else:
            st.session_state["current_view"] = "Dashboard"
    elif label == "History":
        st.session_state["current_view"] = "Documentation"
        st.session_state["selected_thesis_id"] = None
    elif label == "Settings":
        st.session_state["current_view"] = "Settings"
        st.session_state["selected_thesis_id"] = None


def render_sidebar_primary_navigation(current_view):
    """Render primary navigation controls."""
    primary_nav_labels = ["Workspace", "Theses", "History", "Settings"]
    for nav_label in primary_nav_labels:
        button_type = "primary" if _is_primary_nav_active(nav_label, current_view) else "secondary"
        if st.button(nav_label, key=f"nav_{nav_label}", use_container_width=True, type=button_type):
            _apply_primary_navigation(nav_label)
            st.rerun()
        if nav_label == "History":
            st.markdown("<div class='athena-history-map'>Documentation</div>", unsafe_allow_html=True)


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


# Sidebar navigation
with st.sidebar:
    theses_df = fetch_dataframe(
        """
        SELECT id, company_name, account_type, portfolio_role, primary_horizon
        FROM theses
        ORDER BY company_name
        """
    )
    selected_thesis_id = st.session_state.get("selected_thesis_id")
    current_view = st.session_state.get("current_view", "Dashboard")

    _render_sidebar_styles()
    render_sidebar_brand()
    st.divider()
    render_sidebar_primary_navigation(current_view)
    st.markdown("<br>", unsafe_allow_html=True)
    render_active_thesis_card(theses_df, selected_thesis_id)
    render_sidebar_portfolio(theses_df)
    st.divider()
    render_sidebar_actions()

_capture_navigation_event()

# Main content area
if st.session_state['current_view'] == 'Dashboard':

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
                "Status": thesis_row["status"] if pd.notna(thesis_row["status"]) and str(thesis_row["status"]).strip() else "—",
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

    workspace_vm = {
        "header": {
            "analyst_name": st.session_state.get("analyst_name"),
            "primary_text": "Continue where you left off.",
        },
        "hero": hero_thesis_data,
        "focus": watchlist_rows_sorted,
        "portfolio": {
            "rows": portfolio_rows,
            "display_df": portfolio_display_df,
        },
        "metrics": metric_tiles,
        "governance": {
            "display_df": governance_display_df,
        },
        "historical": {
            "outcome_distribution_df": outcome_distribution_df,
            "framework_theses_df": framework_theses_df,
        },
        "watchlist": {
            "display_df": watchlist_display_df,
        },
        "mnemosyne": mnemosyne_data,
        "assessment": None,
        "decision": None,
        "evidence": None,
    }

    render_workspace(workspace_vm)

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
                preparation_status = prepare_evaluation(
                    ticker=ticker,
                    observation_date=observation_date,
                    company_name=company_name,
                    reviewer=reviewer,
                )
                st.session_state['engine_preparation_status'] = preparation_status

                thesis_id = preparation_status.get("thesis_id")
                readiness_status = preparation_status.get("readiness_status")

                if thesis_id is not None and readiness_status in ["ready_for_analyst", "partial"]:
                    open_thesis_workspace(thesis_id)

                render_preparation_status(preparation_status)

elif st.session_state['current_view'] in ['Thesis Detail', 'Thesis Workspace']:
    # Get thesis data
    thesis_id = st.session_state['selected_thesis_id']
    thesis_df = fetch_dataframe(
        "SELECT * FROM theses WHERE id = ?",
        (thesis_id,)
    )
    
    if not thesis_df.empty:
        thesis = thesis_df.iloc[0]
        thesis_validation_mode_enabled = int(thesis['validation_mode']) == 1 if pd.notna(thesis['validation_mode']) else False
        thesis_cutoff_date = None
        if pd.notna(thesis['evidence_cutoff_date']) and str(thesis['evidence_cutoff_date']).strip():
            thesis_cutoff_date = pd.to_datetime(thesis['evidence_cutoff_date']).date()

        default_validation_review_date = (
            thesis_cutoff_date
            if thesis_validation_mode_enabled and thesis_cutoff_date is not None
            else datetime.now().date()
        )
        
        # Company name as header
        st.header(thesis['company_name'])

        engine_preparation_status = st.session_state.get("engine_preparation_status")
        if (
            isinstance(engine_preparation_status, dict)
            and engine_preparation_status.get("thesis_id") == thesis_id
        ):
            render_preparation_status(engine_preparation_status)
        
        # Metadata row
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Ticker", thesis['ticker'] or "-")
        with col2:
            st.metric("Status", thesis['status'] or "-")
        with col3:
            st.metric("DRL", thesis['drl'] or "-")
        with col4:
            st.metric("Horizon", thesis['primary_horizon'] or "-")
        with col5:
            st.metric("Reviewer", thesis['reviewer'] or "-")

        st.caption("Thesis Workspace")
        
        st.divider()
        
        # Tabs
        tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11 = st.tabs(
            [
                "Assessment Workspace",
                "Overview",
                "Evidence",
                "Business Quality",
                "Industry",
                "Financials",
                "Management",
                "Valuation",
                "Risk",
                "Decision",
                "Audit Trail"
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
                    evidence_title = st.text_input("Title *", placeholder="e.g., NVIDIA Q2 10-Q Filing")
                
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
                                st.rerun()
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
                        with st.form("observation_update_form"):
                            col1, col2 = st.columns(2)
                            with col1:
                                update_pillar_id = st.text_input(
                                    "Update Pillar ID",
                                    value=str(selected_observation["pillar_id"]) if pd.notna(selected_observation["pillar_id"]) else "",
                                    key="observation_update_pillar_id",
                                )
                            with col2:
                                current_category = str(selected_observation["observation_category"]).strip() if pd.notna(selected_observation["observation_category"]) else OBSERVATION_CATEGORY_OPTIONS[0]
                                update_category_index = OBSERVATION_CATEGORY_OPTIONS.index(current_category) if current_category in OBSERVATION_CATEGORY_OPTIONS else 0
                                update_observation_category = st.selectbox(
                                    "Update Category",
                                    options=OBSERVATION_CATEGORY_OPTIONS,
                                    index=update_category_index,
                                    key="observation_update_category",
                                )

                            update_observation_text = st.text_area(
                                "Update Observation Text",
                                value=str(selected_observation["observation_text"]) if pd.notna(selected_observation["observation_text"]) else "",
                                height=100,
                                key="observation_update_text",
                            )
                            update_evidence_quote = st.text_area(
                                "Update Evidence Quote",
                                value=str(selected_observation["evidence_quote"]) if pd.notna(selected_observation["evidence_quote"]) else "",
                                height=80,
                                key="observation_update_quote",
                            )
                            update_source_location = st.text_input(
                                "Update Source Location",
                                value=str(selected_observation["source_location"]) if pd.notna(selected_observation["source_location"]) else "",
                                key="observation_update_source_location",
                            )

                            col1, col2, col3 = st.columns(3)
                            with col1:
                                current_confidence = str(selected_observation["analyst_confidence"]).strip() if pd.notna(selected_observation["analyst_confidence"]) else "Medium"
                                confidence_options = ["Low", "Medium", "High"]
                                confidence_index = confidence_options.index(current_confidence) if current_confidence in confidence_options else 1
                                update_analyst_confidence = st.selectbox(
                                    "Update Analyst Confidence",
                                    options=confidence_options,
                                    index=confidence_index,
                                    key="observation_update_confidence",
                                )
                            with col2:
                                current_status = str(selected_observation["status"]).strip() if pd.notna(selected_observation["status"]) else OBSERVATION_STATUS_ACTIVE
                                status_index = OBSERVATION_STATUS_OPTIONS.index(current_status) if current_status in OBSERVATION_STATUS_OPTIONS else 0
                                update_status = st.selectbox(
                                    "Update Status",
                                    options=OBSERVATION_STATUS_OPTIONS,
                                    index=status_index,
                                    key="observation_update_status",
                                )
                            with col3:
                                update_by = st.text_input(
                                    "Updated By",
                                    value=thesis['reviewer'] if thesis['reviewer'] else "System",
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
                                        st.rerun()
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
            selected_pillar = st.selectbox("Select Pillar to Score", pillar_options)

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
                        default=linked_evidence_defaults,
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
                    if not selected_pillar or selected_pillar == "":
                        st.error("Pillar is required.")
                    elif not confidence_basis.strip():
                        st.error("Confidence Basis is required.")
                    elif not judgment.strip():
                        st.error("Judgment is required.")
                    elif not falsification_trigger.strip():
                        st.error("Falsification Trigger is required.")
                    else:
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
                summary_field("Recommendation", decision_context["recommendation"] or "—")
                summary_field("Review Date", decision_context["review_date"] or "—")
                summary_field("Horizon Map", decision_context["horizon_map"] or "—")
                summary_field("Action", decision_context["action"] or "—")
                summary_field("Decision Rationale", decision_context["decision_rationale"] or "—")
                summary_field("Key Risks", decision_context["key_risks"] or "—")
                summary_field("Falsification Summary", decision_context["falsification_summary"] or "—")
                summary_field("Next Review Date", decision_context["next_review_date"] or "—")
                summary_field("Created At", decision_context["created_at"] or "—")

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
            
            # Check for existing decision
            existing_decision_df = fetch_dataframe(
                "SELECT * FROM decision_logs WHERE thesis_id = ?",
                (thesis_id,)
            )
            existing_decision = existing_decision_df.iloc[0] if not existing_decision_df.empty else None
            
            with st.form("decision_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    recommendation_options = ["", "Observe", "Ready with Conditions", "Ready", "High Conviction", "Avoid", "Hold", "Sell"]
                    rec_default_idx = 0
                    if existing_decision is not None and pd.notna(existing_decision['recommendation']):
                        try:
                            rec_default_idx = recommendation_options.index(existing_decision['recommendation'])
                        except ValueError:
                            rec_default_idx = 0
                    recommendation = st.selectbox(
                        "Recommendation",
                        recommendation_options,
                        index=rec_default_idx,
                        key="decision_rec"
                    )
                
                with col2:
                    review_date = st.date_input(
                        "Review Date",
                        value=pd.to_datetime(existing_decision['review_date']).date() if existing_decision is not None and pd.notna(existing_decision['review_date']) else datetime.now().date(),
                        key="decision_date"
                    )
                
                horizon_map = st.text_area(
                    "Horizon Map",
                    value=existing_decision['horizon_map'] if existing_decision is not None and pd.notna(existing_decision['horizon_map']) else "",
                    placeholder="e.g., 1-Year: Observe | 3-Year: Ready with Conditions | 10-Year: High Conviction",
                    height=80,
                    key="decision_horizon"
                )
                
                action = st.text_area(
                    "Action",
                    value=existing_decision['action'] if existing_decision is not None and pd.notna(existing_decision['action']) else "",
                    placeholder="What action should be taken?",
                    height=80,
                    key="decision_action"
                )
                
                decision_rationale = st.text_area(
                    "Decision Rationale",
                    value=existing_decision['decision_rationale'] if existing_decision is not None and pd.notna(existing_decision['decision_rationale']) else "",
                    placeholder="Explain the reasoning behind this decision",
                    height=80,
                    key="decision_rationale"
                )
                
                key_risks = st.text_area(
                    "Key Risks",
                    value=existing_decision['key_risks'] if existing_decision is not None and pd.notna(existing_decision['key_risks']) else "",
                    placeholder="What are the key risks?",
                    height=80,
                    key="decision_risks"
                )
                
                falsification_summary = st.text_area(
                    "Falsification Summary",
                    value=existing_decision['falsification_summary'] if existing_decision is not None and pd.notna(existing_decision['falsification_summary']) else "",
                    placeholder="Summary of falsification criteria",
                    height=80,
                    key="decision_false"
                )
                
                next_review_date = st.date_input(
                    "Next Review Date",
                    value=pd.to_datetime(existing_decision['next_review_date']).date() if existing_decision is not None and pd.notna(existing_decision['next_review_date']) else datetime.now().date(),
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
                        st.rerun()
            
            st.divider()
            
            # Display existing decision
            section_header("Current Decision")
            if existing_decision is not None:
                summary_field("Recommendation", existing_decision['recommendation'] or "—")
                summary_field("Review Date", existing_decision['review_date'] or "—")
                summary_field("Horizon Map", existing_decision['horizon_map'] or "—")
                summary_field("Action", existing_decision['action'] or "—")
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
    st.header("Settings")
    empty_state("**Placeholder:** Settings interface coming soon.")

elif st.session_state['current_view'] == 'Documentation':
    st.header("Documentation")
    empty_state("**Placeholder:** Documentation coming soon.")

