import streamlit as st
from auth_utils import get_supabase
from file_utils import export_to_word
import pandas as pd

# Helper function to fetch reports
def _fetch_reports(user_id, role):
    supabase = get_supabase()
    try:
        # Build query: Admins see all, Assessors see theirs, ordered by the creation timestamp
        query = supabase.table("assessment_reports").select("*")
        if role != 'admin':
            query = query.eq("created_by", user_id)
        
        response = query.order("created_at", desc=True).execute()
        return response.data
    except Exception as e:
        st.error(f"Error fetching history: {e}")
        return []

# Helper function to delete a report
def _delete_report(report_id):
    supabase = get_supabase()
    try:
        supabase.table("assessment_reports").delete().eq("id", report_id).execute()
        st.success(f"Report {report_id} deleted successfully.")
        # Invalidate the cached reports in session state
        if 'assessment_reports' in st.session_state:
            del st.session_state.assessment_reports
        return True
    except Exception as e:
        st.error(f"Error deleting report: {e}")
        return False


def main():
    st.title("📜 Assessment History")
    supabase = get_supabase()
    user_id = st.session_state.user_session.id
    role = st.session_state.user_role

    try:
        # Load reports into session state if not already loaded or if refresh is requested
        # Using a button to explicitly refresh the list
        if 'assessment_reports' not in st.session_state or st.button("Refresh History"):
            st.session_state.assessment_reports = _fetch_reports(user_id, role)
    except Exception as e:
        st.error(f"Error fetching history: {e}")
        st.session_state.assessment_reports = []

    reports = st.session_state.assessment_reports

    if not reports:
        st.info("No reports found.")
        return # Exit early if no reports

    # Search implementation
    search_query = st.text_input("Search reports by student name or content", "")
    
    filtered_reports = []
    if search_query:
        search_query_lower = search_query.lower()
        for r in reports:
            student_name = r.get('student_name', '').lower()
            report_text = r.get('report_text', '').lower()
            if search_query_lower in student_name or search_query_lower in report_text:
                filtered_reports.append(r)
    else:
        filtered_reports = reports

    if not filtered_reports:
        st.info("No reports found matching your search criteria.")
    else:
        for r in filtered_reports:
            with st.expander(f"📅 {r.get('assessment_date')} | 👤 {r.get('student_name')} | 📚 {r.get('unit_codes', 'N/A').split(',')[0]}"):
                st.write(r['report_text'])

                doc_bytes = export_to_word(
                    r['student_name'], 
                    r['assessment_date'], 
                    r['report_text'], 
                    st.session_state.get('assessor_name', 'Assessor'), 
                    st.session_state.get('assessor_id', 'ID'),
                    timeline="N/A", # Not stored in DB for history
                    atmosphere="N/A", # Not stored in DB for history
                    selected_pcs=r.get('unit_codes', '') # This will be a comma-separated string of unit codes
                )
                st.download_button(
                    label="📥 Download Word",
                    data=doc_bytes,
                    file_name=f"NSQ_{r['student_name']}.docx",
                    key=f"dl_{r['id']}"
                )
                
                # Deletion button
                if role == 'admin' or r.get('created_by') == user_id:
                    if st.button("🗑️ Delete Report", key=f"delete_{r['id']}"):
                        if _delete_report(r['id']):
                            st.session_state.assessment_reports = _fetch_reports(user_id, role) # Re-fetch after deletion
                            st.rerun()

if __name__ == "__main__":
    main()