import streamlit as st
from auth_utils import get_supabase, get_admin_supabase

def main():
    st.title("⚙️ Admin Settings")
    st.subheader("Add New Assessor")
    
    with st.form("new_user"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        full_name = st.text_input("Full Name")
        submit = st.form_submit_button("Create Assessor Account")
        
        if submit:
            try:
                # Use the Admin client for auth and database insertion to bypass RLS
                admin_client = get_admin_supabase()
                
                # 1. Create Auth User
                auth_user = admin_client.auth.admin.create_user({
                    "email": email, "password": password, "email_confirm": True
                })
                # 2. Add to Profile Table
                admin_client.table("user_profiles").insert({
                    "id": auth_user.user.id, "email": email, "role": "assessor", "full_name": full_name
                }).execute()
                st.success(f"Assessor account for {email} created successfully!")
            except Exception as e:
                st.error(f"Failed to create user: {e}")