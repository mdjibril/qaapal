import streamlit as st
from supabase import create_client

def get_supabase():
    url = st.secrets["connections"]["supabase"]["DATABASE_URL"]
    key = st.secrets["connections"]["supabase"]["API_KEY"]
    return create_client(url, key)

def get_user_role(user_id):
    supabase = get_supabase()
    response = supabase.table("user_profiles").select("role").eq("id", user_id).single().execute()
    return response.data.get("role") if response.data else "assessor"

def check_auth():
    return st.session_state.get('user_session', None)

def login_form():
    st.title("🔐 Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        try:
            user = get_supabase().auth.sign_in_with_password({"email": email, "password": password})
            st.session_state['user_session'] = user.user
            st.session_state['user_role'] = get_user_role(user.user.id)
            st.rerun()
        except Exception as e:
            st.error("Invalid credentials.")
