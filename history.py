import streamlit as st
from auth_utils import get_supabase, get_admin_supabase
from file_utils import export_to_word
import pandas as pd

# Helper function to fetch reports
def _fetch_reports(user_id, role):
    # Admins use the admin client to bypass RLS on user_profiles for full name retrieval
    client = get_admin_supabase() if role == 'admin' else get_supabase()
    try:
        # Build query: Admins see all, Assessors see theirs, ordered by the creation timestamp
        query = client.table("assessment_reports").select("*, user_profiles(full_name)") # Fetch full_name from user_profiles
        if role != 'admin':
            query = query.eq("created_by", user_id)
        
        response = query.order("created_at", desc=True).execute()
        return response.data
    except Exception as e:
        st.error(f"Error fetching history: {e}")
        return []

# Helper function to delete a report
def _delete_report(report_id, role):
    # Admins use the service role client to bypass RLS for deletion
    client = get_admin_supabase() if role == 'admin' else get_supabase()
    try:
        res = client.table("assessment_reports").delete().eq("id", report_id).execute()
        if not res.data:
            st.error(f"Deletion failed: Report {report_id} not found or permission denied.")
            return False
        if 'assessment_reports' in st.session_state:
            del st.session_state.assessment_reports
        return True
    except Exception as e:
        st.error(f"Error deleting report: {e}")
        return False


# Callback for checkbox state change
def _on_checkbox_change(report_id):
    if f"selected_{report_id}" in st.session_state:
        if st.session_state[f"selected_{report_id}"]:
            st.session_state.selected_report_ids.add(report_id)
        else:
            st.session_state.selected_report_ids.discard(report_id)

# Helper function to display a single report item
def display_report_item(r, current_user_id, current_user_role):
    report_id = r['id']
    is_selected = report_id in st.session_state.selected_report_ids

    # Determine the assessor's name and ID for this specific report
    report_assessor_name = (r.get('user_profiles') or {}).get('full_name', 'Unknown Assessor')
    report_assessor_id = r.get('created_by', 'ID') # Use created_by as the assessor ID for the report

    col_checkbox, col_expander = st.columns([0.05, 0.95]) # Adjusted column width for checkbox
    with col_checkbox:
        st.checkbox("", key=f"selected_{report_id}", value=is_selected, on_change=_on_checkbox_change, args=(report_id,))
    
    with col_expander:
        with st.expander(f"📅 {r.get('assessment_date')} | 👤 {r.get('student_name')} | 📚 {r.get('unit_codes', 'N/A').split(',')[0]}"):
            st.write(r['report_text'])

            doc_bytes = export_to_word(
                r['student_name'], 
                r['assessment_date'], 
                r['report_text'], 
                report_assessor_name, # Use the assessor name from the report data
                report_assessor_id,   # Use the determined assessor ID
                timeline="N/A", # Not stored in DB for history
                atmosphere="N/A", # Not stored in DB for history
                selected_pcs=r.get('unit_codes', '') # This will be a comma-separated string of unit codes
            )
            st.download_button(
                label="📥 Download Word",
                data=doc_bytes,
                file_name=f"NSQ_{r['student_name']}.docx",
                key=f"dl_{report_id}"
            )
            
            # Single deletion button
            if current_user_role == 'admin' or r.get('created_by') == current_user_id:
                if st.button("🗑️ Delete Report", key=f"delete_single_{report_id}"):
                    if _delete_report(report_id, current_user_role):
                        st.toast(f"Report for {r.get('student_name')} deleted.")
                        st.rerun()

def main():
    st.title("� Assessment History")
    supabase = get_supabase()
    user_id = st.session_state.user_session.id
    role = st.session_state.user_role

    # Initialize selected_report_ids if not present
    if 'selected_report_ids' not in st.session_state:
        st.session_state.selected_report_ids = set()

    try:
        # Load reports into session state if not already loaded or if refresh is requested
        # Using a button to explicitly refresh the list
        # Refresh button at the top
        if st.button("Refresh History"):
            if 'assessment_reports' in st.session_state:
                del st.session_state.assessment_reports
            st.session_state.selected_report_ids = set() # Clear selection on refresh
            st.rerun() # Rerun to re-fetch reports

        if 'assessment_reports' not in st.session_state:
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
            assessor_name = (r.get('user_profiles') or {}).get('full_name', '').lower()
            if search_query_lower in student_name or search_query_lower in report_text:
                filtered_reports.append(r)
    else:
        filtered_reports = reports

    if not filtered_reports:
        st.info("No reports found matching your search criteria.")
    else:
        # --- Bulk Actions Toolbar ---
        col_select, col_delete = st.columns([0.2, 0.8])
        
        with col_select:
            # Select All logic
            all_filtered_ids = [r['id'] for r in filtered_reports]
            is_all_selected = all(rid in st.session_state.selected_report_ids for rid in all_filtered_ids)
            if st.checkbox("Select All", value=is_all_selected, key="select_all_toggle"):
                for rid in all_filtered_ids:
                    st.session_state.selected_report_ids.add(rid)
                    st.session_state[f"selected_{rid}"] = True
            elif st.session_state.get("select_all_toggle") == False and is_all_selected:
                for rid in all_filtered_ids:
                    st.session_state.selected_report_ids.discard(rid)
                    st.session_state[f"selected_{rid}"] = False

        with col_delete:
            if st.session_state.selected_report_ids:
                # Use a session state flag to handle the confirmation workflow
                if not st.session_state.get('confirm_bulk_delete_active'):
                    if st.button(f"🗑️ Delete {len(st.session_state.selected_report_ids)} Selected", type="secondary"):
                        st.session_state.confirm_bulk_delete_active = True
                        st.rerun()
                else:
                    st.warning(f"⚠️ Confirm deletion of {len(st.session_state.selected_report_ids)} reports?")
                    c1, c2 = st.columns([0.2, 0.2])
                    if c1.button("Yes, Delete", type="primary", key="confirm_bulk_yes"):
                        try:
                            # Perform bulk delete in one query for efficiency
                            client_to_use = get_admin_supabase() if role == 'admin' else supabase
                            ids_to_del = list(st.session_state.selected_report_ids)
                            res = client_to_use.table("assessment_reports").delete().in_("id", ids_to_del).execute()
                            
                            if not res.data:
                                st.error("Bulk delete failed: No reports were removed. Check permissions.")
                                st.session_state.confirm_bulk_delete_active = False
                                st.stop()

                            # Reset states
                            st.session_state.selected_report_ids = set()
                            st.session_state.confirm_bulk_delete_active = False
                            if 'assessment_reports' in st.session_state:
                                del st.session_state.assessment_reports
                            st.success("Selected reports deleted successfully.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Bulk delete failed: {e}")
                    
                    if c2.button("Cancel", key="confirm_bulk_no"):
                        st.session_state.confirm_bulk_delete_active = False
                        st.rerun()
        
        # Grouping logic for admin
        if role == 'admin':
            reports_by_assessor = {}
            for r in filtered_reports:
                assessor_full_name = (r.get('user_profiles') or {}).get('full_name', 'Unknown Assessor')
                reports_by_assessor.setdefault(assessor_full_name, []).append(r)
            
            sorted_assessor_names = sorted(reports_by_assessor.keys())
            for assessor_name in sorted_assessor_names:
                assessor_reports = reports_by_assessor[assessor_name]
                with st.expander(f"Assessor: {assessor_name} ({len(assessor_reports)} reports)"):
                    for r in assessor_reports:
                        display_report_item(r, user_id, role)
        else:
            # Original display logic for non-admin users
            for r in filtered_reports:
                display_report_item(r, user_id, role)

if __name__ == "__main__":
    main()