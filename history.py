import streamlit as st
from auth_utils import get_supabase, get_admin_supabase
from file_utils import export_to_word
import pandas as pd

# Helper function to fetch reports
def _fetch_reports(user_id, role, search_query=None, page=1, page_size=20, assessor_filter=None):
    # Admins use the admin client to bypass RLS on user_profiles for full name retrieval
    client = get_admin_supabase() if role == 'admin' else get_supabase()
    try:
        # Build query with count="exact" for pagination
        query = client.table("assessment_reports").select("*, user_profiles(full_name)", count="exact") 
        
        # Admin can filter by a specific assessor, otherwise they see all
        if role == 'admin':
            if assessor_filter:
                query = query.eq("created_by", assessor_filter)
        else:
            # Assessors only see their own
            query = query.eq("created_by", user_id)
        
        if search_query:
            # Server-side search logic: search student_name OR report_text
            q = f"%{search_query}%"
            query = query.or_(f"student_name.ilike.{q},report_text.ilike.{q}")

        start = (page - 1) * page_size
        end = start + page_size - 1
        response = query.order("created_at", desc=True).range(start, end).execute()
        return response.data, response.count
    except Exception as e:
        st.error(f"Error fetching history: {e}")
        return [], 0

# Helper function for Admin to see all assessors
def _fetch_assessors():
    client = get_admin_supabase()
    try:
        # Fetch users who are either assessors or admins to populate the filter
        res = client.table("user_profiles").select("id, full_name").order("full_name").execute()
        return res.data
    except Exception as e:
        st.error(f"Error fetching assessors: {e}")
        return []

# Helper function to delete a report
def _delete_report(report_id, role, current_user_id):
    # Use the admin client to ensure the operation completes, 
    # but strictly enforce ownership for non-admin users.
    client = get_admin_supabase()
    try:
        query = client.table("assessment_reports").delete().eq("id", report_id)
        if role != 'admin':
            query = query.eq("created_by", current_user_id)
        
        res = query.execute()
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
        with st.expander(f"📅 {r.get('assessment_date')} | 👤 {r.get('student_name')} | 📚 {r.get('unit_codes', 'N/A')}"):
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
                    if _delete_report(report_id, current_user_role, current_user_id):
                        st.toast(f"Report for {r.get('student_name')} deleted.")
                        st.rerun()

def main():
    st.title("� Assessment History")
    supabase = get_supabase()
    user_id = st.session_state.user_session.id
    role = st.session_state.user_role

    # Initialize pagination and search state
    if 'history_page' not in st.session_state: st.session_state.history_page = 1
    if 'selected_report_ids' not in st.session_state: st.session_state.selected_report_ids = set()
    if 'search_query' not in st.session_state: st.session_state.search_query = ""
    if 'admin_assessor_filter' not in st.session_state: st.session_state.admin_assessor_filter = "All"

    # Admin-specific Filter UI
    if role == 'admin':
        assessors = _fetch_assessors()
        options = {"All": "All Assessors"}
        for a in assessors:
            options[a['id']] = a['full_name']
        
        selected_assessor = st.selectbox(
            "Filter by Assessor", 
            options=list(options.keys()), 
            format_func=lambda x: options[x],
            index=list(options.keys()).index(st.session_state.admin_assessor_filter) if st.session_state.admin_assessor_filter in options else 0
        )
        
        if selected_assessor != st.session_state.admin_assessor_filter:
            st.session_state.admin_assessor_filter = selected_assessor
            st.session_state.history_page = 1 # Reset to page 1 on filter change
            st.rerun()

    # Search implementation at the top
    search_input = st.text_input("Search reports by student name or content", value=st.session_state.search_query)
    
    # Reset page if search query changes
    if search_input != st.session_state.search_query:
        st.session_state.search_query = search_input
        st.session_state.history_page = 1
        st.rerun()

    page_size = 20
    
    try:
        # Fetch only the current page of reports based on search
        reports, total_count = _fetch_reports(
            user_id, role, 
            search_query=st.session_state.search_query, 
            page=st.session_state.history_page, 
            page_size=page_size,
            assessor_filter=st.session_state.admin_assessor_filter if st.session_state.admin_assessor_filter != "All" else None
        )
    except Exception:
        reports, total_count = [], 0

    if not reports and not st.session_state.search_query:
        st.info("No reports found.")
        if st.button("Refresh"): st.rerun()
        return

    # Pagination controls UI
    total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 1
    
    col_p1, col_p2, col_p3 = st.columns([1, 2, 1])
    with col_p1:
        if st.session_state.history_page > 1:
            if st.button("⬅️ Previous"):
                st.session_state.history_page -= 1
                st.rerun()
    with col_p2:
        st.write(f"Page **{st.session_state.history_page}** of {total_pages} (Total: {total_count})")
    with col_p3:
        if st.session_state.history_page < total_pages:
            if st.button("Next ➡️"):
                st.session_state.history_page += 1
                st.rerun()

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
                            # Use the admin client for bulk delete, filtering by user_id if not admin
                            admin_client = get_admin_supabase()
                            ids_to_del = list(st.session_state.selected_report_ids)
                            query = admin_client.table("assessment_reports").delete().in_("id", ids_to_del)
                            if role != 'admin':
                                query = query.eq("created_by", user_id)
                            
                            res = query.execute()
                            
                            if not res.data:
                                st.error("Bulk delete failed: No reports were removed. Check permissions.")
                                st.session_state.confirm_bulk_delete_active = False
                                st.stop()

                            # Reset states
                            st.session_state.selected_report_ids = set()
                            st.session_state.confirm_bulk_delete_active = False
                            st.success("Selected reports deleted successfully.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Bulk delete failed: {e}")
                    
                    if c2.button("Cancel", key="confirm_bulk_no"):
                        st.session_state.confirm_bulk_delete_active = False
                        st.rerun()
        
        # Grouping logic for admin: 
        # Only group if a specific assessor is selected; otherwise, show a flat chronological list.
        if role == 'admin' and st.session_state.admin_assessor_filter != "All":
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