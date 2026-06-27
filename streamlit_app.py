import streamlit as st
import sqlite3
import pandas as pd
import json
import uuid
from datetime import datetime

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
]

TERMINAL_INTAKE_STATUSES = [
    INTAKE_STATUS_PROMOTED,
    INTAKE_STATUS_REJECTED,
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
    page_title="Investment Management System",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Database configuration
DATABASE_FILE = "/Users/phillipcaswell/ims_mvp.db"


# Database initialization function
def init_db():
    """Initialize SQLite database with required tables."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    # Companies table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT NOT NULL,
            ticker TEXT,
            sector TEXT,
            industry TEXT,
            created_at TEXT
        )
    """)
    
    # Theses table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS theses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT NOT NULL,
            ticker TEXT,
            decision_question TEXT NOT NULL,
            account_type TEXT,
            portfolio_role TEXT,
            primary_horizon TEXT,
            regime_state TEXT,
            reviewer TEXT,
            status TEXT,
            drl INTEGER,
            created_at TEXT
        )
    """)

    try:
        cursor.execute("ALTER TABLE theses ADD COLUMN validation_mode INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE theses ADD COLUMN evidence_cutoff_date TEXT DEFAULT NULL")
    except sqlite3.OperationalError:
        pass
    
    # Evidence items table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS evidence_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            thesis_id INTEGER,
            source_name TEXT,
            source_type TEXT,
            publication_date TEXT,
            evidence_grade TEXT,
            confidence_basis TEXT,
            url_or_citation TEXT,
            related_pillar TEXT,
            evidence_summary TEXT,
            created_at TEXT
        )
    """)

    # Evidence Repository MVP columns (safe additive migration)
    try:
        cursor.execute("ALTER TABLE evidence_items ADD COLUMN title TEXT DEFAULT NULL")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE evidence_items ADD COLUMN source_publisher TEXT DEFAULT NULL")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE evidence_items ADD COLUMN key_takeaway TEXT DEFAULT NULL")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE evidence_items ADD COLUMN tags TEXT DEFAULT NULL")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE evidence_items ADD COLUMN credibility_score INTEGER DEFAULT NULL")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE evidence_items ADD COLUMN materiality_score INTEGER DEFAULT NULL")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE evidence_items ADD COLUMN thesis_alignment TEXT DEFAULT NULL")
    except sqlite3.OperationalError:
        pass
    
    # Pillar scores table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pillar_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            thesis_id INTEGER,
            pillar_id TEXT,
            pillar_name TEXT,
            score INTEGER,
            rag_status TEXT,
            evidence_grade TEXT,
            confidence_basis TEXT,
            primary_sources TEXT,
            evidence_items TEXT,
            inference TEXT,
            inference_confidence TEXT,
            falsification_trigger TEXT,
            score_rationale TEXT,
            reviewer TEXT,
            review_date TEXT,
            drl INTEGER,
            created_at TEXT
        )
    """)

    try:
        cursor.execute("ALTER TABLE pillar_scores ADD COLUMN judgment TEXT DEFAULT NULL")
    except sqlite3.OperationalError:
        pass

    cursor.execute(
        """
        UPDATE pillar_scores
        SET judgment = inference
        WHERE judgment IS NULL AND inference IS NOT NULL
        """
    )
    
    # Decision logs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS decision_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            thesis_id INTEGER,
            recommendation TEXT,
            horizon_map TEXT,
            action TEXT,
            review_date TEXT,
            decision_rationale TEXT,
            key_risks TEXT,
            falsification_summary TEXT,
            next_review_date TEXT,
            created_at TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS evidence_staging (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            staging_uuid TEXT NOT NULL UNIQUE,
            thesis_id INTEGER,
            source_type TEXT,
            source_name TEXT,
            source_url TEXT,
            publication_date TEXT,
            retrieval_date TEXT,
            author_publisher TEXT,
            evidence_summary TEXT,
            key_takeaway TEXT,
            preliminary_grade TEXT,
            source_quality_notes TEXT,
            duplicate_flag INTEGER DEFAULT 0,
            duplicate_notes TEXT,
            intake_status TEXT DEFAULT 'Pending',
            rejection_reason TEXT,
            reviewed_by TEXT,
            review_date TEXT,
            promoted_evidence_id INTEGER,
            promoted_at TEXT,
            created_by TEXT,
            created_at TEXT,
            FOREIGN KEY (thesis_id) REFERENCES theses(id),
            FOREIGN KEY (promoted_evidence_id) REFERENCES evidence_items(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS thesis_reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            thesis_id INTEGER NOT NULL,
            decision_log_id INTEGER NOT NULL,
            review_date TEXT,
            review_horizon TEXT,
            outcome_summary TEXT,
            outcome_attribution_type TEXT,
            outcome_evidence TEXT,
            thesis_quality_assessment TEXT,
            decision_quality_preserved INTEGER DEFAULT 1,
            decision_quality_notes TEXT,
            framework_review_eligible INTEGER DEFAULT 0,
            framework_notes TEXT,
            reviewer TEXT,
            created_at TEXT,
            UNIQUE(thesis_id, decision_log_id, review_horizon),
            FOREIGN KEY (thesis_id) REFERENCES theses(id),
            FOREIGN KEY (decision_log_id) REFERENCES decision_logs(id)
        )
    """)
    
    # Thesis events table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS thesis_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            thesis_id INTEGER,
            event_type TEXT,
            event_description TEXT,
            created_by TEXT,
            created_at TEXT,
            version TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pillar_evidence_links (
            id INTEGER PRIMARY KEY,
            pillar_score_id INTEGER NOT NULL,
            evidence_item_id INTEGER NOT NULL,
            created_by TEXT,
            created_at TEXT,
            UNIQUE(pillar_score_id, evidence_item_id),
            FOREIGN KEY (pillar_score_id) REFERENCES pillar_scores(id),
            FOREIGN KEY (evidence_item_id) REFERENCES evidence_items(id)
        )
    """)

    conn.commit()
    conn.close()


# Helper functions
def run_query(query, params=()):
    """Execute a query without returning results."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute(query, params)
    conn.commit()
    conn.close()


def fetch_dataframe(query, params=()):
    """Execute a query and return results as a pandas DataFrame."""
    conn = sqlite3.connect(DATABASE_FILE)
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


def insert_query(query, params=()):
    """Execute an INSERT query and return the last row ID."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute(query, params)
    conn.commit()
    row_id = cursor.lastrowid
    conn.close()
    return row_id


def is_validation_configuration_locked(thesis_id):
    """Validation mode and cutoff lock after first recorded decision."""
    decision_count_df = fetch_dataframe(
        "SELECT COUNT(*) AS decision_count FROM decision_logs WHERE thesis_id = ?",
        (thesis_id,)
    )
    decision_count = int(decision_count_df.iloc[0]["decision_count"]) if not decision_count_df.empty else 0
    return decision_count > 0


def log_event(
    thesis_id,
    event_type,
    description,
    created_by="System",
    version="1.0"
):
    """Log an event to the thesis_events table."""
    run_query(
        """
        INSERT INTO thesis_events
        (
            thesis_id,
            event_type,
            event_description,
            created_by,
            created_at,
            version
        )
        VALUES (?,?,?,?,?,?)
        """,
        (
            thesis_id,
            event_type,
            description,
            created_by,
            datetime.now().isoformat(),
            version,
        ),
    )


def get_overview_metrics(thesis_id):
    """Get overview metrics for a thesis."""
    # Count evidence items
    evidence_df = fetch_dataframe(
        "SELECT COUNT(*) as count FROM evidence_items WHERE thesis_id = ?",
        (thesis_id,)
    )
    evidence_count = evidence_df['count'].iloc[0]
    
    # Count business pillars completed (non-null scores)
    business_df = fetch_dataframe(
        "SELECT COUNT(*) as count FROM pillar_scores WHERE thesis_id = ? AND pillar_id LIKE 'B%' AND score IS NOT NULL",
        (thesis_id,)
    )
    business_pillars_completed = business_df['count'].iloc[0]
    
    # Count investment pillars completed (non-null scores)
    investment_df = fetch_dataframe(
        "SELECT COUNT(*) as count FROM pillar_scores WHERE thesis_id = ? AND pillar_id LIKE 'I%' AND score IS NOT NULL",
        (thesis_id,)
    )
    investment_pillars_completed = investment_df['count'].iloc[0]
    
    # Count audit events
    events_df = fetch_dataframe(
        "SELECT COUNT(*) as count FROM thesis_events WHERE thesis_id = ?",
        (thesis_id,)
    )
    audit_event_count = events_df['count'].iloc[0]
    
    return {
        "evidence_count": evidence_count,
        "business_pillars_completed": business_pillars_completed,
        "investment_pillars_completed": investment_pillars_completed,
        "audit_event_count": audit_event_count
    }


def get_business_evidence_coverage(thesis_id):
    """Compute B1-B7 evidence coverage using exact related_pillar matching."""
    business_pillars = ["B1", "B2", "B3", "B4", "B5", "B6", "B7"]
    pillar_names = {
        "B1": "Business Quality",
        "B2": "Competitive Advantage",
        "B3": "Revenue Quality",
        "B4": "Financial Resilience",
        "B5": "Execution Capability",
        "B6": "Industry Position",
        "B7": "Systems Importance"
    }

    coverage_rows = []
    grade_priority = ["A", "B", "C", "D"]
    for pillar_id in business_pillars:
        pillar_df = fetch_dataframe(
            """
            SELECT evidence_grade, COUNT(*) AS item_count
            FROM evidence_items
            WHERE thesis_id = ? AND related_pillar = ?
            GROUP BY evidence_grade
            """,
            (thesis_id, pillar_id)
        )

        grades = (
            pillar_df["evidence_grade"]
            .dropna()
            .astype(str)
            .str.strip()
            .tolist()
        )

        highest_grade = next(
            (g for g in grade_priority if g in grades),
            "—"
        )

        if pillar_df.empty:
            coverage_status = "🔴 Missing"
        else:
            if any(grade in [GRADE_A, GRADE_B] for grade in grades):
                coverage_status = "🟢 Supported"
            else:
                coverage_status = "🟡 Weak"

        coverage_rows.append(
            {
                "Pillar": f"{pillar_id} — {pillar_names[pillar_id]}",
                "Coverage": coverage_status,
                "Evidence Items": int(pillar_df["item_count"].sum()) if not pillar_df.empty else 0,
                "Grades Present": ", ".join(sorted(set(grades))) if grades else "—",
                "Highest Grade": highest_grade,
            }
        )

    return coverage_rows


def get_available_evidence_items(thesis_id):
    """Return evidence options for linkage in the active thesis."""
    evidence_df = fetch_dataframe(
        """
        SELECT
            id,
            title,
            source_name,
            source_publisher,
            evidence_grade,
            related_pillar
        FROM evidence_items
        WHERE thesis_id = ?
        ORDER BY id ASC
        """,
        (thesis_id,)
    )

    option_labels = {}
    option_ids = []

    for _, row in evidence_df.iterrows():
        evidence_id = int(row["id"])
        title = str(row["title"]).strip() if pd.notna(row["title"]) and str(row["title"]).strip() else "—"
        source_display = "—"
        if pd.notna(row["source_name"]) and str(row["source_name"]).strip():
            source_display = str(row["source_name"]).strip()
        elif pd.notna(row["source_publisher"]) and str(row["source_publisher"]).strip():
            source_display = str(row["source_publisher"]).strip()

        grade_display = str(row["evidence_grade"]).strip() if pd.notna(row["evidence_grade"]) and str(row["evidence_grade"]).strip() else "—"
        pillar_display = str(row["related_pillar"]).strip() if pd.notna(row["related_pillar"]) and str(row["related_pillar"]).strip() else "—"

        option_labels[evidence_id] = (
            f"#{evidence_id} | {title} | Source: {source_display} | "
            f"Grade: {grade_display} | Pillar: {pillar_display}"
        )
        option_ids.append(evidence_id)

    return option_ids, option_labels


def get_linked_evidence_ids(pillar_score_id):
    """Return currently linked evidence IDs for a pillar score."""
    link_df = fetch_dataframe(
        """
        SELECT evidence_item_id
        FROM pillar_evidence_links
        WHERE pillar_score_id = ?
        ORDER BY evidence_item_id ASC
        """,
        (pillar_score_id,)
    )
    if link_df.empty:
        return []
    return link_df["evidence_item_id"].astype(int).tolist()


def sync_pillar_evidence_links(pillar_score_id, selected_evidence_ids, created_by):
    """Synchronize evidence link rows with selected IDs and log link events."""
    existing_ids = set(get_linked_evidence_ids(pillar_score_id))
    selected_ids = set(int(eid) for eid in selected_evidence_ids)

    to_add = sorted(selected_ids - existing_ids)
    to_remove = sorted(existing_ids - selected_ids)

    thesis_df = fetch_dataframe(
        "SELECT thesis_id FROM pillar_scores WHERE id = ?",
        (pillar_score_id,)
    )
    thesis_id = int(thesis_df.iloc[0]["thesis_id"]) if not thesis_df.empty else None

    for evidence_item_id in to_add:
        insert_query(
            """
            INSERT INTO pillar_evidence_links
            (pillar_score_id, evidence_item_id, created_by, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                pillar_score_id,
                evidence_item_id,
                created_by,
                datetime.now().isoformat()
            )
        )

        if thesis_id is not None:
            log_event(
                thesis_id=thesis_id,
                event_type=EVENT_EVIDENCE_LINKED,
                description=(
                    f"Linked evidence to pillar: action=linked, "
                    f"pillar_score_id={pillar_score_id}, evidence_item_id={evidence_item_id}"
                ),
                created_by=created_by,
                version="1.0"
            )

    for evidence_item_id in to_remove:
        run_query(
            """
            DELETE FROM pillar_evidence_links
            WHERE pillar_score_id = ? AND evidence_item_id = ?
            """,
            (pillar_score_id, evidence_item_id)
        )

        if thesis_id is not None:
            log_event(
                thesis_id=thesis_id,
                event_type=EVENT_EVIDENCE_UNLINKED,
                description=(
                    f"Unlinked evidence from pillar: action=unlinked, "
                    f"pillar_score_id={pillar_score_id}, evidence_item_id={evidence_item_id}"
                ),
                created_by=created_by,
                version="1.0"
            )


def promote_staged_evidence(staging_uuid, analyst):
    """Promote analyst-confirmed staged evidence into the official evidence repository."""
    staging_df = fetch_dataframe(
        "SELECT * FROM evidence_staging WHERE staging_uuid = ? LIMIT 1",
        (staging_uuid,)
    )

    if staging_df.empty:
        return {
            "success": False,
            "message": "Staged evidence not found.",
            "promoted_evidence_id": None,
        }

    staging_record = staging_df.iloc[0]
    current_status = str(staging_record["intake_status"]).strip() if pd.notna(staging_record["intake_status"]) else INTAKE_STATUS_PENDING

    if current_status in TERMINAL_INTAKE_STATUSES:
        return {
            "success": False,
            "message": f"Promotion blocked: terminal status '{current_status}'.",
            "promoted_evidence_id": None,
        }

    if current_status != INTAKE_STATUS_CONFIRMED:
        return {
            "success": False,
            "message": "Promotion blocked: staged evidence must be Confirmed before promotion.",
            "promoted_evidence_id": None,
        }

    if pd.isna(staging_record["thesis_id"]):
        return {
            "success": False,
            "message": "Promotion blocked: thesis_id is required to promote evidence.",
            "promoted_evidence_id": None,
        }

    thesis_df = fetch_dataframe(
        "SELECT id, validation_mode, evidence_cutoff_date FROM theses WHERE id = ? LIMIT 1",
        (int(staging_record["thesis_id"]),)
    )

    if not thesis_df.empty:
        thesis_record = thesis_df.iloc[0]
        validation_mode_enabled = int(thesis_record["validation_mode"]) == 1 if pd.notna(thesis_record["validation_mode"]) else False
        cutoff_raw = str(thesis_record["evidence_cutoff_date"]).strip() if pd.notna(thesis_record["evidence_cutoff_date"]) else ""
        publication_raw = str(staging_record["publication_date"]).strip() if pd.notna(staging_record["publication_date"]) else ""

        if validation_mode_enabled and cutoff_raw and publication_raw:
            publication_date = pd.to_datetime(publication_raw, errors="coerce")
            cutoff_date = pd.to_datetime(cutoff_raw, errors="coerce")

            if pd.notna(publication_date) and pd.notna(cutoff_date) and publication_date.date() > cutoff_date.date():
                log_event(
                    thesis_id=int(staging_record["thesis_id"]),
                    event_type=EVENT_EVIDENCE_PROMOTION_BLOCKED,
                    description=(
                        f"staging_uuid={staging_uuid}|"
                        f"publication_date={publication_date.date().isoformat()}|"
                        f"cutoff_date={cutoff_date.date().isoformat()}|"
                        "block_reason=PublicationDateAfterCutoff"
                    ),
                    created_by=analyst if analyst and str(analyst).strip() else "System",
                    version="1.0"
                )
                return {
                    "success": False,
                    "message": "Promotion blocked: publication_date is after evidence_cutoff_date for this thesis.",
                    "promoted_evidence_id": None,
                }

    promoted_evidence_id = insert_query(
        """
        INSERT INTO evidence_items
        (
            thesis_id,
            source_name,
            source_type,
            publication_date,
            evidence_grade,
            confidence_basis,
            url_or_citation,
            related_pillar,
            evidence_summary,
            created_at,
            title,
            source_publisher,
            key_takeaway,
            tags,
            credibility_score,
            materiality_score,
            thesis_alignment
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            int(staging_record["thesis_id"]),
            staging_record["source_name"] if pd.notna(staging_record["source_name"]) else None,
            staging_record["source_type"] if pd.notna(staging_record["source_type"]) else None,
            staging_record["publication_date"] if pd.notna(staging_record["publication_date"]) else None,
            staging_record["preliminary_grade"] if pd.notna(staging_record["preliminary_grade"]) else None,
            staging_record["source_quality_notes"] if pd.notna(staging_record["source_quality_notes"]) else None,
            staging_record["source_url"] if pd.notna(staging_record["source_url"]) else None,
            None,
            staging_record["evidence_summary"] if pd.notna(staging_record["evidence_summary"]) else None,
            datetime.now().isoformat(),
            staging_record["source_name"] if pd.notna(staging_record["source_name"]) else None,
            staging_record["author_publisher"] if pd.notna(staging_record["author_publisher"]) else None,
            staging_record["key_takeaway"] if pd.notna(staging_record["key_takeaway"]) else None,
            None,
            None,
            None,
            None,
        )
    )

    run_query(
        """
        UPDATE evidence_staging
        SET promoted_evidence_id = ?,
            promoted_at = ?,
            intake_status = ?,
            reviewed_by = ?,
            review_date = ?
        WHERE staging_uuid = ?
        """,
        (
            int(promoted_evidence_id),
            datetime.now().isoformat(),
            INTAKE_STATUS_PROMOTED,
            analyst,
            datetime.now().isoformat(),
            staging_uuid,
        )
    )

    log_event(
        thesis_id=int(staging_record["thesis_id"]),
        event_type=EVENT_EVIDENCE_PROMOTED,
        description=f"Staged evidence promoted: staging_uuid={staging_uuid}, promoted_evidence_id={promoted_evidence_id}",
        created_by=analyst if analyst and str(analyst).strip() else "System",
        version="1.0"
    )

    return {
        "success": True,
        "message": "Staged evidence promoted successfully.",
        "promoted_evidence_id": int(promoted_evidence_id),
    }


def build_thesis_json(thesis_id):
    """Build a comprehensive JSON export of a thesis with all related data."""
    # Get thesis
    thesis_df = fetch_dataframe(
        "SELECT * FROM theses WHERE id = ?",
        (thesis_id,)
    )
    thesis_dict = thesis_df.iloc[0].to_dict() if not thesis_df.empty else {}
    
    # Get evidence items
    evidence_df = fetch_dataframe(
        "SELECT * FROM evidence_items WHERE thesis_id = ? ORDER BY created_at DESC",
        (thesis_id,)
    )
    evidence_list = evidence_df.to_dict('records')
    
    # Get business assessments
    business_df = fetch_dataframe(
        "SELECT * FROM pillar_scores WHERE thesis_id = ? AND pillar_id LIKE 'B%' ORDER BY pillar_id",
        (thesis_id,)
    )
    business_list = business_df.to_dict('records')
    
    # Get investment assessments
    investment_df = fetch_dataframe(
        "SELECT * FROM pillar_scores WHERE thesis_id = ? AND pillar_id LIKE 'I%' ORDER BY pillar_id",
        (thesis_id,)
    )
    investment_list = investment_df.to_dict('records')
    
    # Get decision log
    decision_df = fetch_dataframe(
        "SELECT * FROM decision_logs WHERE thesis_id = ?",
        (thesis_id,)
    )
    decision_dict = decision_df.iloc[0].to_dict() if not decision_df.empty else {}
    
    # Get thesis events
    events_df = fetch_dataframe(
        "SELECT * FROM thesis_events WHERE thesis_id = ? ORDER BY created_at DESC",
        (thesis_id,)
    )
    events_list = events_df.to_dict('records')
    
    return {
        "thesis": thesis_dict,
        "evidence_items": evidence_list,
        "business_assessments": business_list,
        "investment_assessments": investment_list,
        "decision_log": decision_dict,
        "audit_trail": events_list
    }


def validate_decision_gate(thesis_id):
    """Validate constitutional completion for decision eligibility."""
    required_pillars = ["B1", "B2", "B3", "B4", "B5", "B6", "B7", "I1", "I2", "I3", "I4"]
    pillar_df = fetch_dataframe(
        """
        SELECT pillar_id, score, judgment, confidence_basis, falsification_trigger
        FROM pillar_scores
        WHERE thesis_id = ? AND pillar_id IN (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (thesis_id, *required_pillars)
    )

    by_pillar = {}
    if not pillar_df.empty:
        for _, row in pillar_df.iterrows():
            pid = str(row["pillar_id"]).strip()
            if pid not in by_pillar:
                by_pillar[pid] = row

    missing = []
    completed = 0

    for pillar_id in required_pillars:
        row = by_pillar.get(pillar_id)
        pillar_missing = False

        if row is None or pd.isna(row["score"]):
            missing.append({"pillar_id": pillar_id, "field": "score", "label": "Score"})
            pillar_missing = True

        if row is None or pd.isna(row["judgment"]) or not str(row["judgment"]).strip():
            missing.append({"pillar_id": pillar_id, "field": "judgment", "label": "Judgment"})
            pillar_missing = True

        if row is None or pd.isna(row["confidence_basis"]) or not str(row["confidence_basis"]).strip():
            missing.append({"pillar_id": pillar_id, "field": "confidence_basis", "label": "Confidence Basis"})
            pillar_missing = True

        if row is None or pd.isna(row["falsification_trigger"]) or not str(row["falsification_trigger"]).strip():
            missing.append({"pillar_id": pillar_id, "field": "falsification_trigger", "label": "Falsification Trigger"})
            pillar_missing = True

        if not pillar_missing:
            completed += 1

    return {
        "eligible": len(missing) == 0,
        "completed": completed,
        "required": 11,
        "missing": missing,
        "red_conditions": [],
        "validated_at": datetime.now().isoformat()
    }


def compute_hermes_inbox():
    """Compute a read-only workflow inbox from governed data sources."""
    tasks = []

    framework_review_df = fetch_dataframe(
        """
        SELECT
            tr.thesis_id,
            t.company_name,
            MAX(tr.review_date) AS due_date
        FROM thesis_reviews tr
        LEFT JOIN theses t ON t.id = tr.thesis_id
        WHERE tr.framework_review_eligible = 1
        GROUP BY tr.thesis_id, t.company_name
        """
    )
    for _, row in framework_review_df.iterrows():
        tasks.append(
            {
                "task_type": "Framework Review Consideration Eligible",
                "priority": HERMES_PRIORITY_CRITICAL,
                "source": "thesis_reviews",
                "thesis_id": int(row["thesis_id"]) if pd.notna(row["thesis_id"]) else None,
                "company_name": str(row["company_name"]).strip() if pd.notna(row["company_name"]) and str(row["company_name"]).strip() else "Unassigned",
                "description": "Framework review consideration is eligible.",
                "due_date": str(row["due_date"]).strip() if pd.notna(row["due_date"]) and str(row["due_date"]).strip() else None,
                "action": "Review historical observations.",
            }
        )

    review_past_due_df = fetch_dataframe(
        """
        SELECT
            d.thesis_id,
            t.company_name,
            d.next_review_date
        FROM decision_logs d
        JOIN (
            SELECT thesis_id, MAX(id) AS max_id
            FROM decision_logs
            GROUP BY thesis_id
        ) latest
            ON latest.thesis_id = d.thesis_id
           AND latest.max_id = d.id
        LEFT JOIN theses t ON t.id = d.thesis_id
        WHERE d.next_review_date IS NOT NULL
          AND date(d.next_review_date) < date('now')
        """
    )
    for _, row in review_past_due_df.iterrows():
        tasks.append(
            {
                "task_type": "Review Past Due",
                "priority": HERMES_PRIORITY_HIGH,
                "source": "decision_logs",
                "thesis_id": int(row["thesis_id"]) if pd.notna(row["thesis_id"]) else None,
                "company_name": str(row["company_name"]).strip() if pd.notna(row["company_name"]) and str(row["company_name"]).strip() else "Unassigned",
                "description": "Next review date is past due.",
                "due_date": str(row["next_review_date"]).strip() if pd.notna(row["next_review_date"]) and str(row["next_review_date"]).strip() else None,
                "action": "Perform thesis review.",
            }
        )

    pending_staging_df = fetch_dataframe(
        """
        SELECT
            es.staging_uuid,
            es.thesis_id,
            t.company_name,
            es.source_name,
            es.created_at
        FROM evidence_staging es
        LEFT JOIN theses t ON t.id = es.thesis_id
        WHERE es.intake_status = ?
        ORDER BY es.created_at ASC
        """,
        (INTAKE_STATUS_PENDING,)
    )
    for _, row in pending_staging_df.iterrows():
        source_name = str(row["source_name"]).strip() if pd.notna(row["source_name"]) and str(row["source_name"]).strip() else "Unnamed Source"
        tasks.append(
            {
                "task_type": "Evidence Awaiting Review",
                "priority": HERMES_PRIORITY_HIGH,
                "source": "evidence_staging",
                "thesis_id": int(row["thesis_id"]) if pd.notna(row["thesis_id"]) else None,
                "company_name": str(row["company_name"]).strip() if pd.notna(row["company_name"]) and str(row["company_name"]).strip() else "Unassigned",
                "description": f"Pending staged evidence: {source_name}.",
                "due_date": str(row["created_at"]).strip() if pd.notna(row["created_at"]) and str(row["created_at"]).strip() else None,
                "action": "Review staged evidence.",
            }
        )

    confirmed_staging_df = fetch_dataframe(
        """
        SELECT
            es.staging_uuid,
            es.thesis_id,
            t.company_name,
            es.source_name,
            es.review_date
        FROM evidence_staging es
        LEFT JOIN theses t ON t.id = es.thesis_id
        WHERE es.intake_status = ?
        ORDER BY es.review_date ASC
        """,
        (INTAKE_STATUS_CONFIRMED,)
    )
    for _, row in confirmed_staging_df.iterrows():
        source_name = str(row["source_name"]).strip() if pd.notna(row["source_name"]) and str(row["source_name"]).strip() else "Unnamed Source"
        tasks.append(
            {
                "task_type": "Evidence Awaiting Promotion",
                "priority": HERMES_PRIORITY_HIGH,
                "source": "evidence_staging",
                "thesis_id": int(row["thesis_id"]) if pd.notna(row["thesis_id"]) else None,
                "company_name": str(row["company_name"]).strip() if pd.notna(row["company_name"]) and str(row["company_name"]).strip() else "Unassigned",
                "description": f"Confirmed staged evidence pending promotion: {source_name}.",
                "due_date": str(row["review_date"]).strip() if pd.notna(row["review_date"]) and str(row["review_date"]).strip() else None,
                "action": "Promote confirmed evidence.",
            }
        )

    no_decision_df = fetch_dataframe(
        """
        SELECT
            t.id AS thesis_id,
            t.company_name
        FROM theses t
        WHERE NOT EXISTS (
            SELECT 1
            FROM decision_logs d
            WHERE d.thesis_id = t.id
        )
        ORDER BY t.company_name ASC
        """
    )
    for _, row in no_decision_df.iterrows():
        tasks.append(
            {
                "task_type": "Decision Not Recorded",
                "priority": HERMES_PRIORITY_MEDIUM,
                "source": "decision_logs",
                "thesis_id": int(row["thesis_id"]) if pd.notna(row["thesis_id"]) else None,
                "company_name": str(row["company_name"]).strip() if pd.notna(row["company_name"]) and str(row["company_name"]).strip() else "Unassigned",
                "description": "No governed decision record found for this thesis.",
                "due_date": None,
                "action": "Complete governed decision.",
            }
        )

    thesis_candidates_df = fetch_dataframe(
        """
        SELECT id, company_name
        FROM theses
        ORDER BY company_name ASC
        """
    )
    for _, row in thesis_candidates_df.iterrows():
        thesis_id = int(row["id"])
        gate_result = validate_decision_gate(thesis_id)
        if gate_result["eligible"]:
            continue

        missing_count = len(gate_result["missing"])
        tasks.append(
            {
                "task_type": "Governance Incomplete",
                "priority": HERMES_PRIORITY_LOW,
                "source": "validate_decision_gate",
                "thesis_id": thesis_id,
                "company_name": str(row["company_name"]).strip() if pd.notna(row["company_name"]) and str(row["company_name"]).strip() else "Unassigned",
                "description": f"Governance gate incomplete with {missing_count} missing requirement(s).",
                "due_date": None,
                "action": "Complete missing governance requirements.",
            }
        )

    def _sort_key(item):
        due_date_value = item["due_date"] if item["due_date"] else "9999-12-31"
        return (
            int(item["priority"]),
            due_date_value,
            str(item["company_name"]).lower(),
        )

    return sorted(tasks, key=_sort_key)


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


def timeline_table(dataframe):
    """Display a timeline table with consistent formatting."""
    if not dataframe.empty:
        st.dataframe(dataframe, use_container_width=True)
    else:
        empty_state("No events yet.")


def summary_field(label, value):
    """Display a label/value pair consistently."""
    st.write(f"**{label}:** {value}")


# Initialize database on app start
init_db()

# Application header
st.title("Investment Management System (IMS)")
st.markdown("### Manual Evaluation MVP")
st.markdown("---")
st.markdown("**Governed by:** IMS Charter v1.0")
st.markdown("---")

# Initialize session state
if 'current_view' not in st.session_state:
    st.session_state['current_view'] = 'Dashboard'
if 'selected_thesis_id' not in st.session_state:
    st.session_state['selected_thesis_id'] = None
if 'selected_evidence_id' not in st.session_state:
    st.session_state['selected_evidence_id'] = None

# Sidebar navigation
with st.sidebar:
    st.title("Navigation")
    
    # Dashboard and New Thesis
    if st.button("🏠 Dashboard"):
        st.session_state['current_view'] = 'Dashboard'
        st.session_state['selected_thesis_id'] = None
    
    if st.button("➕ New Thesis"):
        st.session_state['current_view'] = 'New Thesis'
        st.session_state['selected_thesis_id'] = None

    if st.button("📬 Hermes — Workflow Inbox"):
        st.session_state['current_view'] = 'Hermes Workflow Inbox'
        st.session_state['selected_thesis_id'] = None
    
    st.divider()
    
    # Active Theses
    st.subheader("Active Theses")
    theses_df = fetch_dataframe("SELECT id, company_name FROM theses ORDER BY company_name")
    
    for idx, row in theses_df.iterrows():
        if st.button(row['company_name'], key=f"thesis_{row['id']}"):
            st.session_state['current_view'] = 'Thesis Workspace'
            st.session_state['selected_thesis_id'] = row['id']
    
    st.divider()
    
    # Settings and Documentation
    if st.button("⚙️ Settings"):
        st.session_state['current_view'] = 'Settings'
        st.session_state['selected_thesis_id'] = None
    
    if st.button("📋 Documentation"):
        st.session_state['current_view'] = 'Documentation'
        st.session_state['selected_thesis_id'] = None

# Main content area
if st.session_state['current_view'] == 'Dashboard':
    st.header("Dashboard")

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

    st.divider()
    section_header("Executive Summary")

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

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        metric_card("Active Theses", active_theses_count)
    with col2:
        metric_card("Decision Eligible", decision_eligible_count)
    with col3:
        metric_card("Needs Review", needs_review_count)
    with col4:
        metric_card("Framework Review Consideration Eligible", framework_review_eligible_count)

    st.divider()
    section_header("Portfolio Table")

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
        st.dataframe(portfolio_display_df, use_container_width=True)

        st.caption("Open Thesis")
        for row in portfolio_rows:
            label = f"View {row['Company']}"
            if st.button(label, key=f"dashboard_open_{row['thesis_id']}"):
                st.session_state['selected_thesis_id'] = row['thesis_id']
                st.session_state['current_view'] = 'Thesis Detail'
                st.rerun()
    else:
        empty_state("No theses found. Click '➕ New Thesis' to create one.")

    st.divider()
    section_header("Governance Health")

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

    if governance_rows:
        governance_df = pd.DataFrame(governance_rows).sort_values(
            by=["_gate_sort", "Company"],
            ascending=[True, True]
        )
        governance_display_df = governance_df[
            ["Company", "Gate Status", "Completed", "Last Decision Date", "Next Review Date"]
        ]
        st.dataframe(governance_display_df, use_container_width=True)
    else:
        empty_state("No theses available.")

    st.divider()
    section_header("Historical Review Summary")

    outcome_distribution_df = fetch_dataframe(
        """
        SELECT outcome_attribution_type AS 'Outcome Type', COUNT(*) AS Count
        FROM thesis_reviews
        GROUP BY outcome_attribution_type
        ORDER BY outcome_attribution_type
        """
    )
    if not outcome_distribution_df.empty:
        st.dataframe(outcome_distribution_df, use_container_width=True)
    else:
        empty_state("No thesis reviews recorded yet.")

    framework_theses_df = fetch_dataframe(
        """
        SELECT t.company_name AS Company, tr.review_horizon AS 'Review Horizon', tr.review_date AS 'Review Date'
        FROM thesis_reviews tr
        JOIN theses t ON t.id = tr.thesis_id
        WHERE tr.framework_review_eligible = 1
        ORDER BY t.company_name ASC, tr.review_date DESC
        """
    )
    if not framework_theses_df.empty:
        st.dataframe(framework_theses_df, use_container_width=True)
    else:
        empty_state("No theses currently flagged for framework review consideration.")

    st.divider()
    section_header("Watchlist / Review Queue")

    watchlist_rows = []
    for _, thesis_row in theses_df.iterrows():
        tid = int(thesis_row["id"])
        priority_value, reason_text = get_priority_and_reason(tid)
        if priority_value is None:
            continue

        watchlist_rows.append(
            {
                "Priority": priority_value,
                "Company": thesis_row["company_name"],
                "Ticker": thesis_row["ticker"] if pd.notna(thesis_row["ticker"]) and str(thesis_row["ticker"]).strip() else "—",
                "Reason": reason_text,
            }
        )

    if watchlist_rows:
        watchlist_df = pd.DataFrame(watchlist_rows).sort_values(
            by=["Priority", "Company"],
            ascending=[True, True]
        )
        st.dataframe(watchlist_df, use_container_width=True)
    else:
        st.info("No items require immediate attention.")
    st.info("Workflow coordination is available in 📬 Hermes — Workflow Inbox.")

    st.divider()
    section_header("Mnemosyne — Historical Observations")
    st.markdown(
        "Historical observations are advisory only.\n"
        "They do not modify decision records, thesis reviews,\n"
        "or the investment framework."
    )

    total_reviews_df = fetch_dataframe(
        "SELECT COUNT(*) AS total_reviews FROM thesis_reviews"
    )
    total_reviews = int(total_reviews_df.iloc[0]["total_reviews"]) if not total_reviews_df.empty else 0

    if total_reviews < MNEMOSYNE_MINIMUM_REVIEW_VOLUME:
        st.warning(
            "Preliminary Observation\n\n"
            "Historical review volume is currently below the constitutional minimum of\n"
            "10 reviews.\n\n"
            "Trends shown below are descriptive only and should not be used to modify\n"
            "the investment framework."
        )
        mnemosyne_banner_mode = "Preliminary Observation"
    else:
        st.info(
            "Observation Mode\n\n"
            "Historical review volume is sufficient for exploratory pattern analysis.\n\n"
            "Observations remain informational and do not constitute framework\n"
            "recommendations."
        )
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

        st.dataframe(pd.DataFrame(distribution_display_rows), use_container_width=True)
    else:
        empty_state("No thesis reviews available for historical observation yet.")

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

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        metric_card("Total Thesis Reviews", total_reviews)
    with col2:
        metric_card("Distinct Theses Reviewed", distinct_theses)
    with col3:
        metric_card("Review Horizons Completed", review_horizons_completed)
    with col4:
        metric_card("Framework Review Consideration Count", framework_review_consideration_count)

    st.markdown(
        "Observations derived from:\n\n"
        f"• Thesis Reviews: {total_reviews}\n\n"
        f"• Distinct Theses: {distinct_theses}\n\n"
        "• Generated:\n"
        f"{datetime.now().strftime('%Y-%m-%d %H:%M')}"
    )

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
    st.header("Create New Thesis")
    
    with st.form("new_thesis_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            company_name = st.text_input("Company Name *", placeholder="Enter company name")
        
        with col2:
            ticker = st.text_input("Ticker", placeholder="e.g., AAPL")
        
        decision_question = st.text_area("Decision Question *", placeholder="What is the investment decision?", height=80)
        
        col1, col2 = st.columns(2)
        
        with col1:
            account_type = st.selectbox(
                "Account Type",
                ["", "Taxable", "Roth IRA", "401(k)", "Other"]
            )
        
        with col2:
            portfolio_role = st.selectbox(
                "Portfolio Role",
                ["", "Core", "Satellite", "Speculative", "Income", "Growth", "Watchlist"]
            )
        
        col1, col2 = st.columns(2)
        
        with col1:
            primary_horizon = st.selectbox(
                "Primary Horizon",
                ["", "1 Year", "3 Years", "5 Years", "10 Years", "20 Years"]
            )
        
        with col2:
            regime_state = st.text_input("Regime State", placeholder="e.g., Bull, Bear, Transition")
        
        col1, col2 = st.columns(2)
        
        with col1:
            reviewer = st.text_input("Reviewer", placeholder="Name of reviewer")
        
        with col2:
            status = st.selectbox(
                "Status",
                ["", "Draft", "Evidence Collection", "Scoring", "Decision Review", "Active Monitoring", "Closed"]
            )

        validation_mode_enabled = st.checkbox(
            "Validation Mode (Historical Case Validation)",
            value=False,
            help="Enable historical case validation with an evidence publication cutoff date."
        )

        evidence_cutoff_date = st.date_input(
            "Evidence Cutoff Date",
            value=datetime.now().date(),
            min_value=datetime(1900, 1, 1).date(),
            help="Evidence with publication_date after this date is blocked from promotion when validation mode is enabled."
        )
        
        drl = st.selectbox("DRL", [""] + list(range(1, 10)))
        
        submitted = st.form_submit_button("Create Thesis", use_container_width=True)
        
        if submitted:
            # Validation
            if not company_name.strip():
                st.error("Company Name is required.")
            elif not decision_question.strip():
                st.error("Decision Question is required.")
            else:
                # Insert into database and capture thesis_id
                thesis_id = insert_query(
                    """
                    INSERT INTO theses 
                    (company_name, ticker, decision_question, account_type, portfolio_role, 
                     primary_horizon, regime_state, reviewer, status, drl, validation_mode,
                     evidence_cutoff_date, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        company_name.strip(),
                        ticker.strip() if ticker else None,
                        decision_question.strip(),
                        account_type if account_type else None,
                        portfolio_role if portfolio_role else None,
                        primary_horizon if primary_horizon else None,
                        regime_state.strip() if regime_state else None,
                        reviewer.strip() if reviewer else None,
                        status if status else None,
                        int(drl) if drl else None,
                        1 if validation_mode_enabled else 0,
                        evidence_cutoff_date.isoformat() if validation_mode_enabled and evidence_cutoff_date else None,
                        datetime.now().isoformat()
                    )
                )
                # Log event
                event_created_by = reviewer.strip() if reviewer else "System"
                log_event(
                    thesis_id=thesis_id,
                    event_type=EVENT_EVALUATION_CREATED,
                    description="Initial thesis created.",
                    created_by=event_created_by,
                    version="1.0"
                )
                st.success(f"✓ Thesis created for {company_name}")
                st.session_state['current_view'] = 'Dashboard'
                st.session_state['selected_thesis_id'] = None
                st.rerun()

elif st.session_state['current_view'] in ['Thesis Detail', 'Thesis Workspace']:
    # Get thesis data
    thesis_id = st.session_state['selected_thesis_id']
    thesis_df = fetch_dataframe(
        "SELECT * FROM theses WHERE id = ?",
        (thesis_id,)
    )
    
    if not thesis_df.empty:
        thesis = thesis_df.iloc[0]
        
        # Company name as header
        st.header(thesis['company_name'])
        
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
        tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10 = st.tabs(
            [
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
            # Get overview metrics
            metrics = get_overview_metrics(thesis_id)
            validation_locked = is_validation_configuration_locked(thesis_id)
            
            # Section 1: Evaluation Summary
            section_header("Evaluation Summary")
            col1, col2 = st.columns(2)
            with col1:
                summary_field("Company", thesis['company_name'])
                summary_field("Ticker", thesis['ticker'] or "—")
                summary_field("Reviewer", thesis['reviewer'] or "—")
                summary_field("DRL", thesis['drl'] or "—")
                validation_mode_enabled = int(thesis['validation_mode']) == 1 if pd.notna(thesis['validation_mode']) else False
                summary_field("Validation Mode", "Enabled" if validation_mode_enabled else "Disabled")
            with col2:
                summary_field("Status", thesis['status'] or "—")
                summary_field("Primary Horizon", thesis['primary_horizon'] or "—")
                summary_field("Regime State", thesis['regime_state'] or "—")
                summary_field("Created", thesis['created_at'] or "—")
                summary_field("Evidence Cutoff Date", thesis['evidence_cutoff_date'] if pd.notna(thesis['evidence_cutoff_date']) and str(thesis['evidence_cutoff_date']).strip() else "—")

            if validation_locked:
                st.info("Validation mode and evidence cutoff date are immutable after the first decision record. Use a new thesis for a different historical scenario.")
            
            summary_field("Decision Question", thesis['decision_question'])
            
            st.divider()
            
            # Section 2: Progress
            section_header("Progress")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                metric_card("Evidence Items", metrics['evidence_count'])
            with col2:
                metric_card("Business Pillars", metrics['business_pillars_completed'])
            with col3:
                metric_card("Investment Pillars", metrics['investment_pillars_completed'])
            with col4:
                metric_card("Audit Events", metrics['audit_event_count'])
            
            st.divider()
            
            # Section 3: Timeline
            section_header("Timeline")
            timeline_df = fetch_dataframe(
                "SELECT created_at as Timestamp, event_type as 'Event Type', event_description as Description, created_by as 'Created By' FROM thesis_events WHERE thesis_id = ? ORDER BY created_at DESC LIMIT 20",
                (thesis_id,)
            )
            timeline_table(timeline_df)
            
            st.divider()
            
            # Section 4: IMS Constitutional Status
            section_header("IMS Constitutional Status")
            
            # Milestones derived from metrics
            milestones = [
                ("Evaluation Created", True),
                ("Evidence Collection Started", metrics["evidence_count"] > 0),
                ("Business Assessment Started", metrics["business_pillars_completed"] > 0),
                ("Investment Assessment Started", metrics["investment_pillars_completed"] > 0),
                ("Decision Recorded", False),
                ("Monitoring Started", False)
            ]
            
            for label, is_checked in milestones:
                st.checkbox(label, value=is_checked, disabled=True)

            st.divider()

            # Keep JSON export functionality available inside the workspace.
            section_header("JSON Export")

            thesis_json = build_thesis_json(thesis_id)
            st.json(thesis_json)

            json_string = json.dumps(thesis_json, indent=2, default=str)
            st.download_button(
                label="Download IMS Evaluation JSON",
                data=json_string,
                file_name=f"ims_thesis_{thesis_id}.json",
                mime="application/json",
                key="json_download"
            )

            if st.button("Log This Export", key="json_log"):
                log_event(
                    thesis_id=thesis_id,
                    event_type=EVENT_JSON_EXPORTED,
                    description="JSON export logged by reviewer.",
                    created_by=thesis['reviewer'] if thesis['reviewer'] else "System",
                    version="1.0"
                )
                st.success("✓ Export logged")
                st.rerun()
        
        with tab2:
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
                                run_query(
                                    """
                                    UPDATE evidence_items
                                    SET source_name = ?,
                                        title = ?,
                                        source_type = ?,
                                        source_publisher = ?,
                                        url_or_citation = ?,
                                        publication_date = ?,
                                        evidence_summary = ?,
                                        key_takeaway = ?,
                                        tags = ?,
                                        credibility_score = ?,
                                        materiality_score = ?,
                                        thesis_alignment = ?
                                    WHERE id = ? AND thesis_id = ?
                                    """,
                                    (
                                        edit_title.strip(),
                                        edit_title.strip(),
                                        edit_source_type,
                                        edit_source_publisher.strip(),
                                        edit_url.strip() if edit_url else None,
                                        edit_publication_date.isoformat() if edit_publication_date else None,
                                        edit_summary.strip(),
                                        edit_key_takeaway.strip(),
                                        edit_tags.strip() if edit_tags else None,
                                        int(edit_credibility_score),
                                        int(edit_materiality_score),
                                        edit_thesis_alignment,
                                        st.session_state['selected_evidence_id'],
                                        thesis_id
                                    )
                                )

                                event_created_by = thesis['reviewer'] if thesis['reviewer'] else "System"
                                log_event(
                                    thesis_id=thesis_id,
                                    event_type=EVENT_EVIDENCE_UPDATED,
                                    description=f"Evidence item updated: {edit_title.strip()}",
                                    created_by=event_created_by,
                                    version="1.0"
                                )

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
                        key="theia_intake_publication_date"
                    )
                with col2:
                    intake_retrieval_date = st.date_input(
                        "Retrieval Date",
                        value=datetime.now().date(),
                        key="theia_intake_retrieval_date"
                    )

                intake_author_publisher = st.text_input("Author / Publisher", key="theia_intake_author_publisher")
                intake_evidence_summary = st.text_area("Evidence Summary", height=90, key="theia_intake_summary")
                intake_key_takeaway = st.text_area("Key Takeaway", height=90, key="theia_intake_key_takeaway")
                intake_source_quality_notes = st.text_area("Source Quality Notes", height=90, key="theia_intake_quality_notes")

                intake_duplicate_flag = st.checkbox("Duplicate Flag", value=False, key="theia_intake_duplicate_flag")
                intake_duplicate_notes = st.text_area("Duplicate Notes", height=70, key="theia_intake_duplicate_notes")
                intake_created_by = st.text_input(
                    "Created By",
                    value=thesis['reviewer'] if thesis['reviewer'] else "System",
                    key="theia_intake_created_by"
                )

                intake_submitted = st.form_submit_button("Stage Evidence", use_container_width=True)

                if intake_submitted:
                    staging_uuid = str(uuid.uuid4())
                    insert_query(
                        """
                        INSERT INTO evidence_staging
                        (
                            staging_uuid,
                            thesis_id,
                            source_type,
                            source_name,
                            source_url,
                            publication_date,
                            retrieval_date,
                            author_publisher,
                            evidence_summary,
                            key_takeaway,
                            preliminary_grade,
                            source_quality_notes,
                            duplicate_flag,
                            duplicate_notes,
                            intake_status,
                            created_by,
                            created_at
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            staging_uuid,
                            int(intake_thesis_id) if intake_thesis_id is not None else None,
                            intake_source_type if intake_source_type else None,
                            intake_source_name.strip() if intake_source_name else None,
                            intake_source_url.strip() if intake_source_url else None,
                            intake_publication_date.isoformat() if intake_publication_date else None,
                            intake_retrieval_date.isoformat() if intake_retrieval_date else None,
                            intake_author_publisher.strip() if intake_author_publisher else None,
                            intake_evidence_summary.strip() if intake_evidence_summary else None,
                            intake_key_takeaway.strip() if intake_key_takeaway else None,
                            intake_preliminary_grade if intake_preliminary_grade else None,
                            intake_source_quality_notes.strip() if intake_source_quality_notes else None,
                            1 if intake_duplicate_flag else 0,
                            intake_duplicate_notes.strip() if intake_duplicate_notes else None,
                            INTAKE_STATUS_PENDING,
                            intake_created_by.strip() if intake_created_by else "System",
                            datetime.now().isoformat(),
                        )
                    )

                    if intake_thesis_id is not None:
                        log_event(
                            thesis_id=int(intake_thesis_id),
                            event_type=EVENT_EVIDENCE_STAGED,
                            description=f"Evidence staged: staging_uuid={staging_uuid}",
                            created_by=intake_created_by.strip() if intake_created_by else "System",
                            version="1.0"
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

                    if current_status in TERMINAL_INTAKE_STATUSES:
                        st.info(f"Status is terminal ({current_status}). No further status transitions are allowed.")
                    else:
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            if current_status == INTAKE_STATUS_PENDING and st.button("Mark as Reviewed", key="theia_mark_reviewed"):
                                run_query(
                                    """
                                    UPDATE evidence_staging
                                    SET intake_status = ?, reviewed_by = ?, review_date = ?
                                    WHERE staging_uuid = ?
                                    """,
                                    (
                                        INTAKE_STATUS_REVIEWED,
                                        reviewer_name.strip() if reviewer_name else "System",
                                        datetime.now().isoformat(),
                                        selected_staging_uuid,
                                    )
                                )
                                if pd.notna(selected_staging["thesis_id"]):
                                    log_event(
                                        thesis_id=int(selected_staging["thesis_id"]),
                                        event_type=EVENT_EVIDENCE_REVIEWED,
                                        description=f"Evidence reviewed: staging_uuid={selected_staging_uuid}",
                                        created_by=reviewer_name.strip() if reviewer_name else "System",
                                        version="1.0"
                                    )
                                st.success("✓ Staged evidence marked as Reviewed")
                                st.rerun()

                        with col2:
                            if current_status == INTAKE_STATUS_REVIEWED and st.button("Mark as Confirmed", key="theia_mark_confirmed"):
                                run_query(
                                    """
                                    UPDATE evidence_staging
                                    SET intake_status = ?, reviewed_by = ?, review_date = ?, rejection_reason = NULL
                                    WHERE staging_uuid = ?
                                    """,
                                    (
                                        INTAKE_STATUS_CONFIRMED,
                                        reviewer_name.strip() if reviewer_name else "System",
                                        datetime.now().isoformat(),
                                        selected_staging_uuid,
                                    )
                                )
                                st.success("✓ Staged evidence marked as Confirmed")
                                st.rerun()

                        with col3:
                            if current_status == INTAKE_STATUS_REVIEWED and st.button("Mark as Rejected", key="theia_mark_rejected"):
                                if not rejection_reason_input.strip():
                                    st.error("Rejection requires a non-empty rejection_reason.")
                                else:
                                    run_query(
                                        """
                                        UPDATE evidence_staging
                                        SET intake_status = ?, reviewed_by = ?, review_date = ?, rejection_reason = ?
                                        WHERE staging_uuid = ?
                                        """,
                                        (
                                            INTAKE_STATUS_REJECTED,
                                            reviewer_name.strip() if reviewer_name else "System",
                                            datetime.now().isoformat(),
                                            rejection_reason_input.strip(),
                                            selected_staging_uuid,
                                        )
                                    )
                                    if pd.notna(selected_staging["thesis_id"]):
                                        log_event(
                                            thesis_id=int(selected_staging["thesis_id"]),
                                            event_type=EVENT_EVIDENCE_REJECTED,
                                            description=f"Evidence rejected: staging_uuid={selected_staging_uuid}",
                                            created_by=reviewer_name.strip() if reviewer_name else "System",
                                            version="1.0"
                                        )
                                    st.success("✓ Staged evidence marked as Rejected")
                                    st.rerun()

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
        
        with tab3:
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
                        value=pd.to_datetime(existing_record['review_date']).date() if existing_record is not None and pd.notna(existing_record['review_date']) else datetime.now().date()
                    )

                submitted = st.form_submit_button("Save Business Quality Score", use_container_width=True)

                if submitted:
                    created_by = reviewer.strip() if reviewer and reviewer.strip() else (thesis['reviewer'] if thesis['reviewer'] else "System")
                    pillar_score_id = None

                    check_df = fetch_dataframe(
                        "SELECT * FROM pillar_scores WHERE thesis_id = ? AND pillar_id = ?",
                        (thesis_id, pillar_id)
                    )

                    if not check_df.empty:
                        run_query(
                            """
                            UPDATE pillar_scores
                            SET pillar_name = ?,
                                score = ?,
                                rag_status = ?,
                                evidence_grade = ?,
                                judgment = ?,
                                confidence_basis = ?,
                                falsification_trigger = ?,
                                reviewer = ?,
                                review_date = ?
                            WHERE thesis_id = ? AND pillar_id = ?
                            """,
                            (
                                pillar_name,
                                score,
                                rag_status,
                                evidence_grade,
                                judgment.strip() if judgment else None,
                                confidence_basis.strip() if confidence_basis else None,
                                falsification_trigger.strip() if falsification_trigger else None,
                                reviewer.strip() if reviewer else None,
                                review_date.isoformat() if review_date else None,
                                thesis_id,
                                pillar_id
                            )
                        )

                        log_event(
                            thesis_id=thesis_id,
                            event_type=EVENT_BUSINESS_ASSESSMENT_UPDATED,
                            description=f"Business assessment updated: {pillar_id} {pillar_name}",
                            created_by=created_by,
                            version="1.0"
                        )

                        resolved_df = fetch_dataframe(
                            "SELECT id FROM pillar_scores WHERE thesis_id = ? AND pillar_id = ?",
                            (thesis_id, pillar_id)
                        )
                        if not resolved_df.empty:
                            pillar_score_id = int(resolved_df.iloc[0]['id'])

                        st.success(f"✓ Business assessment updated for {pillar_id} {pillar_name}")
                    else:
                        pillar_score_id = insert_query(
                            """
                            INSERT INTO pillar_scores
                            (thesis_id, pillar_id, pillar_name, score, rag_status, evidence_grade,
                             judgment, confidence_basis, primary_sources, evidence_items,
                             falsification_trigger,
                             reviewer, review_date, drl, created_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                thesis_id,
                                pillar_id,
                                pillar_name,
                                score,
                                rag_status,
                                evidence_grade,
                                judgment.strip() if judgment else None,
                                confidence_basis.strip() if confidence_basis else None,
                                None,
                                None,
                                falsification_trigger.strip() if falsification_trigger else None,
                                reviewer.strip() if reviewer else None,
                                review_date.isoformat() if review_date else None,
                                None,
                                datetime.now().isoformat()
                            )
                        )

                        log_event(
                            thesis_id=thesis_id,
                            event_type=EVENT_BUSINESS_ASSESSMENT_COMPLETED,
                            description=f"Business assessment saved: {pillar_id} {pillar_name}",
                            created_by=created_by,
                            version="1.0"
                        )

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
        
        with tab4:
            empty_state("Industry Module Coming Next")

        with tab5:
            empty_state("Financials Module Coming Next")

        with tab6:
            empty_state("Management Module Coming Next")

        with tab7:
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

            available_evidence_ids, available_evidence_labels = get_available_evidence_items(thesis_id)
            linked_evidence_defaults = []
            if existing_pillar_score_id is not None:
                linked_evidence_defaults = get_linked_evidence_ids(existing_pillar_score_id)

            investment_judgment_default = ""
            if existing_record is not None:
                if 'judgment' in existing_record.index and pd.notna(existing_record['judgment']) and str(existing_record['judgment']).strip() != "":
                    investment_judgment_default = str(existing_record['judgment'])
                elif pd.notna(existing_record['inference']) and str(existing_record['inference']).strip() != "":
                    investment_judgment_default = str(existing_record['inference'])
            
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
                        value=pd.to_datetime(existing_record['review_date']).date() if existing_record is not None and pd.notna(existing_record['review_date']) else datetime.now().date(),
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
                        
                        # Check if record exists
                        check_df = fetch_dataframe(
                            "SELECT * FROM pillar_scores WHERE thesis_id = ? AND pillar_id = ?",
                            (thesis_id, pillar_id)
                        )
                        
                        if not check_df.empty:
                            # UPDATE existing record
                            pillar_score_id = int(check_df.iloc[0]['id']) if pd.notna(check_df.iloc[0]['id']) else None
                            run_query(
                                """
                                UPDATE pillar_scores
                                SET score = ?, rag_status = ?, evidence_grade = ?,
                                    confidence_basis = ?, primary_sources = ?,
                                    judgment = ?, falsification_trigger = ?,
                                    reviewer = ?, review_date = ?, drl = ?
                                WHERE thesis_id = ? AND pillar_id = ?
                                """,
                                (
                                    score,
                                    rag_status if rag_status else None,
                                    evidence_grade if evidence_grade else None,
                                    confidence_basis.strip(),
                                    primary_sources.strip() if primary_sources else None,
                                    judgment.strip(),
                                    falsification_trigger.strip(),
                                    reviewer.strip() if reviewer else None,
                                    review_date.isoformat() if review_date else None,
                                    int(drl) if drl else None,
                                    thesis_id,
                                    pillar_id
                                )
                            )
                            
                            log_event(
                                thesis_id=thesis_id,
                                event_type=EVENT_INVESTMENT_ASSESSMENT_UPDATED,
                                description=f"Investment assessment updated: {pillar_id} {pillar_name}",
                                created_by=created_by,
                                version="1.0"
                            )
                            
                            st.success(f"✓ Investment assessment updated for {pillar_id} {pillar_name}")
                        else:
                            # INSERT new record
                            pillar_score_id = insert_query(
                                """
                                INSERT INTO pillar_scores
                                (thesis_id, pillar_id, pillar_name, score, rag_status, evidence_grade,
                                 confidence_basis, primary_sources, judgment,
                                 falsification_trigger,
                                 reviewer, review_date, drl, created_at)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                """,
                                (
                                    thesis_id,
                                    pillar_id,
                                    pillar_name,
                                    score,
                                    rag_status if rag_status else None,
                                    evidence_grade if evidence_grade else None,
                                    confidence_basis.strip(),
                                    primary_sources.strip() if primary_sources else None,
                                    judgment.strip(),
                                    falsification_trigger.strip(),
                                    reviewer.strip() if reviewer else None,
                                    review_date.isoformat() if review_date else None,
                                    int(drl) if drl else None,
                                    datetime.now().isoformat()
                                )
                            )
                            
                            log_event(
                                thesis_id=thesis_id,
                                event_type=EVENT_INVESTMENT_ASSESSMENT_COMPLETED,
                                description=f"Investment assessment saved: {pillar_id} {pillar_name}",
                                created_by=created_by,
                                version="1.0"
                            )
                            
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
        
        with tab8:
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

                default_review_date = datetime.now().date()
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
                        elif not outcome_summary.strip():
                            st.error("Outcome Summary is required.")
                        elif not outcome_evidence.strip():
                            st.error("Outcome Evidence is required.")
                        elif not thesis_quality_assessment.strip():
                            st.error("Thesis Quality Assessment is required.")
                        elif not decision_quality_notes.strip():
                            st.error("Decision Quality Notes is required.")
                        elif not reviewer.strip():
                            st.error("Reviewer is required.")
                        else:
                            review_exists_df = fetch_dataframe(
                                """
                                SELECT id
                                FROM thesis_reviews
                                WHERE thesis_id = ? AND decision_log_id = ? AND review_horizon = ?
                                LIMIT 1
                                """,
                                (thesis_id, decision_log_id, review_horizon)
                            )

                            if not review_exists_df.empty:
                                review_id = int(review_exists_df.iloc[0]["id"])
                                run_query(
                                    """
                                    UPDATE thesis_reviews
                                    SET review_date = ?,
                                        outcome_summary = ?,
                                        outcome_attribution_type = ?,
                                        outcome_evidence = ?,
                                        thesis_quality_assessment = ?,
                                        decision_quality_preserved = ?,
                                        decision_quality_notes = ?,
                                        framework_review_eligible = ?,
                                        framework_notes = ?,
                                        reviewer = ?
                                    WHERE id = ?
                                    """,
                                    (
                                        review_date.isoformat() if review_date else None,
                                        outcome_summary.strip(),
                                        outcome_attribution_type,
                                        outcome_evidence.strip(),
                                        thesis_quality_assessment.strip(),
                                        1 if decision_quality_preserved else 0,
                                        decision_quality_notes.strip(),
                                        framework_review_eligible,
                                        framework_notes.strip() if framework_notes else None,
                                        reviewer.strip(),
                                        review_id
                                    )
                                )

                                log_event(
                                    thesis_id=thesis_id,
                                    event_type=EVENT_THESIS_REVIEW_UPDATED,
                                    description=(
                                        f"Thesis review updated: decision_log_id={decision_log_id}, "
                                        f"review_horizon={review_horizon}, "
                                        f"outcome_attribution_type={outcome_attribution_type}, "
                                        f"framework_review_eligible={framework_review_eligible}"
                                    ),
                                    created_by=reviewer.strip(),
                                    version="1.0"
                                )

                                st.success("✓ Thesis review updated")
                            else:
                                insert_query(
                                    """
                                    INSERT INTO thesis_reviews
                                    (
                                        thesis_id,
                                        decision_log_id,
                                        review_date,
                                        review_horizon,
                                        outcome_summary,
                                        outcome_attribution_type,
                                        outcome_evidence,
                                        thesis_quality_assessment,
                                        decision_quality_preserved,
                                        decision_quality_notes,
                                        framework_review_eligible,
                                        framework_notes,
                                        reviewer,
                                        created_at
                                    )
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                    """,
                                    (
                                        thesis_id,
                                        decision_log_id,
                                        review_date.isoformat() if review_date else None,
                                        review_horizon,
                                        outcome_summary.strip(),
                                        outcome_attribution_type,
                                        outcome_evidence.strip(),
                                        thesis_quality_assessment.strip(),
                                        1 if decision_quality_preserved else 0,
                                        decision_quality_notes.strip(),
                                        framework_review_eligible,
                                        framework_notes.strip() if framework_notes else None,
                                        reviewer.strip(),
                                        datetime.now().isoformat()
                                    )
                                )

                                log_event(
                                    thesis_id=thesis_id,
                                    event_type=EVENT_THESIS_REVIEW_CREATED,
                                    description=(
                                        f"Thesis review created: decision_log_id={decision_log_id}, "
                                        f"review_horizon={review_horizon}, "
                                        f"outcome_attribution_type={outcome_attribution_type}, "
                                        f"framework_review_eligible={framework_review_eligible}"
                                    ),
                                    created_by=reviewer.strip(),
                                    version="1.0"
                                )

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

        with tab9:
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
                        if existing_decision is not None:
                            # UPDATE existing decision
                            run_query(
                                """
                                UPDATE decision_logs
                                SET recommendation = ?, horizon_map = ?, action = ?,
                                    review_date = ?, decision_rationale = ?, key_risks = ?,
                                    falsification_summary = ?, next_review_date = ?
                                WHERE thesis_id = ?
                                """,
                                (
                                    recommendation if recommendation else None,
                                    horizon_map.strip() if horizon_map else None,
                                    action.strip() if action else None,
                                    review_date.isoformat() if review_date else None,
                                    decision_rationale.strip() if decision_rationale else None,
                                    key_risks.strip() if key_risks else None,
                                    falsification_summary.strip() if falsification_summary else None,
                                    next_review_date.isoformat() if next_review_date else None,
                                    thesis_id
                                )
                            )
                        else:
                            # INSERT new decision
                            insert_query(
                                """
                                INSERT INTO decision_logs
                                (thesis_id, recommendation, horizon_map, action, review_date,
                                 decision_rationale, key_risks, falsification_summary, next_review_date, created_at)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                """,
                                (
                                    thesis_id,
                                    recommendation if recommendation else None,
                                    horizon_map.strip() if horizon_map else None,
                                    action.strip() if action else None,
                                    review_date.isoformat() if review_date else None,
                                    decision_rationale.strip() if decision_rationale else None,
                                    key_risks.strip() if key_risks else None,
                                    falsification_summary.strip() if falsification_summary else None,
                                    next_review_date.isoformat() if next_review_date else None,
                                    datetime.now().isoformat()
                                )
                            )

                        log_event(
                            thesis_id=thesis_id,
                            event_type=EVENT_DECISION_RECORDED,
                            description=f"Decision recorded or updated. validated_at={gate_result['validated_at']}",
                            created_by=thesis['reviewer'] if thesis['reviewer'] else "System",
                            version="1.0"
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
        
        with tab10:
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

