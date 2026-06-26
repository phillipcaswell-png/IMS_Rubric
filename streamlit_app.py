import streamlit as st
import sqlite3
import pandas as pd
import json
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
EVENT_INVESTMENT_ASSESSMENT_COMPLETED = "Investment Assessment Completed"
EVENT_INVESTMENT_ASSESSMENT_UPDATED = "Investment Assessment Updated"
EVENT_RECOMMENDATION_CHANGED = "Recommendation Changed"
EVENT_REVIEW_SCHEDULED = "Review Scheduled"
EVENT_JSON_EXPORTED = "JSON Exported"

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
DATABASE_FILE = "ims_mvp.db"


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
    
    # Status metrics
    total_df = fetch_dataframe("SELECT COUNT(*) as count FROM theses")
    total_count = total_df['count'].iloc[0]
    
    draft_df = fetch_dataframe("SELECT COUNT(*) as count FROM theses WHERE status = ?", (STATUS_DRAFT,))
    draft_count = draft_df['count'].iloc[0]
    
    evidence_df = fetch_dataframe("SELECT COUNT(*) as count FROM theses WHERE status = ?", (STATUS_EVIDENCE_COLLECTION,))
    evidence_count = evidence_df['count'].iloc[0]
    
    scoring_df = fetch_dataframe("SELECT COUNT(*) as count FROM theses WHERE status = ?", (STATUS_SCORING,))
    scoring_count = scoring_df['count'].iloc[0]
    
    monitoring_df = fetch_dataframe("SELECT COUNT(*) as count FROM theses WHERE status = ?", (STATUS_ACTIVE_MONITORING,))
    monitoring_count = monitoring_df['count'].iloc[0]
    
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        metric_card("Total Theses", total_count)
    with col2:
        metric_card("Draft", draft_count)
    with col3:
        metric_card("Evidence Collection", evidence_count)
    with col4:
        metric_card("Scoring", scoring_count)
    with col5:
        metric_card("Active Monitoring", monitoring_count)
    
    # Theses table
    st.divider()
    section_header("All Theses")
    theses_df = fetch_dataframe("SELECT id, company_name, ticker, status, drl, primary_horizon, reviewer FROM theses ORDER BY company_name")
    if not theses_df.empty:
        st.dataframe(theses_df, use_container_width=True)
    else:
        empty_state("No theses found. Click '➕ New Thesis' to create one.")
    
    # Recent Activity
    st.divider()
    section_header("Recent Activity")
    activity_df = fetch_dataframe(
        """SELECT t.company_name as Company, e.event_type as 'Event Type', 
           e.event_description as Description, e.created_by as 'Created By', 
           e.created_at as 'Created At'
        FROM thesis_events e
        JOIN theses t ON e.thesis_id = t.id
        ORDER BY e.created_at DESC LIMIT 10"""
    )
    if not activity_df.empty:
        st.dataframe(activity_df, use_container_width=True)
    else:
        empty_state("No recent activity.")

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
                     primary_horizon, regime_state, reviewer, status, drl, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            
            # Section 1: Evaluation Summary
            section_header("Evaluation Summary")
            col1, col2 = st.columns(2)
            with col1:
                summary_field("Company", thesis['company_name'])
                summary_field("Ticker", thesis['ticker'] or "—")
                summary_field("Reviewer", thesis['reviewer'] or "—")
                summary_field("DRL", thesis['drl'] or "—")
            with col2:
                summary_field("Status", thesis['status'] or "—")
                summary_field("Primary Horizon", thesis['primary_horizon'] or "—")
                summary_field("Regime State", thesis['regime_state'] or "—")
                summary_field("Created", thesis['created_at'] or "—")
            
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
                             url_or_citation, evidence_summary, created_at,
                             title, source_publisher, key_takeaway, tags,
                             credibility_score, materiality_score, thesis_alignment)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                thesis_id,
                                evidence_title.strip(),
                                source_type,
                                publication_date.isoformat() if publication_date else None,
                                url_or_citation.strip() if url_or_citation else None,
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
        
        with tab3:
            section_header("Business Quality Scoring")

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

            judgment_default = ""
            if existing_record is not None:
                if 'judgment' in existing_record.index and pd.notna(existing_record['judgment']) and str(existing_record['judgment']).strip() != "":
                    judgment_default = str(existing_record['judgment'])
                elif pd.notna(existing_record['inference']) and str(existing_record['inference']).strip() != "":
                    judgment_default = str(existing_record['inference'])

            with st.form("business_quality_scoring_form"):
                if pillar_id == "B4":
                    st.info("Financial resilience should account for non-linearity: unusually high cash positions relative to revenue may indicate inefficient capital allocation rather than strength.")
                elif pillar_id == "B7":
                    st.info("Systems importance should account for dependency quality: reliance on a single government program or contract should not automatically receive a high score.")

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

                        st.success(f"✓ Business assessment updated for {pillar_id} {pillar_name}")
                    else:
                        insert_query(
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

                    st.rerun()
            
            st.divider()
            
            # Display Business Assessment Scores
            section_header("Business Assessment Scores")
            business_df = fetch_dataframe(
                """
                SELECT 
                    pillar_id, pillar_name, score, rag_status, evidence_grade,
                    judgment, confidence_basis, primary_sources, evidence_items,
                    falsification_trigger,
                    reviewer, review_date, drl, created_at
                FROM pillar_scores
                WHERE thesis_id = ? AND pillar_id LIKE 'B%'
                ORDER BY pillar_id ASC
                """,
                (thesis_id,)
            )
            
            if not business_df.empty:
                st.dataframe(business_df, use_container_width=True)
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
            if selected_pillar and selected_pillar != "":
                pillar_id_check = selected_pillar.split(" ", 1)[0]
                existing_df = fetch_dataframe(
                    "SELECT * FROM pillar_scores WHERE thesis_id = ? AND pillar_id = ?",
                    (thesis_id, pillar_id_check)
                )
                if not existing_df.empty:
                    existing_record = existing_df.iloc[0]
            
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
                    evidence_items = st.text_input(
                        "Evidence Items",
                        value=existing_record['evidence_items'] if existing_record is not None and pd.notna(existing_record['evidence_items']) else "",
                        placeholder="Related evidence items",
                        key="invest_items"
                    )
                
                inference = st.text_area(
                    "Inference *",
                    value=existing_record['inference'] if existing_record is not None and pd.notna(existing_record['inference']) else "",
                    placeholder="What is your inference from this assessment?",
                    height=80,
                    key="invest_inference"
                )
                
                col1, col2 = st.columns(2)
                
                with col1:
                    conf_options = ["", "Low", "Moderate", "High"]
                    conf_default_idx = 0
                    if existing_record is not None and pd.notna(existing_record['inference_confidence']):
                        try:
                            conf_default_idx = conf_options.index(existing_record['inference_confidence'])
                        except ValueError:
                            conf_default_idx = 0
                    inference_confidence = st.selectbox(
                        "Inference Confidence",
                        conf_options,
                        index=conf_default_idx,
                        key="invest_inf_conf"
                    )
                
                with col2:
                    falsification_trigger = st.text_input(
                        "Falsification Trigger *",
                        value=existing_record['falsification_trigger'] if existing_record is not None and pd.notna(existing_record['falsification_trigger']) else "",
                        placeholder="What would prove this wrong?",
                        key="invest_fals"
                    )
                
                score_rationale = st.text_area(
                    "Score Rationale *",
                    value=existing_record['score_rationale'] if existing_record is not None and pd.notna(existing_record['score_rationale']) else "",
                    placeholder="Explain how you arrived at this score",
                    height=80,
                    key="invest_rationale"
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
                    elif not inference.strip():
                        st.error("Inference is required.")
                    elif not falsification_trigger.strip():
                        st.error("Falsification Trigger is required.")
                    elif not score_rationale.strip():
                        st.error("Score Rationale is required.")
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
                            run_query(
                                """
                                UPDATE pillar_scores
                                SET score = ?, rag_status = ?, evidence_grade = ?,
                                    confidence_basis = ?, primary_sources = ?, evidence_items = ?,
                                    inference = ?, inference_confidence = ?, falsification_trigger = ?,
                                    score_rationale = ?, reviewer = ?, review_date = ?, drl = ?
                                WHERE thesis_id = ? AND pillar_id = ?
                                """,
                                (
                                    score,
                                    rag_status if rag_status else None,
                                    evidence_grade if evidence_grade else None,
                                    confidence_basis.strip(),
                                    primary_sources.strip() if primary_sources else None,
                                    evidence_items.strip() if evidence_items else None,
                                    inference.strip(),
                                    inference_confidence if inference_confidence else None,
                                    falsification_trigger.strip(),
                                    score_rationale.strip(),
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
                            insert_query(
                                """
                                INSERT INTO pillar_scores
                                (thesis_id, pillar_id, pillar_name, score, rag_status, evidence_grade,
                                 confidence_basis, primary_sources, evidence_items, inference,
                                 inference_confidence, falsification_trigger, score_rationale,
                                 reviewer, review_date, drl, created_at)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                                    evidence_items.strip() if evidence_items else None,
                                    inference.strip(),
                                    inference_confidence if inference_confidence else None,
                                    falsification_trigger.strip(),
                                    score_rationale.strip(),
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
            empty_state("Risk Module Coming Next")

        with tab9:
            # Decision Form
            section_header("Record Decision")
            
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
                        event_type=EVENT_RECOMMENDATION_CHANGED,
                        description="Decision recorded or updated.",
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

