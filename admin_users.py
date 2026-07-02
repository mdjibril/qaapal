import streamlit as st
from auth_utils import get_supabase, get_admin_supabase
import pandas as pd
import database as db

def main():
    st.title("👥 User Management")
    
    tab_list, tab_create = st.tabs(["📋 User Directory", "➕ Create New Account"])
    
    with tab_list:
        st.subheader("System Users")
        try:
            admin_client = get_admin_supabase()
            # Fetch user profiles joined with their organization data
            response = admin_client.table("user_profiles")\
                .select("id, email, full_name, role, org_id, organizations(subscription_tier, credits_balance)")\
                .order("full_name")\
                .execute()
            
            if response.data:
                # Flatten the nested organization data for the DataFrame
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
                
                df = pd.DataFrame(flat_data)
                
                # Display Quick Metrics
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Total Users", len(df))
                m2.metric("Assessors", len(df[df['Role'] == 'assessor']))
                m3.metric("Students", len(df[df['Role'] == 'student']))
                m4.metric("Avg Credits", int(df['Credits'].mean()) if not df.empty else 0)
                
                # Display the user list
                st.dataframe(df.drop(columns=['id', 'org_id']), width="stretch")
                
                # --- PLAN MANAGEMENT SECTION ---
                st.markdown("---")
                st.subheader("🛠️ Plan & Credit Management")
                
                # Filter out admins for management to prevent self-lockout
                manageable_df = df[df['Role'] != 'admin']
                
                if not manageable_df.empty:
                    selected_users = st.multiselect(
                        "Select Users to Update (Batch or Single)",
                        options=manageable_df.to_dict('records'),
                        format_func=lambda x: f"{x['Full Name']} ({x['Email']}) | Plan: {x['Plan']} | Credits: {x['Credits']}"
                    )
                    
                    if selected_users:
                        col_plan, col_cred = st.columns(2)
                        
                        with col_plan:
                            new_tier = st.selectbox(
                                "Select Target Plan", 
                                ['free', 'platform_pass', 'pro', 'enterprise'],
                                format_func=lambda x: x.replace('_', ' ').title()
                            )
                            if st.button(f"Apply {new_tier.title()} Plan"):
                                with st.spinner("Updating subscription tiers..."):
                                    for user in selected_users:
                                        if user['org_id']:
                                            db.upgrade_org_tier(user['org_id'], new_tier)
                                    st.success("Plan update complete!")
                                    st.rerun()
                                    
                        with col_cred:
                            if len(selected_users) == 1:
                                current_cred = selected_users[0]['Credits']
                                new_credits = st.number_input("Set Credit Balance", min_value=0, value=int(current_cred), step=1)
                                if st.button("Update Credits"):
                                    if selected_users[0]['org_id']:
                                        success, err = db.update_org_credits(selected_users[0]['org_id'], new_credits)
                                        if success:
                                            st.success("Credits updated successfully!")
                                            st.rerun()
                                        else:
                                            st.error(f"Failed to update credits: {err}")
                            else:
                                st.info("Credit adjustments must be done for a single user at a time.")
                else:
                    st.info("No student or assessor accounts found to manage.")

                if st.button("Refresh List"):
                    st.rerun()
            else:
                st.info("No users found in the directory.")
        except Exception as e:
            st.error(f"Error loading user directory: {e}")

    with tab_create:
        st.subheader("Add New User")
        with st.form("new_user_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                email = st.text_input("Email Address")
                password = st.text_input("Password", type="password", help="Minimum 6 characters")
                full_name = st.text_input("Full Name (e.g. John Doe)")
                role = st.selectbox("System Role", ["assessor", "student"], index=0)
            
            with col2:
                org_name = st.text_input("Organization / Center Name")
                primary_trade = st.text_input("Primary Trade / Sector")
                marketing_source = st.selectbox(
                    "Marketing Source",
                    ["Direct Admin Entry", "LinkedIn", "WhatsApp Group", "NBTE/NSQ Event", "Word of Mouth", "Other"]
                )
                report_volume = st.selectbox(
                    "Expected Monthly Volume",
                    ["1-10 reports", "11-50 reports", "51-100 reports", "100+ reports"]
                )

            st.info("💡 Creating an account here bypasses email confirmation. The user will be linked to a new organization workspace automatically.")
            submit = st.form_submit_button("Create Account")
            
            if submit:
                if not email or not password or not full_name or not org_name:
                    st.error("Please fill in all required fields.")
                else:
                    try:
                        admin_client = get_admin_supabase()
                        
                        # 1. Create Auth User via Service Role
                        # We pass the metadata so the DB trigger handle_new_user_setup can process it
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

                        # 2. Update the role specifically if it's different from the default 'assessor'
                        # The trigger creates the profile, so we use an update to set the specific role chosen
                        admin_client.table("user_profiles").update({
                            "role": role
                        }).eq("id", auth_user.user.id).execute()

                        # 3. Log the activity for the admin
                        st.success(f"Successfully created {role} account for {full_name}!")
                        st.balloons()
                        
                        # Optional: Log to admin audit trail if you implement one later
                        admin_client.table("assessment_reports").insert({
                            "student_name": "SYSTEM LOG",
                            "report_text": f"Admin created new user: {email} with role {role}",
                            "created_by": st.session_state.user_session.id
                        }).execute()
                    except Exception as e:
                        st.error(f"Failed to create user: {e}")