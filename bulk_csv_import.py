import streamlit as st
import pandas as pd
from io import StringIO
from security_utils import sanitize_text_input
import database as db
from app_state import ensure_session_defaults


def _admin_gate():
    """Security gate: only system admin can access this page."""
    role = st.session_state.get('user_role', 'assessor')
    if role != 'admin':
        st.error("Access denied. This feature is only available to system administrators.")
        st.stop()


def main():
    ensure_session_defaults(
        {
            "bulk_import_results": [],
        }
    )

    _admin_gate()

    st.title("📋 Bulk CSV Import")
    st.caption("Admin-only: Batch-create student portfolios from a CSV roster.")

    st.markdown("""
    **CSV Format:** The file must contain at least a `student_name` column.
    Optional columns: `student_email`, `candidate_ref`, `trade_id`, `trade_level_id`.

    Example:
    ```csv
    student_name,student_email,candidate_ref,trade_id,trade_level_id
    John Doe,john@example.com,NSQ-001,1,2
    Jane Smith,jane@example.com,NSQ-002,1,2
    ```
    """)

    user_id = st.session_state.user_session.id

    uploaded_file = st.file_uploader(
        "Upload CSV roster",
        type=["csv"],
        help="CSV with student_name, student_email, candidate_ref, trade_id, trade_level_id"
    )

    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            st.markdown("##### Preview")
            st.dataframe(df.head(10), width='stretch', hide_index=True)
            st.caption(f"Total rows: {len(df)}")

            required_cols = ['student_name']
            missing = [c for c in required_cols if c not in df.columns]
            if missing:
                st.error(f"Missing required column: {', '.join(missing)}")
            else:
                if st.button("Import All Students", type="primary"):
                    imported = 0
                    skipped = 0
                    errors = []

                    for idx, row in df.iterrows():
                        raw_name = str(row.get('student_name', '')).strip()
                        student_name = sanitize_text_input(raw_name, 150)
                        if not student_name:
                            skipped += 1
                            continue

                        student_email = sanitize_text_input(str(row.get('student_email', '')), 150) or None
                        candidate_ref = sanitize_text_input(str(row.get('candidate_ref', '')), 150) or None

                        trade_id = None
                        if 'trade_id' in df.columns and pd.notna(row.get('trade_id')):
                            try:
                                trade_id = int(row['trade_id'])
                            except (ValueError, TypeError):
                                trade_id = None

                        level_id = None
                        if 'trade_level_id' in df.columns and pd.notna(row.get('trade_level_id')):
                            try:
                                level_id = int(row['trade_level_id'])
                            except (ValueError, TypeError):
                                level_id = None

                        result, err = db.create_student_portfolio(
                            student_name=student_name,
                            trade_id=trade_id,
                            trade_level_id=level_id,
                            student_email=student_email,
                            candidate_ref=candidate_ref,
                            user_id=user_id
                        )
                        if result:
                            imported += 1
                        else:
                            skipped += 1
                            errors.append(f"Row {idx+2}: {student_name} — {err}")

                    st.success(f"✅ Imported {imported} students. Skipped {skipped}.")
                    if errors:
                        with st.expander(f"⚠️ {len(errors)} errors"):
                            for e in errors:
                                st.error(e)

        except Exception as e:
            st.error(f"Failed to parse CSV: {e}")
