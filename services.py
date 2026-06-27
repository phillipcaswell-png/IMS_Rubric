import sqlite3
import uuid
from datetime import datetime

import pandas as pd


# =============================================================================
# DATABASE SERVICES
# =============================================================================

DATABASE_FILE = "/Users/phillipcaswell/ims_mvp.db"


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

    try:
        cursor.execute("ALTER TABLE evidence_items ADD COLUMN status TEXT DEFAULT 'Promoted'")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE evidence_items ADD COLUMN source_text TEXT DEFAULT NULL")
    except sqlite3.OperationalError:
        pass

    cursor.execute(
        """
        UPDATE evidence_items
        SET status = 'Promoted'
        WHERE status IS NULL OR TRIM(status) = ''
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS evidence_observations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            evidence_item_id INTEGER NOT NULL,
            pillar_id TEXT,
            observation_category TEXT NOT NULL,
            observation_text TEXT NOT NULL,
            evidence_quote TEXT,
            source_location TEXT,
            analyst_confidence TEXT,
            created_by TEXT NOT NULL,
            created_at TEXT NOT NULL,
            status TEXT DEFAULT 'Active',
            FOREIGN KEY (evidence_item_id) REFERENCES evidence_items(id)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS audit_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            thesis_id INTEGER,
            event_type TEXT NOT NULL,
            entity_type TEXT,
            entity_id INTEGER,
            details TEXT,
            created_by TEXT,
            created_at TEXT NOT NULL,
            version TEXT
        )
        """
    )

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

    try:
        cursor.execute("ALTER TABLE evidence_staging ADD COLUMN archive_reason TEXT DEFAULT NULL")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE evidence_staging ADD COLUMN source_text TEXT DEFAULT NULL")
    except sqlite3.OperationalError:
        pass

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


# =============================================================================
# THESIS SERVICES
# =============================================================================

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
EVENT_EVIDENCE_ARCHIVED = "Evidence Archived"
EVENT_EVIDENCE_OBSERVATION_CREATED = "Evidence Observation Created"
EVENT_EVIDENCE_OBSERVATION_UPDATED = "Evidence Observation Updated"

INTAKE_STATUS_PENDING = "Pending"
INTAKE_STATUS_REVIEWED = "Reviewed"
INTAKE_STATUS_CONFIRMED = "Confirmed"
INTAKE_STATUS_PROMOTED = "Promoted"
INTAKE_STATUS_REJECTED = "Rejected"
INTAKE_STATUS_ARCHIVED = "Archived"

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

GRADE_A = "A"
GRADE_B = "B"
GRADE_C = "C"
GRADE_D = "D"

OBSERVATION_STATUS_ACTIVE = "Active"
OBSERVATION_STATUS_INACTIVE = "Inactive"
OBSERVATION_STATUS_OPTIONS = [
    OBSERVATION_STATUS_ACTIVE,
    OBSERVATION_STATUS_INACTIVE,
]

OBSERVATION_CATEGORY_FACT = "Fact"
OBSERVATION_CATEGORY_MANAGEMENT_STATEMENT = "Management Statement"
OBSERVATION_CATEGORY_RISK_DISCLOSURE = "Risk Disclosure"
OBSERVATION_CATEGORY_CAPITAL_ALLOCATION = "Capital Allocation"
OBSERVATION_CATEGORY_FINANCIAL_TREND = "Financial Trend"
OBSERVATION_CATEGORY_COMPETITIVE_POSITION = "Competitive Position"
OBSERVATION_CATEGORY_INDUSTRY_OBSERVATION = "Industry Observation"
OBSERVATION_CATEGORY_OTHER = "Other"

OBSERVATION_CATEGORY_OPTIONS = [
    OBSERVATION_CATEGORY_FACT,
    OBSERVATION_CATEGORY_MANAGEMENT_STATEMENT,
    OBSERVATION_CATEGORY_RISK_DISCLOSURE,
    OBSERVATION_CATEGORY_CAPITAL_ALLOCATION,
    OBSERVATION_CATEGORY_FINANCIAL_TREND,
    OBSERVATION_CATEGORY_COMPETITIVE_POSITION,
    OBSERVATION_CATEGORY_INDUSTRY_OBSERVATION,
    OBSERVATION_CATEGORY_OTHER,
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

HERMES_PRIORITY_CRITICAL = 1
HERMES_PRIORITY_HIGH = 2
HERMES_PRIORITY_MEDIUM = 3
HERMES_PRIORITY_LOW = 4


def create_thesis(
    company_name,
    ticker,
    decision_question,
    account_type,
    portfolio_role,
    primary_horizon,
    regime_state,
    reviewer,
    status,
    drl,
    validation_mode_enabled,
    evidence_cutoff_date,
):
    """Create thesis record and log creation event."""
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
            datetime.now().isoformat(),
        ),
    )

    event_created_by = reviewer.strip() if reviewer else "System"
    log_event(
        thesis_id=thesis_id,
        event_type=EVENT_EVALUATION_CREATED,
        description="Initial thesis created.",
        created_by=event_created_by,
        version="1.0",
    )
    return thesis_id


def get_overview_metrics(thesis_id):
    """Get overview metrics for a thesis."""
    evidence_df = fetch_dataframe(
        "SELECT COUNT(*) as count FROM evidence_items WHERE thesis_id = ?",
        (thesis_id,),
    )
    evidence_count = evidence_df["count"].iloc[0]

    business_df = fetch_dataframe(
        "SELECT COUNT(*) as count FROM pillar_scores WHERE thesis_id = ? AND pillar_id LIKE 'B%' AND score IS NOT NULL",
        (thesis_id,),
    )
    business_pillars_completed = business_df["count"].iloc[0]

    investment_df = fetch_dataframe(
        "SELECT COUNT(*) as count FROM pillar_scores WHERE thesis_id = ? AND pillar_id LIKE 'I%' AND score IS NOT NULL",
        (thesis_id,),
    )
    investment_pillars_completed = investment_df["count"].iloc[0]

    events_df = fetch_dataframe(
        "SELECT COUNT(*) as count FROM thesis_events WHERE thesis_id = ?",
        (thesis_id,),
    )
    audit_event_count = events_df["count"].iloc[0]

    return {
        "evidence_count": evidence_count,
        "business_pillars_completed": business_pillars_completed,
        "investment_pillars_completed": investment_pillars_completed,
        "audit_event_count": audit_event_count,
    }


def build_thesis_json(thesis_id):
    """Build a comprehensive JSON export of a thesis with all related data."""
    thesis_df = fetch_dataframe(
        "SELECT * FROM theses WHERE id = ?",
        (thesis_id,),
    )
    thesis_dict = thesis_df.iloc[0].to_dict() if not thesis_df.empty else {}

    evidence_df = fetch_dataframe(
        "SELECT * FROM evidence_items WHERE thesis_id = ? ORDER BY created_at DESC",
        (thesis_id,),
    )
    evidence_list = evidence_df.to_dict("records")

    business_df = fetch_dataframe(
        "SELECT * FROM pillar_scores WHERE thesis_id = ? AND pillar_id LIKE 'B%' ORDER BY pillar_id",
        (thesis_id,),
    )
    business_list = business_df.to_dict("records")

    investment_df = fetch_dataframe(
        "SELECT * FROM pillar_scores WHERE thesis_id = ? AND pillar_id LIKE 'I%' ORDER BY pillar_id",
        (thesis_id,),
    )
    investment_list = investment_df.to_dict("records")

    decision_df = fetch_dataframe(
        "SELECT * FROM decision_logs WHERE thesis_id = ?",
        (thesis_id,),
    )
    decision_dict = decision_df.iloc[0].to_dict() if not decision_df.empty else {}

    events_df = fetch_dataframe(
        "SELECT * FROM thesis_events WHERE thesis_id = ? ORDER BY created_at DESC",
        (thesis_id,),
    )
    events_list = events_df.to_dict("records")

    return {
        "thesis": thesis_dict,
        "evidence_items": evidence_list,
        "business_assessments": business_list,
        "investment_assessments": investment_list,
        "decision_log": decision_dict,
        "audit_trail": events_list,
    }


# =============================================================================
# EVIDENCE SERVICES — THEIA
# =============================================================================


def stage_evidence(
    intake_thesis_id,
    intake_source_type,
    intake_source_name,
    intake_source_url,
    intake_publication_date,
    intake_retrieval_date,
    intake_author_publisher,
    intake_evidence_summary,
    intake_key_takeaway,
    intake_preliminary_grade,
    intake_source_quality_notes,
    intake_duplicate_flag,
    intake_duplicate_notes,
    intake_created_by,
):
    """Insert staged evidence and log staging event."""
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
        ),
    )

    if intake_thesis_id is not None:
        log_event(
            thesis_id=int(intake_thesis_id),
            event_type=EVENT_EVIDENCE_STAGED,
            description=f"Evidence staged: staging_uuid={staging_uuid}",
            created_by=intake_created_by.strip() if intake_created_by else "System",
            version="1.0",
        )

    return staging_uuid


def update_staged_evidence_source_text(staging_uuid, source_text):
    """Update source_text for a staged evidence record without changing status transitions."""
    run_query(
        """
        UPDATE evidence_staging
        SET source_text = ?
        WHERE staging_uuid = ?
        """,
        (
            str(source_text).strip() if source_text is not None and str(source_text).strip() else None,
            str(staging_uuid).strip(),
        ),
    )


def update_evidence_source_text(evidence_item_id: int, source_text: str, updated_by: str) -> bool:
    """Update source_text for a promoted evidence item."""
    evidence_id_value = int(evidence_item_id)
    updated_by_value = str(updated_by).strip() if updated_by is not None else ""
    if not updated_by_value:
        return False

    run_query(
        """
        UPDATE evidence_items
        SET source_text = ?
        WHERE id = ? AND status = ?
        """,
        (
            str(source_text).strip() if source_text is not None and str(source_text).strip() else None,
            evidence_id_value,
            INTAKE_STATUS_PROMOTED,
        ),
    )

    verification_df = fetch_dataframe(
        """
        SELECT id
        FROM evidence_items
        WHERE id = ? AND status = ?
        LIMIT 1
        """,
        (evidence_id_value, INTAKE_STATUS_PROMOTED),
    )
    return not verification_df.empty


def update_evidence_item(
    evidence_item_id: int,
    source_name: str,
    title: str,
    source_type: str,
    source_publisher: str,
    url_or_citation: str,
    publication_date,
    evidence_summary: str,
    key_takeaway: str,
    source_text: str,
    tags: str,
    credibility_score: int,
    materiality_score: int,
    thesis_alignment: str,
    thesis_id: int,
    updated_by: str,
) -> bool:
    """Update a promoted evidence item and log the evidence-updated event."""
    evidence_id_value = int(evidence_item_id)
    thesis_id_value = int(thesis_id)

    exists_df = fetch_dataframe(
        """
        SELECT id
        FROM evidence_items
        WHERE id = ? AND thesis_id = ?
        LIMIT 1
        """,
        (evidence_id_value, thesis_id_value),
    )
    if exists_df.empty:
        return False

    source_name_value = str(source_name).strip() if source_name is not None else ""
    title_value = str(title).strip() if title is not None else ""

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
            source_text = ?,
            tags = ?,
            credibility_score = ?,
            materiality_score = ?,
            thesis_alignment = ?
        WHERE id = ? AND thesis_id = ?
        """,
        (
            source_name_value,
            title_value,
            str(source_type).strip() if source_type is not None and str(source_type).strip() else None,
            str(source_publisher).strip() if source_publisher is not None and str(source_publisher).strip() else None,
            str(url_or_citation).strip() if url_or_citation is not None and str(url_or_citation).strip() else None,
            str(publication_date).strip() if publication_date is not None and str(publication_date).strip() else None,
            str(evidence_summary).strip() if evidence_summary is not None and str(evidence_summary).strip() else None,
            str(key_takeaway).strip() if key_takeaway is not None and str(key_takeaway).strip() else None,
            str(source_text).strip() if source_text is not None and str(source_text).strip() else None,
            str(tags).strip() if tags is not None and str(tags).strip() else None,
            int(credibility_score) if credibility_score is not None else None,
            int(materiality_score) if materiality_score is not None else None,
            str(thesis_alignment).strip() if thesis_alignment is not None and str(thesis_alignment).strip() else None,
            evidence_id_value,
            thesis_id_value,
        ),
    )

    created_by_value = str(updated_by).strip() if updated_by is not None and str(updated_by).strip() else "System"
    log_event(
        thesis_id=thesis_id_value,
        event_type=EVENT_EVIDENCE_UPDATED,
        description=f"Evidence item updated: {title_value}",
        created_by=created_by_value,
        version="1.0",
    )

    return True


def update_staged_evidence_status(
    staging_uuid,
    target_status,
    reviewer_name,
    rejection_reason_input,
    thesis_id,
):
    """Apply staged evidence status transitions for reviewed/confirmed/rejected."""
    reviewer_value = reviewer_name.strip() if reviewer_name else "System"

    if target_status == INTAKE_STATUS_REVIEWED:
        run_query(
            """
            UPDATE evidence_staging
            SET intake_status = ?, reviewed_by = ?, review_date = ?
            WHERE staging_uuid = ?
            """,
            (
                INTAKE_STATUS_REVIEWED,
                reviewer_value,
                datetime.now().isoformat(),
                staging_uuid,
            ),
        )
        if thesis_id is not None:
            log_event(
                thesis_id=int(thesis_id),
                event_type=EVENT_EVIDENCE_REVIEWED,
                description=f"Evidence reviewed: staging_uuid={staging_uuid}",
                created_by=reviewer_value,
                version="1.0",
            )
        return {"success": True, "message": "✓ Staged evidence marked as Reviewed"}

    if target_status == INTAKE_STATUS_CONFIRMED:
        run_query(
            """
            UPDATE evidence_staging
            SET intake_status = ?, reviewed_by = ?, review_date = ?, rejection_reason = NULL
            WHERE staging_uuid = ?
            """,
            (
                INTAKE_STATUS_CONFIRMED,
                reviewer_value,
                datetime.now().isoformat(),
                staging_uuid,
            ),
        )
        return {"success": True, "message": "✓ Staged evidence marked as Confirmed"}

    if target_status == INTAKE_STATUS_REJECTED:
        if not rejection_reason_input.strip():
            return {"success": False, "message": "Rejection requires a non-empty rejection_reason."}

        run_query(
            """
            UPDATE evidence_staging
            SET intake_status = ?, reviewed_by = ?, review_date = ?, rejection_reason = ?
            WHERE staging_uuid = ?
            """,
            (
                INTAKE_STATUS_REJECTED,
                reviewer_value,
                datetime.now().isoformat(),
                rejection_reason_input.strip(),
                staging_uuid,
            ),
        )
        if thesis_id is not None:
            log_event(
                thesis_id=int(thesis_id),
                event_type=EVENT_EVIDENCE_REJECTED,
                description=f"Evidence rejected: staging_uuid={staging_uuid}",
                created_by=reviewer_value,
                version="1.0",
            )
        return {"success": True, "message": "✓ Staged evidence marked as Rejected"}

    return {"success": False, "message": "Unsupported staged evidence transition."}


def archive_staged_evidence(staging_uuid, analyst, archive_reason):
    """Archive a staged evidence record without deleting audit history."""
    staging_df = fetch_dataframe(
        "SELECT * FROM evidence_staging WHERE staging_uuid = ? LIMIT 1",
        (staging_uuid,),
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
            "message": f"Archive blocked: terminal status '{current_status}'.",
            "promoted_evidence_id": None,
        }

    if not archive_reason or not str(archive_reason).strip():
        return {
            "success": False,
            "message": "Archive requires a non-empty archive_reason.",
            "promoted_evidence_id": None,
        }

    analyst_value = analyst.strip() if analyst and str(analyst).strip() else "System"
    run_query(
        """
        UPDATE evidence_staging
        SET intake_status = ?,
            archive_reason = ?,
            reviewed_by = ?,
            review_date = ?
        WHERE staging_uuid = ?
        """,
        (
            INTAKE_STATUS_ARCHIVED,
            str(archive_reason).strip(),
            analyst_value,
            datetime.now().isoformat(),
            staging_uuid,
        ),
    )

    if pd.notna(staging_record["thesis_id"]):
        log_event(
            thesis_id=int(staging_record["thesis_id"]),
            event_type=EVENT_EVIDENCE_ARCHIVED,
            description=f"Evidence archived: staging_uuid={staging_uuid}",
            created_by=analyst_value,
            version="1.0",
        )

    return {
        "success": True,
        "message": "Staged evidence archived successfully.",
        "promoted_evidence_id": None,
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
        "B7": "Systems Importance",
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
            (thesis_id, pillar_id),
        )

        grades = (
            pillar_df["evidence_grade"]
            .dropna()
            .astype(str)
            .str.strip()
            .tolist()
        )

        highest_grade = next((g for g in grade_priority if g in grades), "—")

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
        (thesis_id,),
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
        (pillar_score_id,),
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
        (pillar_score_id,),
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
                datetime.now().isoformat(),
            ),
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
                version="1.0",
            )

    for evidence_item_id in to_remove:
        run_query(
            """
            DELETE FROM pillar_evidence_links
            WHERE pillar_score_id = ? AND evidence_item_id = ?
            """,
            (pillar_score_id, evidence_item_id),
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
                version="1.0",
            )


def promote_staged_evidence(staging_uuid, analyst):
    """Promote analyst-confirmed staged evidence into the official evidence repository."""
    staging_df = fetch_dataframe(
        "SELECT * FROM evidence_staging WHERE staging_uuid = ? LIMIT 1",
        (staging_uuid,),
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
        (int(staging_record["thesis_id"]),),
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
                    version="1.0",
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
            source_text,
            tags,
            credibility_score,
            materiality_score,
            thesis_alignment
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            staging_record["source_text"] if "source_text" in staging_record.index and pd.notna(staging_record["source_text"]) else None,
            None,
            None,
            None,
            None,
        ),
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
        ),
    )

    log_event(
        thesis_id=int(staging_record["thesis_id"]),
        event_type=EVENT_EVIDENCE_PROMOTED,
        description=f"Staged evidence promoted: staging_uuid={staging_uuid}, promoted_evidence_id={promoted_evidence_id}",
        created_by=analyst if analyst and str(analyst).strip() else "System",
        version="1.0",
    )

    return {
        "success": True,
        "message": "Staged evidence promoted successfully.",
        "promoted_evidence_id": int(promoted_evidence_id),
    }


def _normalize_observation_status(status):
    if status is None:
        return OBSERVATION_STATUS_ACTIVE
    normalized = str(status).strip()
    if not normalized:
        return OBSERVATION_STATUS_ACTIVE
    if normalized not in OBSERVATION_STATUS_OPTIONS:
        raise ValueError(
            f"Invalid observation status '{normalized}'. Allowed: {', '.join(OBSERVATION_STATUS_OPTIONS)}"
        )
    return normalized


def _normalize_observation_category(observation_category):
    normalized = str(observation_category).strip() if observation_category is not None else ""
    if not normalized:
        raise ValueError("observation_category is required.")
    if normalized not in OBSERVATION_CATEGORY_OPTIONS:
        raise ValueError(
            f"Invalid observation_category '{normalized}'. Allowed: {', '.join(OBSERVATION_CATEGORY_OPTIONS)}"
        )
    return normalized


def _resolve_promoted_evidence_item(evidence_item_id):
    evidence_df = fetch_dataframe(
        """
        SELECT id, thesis_id, COALESCE(status, 'Promoted') AS status
        FROM evidence_items
        WHERE id = ?
        LIMIT 1
        """,
        (int(evidence_item_id),),
    )

    if evidence_df.empty:
        return {
            "ok": False,
            "message": "Observation blocked: evidence_item does not exist in evidence_items (promoted state).",
            "thesis_id": None,
        }

    record = evidence_df.iloc[0]
    status = str(record["status"]).strip() if pd.notna(record["status"]) else "Promoted"
    if status != INTAKE_STATUS_PROMOTED:
        return {
            "ok": False,
            "message": f"Observation blocked: evidence_item status is '{status}', must be '{INTAKE_STATUS_PROMOTED}'.",
            "thesis_id": int(record["thesis_id"]) if pd.notna(record["thesis_id"]) else None,
        }

    return {
        "ok": True,
        "message": "ok",
        "thesis_id": int(record["thesis_id"]) if pd.notna(record["thesis_id"]) else None,
    }


def create_evidence_observation(
    evidence_item_id,
    pillar_id,
    observation_category,
    observation_text,
    evidence_quote,
    source_location,
    analyst_confidence,
    created_by,
    status=OBSERVATION_STATUS_ACTIVE,
):
    """Create a governed analyst observation for a promoted evidence item only."""
    promotion_check = _resolve_promoted_evidence_item(evidence_item_id)
    if not promotion_check["ok"]:
        return {
            "success": False,
            "message": promotion_check["message"],
            "observation_id": None,
        }

    category = _normalize_observation_category(observation_category)
    normalized_status = _normalize_observation_status(status)
    text_value = str(observation_text).strip() if observation_text is not None else ""
    created_by_value = str(created_by).strip() if created_by is not None else ""

    if not text_value:
        raise ValueError("observation_text is required.")
    if not created_by_value:
        raise ValueError("created_by is required.")

    observation_id = insert_query(
        """
        INSERT INTO evidence_observations
        (
            evidence_item_id,
            pillar_id,
            observation_category,
            observation_text,
            evidence_quote,
            source_location,
            analyst_confidence,
            created_by,
            created_at,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            int(evidence_item_id),
            str(pillar_id).strip() if pillar_id is not None and str(pillar_id).strip() else None,
            category,
            text_value,
            str(evidence_quote).strip() if evidence_quote is not None and str(evidence_quote).strip() else None,
            str(source_location).strip() if source_location is not None and str(source_location).strip() else None,
            str(analyst_confidence).strip() if analyst_confidence is not None and str(analyst_confidence).strip() else None,
            created_by_value,
            datetime.now().isoformat(),
            normalized_status,
        ),
    )

    log_event(
        thesis_id=promotion_check["thesis_id"],
        event_type=EVENT_EVIDENCE_OBSERVATION_CREATED,
        description=(
            f"Observation created: observation_id={observation_id}, "
            f"evidence_item_id={int(evidence_item_id)}, pillar_id={pillar_id if pillar_id else '—'}"
        ),
        created_by=created_by_value,
        version="1.0",
    )

    run_query(
        """
        INSERT INTO audit_events
        (
            thesis_id,
            event_type,
            entity_type,
            entity_id,
            details,
            created_by,
            created_at,
            version
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            promotion_check["thesis_id"],
            EVENT_EVIDENCE_OBSERVATION_CREATED,
            "evidence_observation",
            int(observation_id),
            (
                f"Created observation for evidence_item_id={int(evidence_item_id)}|"
                f"pillar_id={pillar_id if pillar_id else ''}|"
                f"category={category}|status={normalized_status}"
            ),
            created_by_value,
            datetime.now().isoformat(),
            "1.0",
        ),
    )

    return {
        "success": True,
        "message": "Observation created successfully.",
        "observation_id": int(observation_id),
    }


def update_evidence_observation(
    observation_id,
    pillar_id,
    observation_category,
    observation_text,
    evidence_quote,
    source_location,
    analyst_confidence,
    status,
    updated_by,
):
    """Update a governed analyst observation and emit audit events."""
    observation_df = fetch_dataframe(
        """
        SELECT eo.id, eo.evidence_item_id, ei.thesis_id
        FROM evidence_observations eo
        JOIN evidence_items ei ON ei.id = eo.evidence_item_id
        WHERE eo.id = ?
        LIMIT 1
        """,
        (int(observation_id),),
    )

    if observation_df.empty:
        return {
            "success": False,
            "message": "Observation not found.",
        }

    observation_row = observation_df.iloc[0]
    evidence_item_id = int(observation_row["evidence_item_id"])
    thesis_id = int(observation_row["thesis_id"]) if pd.notna(observation_row["thesis_id"]) else None

    promotion_check = _resolve_promoted_evidence_item(evidence_item_id)
    if not promotion_check["ok"]:
        return {
            "success": False,
            "message": promotion_check["message"],
        }

    category = _normalize_observation_category(observation_category)
    normalized_status = _normalize_observation_status(status)
    text_value = str(observation_text).strip() if observation_text is not None else ""
    updated_by_value = str(updated_by).strip() if updated_by is not None else ""

    if not text_value:
        raise ValueError("observation_text is required.")
    if not updated_by_value:
        raise ValueError("updated_by is required.")

    run_query(
        """
        UPDATE evidence_observations
        SET pillar_id = ?,
            observation_category = ?,
            observation_text = ?,
            evidence_quote = ?,
            source_location = ?,
            analyst_confidence = ?,
            status = ?
        WHERE id = ?
        """,
        (
            str(pillar_id).strip() if pillar_id is not None and str(pillar_id).strip() else None,
            category,
            text_value,
            str(evidence_quote).strip() if evidence_quote is not None and str(evidence_quote).strip() else None,
            str(source_location).strip() if source_location is not None and str(source_location).strip() else None,
            str(analyst_confidence).strip() if analyst_confidence is not None and str(analyst_confidence).strip() else None,
            normalized_status,
            int(observation_id),
        ),
    )

    log_event(
        thesis_id=thesis_id,
        event_type=EVENT_EVIDENCE_OBSERVATION_UPDATED,
        description=(
            f"Observation updated: observation_id={int(observation_id)}, "
            f"evidence_item_id={evidence_item_id}, pillar_id={pillar_id if pillar_id else '—'}"
        ),
        created_by=updated_by_value,
        version="1.0",
    )

    run_query(
        """
        INSERT INTO audit_events
        (
            thesis_id,
            event_type,
            entity_type,
            entity_id,
            details,
            created_by,
            created_at,
            version
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            thesis_id,
            EVENT_EVIDENCE_OBSERVATION_UPDATED,
            "evidence_observation",
            int(observation_id),
            (
                f"Updated observation for evidence_item_id={evidence_item_id}|"
                f"pillar_id={pillar_id if pillar_id else ''}|"
                f"category={category}|status={normalized_status}"
            ),
            updated_by_value,
            datetime.now().isoformat(),
            "1.0",
        ),
    )

    return {
        "success": True,
        "message": "Observation updated successfully.",
    }


def get_observations_for_evidence(evidence_item_id):
    """Return governed observations for a specific promoted evidence item."""
    return fetch_dataframe(
        """
        SELECT
            eo.id,
            eo.evidence_item_id,
            eo.pillar_id,
            eo.observation_category,
            eo.observation_text,
            eo.evidence_quote,
            eo.source_location,
            eo.analyst_confidence,
            eo.created_by,
            eo.created_at,
            eo.status
        FROM evidence_observations eo
        WHERE eo.evidence_item_id = ?
        ORDER BY eo.id DESC
        """,
        (int(evidence_item_id),),
    )


def get_observations_for_pillar(thesis_id, pillar_id):
    """Return observations for a thesis + pillar by joining through evidence_items."""
    return fetch_dataframe(
        """
        SELECT
            eo.id,
            eo.evidence_item_id,
            ei.thesis_id,
            eo.pillar_id,
            eo.observation_category,
            eo.observation_text,
            eo.evidence_quote,
            eo.source_location,
            eo.analyst_confidence,
            eo.created_by,
            eo.created_at,
            eo.status
        FROM evidence_observations eo
        JOIN evidence_items ei ON eo.evidence_item_id = ei.id
        WHERE ei.thesis_id = ?
          AND eo.pillar_id = ?
        ORDER BY eo.id DESC
        """,
        (int(thesis_id), str(pillar_id).strip()),
    )


# =============================================================================
# DECISION SERVICES — THEMIS
# =============================================================================


def save_pillar_score(
    thesis_id,
    pillar_id,
    pillar_name,
    score,
    rag_status,
    evidence_grade,
    judgment,
    confidence_basis,
    falsification_trigger,
    reviewer,
    review_date,
    created_by,
    primary_sources=None,
    drl=None,
):
    """Save pillar score for both business (B*) and investment (I*) flows."""
    check_df = fetch_dataframe(
        "SELECT * FROM pillar_scores WHERE thesis_id = ? AND pillar_id = ?",
        (thesis_id, pillar_id),
    )

    pillar_score_id = None
    is_update = False

    if not check_df.empty:
        is_update = True
        if str(pillar_id).startswith("B"):
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
                    pillar_id,
                ),
            )

            log_event(
                thesis_id=thesis_id,
                event_type=EVENT_BUSINESS_ASSESSMENT_UPDATED,
                description=f"Business assessment updated: {pillar_id} {pillar_name}",
                created_by=created_by,
                version="1.0",
            )
        else:
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
                    confidence_basis.strip() if confidence_basis else None,
                    primary_sources.strip() if primary_sources else None,
                    judgment.strip() if judgment else None,
                    falsification_trigger.strip() if falsification_trigger else None,
                    reviewer.strip() if reviewer else None,
                    review_date.isoformat() if review_date else None,
                    int(drl) if drl else None,
                    thesis_id,
                    pillar_id,
                ),
            )

            log_event(
                thesis_id=thesis_id,
                event_type=EVENT_INVESTMENT_ASSESSMENT_UPDATED,
                description=f"Investment assessment updated: {pillar_id} {pillar_name}",
                created_by=created_by,
                version="1.0",
            )

        resolved_df = fetch_dataframe(
            "SELECT id FROM pillar_scores WHERE thesis_id = ? AND pillar_id = ?",
            (thesis_id, pillar_id),
        )
        if not resolved_df.empty:
            pillar_score_id = int(resolved_df.iloc[0]["id"])
    else:
        if str(pillar_id).startswith("B"):
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
                    datetime.now().isoformat(),
                ),
            )

            log_event(
                thesis_id=thesis_id,
                event_type=EVENT_BUSINESS_ASSESSMENT_COMPLETED,
                description=f"Business assessment saved: {pillar_id} {pillar_name}",
                created_by=created_by,
                version="1.0",
            )
        else:
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
                    confidence_basis.strip() if confidence_basis else None,
                    primary_sources.strip() if primary_sources else None,
                    judgment.strip() if judgment else None,
                    falsification_trigger.strip() if falsification_trigger else None,
                    reviewer.strip() if reviewer else None,
                    review_date.isoformat() if review_date else None,
                    int(drl) if drl else None,
                    datetime.now().isoformat(),
                ),
            )

            log_event(
                thesis_id=thesis_id,
                event_type=EVENT_INVESTMENT_ASSESSMENT_COMPLETED,
                description=f"Investment assessment saved: {pillar_id} {pillar_name}",
                created_by=created_by,
                version="1.0",
            )

    return {
        "pillar_score_id": pillar_score_id,
        "is_update": is_update,
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
        (thesis_id, *required_pillars),
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
        "validated_at": datetime.now().isoformat(),
    }


def is_validation_configuration_locked(thesis_id):
    """Validation mode and cutoff lock after first recorded decision."""
    decision_count_df = fetch_dataframe(
        "SELECT COUNT(*) AS decision_count FROM decision_logs WHERE thesis_id = ?",
        (thesis_id,),
    )
    decision_count = int(decision_count_df.iloc[0]["decision_count"]) if not decision_count_df.empty else 0
    return decision_count > 0


def record_decision(
    thesis_id,
    recommendation,
    horizon_map,
    action,
    review_date,
    decision_rationale,
    key_risks,
    falsification_summary,
    next_review_date,
    existing_decision,
    validated_at,
    created_by,
):
    """Insert or update decision_logs row and emit decision event."""
    if existing_decision is not None:
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
                thesis_id,
            ),
        )
    else:
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
                datetime.now().isoformat(),
            ),
        )

    log_event(
        thesis_id=thesis_id,
        event_type=EVENT_DECISION_RECORDED,
        description=f"Decision recorded or updated. validated_at={validated_at}",
        created_by=created_by,
        version="1.0",
    )


# =============================================================================
# REVIEW SERVICES — MNEMOSYNE
# =============================================================================


def save_thesis_review(
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
    framework_notes,
    reviewer,
):
    """Insert or update thesis review record for a thesis/decision/horizon."""
    framework_review_eligible = 1 if outcome_attribution_type == OUTCOME_TYPE_A else 0

    review_exists_df = fetch_dataframe(
        """
        SELECT id
        FROM thesis_reviews
        WHERE thesis_id = ? AND decision_log_id = ? AND review_horizon = ?
        LIMIT 1
        """,
        (thesis_id, decision_log_id, review_horizon),
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
                review_id,
            ),
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
            version="1.0",
        )
        return {"is_update": True, "framework_review_eligible": framework_review_eligible}

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
            datetime.now().isoformat(),
        ),
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
        version="1.0",
    )
    return {"is_update": False, "framework_review_eligible": framework_review_eligible}


# =============================================================================
# WORKFLOW SERVICES — HERMES
# =============================================================================


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
        (INTAKE_STATUS_PENDING,),
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
        (INTAKE_STATUS_CONFIRMED,),
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
# ORCHESTRATION SERVICES — ATHENA
# =============================================================================


def get_athena_prebrief(thesis_id) -> dict:
    """
    Read-only orchestration service.
    Coordinates Theia, Hermes, Themis, and Mnemosyne.
    Produces a single governed briefing object.
    Does not enforce, mutate, score, decide, or review.
    """
    thesis_df = fetch_dataframe(
        """
        SELECT id, company_name, status, validation_mode, evidence_cutoff_date, created_at
        FROM theses
        WHERE id = ?
        LIMIT 1
        """,
        (thesis_id,),
    )

    if thesis_df.empty:
        return {
            "lifecycle_state": {
                "thesis_id": int(thesis_id),
                "exists": False,
            },
            "governance_readiness": {
                "eligible": False,
                "completed": 0,
                "required": 11,
                "missing": [],
            },
            "evidence_summary": {
                "repository_count": 0,
                "staging_total": 0,
                "staging_by_status": {},
            },
            "historical_context": {
                "review_count": 0,
                "horizons_present": [],
                "outcome_type_counts": {},
                "framework_review_eligible_count": 0,
            },
            "blockers": {
                "theia": ["Thesis not found."],
                "hermes": ["Thesis not found."],
                "themis": ["Thesis not found."],
                "mnemosyne": ["Thesis not found."],
            },
            "next_action": "Resolve thesis identifier before governance workflow continues.",
            "provenance": {
                "lifecycle_state": "Themis",
                "governance_readiness": "Themis",
                "evidence_summary": "Theia",
                "historical_context": "Mnemosyne",
                "blockers": {
                    "theia": ["evidence_staging"],
                    "hermes": ["compute_hermes_inbox"],
                    "themis": ["validate_decision_gate"],
                    "mnemosyne": ["thesis_reviews"],
                },
                "next_action": "Hermes",
            },
        }

    thesis = thesis_df.iloc[0]
    governance = validate_decision_gate(int(thesis_id))

    decision_count_df = fetch_dataframe(
        "SELECT COUNT(*) AS decision_count FROM decision_logs WHERE thesis_id = ?",
        (thesis_id,),
    )
    decision_count = int(decision_count_df.iloc[0]["decision_count"]) if not decision_count_df.empty else 0

    evidence_count_df = fetch_dataframe(
        "SELECT COUNT(*) AS repository_count FROM evidence_items WHERE thesis_id = ?",
        (thesis_id,),
    )
    repository_count = int(evidence_count_df.iloc[0]["repository_count"]) if not evidence_count_df.empty else 0

    staging_counts_df = fetch_dataframe(
        """
        SELECT intake_status, COUNT(*) AS status_count
        FROM evidence_staging
        WHERE thesis_id = ?
        GROUP BY intake_status
        """,
        (thesis_id,),
    )
    staging_by_status = {}
    if not staging_counts_df.empty:
        for _, row in staging_counts_df.iterrows():
            status_key = str(row["intake_status"]).strip() if pd.notna(row["intake_status"]) else "Unknown"
            staging_by_status[status_key] = int(row["status_count"])
    staging_total = int(sum(staging_by_status.values()))

    latest_publication_df = fetch_dataframe(
        "SELECT MAX(publication_date) AS latest_publication_date FROM evidence_items WHERE thesis_id = ?",
        (thesis_id,),
    )
    latest_publication_date = None
    if not latest_publication_df.empty and pd.notna(latest_publication_df.iloc[0]["latest_publication_date"]):
        latest_publication_date = str(latest_publication_df.iloc[0]["latest_publication_date"])

    reviews_df = fetch_dataframe(
        """
        SELECT review_horizon, outcome_attribution_type, framework_review_eligible, review_date
        FROM thesis_reviews
        WHERE thesis_id = ?
        """,
        (thesis_id,),
    )
    review_count = int(len(reviews_df))
    horizons_present = []
    outcome_type_counts = {}
    framework_review_eligible_count = 0
    latest_review_date = None
    if not reviews_df.empty:
        horizons_present = sorted(
            [
                str(value).strip()
                for value in reviews_df["review_horizon"].dropna().tolist()
                if str(value).strip()
            ]
        )
        outcome_counts_series = (
            reviews_df["outcome_attribution_type"].fillna("Unknown").astype(str).str.strip().value_counts()
        )
        outcome_type_counts = {str(k): int(v) for k, v in outcome_counts_series.to_dict().items()}
        framework_review_eligible_count = int(reviews_df["framework_review_eligible"].fillna(0).astype(int).sum())
        if reviews_df["review_date"].dropna().tolist():
            latest_review_date = str(pd.to_datetime(reviews_df["review_date"]).max().date())

    hermes_tasks = [
        task
        for task in compute_hermes_inbox()
        if task.get("thesis_id") is not None and int(task.get("thesis_id")) == int(thesis_id)
    ]

    blockers_themis = []
    for item in governance["missing"]:
        blockers_themis.append(f"{item['pillar_id']} — {item['label']}")

    blockers_theia = []
    pending_count = staging_by_status.get(INTAKE_STATUS_PENDING, 0)
    reviewed_count = staging_by_status.get(INTAKE_STATUS_REVIEWED, 0)
    confirmed_count = staging_by_status.get(INTAKE_STATUS_CONFIRMED, 0)
    if pending_count > 0:
        blockers_theia.append(f"{pending_count} staged evidence item(s) pending review.")
    if reviewed_count > 0:
        blockers_theia.append(f"{reviewed_count} staged evidence item(s) reviewed but not yet confirmed/rejected.")
    if confirmed_count > 0:
        blockers_theia.append(f"{confirmed_count} staged evidence item(s) confirmed and awaiting promotion.")

    blockers_hermes = [task["task_type"] for task in hermes_tasks]

    blockers_mnemosyne = []
    if decision_count > 0 and review_count == 0:
        blockers_mnemosyne.append("No thesis review recorded for an existing governed decision.")

    next_action = "No immediate governed action from Hermes."
    if hermes_tasks:
        primary_task = sorted(hermes_tasks, key=lambda item: int(item["priority"]))[0]
        next_action = primary_task.get("action") or primary_task.get("task_type")

    lifecycle_state = {
        "thesis_id": int(thesis["id"]),
        "company_name": str(thesis["company_name"]).strip() if pd.notna(thesis["company_name"]) else "Unassigned",
        "status": str(thesis["status"]).strip() if pd.notna(thesis["status"]) and str(thesis["status"]).strip() else "Unspecified",
        "decision_recorded": decision_count > 0,
        "validation_configuration_locked": decision_count > 0,
        "validation_mode": int(thesis["validation_mode"]) == 1 if pd.notna(thesis["validation_mode"]) else False,
        "evidence_cutoff_date": str(thesis["evidence_cutoff_date"]).strip() if pd.notna(thesis["evidence_cutoff_date"]) and str(thesis["evidence_cutoff_date"]).strip() else None,
        "created_at": str(thesis["created_at"]).strip() if pd.notna(thesis["created_at"]) and str(thesis["created_at"]).strip() else None,
    }

    governance_readiness = {
        "eligible": bool(governance["eligible"]),
        "completed": int(governance["completed"]),
        "required": int(governance["required"]),
        "missing": governance["missing"],
        "validated_at": governance["validated_at"],
    }

    evidence_summary = {
        "repository_count": repository_count,
        "staging_total": staging_total,
        "staging_by_status": staging_by_status,
        "latest_repository_publication_date": latest_publication_date,
    }

    historical_context = {
        "review_count": review_count,
        "horizons_present": horizons_present,
        "outcome_type_counts": outcome_type_counts,
        "framework_review_eligible_count": framework_review_eligible_count,
        "latest_review_date": latest_review_date,
    }

    blockers = {
        "theia": blockers_theia,
        "hermes": blockers_hermes,
        "themis": blockers_themis,
        "mnemosyne": blockers_mnemosyne,
    }

    return {
        "lifecycle_state": lifecycle_state,
        "governance_readiness": governance_readiness,
        "evidence_summary": evidence_summary,
        "historical_context": historical_context,
        "blockers": blockers,
        "next_action": next_action,
        "provenance": {
            "lifecycle_state": "Themis",
            "governance_readiness": "Themis",
            "evidence_summary": "Theia",
            "historical_context": "Mnemosyne",
            "blockers": {
                "theia": ["evidence_staging"],
                "hermes": ["compute_hermes_inbox"],
                "themis": ["validate_decision_gate"],
                "mnemosyne": ["thesis_reviews"],
            },
            "next_action": "Hermes",
        },
    }


# =============================================================================
# AUDIT / EVENT SERVICES
# =============================================================================


def log_event(
    thesis_id,
    event_type,
    description,
    created_by="System",
    version="1.0",
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

    run_query(
        """
        INSERT INTO audit_events
        (
            thesis_id,
            event_type,
            entity_type,
            entity_id,
            details,
            created_by,
            created_at,
            version
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            thesis_id,
            event_type,
            "thesis",
            thesis_id,
            description,
            created_by,
            datetime.now().isoformat(),
            version,
        ),
    )
