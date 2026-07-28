import streamlit as st
import os
import database as db
from auth_utils import get_supabase, get_admin_supabase

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
        import os
        try:
            gemini_present = "INTERNAL_AI_KEY" in st.secrets or "INTERNAL_AI_KEY" in os.environ
            groq_present = "GROQ_API_KEY" in st.secrets or "GROQ_API_KEY" in os.environ
            openrouter_present = "OPENROUTER_API_KEY" in st.secrets or "OPENROUTER_API_KEY" in os.environ
            vertex_present = "vertex_ai" in st.secrets or "VERTEX_AI" in os.environ
        except Exception:
            gemini_present = "INTERNAL_AI_KEY" in os.environ
            groq_present = "GROQ_API_KEY" in os.environ
            openrouter_present = "OPENROUTER_API_KEY" in os.environ
            vertex_present = "VERTEX_AI" in os.environ

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Gemini API", "Configured" if gemini_present else "Missing")
        c2.metric("Groq API", "Configured" if groq_present else "Missing")
        c3.metric("OpenRouter API", "Configured" if openrouter_present else "Missing")
        c4.metric("Vertex AI", "Configured" if vertex_present else "Missing")

        st.divider()

        # Webhook logs
        st.subheader("Subscription Webhooks (Mock Activity)")
        mock_logs = [
            {"Date": "2026-07-18 10:00", "Provider": "Selar", "Status": "SUCCESS", "Amount": "₦7000", "Org Email": "assessor1@center.com"},
            {"Date": "2026-07-15 08:30", "Provider": "Monnify", "Status": "SUCCESS", "Amount": "₦7000", "Org Email": "tech_lead@nsqhub.org"},
            {"Date": "2026-07-14 15:45", "Provider": "Monnify", "Status": "FAILED", "Amount": "₦7000", "Org Email": "incomplete@org.com"}
        ]
        st.dataframe(mock_logs, width='stretch', hide_index=True)
        st.info("System integration webhook processing listener works externally and logs transactions to Supabase databases.")


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

        # # API & Environment Configuration
        # st.subheader("API Gateway Status")
        
        # # Determine API Presence without throwing errors on missing secrets
        # import os
        # try:
        #     gemini_present = "INTERNAL_AI_KEY" in st.secrets or "INTERNAL_AI_KEY" in os.environ
        #     groq_present = "GROQ_API_KEY" in st.secrets or "GROQ_API_KEY" in os.environ
        #     openrouter_present = "OPENROUTER_API_KEY" in st.secrets or "OPENROUTER_API_KEY" in os.environ
        #     vertex_present = "vertex_ai" in st.secrets or "VERTEX_AI" in os.environ
        # except Exception:
        #     gemini_present = "INTERNAL_AI_KEY" in os.environ
        #     groq_present = "GROQ_API_KEY" in os.environ
        #     openrouter_present = "OPENROUTER_API_KEY" in os.environ
        #     vertex_present = "VERTEX_AI" in os.environ

        # c1, c2, c3, c4 = st.columns(4)
        # c1.metric("Gemini API", "Configured" if gemini_present else "Missing")
        # c2.metric("Groq API", "Configured" if groq_present else "Missing")
        # c3.metric("OpenRouter API", "Configured" if openrouter_present else "Missing")
        # c4.metric("Vertex AI", "Configured" if vertex_present else "Missing")

        # st.divider()

        # # Webhook logs
        # st.subheader("Subscription Webhooks (Mock Activity)")
        # mock_logs = [
        #     {"Date": "2026-07-18 10:00", "Provider": "Selar", "Status": "SUCCESS", "Amount": "₦7000", "Org Email": "assessor1@center.com"},
        #     {"Date": "2026-07-15 08:30", "Provider": "Monnify", "Status": "SUCCESS", "Amount": "₦7000", "Org Email": "tech_lead@nsqhub.org"},
        #     {"Date": "2026-07-14 15:45", "Provider": "Monnify", "Status": "FAILED", "Amount": "₦7000", "Org Email": "incomplete@org.com"}
        # ]
        # st.dataframe(mock_logs, width='stretch', hide_index=True)
        # st.info("System integration webhook processing listener works externally and logs transactions to Supabase databases.")


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
        # Load and Cache NOS Metadata
        if "admin_nos_cache" not in st.session_state:
            with st.spinner("Fetching national occupational standards cache..."):
                try:
                    admin_client = get_admin_supabase()
                    st.session_state.admin_nos_cache = {
                        "Trades": admin_client.table("trades").select("*").execute().data,
                        "Trade Levels": admin_client.table("trade_levels").select("*").execute().data,
                        "Units": admin_client.table("units").select("*").execute().data,
                        "Learning Outcomes": admin_client.table("learning_outcomes").select("*").execute().data,
                        "Performance Criteria": admin_client.table("performance_criteria").select("*").execute().data,
                    }
                except Exception as e:
                    st.error(f"Failed to sync standard repositories: {e}")
                    st.session_state.admin_nos_cache = {"Trades": [], "Trade Levels": [], "Units": [], "Learning Outcomes": [], "Performance Criteria": []}

        sub_tab_view, sub_tab_edit = st.tabs(["👁️ View Database", "✍️ Edit Content"])

        with sub_tab_view:
            c1, c2 = st.columns([3, 1])
            with c1:
                table_key = st.selectbox("Select Standards Table", list(st.session_state.admin_nos_cache.keys()))
            with c2:
                st.write("") # Padding spacer
                if st.button("🔄 Reload Standards Cache"):
                    del st.session_state.admin_nos_cache
                    st.rerun()

            data = st.session_state.admin_nos_cache.get(table_key, [])
            
            if data:
                # Direct List Search Filtering natively without Pandas
                search_query = st.text_input(f"🔍 Search Standard Criteria ({table_key})", placeholder="Type keywords, codes, descriptions...")
                
                if search_query:
                    q = search_query.lower()
                    filtered_data = []
                    for item in data:
                        match = False
                        for val in item.values():
                            if q in str(val).lower():
                                match = True
                                break
                        if match:
                            filtered_data.append(item)
                else:
                    filtered_data = data
                
                st.dataframe(filtered_data, width='stretch', hide_index=True)
            else:
                st.info("No standards data found.")

        with sub_tab_edit:
            st.subheader("Edit National Standards Content")
            edit_type = st.radio("Choose standard scope to modify:", ["Unit", "Learning Outcome", "Delete NOS"], horizontal=True)

            if edit_type == "Unit":
                units = st.session_state.admin_nos_cache.get("Units", [])
                unit_options = {f"{u['code']}: {u['title']}": u for u in units}
                
                if unit_options:
                    selected_label = st.selectbox("Select Unit to Modify", list(unit_options.keys()))
                    selected_unit = unit_options[selected_label]
                    
                    with st.form("edit_unit_form"):
                        new_code = st.text_input("Unit Code Identifier", value=selected_unit['code'])
                        new_title = st.text_input("Unit Title", value=selected_unit['title'])
                        
                        if st.form_submit_button("Update Standard Unit"):
                            try:
                                admin_client = get_admin_supabase()
                                admin_client.table("units").update({"code": new_code, "title": new_title}).eq("id", selected_unit['id']).execute()
                                st.success("✅ Unit configurations updated successfully!")
                                del st.session_state.admin_nos_cache 
                                st.rerun()
                            except Exception as e:
                                st.error(f"Unit update failed: {e}")
                else:
                    st.info("No units available under current standards cache.")

            elif edit_type == "Learning Outcome":
                los = st.session_state.admin_nos_cache.get("Learning Outcomes", [])
                lo_options = {f"ID {lo['id']} (Unit ID: {lo['unit_id']}): {lo['description'][:60]}...": lo for lo in los}
                
                if lo_options:
                    selected_label = st.selectbox("Select LO to Modify", list(lo_options.keys()))
                    selected_lo = lo_options[selected_label]
                    
                    with st.form("edit_lo_form"):
                        new_num = st.text_input("LO Number Code", value=selected_lo.get('lo_num', ''))
                        new_desc = st.text_area("LO Detailed Description", value=selected_lo['description'])
                        
                        if st.form_submit_button("Update Learning Outcome"):
                            try:
                                admin_client = get_admin_supabase()
                                admin_client.table("learning_outcomes").update({"lo_num": new_num, "description": new_desc}).eq("id", selected_lo['id']).execute()
                                st.success("✅ Learning Outcome standard updated!")
                                del st.session_state.admin_nos_cache
                                st.rerun()
                            except Exception as e:
                                st.error(f"LO update failed: {e}")
                else:
                    st.info("No Learning Outcomes available.")

            elif edit_type == "Delete NOS":
                st.subheader("Danger Zone: Remove NOS Content")
                st.warning(
                    "Deleting a trade will remove its trade levels and units through database cascades. "
                    "Deleting a single level will remove its units, learning outcomes, and performance criteria first, then the level."
                )

                delete_scope = st.radio(
                    "What do you want to delete?",
                    ["Entire Trade Family", "Single Trade Level"],
                    horizontal=True,
                    key="delete_nos_scope"
                )

                trades = st.session_state.admin_nos_cache.get("Trades", [])
                if not trades:
                    st.info("No trades available to delete.")
                else:
                    trade_map = {f"{trade['name']} (ID {trade['id']})": trade for trade in trades}
                    selected_trade_label = st.selectbox(
                        "Select Trade",
                        list(trade_map.keys()),
                        key="delete_nos_trade_select"
                    )
                    selected_trade = trade_map[selected_trade_label]

                    selected_trade_level = None
                    trade_levels = []
                    if delete_scope == "Single Trade Level":
                        trade_levels = db.fetch_trade_levels(selected_trade["id"])
                        if trade_levels:
                            level_map = {
                                f"Level {lvl['level']}" + (f" - {lvl['display_name']}" if lvl.get("display_name") else ""): lvl
                                for lvl in trade_levels
                            }
                            selected_level_label = st.selectbox(
                                "Select Trade Level",
                                list(level_map.keys()),
                                key="delete_nos_level_select"
                            )
                            selected_trade_level = level_map[selected_level_label]
                        else:
                            st.info("No trade levels found for the selected trade.")

                    if delete_scope == "Single Trade Level" and not selected_trade_level:
                        st.info("Pick a level to continue.")
                    else:
                        preview, preview_error = db.fetch_nos_delete_preview(
                            selected_trade["id"],
                            selected_trade_level["id"] if selected_trade_level else None
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
                                    placeholder=confirm_phrase
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
                                                if "admin_nos_cache" in st.session_state:
                                                    del st.session_state.admin_nos_cache
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
