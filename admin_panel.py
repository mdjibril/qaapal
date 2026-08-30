import streamlit as st
import os
import database as db
from auth_utils import get_supabase, get_admin_supabase, get_secret


def _clear_session_keys(*keys):
    for key in keys:
        st.session_state.pop(key, None)


def _clear_session_keys_with_prefix(*prefixes):
    keys_to_remove = [key for key in st.session_state.keys() if key.startswith(prefixes)]
    for key in keys_to_remove:
        del st.session_state[key]


def _clear_nos_branch(prefix, include_table=False):
    keys = [
        f"{prefix}_trade_id",
        f"{prefix}_trade_name",
        f"{prefix}_trade_level_id",
        f"{prefix}_trade_level_label",
        f"{prefix}_unit_id",
        f"{prefix}_unit_label",
        f"{prefix}_lo_id",
        f"{prefix}_lo_label",
        f"{prefix}_pc_id",
        f"{prefix}_pc_label",
        f"{prefix}_search",
        f"{prefix}_trade_search",
        f"{prefix}_level_search",
        f"{prefix}_unit_search",
        f"{prefix}_lo_search",
        f"{prefix}_pc_search",
        f"{prefix}_table",
    ]
    if not include_table:
        keys.remove(f"{prefix}_table")
    _clear_session_keys(*keys)

def main():
    st.title("🛡️ Super Admin Control Center")
    st.markdown("Centralized configuration, user management, metrics, and application audit panel.")

    # Authorization Check
    if st.session_state.get('user_role') != 'admin':
        st.error("Access Denied: You do not have permissions to view this panel.")
        return

    # Use tabs to modularize sub-dashboards
    tab_overview, tab_users, tab_nos, tab_feedback = st.tabs([
        "📊 System Overview",
        "👥 User Directory",
        "📚 NOS Management",
        "💬 Product Feedback"
    ])

    # ==========================================
    # 📊 SYSTEM OVERVIEW
    # ==========================================
    with tab_overview:
        st.subheader("High-Level Metrics")
        
        with st.spinner("Fetching metrics..."):
            metrics = db.fetch_system_metrics()
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Active Users", metrics.get('total_users', 0))
        col2.metric("Total Organizations", metrics.get('total_orgs', 0))
        col3.metric("Reports Generated", metrics.get('total_reports', 0))

        st.divider()

        # API & Environment Configuration
        st.subheader("API Gateway Status")
        
        # Determine API Presence without throwing errors on missing secrets
        gemini_present = bool(get_secret(["INTERNAL_AI_KEY"], "INTERNAL_AI_KEY"))
        groq_present = bool(get_secret(["GROQ_API_KEY"], "GROQ_API_KEY"))
        openrouter_present = bool(get_secret(["OPENROUTER_API_KEY"], "OPENROUTER_API_KEY"))
        vertex_present = bool(get_secret(["vertex_ai", "service_account_json"], "VERTEX_AI"))

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Gemini API", "Configured" if gemini_present else "Missing")
        c2.metric("Groq API", "Configured" if groq_present else "Missing")
        c3.metric("OpenRouter API", "Configured" if openrouter_present else "Missing")
        c4.metric("Vertex AI", "Configured" if vertex_present else "Missing")

        st.divider()

        # Webhook / Subscription Activity
        st.subheader("Subscription Activity")
        try:
            admin_client = get_admin_supabase()
            res = admin_client.table("organizations").select("id, subscription_tier, credits_balance, subscription_start_date, user_profiles!org_id(email)").neq("subscription_tier", "free").execute()
            if res.data:
                activity_data = []
                for o in res.data:
                    up = o.get("user_profiles") or {}
                    email = up.get("email", "N/A") if isinstance(up, dict) else "N/A"
                    start = o.get("subscription_start_date", "")[:10] if o.get("subscription_start_date") else "N/A"
                    activity_data.append({
                        "Date": start,
                        "Tier": o.get("subscription_tier", "N/A").replace("_", " ").title(),
                        "Credits": o.get("credits_balance", 0),
                        "Email": email,
                    })
                st.dataframe(activity_data, width='stretch', hide_index=True)
            else:
                st.info("No paid subscriptions yet.")
        except Exception:
            st.info("Unable to load subscription data.")


        # QA and Recent Reports
        st.subheader("Recent Assessment Reports (QA Audit)")
        with st.spinner("Loading recent reports..."):
            reports = db.fetch_recent_reports(limit=50)

        if reports:
            # Display metadata table
            filtered_reports = []
            for r in reports:
                assessor_name = (r.get('user_profiles') or {}).get('full_name', 'Unknown Assessor')
                trade_name = (r.get('trades') or {}).get('name', 'Unknown Trade')
                filtered_reports.append({
                    "Date": r.get('created_at', '')[:10] if r.get('created_at') else 'N/A',
                    "Candidate Name": r.get('student_name', 'N/A'),
                    "Trade Name": trade_name,
                    "Assessor Name": assessor_name
                })
            
            st.dataframe(filtered_reports, width='stretch', hide_index=True)

            st.markdown("##### Inspect Full Report Details")
            report_map = {r['id']: f"{r.get('student_name')} ({r.get('created_at', '')[:10]})" for r in reports}
            selected_report_id = st.selectbox(
                "Select a report to review its generated output", 
                options=list(report_map.keys()),
                format_func=lambda x: report_map[x]
            )
            
            if selected_report_id:
                report_data = next((r for r in reports if r['id'] == selected_report_id), None)
                if report_data:
                    st.text_area("Audit Report Content", value=report_data.get('report_text', ''), height=250, disabled=True)
        else:
            st.info("No recent assessment reports found in database.")

        st.divider()


    # ==========================================
    # 👥 USER DIRECTORY
    # ==========================================
    with tab_users:
        sub_tab_list, sub_tab_create = st.tabs(["📋 Directory", "➕ Create User Account"])

        with sub_tab_list:
            st.subheader("System Access & Directory Management")
            try:
                admin_client = get_admin_supabase()
                with st.spinner("Loading directory details..."):
                    response = admin_client.table("user_profiles")\
                        .select("id, email, full_name, role, org_id, organizations(subscription_tier, credits_balance)")\
                        .order("full_name")\
                        .execute()
                
                if response.data:
                    flat_data = []
                    for row in response.data:
                        org = row.get('organizations') or {}
                        flat_data.append({
                            "Full Name": row.get('full_name', 'N/A'),
                            "Email": row.get('email', 'N/A'),
                            "Role": row.get('role', 'assessor'),
                            "Plan": (org.get('subscription_tier') or 'free').upper().replace('_', ' '),
                            "Credits": org.get('credits_balance', 0),
                            "org_id": row.get('org_id'),
                            "id": row.get('id')
                        })

                    # Calculate User Directory Metrics
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("Total Directory Accounts", len(flat_data))
                    m2.metric("Registered Assessors", sum(1 for u in flat_data if u['Role'] == 'assessor'))
                    m3.metric("Candidate Accounts", sum(1 for u in flat_data if u['Role'] == 'student'))
                    
                    total_creds = sum(u['Credits'] for u in flat_data)
                    m4.metric("Total Pool Credits", total_creds)

                    # Show Directory
                    display_list = [{k: v for k, v in u.items() if k not in ('id', 'org_id')} for u in flat_data]
                    st.dataframe(display_list, width='stretch', hide_index=True)

                    # --- Plan & Credit Modifications ---
                    st.markdown("---")
                    st.subheader("🛠️ Account Plans & Credit Provisioning")
                    
                    manageable_users = [u for u in flat_data if u['Role'] != 'admin']
                    
                    if manageable_users:
                        selected_users = st.multiselect(
                            "Select target user accounts for plan provisioning/modifications",
                            options=manageable_users,
                            format_func=lambda x: f"{x['Full Name']} ({x['Email']}) | Plan: {x['Plan']} | Credits: {x['Credits']}"
                        )
                        
                        if selected_users:
                            col_plan, col_cred = st.columns(2)
                            
                            with col_plan:
                                new_tier = st.selectbox(
                                    "Assign Target Service Level", 
                                    ['free', 'platform_pass', 'lifetime', 'enterprise'],
                                    format_func=lambda x: x.replace('_', ' ').title()
                                )
                                if st.button(f"Update Plan Tier: {new_tier.title()}"):
                                    with st.spinner("Modifying organization tiers..."):
                                        for user in selected_users:
                                            if user['org_id']:
                                                db.upgrade_org_tier(user['org_id'], new_tier)
                                        st.success(f"Successfully upgraded accounts to {new_tier.title()}!")
                                        st.rerun()
                                        
                            with col_cred:
                                if len(selected_users) == 1:
                                    current_cred = selected_users[0]['Credits']
                                    new_credits = st.number_input("Modify Credit Allocation", min_value=0, value=int(current_cred), step=1)
                                    if st.button("Save Credit Balance"):
                                        if selected_users[0]['org_id']:
                                            success, err = db.update_org_credits(selected_users[0]['org_id'], new_credits)
                                            if success:
                                                st.success("User credit allocation updated!")
                                                st.rerun()
                                            else:
                                                st.error(f"Failed to update credit allocation: {err}")

                                    st.markdown("**⚡ Credit Pack Top-Up**")
                                    credit_pack = st.selectbox(
                                        "Select pack to apply",
                                        [20, 150, 400],
                                        format_func=lambda x: f"{x} Reports"
                                    )
                                    if st.button("Apply Credit Pack"):
                                        if selected_users[0]['org_id']:
                                            success, err = db.top_up_org_credits(selected_users[0]['org_id'], credit_pack)
                                            if success:
                                                st.success(f"Added {credit_pack} credits!")
                                                st.rerun()
                                            else:
                                                st.error(f"Failed to apply credit pack: {err}")
                                else:
                                    st.info("Bulk operations for numeric credits are disabled. Please modify credits individually.")

                            # DANGER ZONE
                            st.markdown("---")
                            st.subheader("⚠️ Account Deletion & Termination")
                            st.warning("Deleting user profiles will permanently wipe their credentials, generated logs, statements, and assessment metrics. This action is not reversible.")
                            
                            if st.button("🗑️ Delete Selected Accounts and All Child Data", type="primary"):
                                with st.spinner("Wiping selected accounts..."):
                                    try:
                                        admin_client = get_admin_supabase()
                                        for user in selected_users:
                                            user_id = user['id']
                                            org_id  = user['org_id']

                                            # Delete associated metrics
                                            admin_client.table('assessment_reports').delete().eq('created_by', user_id).execute()
                                            admin_client.table('student_statements').delete().eq('created_by', user_id).execute()
                                            admin_client.table('witness_statements').delete().eq('created_by', user_id).execute()
                                            admin_client.table('product_feedback').delete().eq('user_id', user_id).execute()

                                            # Remove from GoTrue/Supabase Auth
                                            admin_client.auth.admin.delete_user(user_id)

                                            # Clear empty organization structures
                                            if org_id:
                                                remaining = admin_client.table('user_profiles')\
                                                    .select('id', count='exact')\
                                                    .eq('org_id', org_id)\
                                                    .execute()
                                                remaining_count = remaining.count if hasattr(remaining, 'count') and remaining.count is not None else len(remaining.data)
                                                if remaining_count == 0:
                                                    admin_client.table('organizations').delete().eq('id', org_id).execute()

                                        st.success("Successfully purged accounts, credentials, and orphaned organizations.")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Termination action failed: {e}")
                    else:
                        st.info("No assessor or candidate accounts are currently registered under your tenancy.")
                else:
                    st.info("No active directories found.")
            except Exception as e:
                st.error(f"Failed to query directories: {e}")

        with sub_tab_create:
            st.subheader("Provision New Account Identity")
            with st.form("new_user_form", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1:
                    email = st.text_input("User Email Address")
                    password = st.text_input("User Access Password", type="password", help="Must contain at least 6 characters")
                    full_name = st.text_input("Full Registered Name (e.g. John Doe)")
                    role = st.selectbox("Role Identity Assignment", ["assessor", "student"], index=0)
                
                with col2:
                    org_name = st.text_input("Institution / Organization Name")
                    primary_trade = st.text_input("Primary Assessment Sector")
                    marketing_source = st.selectbox(
                        "Registration Source Channel",
                        ["Direct Admin Entry", "LinkedIn", "WhatsApp Group", "NBTE/NSQ Event", "Word of Mouth", "Other"]
                    )
                    report_volume = st.selectbox(
                        "Estimated Usage Metrics",
                        ["1-10 reports", "11-50 reports", "51-100 reports", "100+ reports"]
                    )

                st.info("💡 Creating an identity bypasses primary email verification loops. It assigns them workspace access instantly.")
                submit = st.form_submit_button("Provision Access Credentials")
                
                if submit:
                    if not email or not password or not full_name or not org_name:
                        st.error("All highlighted fields are required to establish user workspaces.")
                    else:
                        try:
                            admin_client = get_admin_supabase()
                            
                            # Create via Admin SDK
                            auth_user = admin_client.auth.admin.create_user({
                                "email": email, 
                                "password": password, 
                                "email_confirm": True,
                                "user_metadata": {
                                    "full_name": full_name,
                                    "org_name": org_name,
                                    "marketing_source": marketing_source,
                                    "primary_trade": primary_trade,
                                    "monthly_volume": report_volume,
                                    "role": role
                                }
                            })

                            # Force updates to roles structure
                            admin_client.table("user_profiles").update({
                                "role": role
                            }).eq("id", auth_user.user.id).execute()

                            st.success(f"Access granted! Assessor identity generated for {full_name}.")
                            st.balloons()
                        except Exception as e:
                            st.error(f"Failed to register credentials: {e}")


    # ==========================================
    # 📚 NOS & TRADES
    # ==========================================
    with tab_nos:
        sub_tab_view, sub_tab_edit, sub_tab_delete = st.tabs(["👁️ View Database", "✍️ Update Content", "🗑️ Delete Content"])

        def _filter_rows(rows, query, fields=None):
            if not query:
                return rows
            q = query.strip().lower()
            if not q:
                return rows
            filtered = []
            for row in rows:
                probe_fields = fields or list(row.keys())
                if any(q in str(row.get(field, "")).lower() for field in probe_fields):
                    filtered.append(row)
            return filtered

        def _render_selectbox(
            label,
            rows,
            display_fn,
            key,
            none_message,
            search_key,
            search_fields=None,
            on_change=None,
            on_change_args=None,
        ):
            search_query = st.text_input(f"🔎 {label} Search", placeholder="Type to filter...", key=search_key)
            filtered_rows = _filter_rows(rows, search_query, search_fields)
            if not filtered_rows:
                st.info(none_message)
                return None, filtered_rows
            options = [display_fn(row) for row in filtered_rows]
            selected_label = st.selectbox(
                label,
                options,
                key=key,
                on_change=on_change,
                args=on_change_args or (),
            )
            selected_row = next((row for row in filtered_rows if display_fn(row) == selected_label), None)
            return selected_row, filtered_rows

        with sub_tab_view:
            view_table = st.selectbox(
                "Select Standards Table",
                ["Trades", "Trade Levels", "Units", "Learning Outcomes", "Performance Criteria"],
                key="nos_view_table",
            )
            if st.session_state.get("nos_view_last_table") != view_table:
                _clear_session_keys(
                    "nos_view_trade_select",
                    "nos_view_level_select",
                    "nos_view_unit_select",
                    "nos_view_lo_select",
                    "nos_view_pc_select",
                    "nos_view_trade_id",
                    "nos_view_trade_name",
                    "nos_view_trade_level_id",
                    "nos_view_trade_level_label",
                    "nos_view_unit_id",
                    "nos_view_unit_label",
                    "nos_view_lo_id",
                    "nos_view_lo_label",
                    "nos_view_pc_id",
                    "nos_view_pc_label",
                    "nos_view_trade_search",
                    "nos_view_level_search",
                    "nos_view_unit_search",
                    "nos_view_lo_search",
                    "nos_view_pc_search",
                )
                st.session_state.nos_view_last_table = view_table

            trades = db.fetch_trades()
            if not trades:
                st.info("No trades available.")
            elif view_table == "Trades":
                search_query = st.text_input(
                    "🔍 Search Trades",
                    placeholder="Type keywords, codes, descriptions...",
                    key="nos_view_trade_search",
                )
                filtered_rows = _filter_rows(trades, search_query, ["name", "id"])
                st.caption(f"Showing {len(filtered_rows)} record(s).")
                st.dataframe(filtered_rows, width="stretch", hide_index=True)
            elif view_table == "Trade Levels":
                selected_trade, _ = _render_selectbox(
                    "Select Trade",
                    trades,
                    lambda trade: f"{trade['name']} (ID {trade['id']})",
                    key="nos_view_trade_select",
                    none_message="No trades available.",
                    search_key="nos_view_trade_search",
                    search_fields=["name", "id"],
                )
                if selected_trade:
                    if st.session_state.get("nos_view_trade_id") != selected_trade["id"]:
                        _clear_session_keys(
                            "nos_view_level_select",
                            "nos_view_unit_select",
                            "nos_view_lo_select",
                            "nos_view_pc_select",
                            "nos_view_trade_level_id",
                            "nos_view_unit_id",
                            "nos_view_lo_id",
                            "nos_view_pc_id",
                            "nos_view_level_search",
                            "nos_view_unit_search",
                            "nos_view_lo_search",
                            "nos_view_pc_search",
                        )
                    st.session_state.nos_view_trade_id = selected_trade["id"]
                    st.session_state.nos_view_trade_name = selected_trade["name"]
                    rows = db.fetch_trade_levels(selected_trade["id"])
                    search_query = st.text_input(
                        "🔍 Search Trade Levels",
                        placeholder="Type keywords, codes, descriptions...",
                        key="nos_view_level_search",
                    )
                    filtered_rows = _filter_rows(rows, search_query, ["level", "display_name", "trade_id", "id"])
                    st.caption(f"Showing {len(filtered_rows)} record(s) for {selected_trade['name']}.")
                    st.dataframe(filtered_rows, width="stretch", hide_index=True)
            elif view_table == "Units":
                selected_trade, _ = _render_selectbox(
                    "Select Trade",
                    trades,
                    lambda trade: f"{trade['name']} (ID {trade['id']})",
                    key="nos_view_trade_select",
                    none_message="No trades available.",
                    search_key="nos_view_trade_search",
                    search_fields=["name", "id"],
                )
                if selected_trade:
                    if st.session_state.get("nos_view_trade_id") != selected_trade["id"]:
                        _clear_session_keys(
                            "nos_view_trade_level_id",
                            "nos_view_unit_id",
                            "nos_view_lo_id",
                            "nos_view_pc_id",
                            "nos_view_level_search",
                            "nos_view_unit_search",
                            "nos_view_lo_search",
                            "nos_view_pc_search",
                        )
                    st.session_state.nos_view_trade_id = selected_trade["id"]
                    st.session_state.nos_view_trade_name = selected_trade["name"]
                    trade_levels = db.fetch_trade_levels(selected_trade["id"])
                    selected_level, _ = _render_selectbox(
                        "Select Trade Level",
                        trade_levels,
                        lambda lvl: f"Level {lvl['level']}" + (f" - {lvl['display_name']}" if lvl.get("display_name") else ""),
                        key="nos_view_level_select",
                        none_message="No trade levels found for this trade.",
                        search_key="nos_view_level_search",
                        search_fields=["level", "display_name", "trade_id", "id"],
                    )
                    if selected_level:
                        if st.session_state.get("nos_view_trade_level_id") != selected_level["id"]:
                            _clear_session_keys(
                                "nos_view_unit_select",
                                "nos_view_lo_select",
                                "nos_view_pc_select",
                                "nos_view_unit_id",
                                "nos_view_lo_id",
                                "nos_view_pc_id",
                                "nos_view_unit_search",
                                "nos_view_lo_search",
                                "nos_view_pc_search",
                            )
                        st.session_state.nos_view_trade_level_id = selected_level["id"]
                        st.session_state.nos_view_trade_level_label = selected_level.get("display_name") or f"Level {selected_level['level']}"
                        rows = db.fetch_units_by_trade_level(selected_level["id"])
                        search_query = st.text_input(
                            "🔍 Search Units",
                            placeholder="Type keywords, codes, descriptions...",
                            key="nos_view_unit_search",
                        )
                        filtered_rows = _filter_rows(rows, search_query, ["code", "title", "trade_id", "trade_level_id", "id"])
                        st.caption(
                            f"Showing {len(filtered_rows)} record(s) for {selected_trade['name']} / {st.session_state.nos_view_trade_level_label}."
                        )
                        st.dataframe(filtered_rows, width="stretch", hide_index=True)
            elif view_table == "Learning Outcomes":
                selected_trade, _ = _render_selectbox(
                    "Select Trade",
                    trades,
                    lambda trade: f"{trade['name']} (ID {trade['id']})",
                    key="nos_view_trade_select",
                    none_message="No trades available.",
                    search_key="nos_view_trade_search",
                    search_fields=["name", "id"],
                )
                if selected_trade:
                    if st.session_state.get("nos_view_trade_id") != selected_trade["id"]:
                        _clear_session_keys(
                            "nos_view_trade_level_id",
                            "nos_view_unit_id",
                            "nos_view_lo_id",
                            "nos_view_pc_id",
                            "nos_view_level_search",
                            "nos_view_unit_search",
                            "nos_view_lo_search",
                            "nos_view_pc_search",
                        )
                    st.session_state.nos_view_trade_id = selected_trade["id"]
                    st.session_state.nos_view_trade_name = selected_trade["name"]
                    trade_levels = db.fetch_trade_levels(selected_trade["id"])
                    selected_level, _ = _render_selectbox(
                        "Select Trade Level",
                        trade_levels,
                        lambda lvl: f"Level {lvl['level']}" + (f" - {lvl['display_name']}" if lvl.get("display_name") else ""),
                        key="nos_view_level_select",
                        none_message="No trade levels found for this trade.",
                        search_key="nos_view_level_search",
                        search_fields=["level", "display_name", "trade_id", "id"],
                    )
                    if selected_level:
                        if st.session_state.get("nos_view_trade_level_id") != selected_level["id"]:
                            _clear_session_keys(
                                "nos_view_unit_id",
                                "nos_view_lo_id",
                                "nos_view_pc_id",
                                "nos_view_unit_search",
                                "nos_view_lo_search",
                                "nos_view_pc_search",
                            )
                        st.session_state.nos_view_trade_level_id = selected_level["id"]
                        st.session_state.nos_view_trade_level_label = selected_level.get("display_name") or f"Level {selected_level['level']}"
                        units = db.fetch_units_by_trade_level(selected_level["id"])
                        selected_unit, _ = _render_selectbox(
                            "Select Unit",
                            units,
                            lambda unit: f"{unit['code']}: {unit['title']}",
                            key="nos_view_unit_select",
                            none_message="No units found for this level.",
                            search_key="nos_view_unit_search",
                            search_fields=["code", "title", "trade_id", "trade_level_id", "id"],
                        )
                        if selected_unit:
                            if st.session_state.get("nos_view_unit_id") != selected_unit["id"]:
                                _clear_session_keys(
                                    "nos_view_lo_select",
                                    "nos_view_pc_select",
                                    "nos_view_lo_id",
                                    "nos_view_pc_id",
                                    "nos_view_lo_search",
                                    "nos_view_pc_search",
                                )
                            st.session_state.nos_view_unit_id = selected_unit["id"]
                            st.session_state.nos_view_unit_label = selected_unit["title"]
                            rows = db.fetch_learning_outcomes_by_unit(selected_unit["id"])
                            search_query = st.text_input(
                                "🔍 Search Learning Outcomes",
                                placeholder="Type keywords, codes, descriptions...",
                                key="nos_view_lo_search",
                            )
                            filtered_rows = _filter_rows(rows, search_query, ["lo_num", "description", "unit_id", "id"])
                            st.caption(
                                f"Showing {len(filtered_rows)} record(s) for {selected_trade['name']} / {st.session_state.nos_view_trade_level_label} / {selected_unit['code']}."
                            )
                            st.dataframe(filtered_rows, width="stretch", hide_index=True)
            else:
                selected_trade, _ = _render_selectbox(
                    "Select Trade",
                    trades,
                    lambda trade: f"{trade['name']} (ID {trade['id']})",
                    key="nos_view_trade_select",
                    none_message="No trades available.",
                    search_key="nos_view_trade_search",
                    search_fields=["name", "id"],
                )
                if selected_trade:
                    if st.session_state.get("nos_view_trade_id") != selected_trade["id"]:
                        _clear_session_keys(
                            "nos_view_level_select",
                            "nos_view_unit_select",
                            "nos_view_lo_select",
                            "nos_view_pc_select",
                            "nos_view_trade_level_id",
                            "nos_view_unit_id",
                            "nos_view_lo_id",
                            "nos_view_pc_id",
                            "nos_view_level_search",
                            "nos_view_unit_search",
                            "nos_view_lo_search",
                            "nos_view_pc_search",
                        )
                    st.session_state.nos_view_trade_id = selected_trade["id"]
                    st.session_state.nos_view_trade_name = selected_trade["name"]
                    trade_levels = db.fetch_trade_levels(selected_trade["id"])
                    selected_level, _ = _render_selectbox(
                        "Select Trade Level",
                        trade_levels,
                        lambda lvl: f"Level {lvl['level']}" + (f" - {lvl['display_name']}" if lvl.get("display_name") else ""),
                        key="nos_view_level_select",
                        none_message="No trade levels found for this trade.",
                        search_key="nos_view_level_search",
                        search_fields=["level", "display_name", "trade_id", "id"],
                    )
                    if selected_level:
                        if st.session_state.get("nos_view_trade_level_id") != selected_level["id"]:
                            _clear_session_keys(
                                "nos_view_unit_select",
                                "nos_view_lo_select",
                                "nos_view_pc_select",
                                "nos_view_unit_id",
                                "nos_view_lo_id",
                                "nos_view_pc_id",
                                "nos_view_unit_search",
                                "nos_view_lo_search",
                                "nos_view_pc_search",
                            )
                        st.session_state.nos_view_trade_level_id = selected_level["id"]
                        st.session_state.nos_view_trade_level_label = selected_level.get("display_name") or f"Level {selected_level['level']}"
                        units = db.fetch_units_by_trade_level(selected_level["id"])
                        selected_unit, _ = _render_selectbox(
                            "Select Unit",
                            units,
                            lambda unit: f"{unit['code']}: {unit['title']}",
                            key="nos_view_unit_select",
                            none_message="No units found for this level.",
                            search_key="nos_view_unit_search",
                            search_fields=["code", "title", "trade_id", "trade_level_id", "id"],
                        )
                        if selected_unit:
                            if st.session_state.get("nos_view_unit_id") != selected_unit["id"]:
                                _clear_session_keys(
                                    "nos_view_lo_id",
                                    "nos_view_pc_id",
                                    "nos_view_lo_search",
                                    "nos_view_pc_search",
                                )
                            st.session_state.nos_view_unit_id = selected_unit["id"]
                            st.session_state.nos_view_unit_label = selected_unit["title"]
                            los = db.fetch_learning_outcomes_by_unit(selected_unit["id"])
                            selected_lo, _ = _render_selectbox(
                                "Select Learning Outcome",
                                los,
                                lambda lo: f"LO {lo['lo_num']}: {lo['description']}",
                                key="nos_view_lo_select",
                                none_message="No learning outcomes found for this unit.",
                                search_key="nos_view_lo_search",
                                search_fields=["lo_num", "description", "unit_id", "id"],
                            )
                            if selected_lo:
                                if st.session_state.get("nos_view_lo_id") != selected_lo["id"]:
                                    _clear_session_keys("nos_view_pc_id", "nos_view_pc_search")
                                st.session_state.nos_view_lo_id = selected_lo["id"]
                                st.session_state.nos_view_lo_label = selected_lo["description"]
                                pcs = db.fetch_performance_criteria_by_lo(selected_lo["id"])
                                search_query = st.text_input(
                                    "🔍 Search Performance Criteria",
                                    placeholder="Type keywords, codes, descriptions...",
                                    key="nos_view_pc_search",
                                )
                                filtered_rows = _filter_rows(pcs, search_query, ["pc_code", "description", "lo_id", "id"])
                                st.caption(
                                    f"Showing {len(filtered_rows)} record(s) for {selected_trade['name']} / {st.session_state.nos_view_trade_level_label} / {selected_unit['code']} / LO {selected_lo['lo_num']}."
                                )
                                st.dataframe(filtered_rows, width="stretch", hide_index=True)

        with sub_tab_edit:
            st.subheader("Update National Standards Content")

            update_modes = ["Trade", "Level", "Unit", "Learning Outcome", "Performance Criteria"]
            selected_mode = st.radio(
                "Edit target",
                update_modes,
                horizontal=True,
                key="nos_update_mode",
            )
            if st.session_state.get("nos_update_last_mode") != selected_mode:
                _clear_session_keys(
                    "update_trade_select",
                    "update_level_select",
                    "update_unit_select",
                    "update_lo_select",
                    "update_pc_select",
                    "update_trade_search",
                    "update_level_search",
                    "update_unit_search",
                    "update_lo_search",
                    "update_pc_search",
                    "nos_update_trade_id",
                    "nos_update_trade_name",
                    "nos_update_trade_level_id",
                    "nos_update_trade_level_label",
                    "nos_update_unit_id",
                    "nos_update_unit_label",
                    "nos_update_lo_id",
                    "nos_update_lo_label",
                    "nos_update_pc_id",
                    "nos_update_pc_label",
                )
                st.session_state.nos_update_last_mode = selected_mode

            trades = db.fetch_trades()
            if not trades:
                st.info("No trades available.")
            else:
                selected_trade, _ = _render_selectbox(
                    "Select Trade",
                    trades,
                    lambda trade: f"{trade['name']} (ID {trade['id']})",
                    key="update_trade_select",
                    none_message="No trades available.",
                    search_key="update_trade_search",
                    search_fields=["name", "id"],
                )

                if selected_trade:
                    if st.session_state.get("nos_update_trade_id") != selected_trade["id"]:
                        _clear_session_keys(
                            "update_level_select",
                            "update_unit_select",
                            "update_lo_select",
                            "update_pc_select",
                            "nos_update_trade_level_id",
                            "nos_update_trade_level_label",
                            "nos_update_unit_id",
                            "nos_update_unit_label",
                            "nos_update_lo_id",
                            "nos_update_lo_label",
                            "nos_update_pc_id",
                            "nos_update_pc_label",
                            "update_level_search",
                            "update_unit_search",
                            "update_lo_search",
                            "update_pc_search",
                        )
                    st.session_state.nos_update_trade_id = selected_trade["id"]
                    st.session_state.nos_update_trade_name = selected_trade["name"]

                    selected_level = None
                    selected_unit = None
                    selected_lo = None
                    selected_pc = None
                    breadcrumb_parts = [selected_trade["name"]]

                    with st.container(border=True):
                        st.markdown("**Breadcrumb**")
                        st.caption(selected_trade["name"])

                    if selected_mode in ("Level", "Unit", "Learning Outcome", "Performance Criteria"):
                        trade_levels = db.fetch_trade_levels(selected_trade["id"])
                        selected_level, _ = _render_selectbox(
                            "Select Level",
                            trade_levels,
                            lambda lvl: f"Level {lvl['level']}" + (f" - {lvl['display_name']}" if lvl.get("display_name") else ""),
                            key="update_level_select",
                            none_message="No trade levels found for this trade.",
                            search_key="update_level_search",
                            search_fields=["level", "display_name", "trade_id", "id"],
                        )
                        if selected_level:
                            if st.session_state.get("nos_update_trade_level_id") != selected_level["id"]:
                                _clear_session_keys(
                                    "update_unit_select",
                                    "update_lo_select",
                                    "update_pc_select",
                                    "nos_update_unit_id",
                                    "nos_update_unit_label",
                                    "nos_update_lo_id",
                                    "nos_update_lo_label",
                                    "nos_update_pc_id",
                                    "nos_update_pc_label",
                                    "update_unit_search",
                                    "update_lo_search",
                                    "update_pc_search",
                                )
                            st.session_state.nos_update_trade_level_id = selected_level["id"]
                            st.session_state.nos_update_trade_level_label = selected_level.get("display_name") or f"Level {selected_level['level']}"
                            breadcrumb_parts.append(st.session_state.nos_update_trade_level_label)

                    if selected_mode in ("Unit", "Learning Outcome", "Performance Criteria") and selected_level:
                        units = db.fetch_units_by_trade_level(selected_level["id"])
                        selected_unit, _ = _render_selectbox(
                            "Select Unit",
                            units,
                            lambda unit: f"{unit['code']}: {unit['title']}",
                            key="update_unit_select",
                            none_message="No units found for this level.",
                            search_key="update_unit_search",
                            search_fields=["code", "title", "trade_id", "trade_level_id", "id"],
                        )
                        if selected_unit:
                            if st.session_state.get("nos_update_unit_id") != selected_unit["id"]:
                                _clear_session_keys(
                                    "update_lo_select",
                                    "update_pc_select",
                                    "nos_update_lo_id",
                                    "nos_update_lo_label",
                                    "nos_update_pc_id",
                                    "nos_update_pc_label",
                                    "update_lo_search",
                                    "update_pc_search",
                                )
                            st.session_state.nos_update_unit_id = selected_unit["id"]
                            st.session_state.nos_update_unit_label = selected_unit["title"]
                            breadcrumb_parts.append(selected_unit["code"])

                    if selected_mode in ("Learning Outcome", "Performance Criteria") and selected_unit:
                        los = db.fetch_learning_outcomes_by_unit(selected_unit["id"])
                        selected_lo, _ = _render_selectbox(
                            "Select Learning Outcome",
                            los,
                            lambda lo: f"LO {lo['lo_num']}: {lo['description']}",
                            key="update_lo_select",
                            none_message="No learning outcomes found for this unit.",
                            search_key="update_lo_search",
                            search_fields=["lo_num", "description", "unit_id", "id"],
                        )
                        if selected_lo:
                            if st.session_state.get("nos_update_lo_id") != selected_lo["id"]:
                                _clear_session_keys(
                                    "update_pc_select",
                                    "nos_update_pc_id",
                                    "nos_update_pc_label",
                                    "update_pc_search",
                                )
                            st.session_state.nos_update_lo_id = selected_lo["id"]
                            st.session_state.nos_update_lo_label = selected_lo["description"]
                            breadcrumb_parts.append(f"LO {selected_lo['lo_num']}")

                    if selected_mode == "Performance Criteria" and selected_lo:
                        pcs = db.fetch_performance_criteria_by_lo(selected_lo["id"])
                        selected_pc, _ = _render_selectbox(
                            "Select Performance Criteria",
                            pcs,
                            lambda pc: f"{pc['pc_code']}: {pc['description']}",
                            key="update_pc_select",
                            none_message="No performance criteria found for this learning outcome.",
                            search_key="update_pc_search",
                            search_fields=["pc_code", "description", "lo_id", "id"],
                        )
                        if selected_pc:
                            st.session_state.nos_update_pc_id = selected_pc["id"]
                            st.session_state.nos_update_pc_label = selected_pc["description"]
                            breadcrumb_parts.append(selected_pc["pc_code"])

                    if breadcrumb_parts:
                        with st.container(border=True):
                            st.markdown("**Current Path**")
                            st.caption(" > ".join(breadcrumb_parts))

                    with st.container(border=True):
                        if selected_mode == "Trade":
                            st.caption("Editing Trade")
                            with st.form("update_trade_form"):
                                new_trade_name = st.text_input("Trade Name", value=selected_trade["name"])
                                if st.form_submit_button("Update Trade"):
                                    success, err = db.update_trade_name(selected_trade["id"], new_trade_name)
                                    if success:
                                        st.success("✅ Trade updated.")
                                        st.rerun()
                                    else:
                                        st.error(f"Trade update failed: {err}")
                        elif selected_mode == "Level":
                            if selected_level:
                                st.caption("Editing Level")
                                with st.form("update_level_form"):
                                    new_level = st.number_input("Level", min_value=1, step=1, value=int(selected_level["level"]))
                                    new_display_name = st.text_input("Display Name", value=selected_level.get("display_name") or "")
                                    if st.form_submit_button("Update Trade Level"):
                                        success, err = db.update_trade_level(selected_level["id"], new_level, new_display_name)
                                        if success:
                                            st.success("✅ Trade level updated.")
                                            st.rerun()
                                        else:
                                            st.error(f"Trade level update failed: {err}")
                            else:
                                st.info("Select a level to edit.")
                        elif selected_mode == "Unit":
                            if selected_unit:
                                st.caption("Editing Unit")
                                with st.form("update_unit_form"):
                                    new_unit_code = st.text_input("Unit Code", value=selected_unit["code"])
                                    new_unit_title = st.text_input("Unit Title", value=selected_unit["title"])
                                    if st.form_submit_button("Update Unit"):
                                        success, err = db.update_unit(selected_unit["id"], new_unit_code, new_unit_title)
                                        if success:
                                            st.success("✅ Unit updated.")
                                            st.rerun()
                                        else:
                                            st.error(f"Unit update failed: {err}")
                            else:
                                st.info("Select a unit to edit.")
                        elif selected_mode == "Learning Outcome":
                            if selected_lo:
                                st.caption("Editing Learning Outcome")
                                with st.form("update_lo_form"):
                                    new_lo_num = st.text_input("LO Number", value=selected_lo["lo_num"])
                                    new_lo_desc = st.text_area("LO Description", value=selected_lo["description"])
                                    if st.form_submit_button("Update Learning Outcome"):
                                        success, err = db.update_learning_outcome(selected_lo["id"], new_lo_num, new_lo_desc)
                                        if success:
                                            st.success("✅ Learning outcome updated.")
                                            st.rerun()
                                        else:
                                            st.error(f"Learning outcome update failed: {err}")
                            else:
                                st.info("Select a learning outcome to edit.")
                        else:
                            if selected_pc:
                                st.caption("Editing Performance Criteria")
                                with st.form("update_pc_form"):
                                    new_pc_code = st.text_input("PC Code", value=selected_pc["pc_code"])
                                    new_pc_desc = st.text_area("PC Description", value=selected_pc["description"])
                                    if st.form_submit_button("Update Performance Criteria"):
                                        success, err = db.update_performance_criterion(selected_pc["id"], new_pc_code, new_pc_desc)
                                        if success:
                                            st.success("✅ Performance criteria updated.")
                                            st.rerun()
                                        else:
                                            st.error(f"Performance criteria update failed: {err}")
                            else:
                                st.info("Select a performance criterion to edit.")

        with sub_tab_delete:
            st.subheader("Danger Zone: Remove NOS Content")
            st.warning(
                "Deleting a trade will remove its trade levels and units through database cascades. "
                "Deleting a single level will remove its units, learning outcomes, and performance criteria first, then the level."
            )

            delete_scope = st.radio(
                "What do you want to delete?",
                ["Entire Trade Family", "Single Trade Level"],
                horizontal=True,
                key="delete_nos_scope",
            )

            trades = db.fetch_trades()
            if not trades:
                st.info("No trades available to delete.")
            else:
                trade_search = st.text_input(
                    "🔎 Trade Search",
                    placeholder="Type to filter trades...",
                    key="delete_trade_search",
                )
                filtered_trades = _filter_rows(trades, trade_search, ["name", "id"])
                trade_map = {f"{trade['name']} (ID {trade['id']})": trade for trade in filtered_trades}
                if not trade_map:
                    st.info("No trades match the search.")
                else:
                    selected_trade_label = st.selectbox(
                        "Select Trade",
                        list(trade_map.keys()),
                        key="delete_nos_trade_select",
                    )
                    selected_trade = trade_map[selected_trade_label]
                    if st.session_state.get("nos_delete_trade_label") != selected_trade_label:
                        _clear_session_keys(
                            "delete_nos_trade_select",
                            "delete_nos_level_select",
                            "nos_delete_trade_level_id",
                            "delete_level_search",
                        )
                    st.session_state.nos_delete_trade_id = selected_trade["id"]
                    st.session_state.nos_delete_trade_label = selected_trade_label

                    selected_trade_level = None
                    trade_levels = []
                    if delete_scope == "Single Trade Level":
                        trade_levels = db.fetch_trade_levels(selected_trade["id"])
                        level_search = st.text_input(
                            "🔎 Level Search",
                            placeholder="Type to filter levels...",
                            key="delete_level_search",
                        )
                        filtered_levels = _filter_rows(trade_levels, level_search, ["level", "display_name", "trade_id", "id"])
                        if filtered_levels:
                            level_map = {
                                f"Level {lvl['level']}" + (f" - {lvl['display_name']}" if lvl.get("display_name") else ""): lvl
                                for lvl in filtered_levels
                            }
                            selected_level_label = st.selectbox(
                                "Select Trade Level",
                                list(level_map.keys()),
                                key="delete_nos_level_select",
                            )
                            selected_trade_level = level_map[selected_level_label]
                            if st.session_state.get("nos_delete_trade_level_label") != selected_level_label:
                                _clear_session_keys("delete_nos_level_select", "nos_delete_trade_level_id")
                            st.session_state.nos_delete_trade_level_id = selected_trade_level["id"]
                            st.session_state.nos_delete_trade_level_label = selected_level_label
                        else:
                            st.info("No trade levels found for the selected trade.")

                    if delete_scope == "Single Trade Level" and not selected_trade_level:
                        st.info("Pick a level to continue.")
                    else:
                        preview, preview_error = db.fetch_nos_delete_preview(
                            selected_trade["id"],
                            selected_trade_level["id"] if selected_trade_level else None,
                        )

                        if preview_error:
                            st.error(f"Unable to load delete preview: {preview_error}")
                        elif preview:
                            trade_label = preview.get("trade", {}).get("name", selected_trade["name"])
                            level_label = preview.get("trade_level", {}).get("display_name")
                            if selected_trade_level and not level_label:
                                level_label = f"Level {selected_trade_level.get('level')}"

                            counts = preview.get("counts", {})
                            st.markdown("##### Delete Preview")
                            if delete_scope == "Entire Trade Family":
                                st.write(f"**Target:** {trade_label}")
                                st.write(f"Trades: {counts.get('trades', 1)}")
                            else:
                                st.write(f"**Target:** {trade_label} / {level_label}")
                                st.write("Trades: 0")
                            st.write(f"Trade Levels: {counts.get('trade_levels', 0)}")
                            st.write(f"Units: {counts.get('units', 0)}")
                            st.write(f"Learning Outcomes: {counts.get('learning_outcomes', 0)}")
                            st.write(f"Performance Criteria: {counts.get('performance_criteria', 0)}")
                            if preview.get("units"):
                                st.caption("Units to be removed: " + ", ".join(u["code"] for u in preview["units"][:10]))

                            with st.form("delete_nos_form"):
                                confirm_phrase = (
                                    f"DELETE {trade_label}"
                                    if delete_scope == "Entire Trade Family"
                                    else f"DELETE {trade_label} LEVEL {selected_trade_level['level']}"
                                )
                                typed_confirm = st.text_input(
                                    "Type the confirmation phrase exactly",
                                    placeholder=confirm_phrase,
                                )
                                acknowledged = st.checkbox("I understand this action cannot be undone.")
                                delete_clicked = st.form_submit_button("Delete Selected NOS", type="primary")

                                if delete_clicked:
                                    if typed_confirm != confirm_phrase:
                                        st.error("Confirmation phrase does not match.")
                                    elif not acknowledged:
                                        st.error("You must acknowledge the warning before deleting.")
                                    else:
                                        try:
                                            if delete_scope == "Entire Trade Family":
                                                success, err = db.delete_nos_trade(selected_trade["id"])
                                            else:
                                                success, err = db.delete_nos_trade_level(selected_trade_level["id"])

                                            if success:
                                                st.success("✅ NOS content deleted successfully.")
                                                st.rerun()
                                            else:
                                                st.error(f"Deletion failed: {err}")
                                        except Exception as e:
                                            st.error(f"Deletion failed: {e}")


    # ==========================================
    # 💬 PRODUCT FEEDBACK
    # ==========================================
    with tab_feedback:
        st.subheader("System Product & UX Feedback Logs")
        st.write("UX review logs generated natively by assessors using the portal.")

        try:
            admin_client = get_admin_supabase()
            
            with st.spinner("Fetching UX reviews..."):
                response = admin_client.table("product_feedback")\
                    .select("created_at, rating, comment, source_page, assessor_role, user_profiles(email, full_name)")\
                    .order("created_at", desc=True)\
                    .execute()
            
            if response.data:
                flat_feedback = []
                for row in response.data:
                    profile = row.get('user_profiles') or {}
                    raw_created = row.get('created_at', '')
                    display_date = raw_created[:16].replace('T', ' ') if raw_created else 'N/A'
                    
                    flat_feedback.append({
                        "Date": display_date,
                        "Rating": "👍 Helpful" if row.get('rating') == 1 else "👎 Needs Improvement",
                        "Comment": row.get('comment') or "",
                        "Page Source": row.get('source_page', '').replace('_', ' ').title() if row.get('source_page') else "",
                        "Assessor Role": row.get('assessor_role') or "N/A",
                        "Assessor Name": profile.get('full_name') or "Unknown",
                        "Assessor Email": profile.get('email') or "Unknown"
                    })

                # Calculate Feedback Analytics
                f_total = len(flat_feedback)
                f_positive = sum(1 for f in flat_feedback if f['Rating'] == "👍 Helpful")
                f_negative = sum(1 for f in flat_feedback if f['Rating'] == "👎 Needs Improvement")

                c1, c2, c3 = st.columns(3)
                c1.metric("Received Feedback Logs", f_total)
                c2.metric("Helpful Reviews (👍)", f_positive)
                c3.metric("Review Interventions (👎)", f_negative)

                st.divider()

                # Display the feedback list
                st.dataframe(
                    flat_feedback,
                    column_config={
                        "Date": st.column_config.TextColumn("Date", width="small"),
                        "Rating": st.column_config.TextColumn("Rating", width="small"),
                        "Comment": st.column_config.TextColumn("Comment", width="large"),
                        "Page Source": st.column_config.TextColumn("Source Page", width="medium"),
                        "Assessor Role": st.column_config.TextColumn("Role", width="small"),
                        "Assessor Name": st.column_config.TextColumn("Name", width="medium"),
                        "Assessor Email": st.column_config.TextColumn("Email", width="medium")
                    },
                    hide_index=True,
                    width='stretch'
                )
            else:
                st.info("No user feedback records available in system database.")
                
            if st.button("🔄 Refresh Feedback Logs"):
                st.rerun()
                
        except Exception as e:
            st.error(f"Failed to query UX feedback logs: {e}")

if __name__ == "__main__":
    main()
