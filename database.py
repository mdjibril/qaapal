import streamlit as st
from auth_utils import get_supabase, get_admin_supabase
import time
import functools
from datetime import datetime, timedelta


def _is_retryable_db_error(error):
    message = str(error).lower()
    retry_markers = (
        "timeout",
        "timed out",
        "connection",
        "network",
        "temporarily",
        "server closed the connection",
        "could not connect",
        "503",
        "504",
    )
    return any(marker in message for marker in retry_markers)


def retry_db_call(max_attempts=3, base_delay=0.25):
    """Retry transient Supabase calls without storing retry state anywhere."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as error:
                    last_error = error
                    if attempt == max_attempts - 1 or not _is_retryable_db_error(error):
                        raise
                    time.sleep(base_delay * (2 ** attempt))
            raise last_error

        return wrapper

    return decorator


@retry_db_call()
def _execute_query(query):
    return query.execute()

def fetch_trades():
    # Use the admin client to fetch the trade list to ensure it's always available 
    # in the sidebar, bypassing RLS restrictions for this specific lookup.
    supabase = get_admin_supabase()
    try:
        # Fetch trades via Supabase API instead of direct SQL to avoid connection issues
        response = _execute_query(supabase.table("trades").select("id, name").order("name"))
        trades = response.data if response.data else []
        return sorted(trades, key=lambda trade: (trade.get("name") or "").casefold())
    except Exception as e:
        st.error(f"Database Error while fetching trades: {e}")
        # Return empty list to prevent downstream crashes
        return []

@st.cache_data(ttl=3600)
def fetch_trade_levels(trade_id):
    supabase = get_admin_supabase()
    try:
        response = _execute_query(
            supabase.table("trade_levels")
            .select("id, trade_id, level, display_name")
            .eq("trade_id", int(trade_id))
            .order("level")
        )
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Error fetching trade levels: {e}")
        return []


@st.cache_data(ttl=3600)
def fetch_all_trade_levels():
    supabase = get_admin_supabase()
    try:
        response = _execute_query(
            supabase.table("trade_levels")
            .select("id, trade_id, level, display_name")
            .order("trade_id")
            .order("level")
        )
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Error fetching trade levels: {e}")
        return []


@st.cache_data(ttl=3600)
def fetch_units_by_trade_level(trade_level_id):
    supabase = get_admin_supabase()
    try:
        response = _execute_query(
            supabase.table("units")
            .select("id, trade_id, trade_level_id, code, title")
            .eq("trade_level_id", int(trade_level_id))
            .order("code")
        )
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Error fetching units: {e}")
        return []


@st.cache_data(ttl=3600)
def fetch_all_units():
    supabase = get_admin_supabase()
    try:
        response = _execute_query(
            supabase.table("units")
            .select("id, trade_id, trade_level_id, code, title")
            .order("id")
        )
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Error fetching units: {e}")
        return []


@st.cache_data(ttl=3600)
def fetch_learning_outcomes_by_unit(unit_id):
    supabase = get_admin_supabase()
    try:
        response = _execute_query(
            supabase.table("learning_outcomes")
            .select("id, unit_id, lo_num, description")
            .eq("unit_id", int(unit_id))
            .order("lo_num")
        )
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Error fetching learning outcomes: {e}")
        return []


@st.cache_data(ttl=3600)
def fetch_all_learning_outcomes():
    supabase = get_admin_supabase()
    try:
        response = _execute_query(
            supabase.table("learning_outcomes")
            .select("id, unit_id, lo_num, description")
            .order("id")
        )
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Error fetching learning outcomes: {e}")
        return []


@st.cache_data(ttl=3600)
def fetch_performance_criteria_by_lo(lo_id):
    supabase = get_admin_supabase()
    try:
        response = _execute_query(
            supabase.table("performance_criteria")
            .select("id, lo_id, pc_code, description")
            .eq("lo_id", int(lo_id))
            .order("pc_code")
        )
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Error fetching performance criteria: {e}")
        return []


@st.cache_data(ttl=3600)
def fetch_all_performance_criteria():
    supabase = get_admin_supabase()
    try:
        response = _execute_query(
            supabase.table("performance_criteria")
            .select("id, lo_id, pc_code, description")
            .order("id")
        )
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Error fetching performance criteria: {e}")
        return []


@st.cache_data(ttl=3600)
def fetch_trade_by_id(trade_id):
    supabase = get_admin_supabase()
    try:
        response = _execute_query(
            supabase.table("trades")
            .select("id, name")
            .eq("id", int(trade_id))
            .single()
        )
        return response.data if response.data else None
    except Exception as e:
        st.error(f"Error fetching trade: {e}")
        return None

@st.cache_data(ttl=3600)
def fetch_nested_nos(trade_id=None, trade_level_id=None):
    supabase = get_admin_supabase()
    
    # ONE query to rule them all: 
    # Fetch units -> their LOs -> their PCs in one nested structure
    try:
        query = supabase.table("units").select(
            "code, title, learning_outcomes(lo_num, description, performance_criteria(pc_code, description))"
        )
        if trade_level_id is not None:
            query = query.eq("trade_level_id", int(trade_level_id))
        elif trade_id is not None:
            query = query.eq("trade_id", int(trade_id))
        else:
            return {}

        response = _execute_query(query)
        
        raw_units = response.data
        
        # Now we transform this nested list into the Dictionary format 
        # your dashboard.py currently expects: { "Unit: Title": { "LO: Desc": [PC List] } }
        structured_data = {}
        
        for unit in raw_units:
            unit_key = f"{unit['code']}: {unit['title']}"
            structured_data[unit_key] = {}
            
            for lo in unit.get('learning_outcomes', []):
                lo_key = f"LO {lo['lo_num']}: {lo['description']}"
                # Get all PC descriptions for this LO
                pcs = [f"{pc['pc_code']}: {pc['description']}" for pc in lo.get('performance_criteria', [])]
                structured_data[unit_key][lo_key] = pcs
                
        return structured_data

    except Exception as e:
        st.error(f"Error fetching NOS: {e}")
        return {}


def fetch_nos_delete_preview(trade_id, trade_level_id=None):
    """Return a lightweight preview of what would be removed by a NOS delete action."""
    supabase = get_admin_supabase()
    try:
        preview = {
            "mode": "trade" if trade_level_id is None else "trade_level",
            "trade": {},
            "trade_level": {},
            "units": [],
            "unit_ids": [],
            "learning_outcomes": [],
            "performance_criteria": [],
            "counts": {
                "trades": 1,
                "trade_levels": 0,
                "units": 0,
                "learning_outcomes": 0,
                "performance_criteria": 0,
            },
        }

        trade_rows = _execute_query(supabase.table("trades").select("id, name").eq("id", int(trade_id))).data or []
        if trade_rows:
            preview["trade"] = trade_rows[0]

        if trade_level_id is not None:
            level_rows = _execute_query(
                supabase.table("trade_levels")
                .select("id, trade_id, level, display_name")
                .eq("id", int(trade_level_id))
            ).data or []
            if level_rows:
                preview["trade_level"] = level_rows[0]
                preview["counts"]["trade_levels"] = 1

            units = _execute_query(
                supabase.table("units")
                .select("id, code, title")
                .eq("trade_level_id", int(trade_level_id))
            ).data or []
        else:
            preview["counts"]["trade_levels"] = len(
                _execute_query(
                    supabase.table("trade_levels")
                    .select("id")
                    .eq("trade_id", int(trade_id))
                ).data or []
            )
            units = _execute_query(
                supabase.table("units")
                .select("id, code, title, trade_level_id")
                .eq("trade_id", int(trade_id))
            ).data or []

        preview["units"] = units
        preview["counts"]["units"] = len(units)
        unit_ids = [u["id"] for u in units]
        preview["unit_ids"] = unit_ids

        los = []
        if unit_ids:
            los = _execute_query(
                supabase.table("learning_outcomes")
                .select("id, unit_id, lo_num, description")
                .in_("unit_id", unit_ids)
            ).data or []
        preview["learning_outcomes"] = los
        preview["counts"]["learning_outcomes"] = len(los)

        lo_ids = [lo["id"] for lo in los]
        pcs = []
        if lo_ids:
            pcs = _execute_query(
                supabase.table("performance_criteria")
                .select("id, lo_id, pc_code, description")
                .in_("lo_id", lo_ids)
            ).data or []
        preview["performance_criteria"] = pcs
        preview["counts"]["performance_criteria"] = len(pcs)

        return preview, None
    except Exception as e:
        return None, str(e)


def delete_nos_trade(trade_id):
    """Delete a trade family. Child levels and units cascade through FK rules."""
    supabase = get_admin_supabase()
    try:
        _execute_query(supabase.table("trades").delete().eq("id", int(trade_id)))
        st.cache_data.clear()
        return True, None
    except Exception as e:
        return False, str(e)


def delete_nos_trade_level(trade_level_id):
    """Delete a single trade level and its dependent units, LOs, and PCs."""
    supabase = get_admin_supabase()
    try:
        _execute_query(supabase.table("units").delete().eq("trade_level_id", int(trade_level_id)))
        _execute_query(supabase.table("trade_levels").delete().eq("id", int(trade_level_id)))
        st.cache_data.clear()
        return True, None
    except Exception as e:
        return False, str(e)


def update_trade_name(trade_id, name):
    supabase = get_admin_supabase()
    try:
        _execute_query(supabase.table("trades").update({"name": name}).eq("id", int(trade_id)))
        st.cache_data.clear()
        return True, None
    except Exception as e:
        return False, str(e)


def update_trade_level(trade_level_id, level, display_name):
    supabase = get_admin_supabase()
    try:
        _execute_query(supabase.table("trade_levels").update({
            "level": int(level),
            "display_name": display_name,
        }).eq("id", int(trade_level_id)))
        st.cache_data.clear()
        return True, None
    except Exception as e:
        return False, str(e)


def update_unit(unit_id, code, title):
    supabase = get_admin_supabase()
    try:
        _execute_query(supabase.table("units").update({
            "code": code,
            "title": title,
        }).eq("id", int(unit_id)))
        st.cache_data.clear()
        return True, None
    except Exception as e:
        return False, str(e)


def update_learning_outcome(lo_id, lo_num, description):
    supabase = get_admin_supabase()
    try:
        _execute_query(supabase.table("learning_outcomes").update({
            "lo_num": lo_num,
            "description": description,
        }).eq("id", int(lo_id)))
        st.cache_data.clear()
        return True, None
    except Exception as e:
        return False, str(e)


def update_performance_criterion(pc_id, pc_code, description):
    supabase = get_admin_supabase()
    try:
        _execute_query(supabase.table("performance_criteria").update({
            "pc_code": pc_code,
            "description": description,
        }).eq("id", int(pc_id)))
        st.cache_data.clear()
        return True, None
    except Exception as e:
        return False, str(e)


def insert_report(name, trade_id, unit_codes, report_content, date, user_id):
    """
    Inserts report and returns (success_bool, report_id_or_error_message)
    """
    supabase = get_supabase()
    
    try:
        if not user_id:
            return False, "User ID missing from session."

        data = {
            "student_name": str(name),
            "trade_id": int(trade_id) if trade_id else None, 
            "unit_codes": str(unit_codes),
            "report_text": str(report_content),
            "assessment_date": str(date),
            "created_by": user_id  # Supabase client handles UUID objects or strings correctly
        }
        
        res = _execute_query(supabase.table("assessment_reports").insert(data))
        st.cache_data.clear()
        
        if res.data and len(res.data) > 0:
            return True, res.data[0]
        
        return True, None

    except Exception as e:
        error_str = str(e)
        print(f"DATABASE INSERT ERROR: {error_str}")
        return False, error_str

def insert_student_statement(user_id, student_name, trade_id, unit_codes, reflection_notes, statement_text):
    """
    Inserts a student's personal statement into the database.
    """
    supabase = get_supabase()
    try:
        data = {
            "user_id": user_id,
            "student_name": student_name,
            "trade_id": int(trade_id) if trade_id else None,
            "unit_codes": str(unit_codes),
            "reflection_notes": str(reflection_notes),
            "statement_text": str(statement_text),
            "created_by": user_id
        }
        _execute_query(supabase.table("student_statements").insert(data))
        st.cache_data.clear()
        return True, None
    except Exception as e:
        return False, str(e)

def insert_witness_statement(user_id, witness_name, witness_role, candidate_name, trade_id, unit_codes, witness_notes, statement_text):
    """
    Inserts a witness statement into the database.
    """
    supabase = get_supabase()
    try:
        data = {
            "witness_name": witness_name,
            "witness_role": witness_role,
            "candidate_name": candidate_name,
            "trade_id": int(trade_id) if trade_id else None,
            "unit_codes": str(unit_codes),
            "witness_notes": str(witness_notes),
            "statement_text": str(statement_text),
            "created_by": user_id
        }
        _execute_query(supabase.table("witness_statements").insert(data))
        st.cache_data.clear()
        return True, None
    except Exception as e:
        return False, str(e)

def upgrade_org_tier(org_id, new_tier='platform_pass'):
    """Updates the organization's tier and sets the subscription start date."""
    supabase = get_admin_supabase()
    try:
        # Set subscription_start_date to now() when upgrading
        _execute_query(supabase.table("organizations").update({"subscription_tier": new_tier, "subscription_start_date": "now()"}).eq("id", org_id))
        return True, None
    except Exception as e:
        return False, str(e)
def decrement_credits(org_id):
    """Subtracts one credit from the organization's balance."""
    supabase = get_admin_supabase()
    try:
        # Get current balance
        res = _execute_query(supabase.table("organizations").select("credits_balance").eq("id", org_id).single())
        current_balance = res.data.get("credits_balance", 0)
        
        if current_balance > 0:
            _execute_query(supabase.table("organizations").update({"credits_balance": current_balance - 1}).eq("id", org_id))
            return True
        return False
    except Exception as e:
        print(f"Credit deduction error: {e}")
        return False

def check_platform_pass_expiry():
    """Checks if the platform_pass subscription has expired."""
    tier = st.session_state.get('subscription_tier', 'free')
    start_date_str = st.session_state.get('subscription_start_date')

    if tier == 'platform_pass' and start_date_str:
        # Parse the date string (e.g., '2024-05-21T12:00:00+00:00')
        try:
            start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
        except ValueError:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%dT%H:%M:%S.%f%z')
        
        # Check if one month has passed (using 30 days as a proxy for a month)
        if datetime.now(start_date.tzinfo) > start_date + timedelta(days=30):
            return True
    return False

def insert_feedback(user_id, rating, source_page, comment=None):
    """
    Inserts a product feedback record.
    rating: 1 for thumbs up, -1 for thumbs down.
    source_page: 'dashboard', 'personal_statement', or 'witness_statement'
    """
    supabase = get_admin_supabase()
    try:
        data = {
            "user_id": user_id,
            "assessor_role": st.session_state.get("assessor_role"),
            "rating": rating,
            "comment": comment[:500] if comment else None,
            "source_page": source_page,
        }
        _execute_query(supabase.table("product_feedback").insert(data))
        return True, None
    except Exception as e:
        return False, str(e)

@st.fragment
def render_feedback_widget(source_page: str):
    """
    Renders a compact 👍 / 👎 feedback widget.
    source_page: identifies which page is calling it ('dashboard', 'personal_statement', 'witness_statement')
    """
    fb_key = f"fb_submitted_{source_page}"
    if st.session_state.get(fb_key):
        st.success("✅ Thanks for your feedback!", icon="🙏")
        return

    st.markdown("---")
    st.markdown("**Was this output useful?**")

    # Optional comment box is always visible now
    comment = st.text_area(
        "Any specific feedback? *(optional)*",
        max_chars=500,
        key=f"fb_comment_input_{source_page}",
        placeholder="e.g. The tone was perfect, or the PC mapping was off..."
    )

    col_up, col_down, col_spacer = st.columns([1, 1, 6])
    user_id = st.session_state.get("user_session", {}).id if st.session_state.get("user_session") else None

    with col_up:
        if st.button("👍", key=f"fb_up_{source_page}", help="Yes, it was helpful"):
            ok, _ = insert_feedback(user_id, 1, source_page, comment)
            if ok:
                st.session_state[fb_key] = True
                st.rerun(scope="fragment")

    with col_down:
        if st.button("👎", key=f"fb_down_{source_page}", help="Needs improvement"):
            ok, _ = insert_feedback(user_id, -1, source_page, comment)
            if ok:
                st.session_state[fb_key] = True
                st.rerun(scope="fragment")

def fetch_system_metrics():
    """Fetches high level counts for the superadmin dashboard."""
    supabase = get_admin_supabase()
    metrics = {"total_users": 0, "total_orgs": 0, "total_reports": 0}
    try:
        res_users = _execute_query(supabase.table("user_profiles").select("id", count="exact"))
        metrics["total_users"] = res_users.count if hasattr(res_users, 'count') and res_users.count is not None else len(res_users.data)
        
        res_orgs = _execute_query(supabase.table("organizations").select("id", count="exact"))
        metrics["total_orgs"] = res_orgs.count if hasattr(res_orgs, 'count') and res_orgs.count is not None else len(res_orgs.data)
        
        res_reports = _execute_query(supabase.table("assessment_reports").select("id", count="exact"))
        metrics["total_reports"] = res_reports.count if hasattr(res_reports, 'count') and res_reports.count is not None else len(res_reports.data)
    except Exception as e:
        print(f"Metrics fetch error: {e}")
    return metrics

def fetch_recent_reports(limit=50):
    """Fetches recent reports for QA by admins."""
    supabase = get_admin_supabase()
    try:
        response = supabase.table("assessment_reports")
        response = response.select("*, user_profiles!created_by(full_name), trades(name)")
        response = _execute_query(response.order("created_at", desc=True).limit(limit))
        return response.data
    except Exception as e:
        print(f"Error fetching recent reports: {e}")
        return []

def update_org_credits(org_id, new_balance):
    """Manually adjust credits for an organization."""
    supabase = get_admin_supabase()
    try:
        _execute_query(supabase.table("organizations").update({"credits_balance": new_balance}).eq("id", org_id))
        return True, None
    except Exception as e:
        return False, str(e)


def top_up_org_credits(org_id, amount):
    """Add AI credits to an organization's purchased balance (credit packs)."""
    supabase = get_admin_supabase()
    try:
        res = _execute_query(supabase.table("organizations").select("ai_credits_purchased, credits_balance").eq("id", org_id).single())
        purchased = (res.data or {}).get("ai_credits_purchased", 0) or 0
        balance = (res.data or {}).get("credits_balance", 0) or 0
        _execute_query(
            supabase.table("organizations")
            .update({
                "ai_credits_purchased": purchased + amount,
                "credits_balance": balance + amount
            })
            .eq("id", org_id)
        )
        return True, None
    except Exception as e:
        return False, str(e)


# ==============================================================
# Phase 6 — QA Assessor Growth & Retention (ADMIN-ONLY)
# ==============================================================

def fetch_student_portfolios(user_id=None, trade_id=None):
    """Fetch all student portfolios (admin-only via RLS)."""
    supabase = get_admin_supabase()
    try:
        query = supabase.table("student_portfolios").select("*, trades(name)")
        if user_id:
            query = query.eq("created_by", user_id)
        if trade_id:
            query = query.eq("trade_id", int(trade_id))
        res = _execute_query(query.order("created_at", desc=True))
        return res.data or []
    except Exception as e:
        print(f"Error fetching portfolios: {e}")
        return []


def fetch_student_portfolio(portfolio_id):
    """Fetch a single portfolio with its trade metadata."""
    supabase = get_admin_supabase()
    try:
        res = _execute_query(
            supabase.table("student_portfolios")
            .select("*, trades(name)")
            .eq("id", portfolio_id)
            .single()
        )
        return res.data
    except Exception as e:
        print(f"Error fetching portfolio: {e}")
        return None


def create_student_portfolio(student_name, trade_id, trade_level_id, student_email=None, candidate_ref=None, user_id=None):
    """Create a new student portfolio (admin-only)."""
    supabase = get_admin_supabase()
    try:
        data = {
            "student_name": student_name,
            "trade_id": int(trade_id) if trade_id else None,
            "trade_level_id": int(trade_level_id) if trade_level_id else None,
            "student_email": student_email,
            "candidate_ref": candidate_ref,
            "created_by": user_id
        }
        res = _execute_query(supabase.table("student_portfolios").insert(data))
        if res.data:
            return res.data[0], None
        return None, "No data returned from insert."
    except Exception as e:
        return None, str(e)


def delete_student_portfolio(portfolio_id):
    """Delete a portfolio and cascade its PC progress (admin-only)."""
    supabase = get_admin_supabase()
    try:
        _execute_query(supabase.table("student_portfolios").delete().eq("id", portfolio_id))
        return True, None
    except Exception as e:
        return False, str(e)


def fetch_pc_progress(portfolio_id):
    """Fetch PC progress for a student portfolio, joined with NOS metadata."""
    supabase = get_admin_supabase()
    try:
        res = _execute_query(
            supabase.table("student_pc_progress")
            .select("*, performance_criteria(pc_code, description), units(code, title)")
            .eq("portfolio_id", portfolio_id)
        )
        return res.data or []
    except Exception as e:
        print(f"Error fetching PC progress: {e}")
        return []


def upsert_pc_progress(portfolio_id, pc_id, unit_id, status, evidence_report_id=None, assessed_by=None):
    """Insert or update PC progress for a student (admin-only)."""
    supabase = get_admin_supabase()
    try:
        data = {
            "portfolio_id": portfolio_id,
            "pc_id": int(pc_id),
            "unit_id": int(unit_id) if unit_id else None,
            "status": status,
            "evidence_report_id": evidence_report_id,
            "assessed_by": assessed_by,
            "assessed_at": "now()"
        }
        res = _execute_query(
            supabase.table("student_pc_progress")
            .upsert(data, on_conflict="portfolio_id,pc_id")
        )
        return True, None
    except Exception as e:
        return False, str(e)


def delete_pc_progress(progress_id):
    """Delete a single PC progress row (admin-only)."""
    supabase = get_admin_supabase()
    try:
        _execute_query(supabase.table("student_pc_progress").delete().eq("id", progress_id))
        return True, None
    except Exception as e:
        return False, str(e)


def fetch_pc_options_for_portfolio(trade_id=None, trade_level_id=None):
    """
    Fetch a flat list of PCs with their IDs and unit IDs for dropdowns.
    Returns a list of dicts: {'label': 'UNIT - LO - PC_CODE', 'pc_id': int, 'unit_id': int}
    """
    supabase = get_admin_supabase()
    try:
        query = supabase.table("units").select(
            "id, code, learning_outcomes(id, lo_num, performance_criteria(id, pc_code, description))"
        )
        if trade_level_id is not None:
            query = query.eq("trade_level_id", int(trade_level_id))
        elif trade_id is not None:
            query = query.eq("trade_id", int(trade_id))
        else:
            return []

        response = _execute_query(query)
        raw_units = response.data or []

        pc_options = []
        for unit in raw_units:
            unit_code = unit.get('code', '')
            unit_id = unit.get('id')
            for lo in unit.get('learning_outcomes', []):
                lo_num = lo.get('lo_num', '')
                for pc in lo.get('performance_criteria', []):
                    pc_code = pc.get('pc_code', '')
                    pc_id = pc.get('id')
                    pc_options.append({
                        'label': f"{unit_code} - {lo_num} - {pc_code}",
                        'pc_id': pc_id,
                        'unit_id': unit_id,
                    })
        return pc_options
    except Exception as e:
        print(f"Error fetching PC options: {e}")
        return []


def fetch_portfolio_by_student_and_trade(student_name, trade_id):
    """Look up a student portfolio by name and trade (admin-only)."""
    supabase = get_admin_supabase()
    try:
        res = _execute_query(
            supabase.table("student_portfolios")
            .select("*")
            .eq("student_name", student_name)
            .eq("trade_id", int(trade_id))
            .order("created_at", desc=True)
            .limit(1)
        )
        if res.data:
            return res.data[0]
        return None
    except Exception as e:
        print(f"Error looking up portfolio: {e}")
        return None


def auto_track_portfolio_progress(student_name, trade_id, trade_level_id, selected_pcs, evidence_report_id, assessed_by):
    """
    After report generation, auto-track PC progress for the student portfolio.
    Maps each selected PC string to its PC/unit IDs and upserts status 'passed'.
    Returns (portfolio_found_bool, count_tracked, error_msg)
    """
    portfolio = fetch_portfolio_by_student_and_trade(student_name, trade_id)
    if not portfolio:
        return False, 0, "No matching portfolio found for this student/trade."

    portfolio_id = portfolio['id']
    pc_options = fetch_pc_options_for_portfolio(trade_id=trade_id, trade_level_id=trade_level_id)

    # Build a lookup keyed by "UNIT - LO - PC_CODE" from selected_pcs
    tracked_count = 0
    error_msg = None
    for selected in selected_pcs:
        # selected format: "UNIT_CODE - LO_NUM - PC_CODE: Description"
        parts = selected.split(' - ')
        if len(parts) < 3:
            continue
        unit_code = parts[0].strip()
        lo_num = parts[1].strip()
        pc_code = parts[2].split(':')[0].strip()

        # Find matching PC option
        match = next(
            (opt for opt in pc_options
             if opt['label'] == f"{unit_code} - {lo_num} - {pc_code}"),
            None
        )
        if match:
            success, err = upsert_pc_progress(
                portfolio_id=portfolio_id,
                pc_id=match['pc_id'],
                unit_id=match['unit_id'],
                status='passed',
                evidence_report_id=evidence_report_id,
                assessed_by=assessed_by
            )
            if success:
                tracked_count += 1
            else:
                error_msg = err

    return True, tracked_count, error_msg


def fetch_assessment_templates(trade_id=None, trade_level_id=None):
    """Fetch assessment templates, optionally filtered by trade/level."""
    supabase = get_admin_supabase()
    try:
        query = supabase.table("assessment_templates").select("*")
        if trade_id:
            query = query.eq("trade_id", int(trade_id))
        if trade_level_id:
            query = query.eq("trade_level_id", int(trade_level_id))
        res = _execute_query(query.order("name"))
        return res.data or []
    except Exception as e:
        print(f"Error fetching templates: {e}")
        return []


def save_assessment_template(name, trade_id, trade_level_id, pc_ids, user_id=None):
    """Create a new assessment template (admin-only)."""
    supabase = get_admin_supabase()
    try:
        data = {
            "name": name,
            "trade_id": int(trade_id) if trade_id else None,
            "trade_level_id": int(trade_level_id) if trade_level_id else None,
            "pc_ids": pc_ids,
            "created_by": user_id
        }
        res = _execute_query(supabase.table("assessment_templates").insert(data))
        if res.data:
            return res.data[0], None
        return None, "No data returned from insert."
    except Exception as e:
        return None, str(e)


def delete_assessment_template(template_id):
    """Delete an assessment template (admin-only)."""
    supabase = get_admin_supabase()
    try:
        _execute_query(supabase.table("assessment_templates").delete().eq("id", template_id))
        return True, None
    except Exception as e:
        return False, str(e)
