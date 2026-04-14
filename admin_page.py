import streamlit as st
from auth_utils import get_supabase

def main():
    st.title("⚙️ Admin Settings")
    st.subheader("Add New Assessor")
    
    with st.form("new_user"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        full_name = st.text_input("Full Name")
        submit = st.form_submit_button("Create Assessor Account")
        
        if submit:
            # 1. Create Auth User
            auth_user = get_supabase().auth.admin.create_user({
                "email": email, "password": password, "email_confirm": True
            })
            # 2. Add to Profile Table
            get_supabase().table("user_profiles").insert({
                "id": auth_user.user.id, "email": email, "role": "assessor", "full_name": full_name
            }).execute()
            st.success("User Created!")