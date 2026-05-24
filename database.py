import streamlit as st
from auth_utils import get_supabase, get_admin_supabase
import pandas as pd
import time
from datetime import datetime, timedelta

def fetch_trades():
    # Use the admin client to fetch the trade list to ensure it's always available 
    # in the sidebar, bypassing RLS restrictions for this specific lookup.
    supabase = get_admin_supabase()
    try:
        # Fetch trades via Supabase API instead of direct SQL to avoid connection issues
        response = supabase.table("trades").select("id, name").execute()
        return pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"Database Error while fetching trades: {e}")
        # Return empty DataFrame with expected columns to prevent downstream crashes
        return pd.DataFrame(columns=["id", "name"])

@st.cache_data(ttl=3600)
def fetch_nested_nos(trade_id):
    supabase = get_supabase()
    
    # ONE query to rule them all: 
    # Fetch units -> their LOs -> their PCs in one nested structure
    try:
        response = supabase.table("units") \
            .select("code, title, learning_outcomes(lo_num, description, performance_criteria(pc_code, description))") \
            .eq("trade_id", trade_id) \
            .execute()
        
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


# @st.cache_data(ttl=3600)
# def fetch_nested_nos(trade_id):
    supabase = get_supabase()
    # print(f"DEBUG: Querying Supabase for trade_id: {trade_id}") # Check your terminal
    
    try:
        # Step 1: Get Units
        units_res = supabase.table("units").select("id, code, title").eq("trade_id", trade_id).execute()
        
        # Add this check to see if the error is hidden in the response
        if not units_res.data and hasattr(units_res, 'error') and units_res.error:
            print(f"SUPABASE API ERROR: {units_res.error}")

        units = units_res.data
            
        if not units:
            print("DEBUG: No units found in Supabase for this ID.")
            return {}

        nested_data = {}
        for u in units:
            unit_label = f"{u['code']}: {u['title']}"
            nested_data[unit_label] = {}
                
            # Step 2: Get LOs
            lo_res = supabase.table("learning_outcomes").select("id, lo_num, description").eq("unit_id", u['id']).execute()
            for lo in lo_res.data:
                lo_label = f"{lo['lo_num']}: {lo['description']}"
                    
                # Step 3: Get PCs
                pc_res = supabase.table("performance_criteria").select("pc_code, description").eq("lo_id", lo['id']).execute()
                nested_data[unit_label][lo_label] = [f"{pc['pc_code']}: {pc['description']}" for pc in pc_res.data]
                    
        return nested_data
    except Exception as e:
        st.error(f"Database Error: {e}")
        return {}

def insert_report(name, trade_id, unit_codes, report_content, date, user_id):
    """
    Inserts report and returns (success_bool, error_message)
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
        
        supabase.table("assessment_reports").insert(data).execute()
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
        supabase.table("student_statements").insert(data).execute()
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
        supabase.table("witness_statements").insert(data).execute()
        return True, None
    except Exception as e:
        return False, str(e)

def upgrade_org_tier(org_id, new_tier='platform_pass'):
    """Updates the organization's tier and sets the subscription start date."""
    supabase = get_admin_supabase()
    try:
        # Set subscription_start_date to now() when upgrading
        supabase.table("organizations").update({"subscription_tier": new_tier, "subscription_start_date": "now()"}).eq("id", org_id).execute()
        return True, None
    except Exception as e:
        return False, str(e)
def decrement_credits(org_id):
    """Subtracts one credit from the organization's balance."""
    supabase = get_admin_supabase()
    try:
        # Get current balance
        res = supabase.table("organizations").select("credits_balance").eq("id", org_id).single().execute()
        current_balance = res.data.get("credits_balance", 0)
        
        if current_balance > 0:
            supabase.table("organizations").update({"credits_balance": current_balance - 1}).eq("id", org_id).execute()
            return True
        return False
    except Exception as e:
        print(f"Credit deduction error: {e}")
        return False

@st.dialog("💳 Monnify Payment Portal")
def mock_payment_dialog(org_id):
    st.write("### Upgrade to Platform Pass")
    st.write("Process your payment securely using Monnify.")
    
    u_session = st.session_state.get('user_session')
    email = u_session.email if u_session else "user@example.com"
    # Mock Naira amount for Platform Pass (approx $5 equivalent)
    amount_naira = 7500
    
    with st.container(border=True):
        st.caption("Order Summary")
        st.write(f"**Plan:** Platform Pass (Monthly)")
        st.write(f"**Amount:** ₦{amount_naira:,}.00")
        st.write(f"**Customer:** {email}")

    st.info("💡 In test mode, clicking 'Pay' simulates a successful response from the Monnify SDK.")
    
    if st.button("Pay with Monnify", type="primary", use_container_width=True):
        with st.spinner("Initializing Monnify Checkout..."):
            time.sleep(1.5) # Simulate SDK initialization
            
            # Simulate the callback/webhook logic from Monnify
            success, err = upgrade_org_tier(org_id)
            if success:
                st.success("✅ Payment Successful!")
                st.toast("Monnify Reference: MNFY-TEST-998877")
                st.session_state['subscription_tier'] = 'platform_pass'
                st.session_state['subscription_start_date'] = datetime.now().isoformat()
                time.sleep(1)
                st.rerun()
            else:
                st.error(f"Monnify Error: {err}")

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