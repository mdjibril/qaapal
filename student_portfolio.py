import streamlit as st
from security_utils import sanitize_text_input
import database as db
from app_state import ensure_session_defaults


def _admin_gate():
    """Security gate: only system admin can access this page."""
    role = st.session_state.get('user_role', 'assessor')
    if role != 'admin':
        st.error("Access denied. This feature is only available to system administrators.")
        st.stop()


def _status_badge(status):
    if status == 'passed':
        return "🟢 Passed"
    elif status == 'in_progress':
        return "🟡 In Progress"
    elif status == 'needs_retest':
        return "🔴 Needs Retest"
    return status


def _render_portfolio_detail(portfolio_id):
    portfolio = db.fetch_student_portfolio(portfolio_id)
    if not portfolio:
        st.error("Portfolio not found.")
        return

    trade_name = (portfolio.get('trades') or {}).get('name', 'N/A')
    st.subheader(f"Portfolio: {portfolio.get('student_name', 'Unnamed')}")
    st.caption(f"Trade: {trade_name} | Created: {portfolio.get('created_at', 'N/A')[:10] if portfolio.get('created_at') else 'N/A'}")

    # PC Progress Matrix
    progress = db.fetch_pc_progress(portfolio_id)
    if progress:
        total_pcs = len(progress)
        passed_count = sum(1 for p in progress if p.get('status') == 'passed')
        in_progress_count = sum(1 for p in progress if p.get('status') == 'in_progress')
        retest_count = sum(1 for p in progress if p.get('status') == 'needs_retest')

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Tracked", total_pcs)
        with col2:
            st.metric("🟢 Passed", passed_count)
        with col3:
            st.metric("🟡 In Progress", in_progress_count)
        with col4:
            st.metric("🔴 Needs Retest", retest_count)

        if total_pcs > 0:
            st.progress(
                passed_count / total_pcs,
                text=f"Completion: {passed_count}/{total_pcs} PCs passed"
            )

        st.markdown("##### PC Progress")
        progress_rows = []
        for p in progress:
            pc = p.get('performance_criteria') or {}
            unit = p.get('units') or {}
            progress_rows.append({
                "Unit": unit.get('code', 'N/A'),
                "PC Code": pc.get('pc_code', 'N/A'),
                "Description": pc.get('description', 'N/A'),
                "Status": _status_badge(p.get('status', 'N/A')),
                "Assessed At": p.get('assessed_at', '')[:10] if p.get('assessed_at') else 'N/A'
            })
        st.dataframe(progress_rows, width='stretch', hide_index=True)
    else:
        st.info("No PC progress recorded yet. Generate a report on the Dashboard to auto-track, or add progress manually below.")

    st.markdown("---")
    col_add, col_del = st.columns(2)
    with col_add:
        st.markdown("##### Add PC Progress")
        trade_id = portfolio.get('trade_id')
        level_id = portfolio.get('trade_level_id')
        pc_options = db.fetch_pc_options_for_portfolio(trade_id=trade_id, trade_level_id=level_id) if trade_id or level_id else []
        if pc_options:
            option_map = {opt['label']: opt for opt in pc_options}
            selected_pc_label = st.selectbox(
                "Select PC",
                options=list(option_map.keys()),
                key=f"pc_select_{portfolio_id}"
            )
            status = st.selectbox("Status", ['passed', 'in_progress', 'needs_retest'], key=f"status_{portfolio_id}")
            if st.button("Save PC Progress", key=f"save_pc_{portfolio_id}"):
                selected_opt = option_map[selected_pc_label]
                success, err = db.upsert_pc_progress(
                    portfolio_id=portfolio_id,
                    pc_id=selected_opt['pc_id'],
                    unit_id=selected_opt['unit_id'],
                    status=status,
                    evidence_report_id=None,
                    assessed_by=st.session_state.user_session.id
                )
                if success:
                    st.toast("PC progress saved.")
                    st.rerun()
                else:
                    st.error(f"Failed to save: {err}")
        else:
            st.info("No NOS data available for this portfolio's trade/level.")

    with col_del:
        st.markdown("##### Delete Portfolio")
        if st.button("Delete This Portfolio", key=f"del_portfolio_{portfolio_id}", type="secondary"):
            success, err = db.delete_student_portfolio(portfolio_id)
            if success:
                st.toast("Portfolio deleted.")
                st.session_state.pop('selected_portfolio_id', None)
                st.rerun()
            else:
                st.error(f"Failed to delete: {err}")


def main():
    ensure_session_defaults(
        {
            "selected_portfolio_id": None,
        }
    )

    _admin_gate()

    st.title("🎓 Student Portfolios")
    st.caption("Admin-only: Track students across multiple assessments.")

    user_id = st.session_state.user_session.id

    # Sidebar / top controls
    st.markdown("---")
    st.subheader("All Portfolios")
    portfolios = db.fetch_student_portfolios()

    if not portfolios:
        st.info("No portfolios yet. Create one below.")

    # Portfolio list with detail view
    col_list, col_detail = st.columns([1, 2])
    with col_list:
        st.markdown("**Select Portfolio**")
        if portfolios:
            portfolio_map = {p['id']: f"{p.get('student_name', 'Unnamed')} ({p.get('candidate_ref', 'N/A')})" for p in portfolios}
            selected_id = st.selectbox(
                "Portfolio",
                options=list(portfolio_map.keys()),
                format_func=lambda x: portfolio_map[x],
                key="portfolio_select",
                label_visibility="collapsed"
            )
            if selected_id:
                st.session_state.selected_portfolio_id = selected_id
        else:
            st.session_state.selected_portfolio_id = None

    with col_detail:
        if st.session_state.selected_portfolio_id:
            _render_portfolio_detail(st.session_state.selected_portfolio_id)
        else:
            st.info("Select a portfolio to view details.")

    st.markdown("---")
    st.subheader("Create New Portfolio")

    # --- Trade/Level selection OUTSIDE form so it reruns on change ---
    st.markdown("**Select Trade & Level**")
    trades = db.fetch_trades()
    trade_id = None
    level_id = None

    if trades:
        sorted_trades = sorted(trades, key=lambda t: (t.get("name") or "").casefold())
        trade_names = [t['name'] for t in sorted_trades]
        selected_trade_name = st.selectbox(
            "Trade",
            trade_names,
            key="portfolio_trade_select"
        )
        selected_trade = next((t for t in sorted_trades if t['name'] == selected_trade_name), None)
        trade_id = selected_trade['id'] if selected_trade else None

        if trade_id:
            trade_levels = db.fetch_trade_levels(trade_id)
            if trade_levels:
                level_options = {
                    f"Level {lvl['level']} - {lvl.get('display_name') or 'Standard'}": lvl['id']
                    for lvl in trade_levels
                }
                selected_level_label = st.selectbox(
                    "Trade Level",
                    options=list(level_options.keys()),
                    key="portfolio_level_select"
                )
                level_id = level_options[selected_level_label]
            else:
                level_id = None
                st.caption("No levels found for this trade.")
    else:
        st.error("No trades found in database.")

    st.markdown("**Student Details**")
    with st.form("create_portfolio_form"):
        raw_name = st.text_input("Student Name", key="new_portfolio_name")
        student_name = sanitize_text_input(raw_name, 150)
        raw_email = st.text_input("Student Email (optional)", key="new_portfolio_email")
        student_email = sanitize_text_input(raw_email, 150) or None
        raw_ref = st.text_input(
            "Candidate Reference (optional)",
            key="new_portfolio_ref",
            help="NSQ registration number, matriculation number, or any external ID the student has."
        )
        candidate_ref = sanitize_text_input(raw_ref, 150) or None

        if st.form_submit_button("Create Portfolio", type="primary"):
            if not student_name:
                st.error("Student name is required.")
            elif not trade_id:
                st.error("Please select a trade.")
            else:
                result, err = db.create_student_portfolio(
                    student_name=student_name,
                    trade_id=trade_id,
                    trade_level_id=level_id,
                    student_email=student_email,
                    candidate_ref=candidate_ref,
                    user_id=user_id
                )
                if result:
                    st.toast("Portfolio created.")
                    st.rerun()
                else:
                    st.error(f"Failed to create: {err}")
