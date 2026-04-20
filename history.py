import streamlit as st
from auth_utils import get_supabase
from file_utils import export_to_word
import pandas as pd

def main():
    st.title("📜 Assessment History")
    supabase = get_supabase()
    user_id = st.session_state.user_session.id
    role = st.session_state.user_role

    try:
        # Build query: Admins see all, Assessors see theirs, ordered by the creation timestamp
        query = supabase.table("assessment_reports").select("*")
        if role != 'admin':
            query = query.eq("created_by", user_id)
        
        response = query.order("created_at", desc=True).execute()
        reports = response.data
    except Exception as e:
        st.error(f"Error fetching history: {e}")
        reports = []

    # st.write(f"Logged in as: {st.session_state.user_session.email}")
    # st.write(f"User ID: {user_id}")
    # st.write(f"Raw Data found: {len(reports)} records")

    if not reports:
        st.info("No reports found.")
    else:
        for r in reports:
            with st.expander(f"📅 {r.get('assessment_date')} | 👤 {r.get('student_name')}"):
                st.write(r['report_text'])

                doc_bytes = export_to_word(
                    r['student_name'], 
                    r['assessment_date'], 
                    r['report_text'], 
                    st.session_state.get('assessor_name', 'Assessor'), 
                    st.session_state.get('assessor_id', 'ID'),
                    selected_pcs=r.get('unit_codes', '')
                )
                st.download_button(
                    label="📥 Download Word",
                    data=doc_bytes,
                    file_name=f"NSQ_{r['student_name']}.docx",
                    key=f"dl_{r['id']}"
                )

if __name__ == "__main__":
    main()