import streamlit as st
from sqlalchemy import create_engine, text
from auth_utils import get_supabase

# Initialize connection using Streamlit's connection pool (for other queries)
def get_engine():
    try:
        return st.connection("postgres", type="sql")
    except:
        return st.connection("local_db", type="sql", url="sqlite:///nsq_audit.db")

conn = get_engine()

def fetch_trades():
    return conn.query("SELECT id, name FROM trades")

@st.cache_data(ttl=3600)
def fetch_nested_nos(trade_id):
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