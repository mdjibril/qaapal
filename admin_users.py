import streamlit as st
from auth_utils import get_supabase, get_admin_supabase
import pandas as pd

def main():
    st.title("👥 User Management")
    
    tab_list, tab_create = st.tabs(["📋 User Directory", "➕ Create New Account"])
    
    with tab_list:
        st.subheader("System Users")
        try:
            admin_client = get_admin_supabase()
            # Fetch all user profiles ordered by name
            response = admin_client.table("user_profiles").select("email, full_name, role").order("full_name").execute()
            
            if response.data:
                df = pd.DataFrame(response.data)
                
                # Display Quick Metrics
                m1, m2, m3 = st.columns(3)
                m1.metric("Total Users", len(df))
                m2.metric("Assessors", len(df[df['role'] == 'assessor']))
                m3.metric("Students", len(df[df['role'] == 'student']))
                
                # Display the user list
                st.dataframe(df, use_container_width=True)
                
                if st.button("Refresh List"):
                    st.rerun()
            else:
                st.info("No users found in the directory.")
        except Exception as e:
            st.error(f"Error loading user directory: {e}")

    with tab_create:
        st.subheader("Add New User")
        with st.form("new_user_form", clear_on_submit=True):
            email = st.text_input("Email Address")
            password = st.text_input("Password", type="password", help="Minimum 6 characters")
            full_name = st.text_input("Full Name")
            role = st.selectbox("Role", ["assessor", "student"], index=0)
            submit = st.form_submit_button("Create Account")
            
            if submit:
                if not email or not password or not full_name:
                    st.error("Please fill in all required fields.")
                else:
                    try:
                        admin_client = get_admin_supabase()
                        # 1. Create Auth User via Service Role (bypasses confirmation emails if email_confirm is True)
                        auth_user = admin_client.auth.admin.create_user({
                            "email": email, "password": password, "email_confirm": True
                        })
                        # 2. Add the metadata record to the profile table
                        admin_client.table("user_profiles").insert({
                            "id": auth_user.user.id, "email": email, "role": role, "full_name": full_name
                        }).execute()
                        st.success(f"Successfully created {role} account for {full_name}!")
                    except Exception as e:
                        st.error(f"Failed to create user: {e}")