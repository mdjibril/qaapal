import streamlit as st
import time
from supabase import create_client, ClientOptions

def get_supabase():
    # Use st.secrets with a default to avoid crashes during debug
    url = st.secrets.get("connections", {}).get("supabase", {}).get("PROJECT_URL")
    key = st.secrets.get("connections", {}).get("supabase", {}).get("ANON_KEY")
    
    if not url or not key:
        st.error("Secrets missing! Check Streamlit Cloud Settings > Secrets.")
        st.stop() # Stops the app here so you can see the error
        
    client = _create_base_client(url, key)
    
    # Attach the authenticated session token if it exists
    session = st.session_state.get("supabase_session")
    if session:
        # Check if the token is expired or about to expire (within 60 seconds)
        # Supabase session objects include 'expires_at' as a Unix timestamp
        if hasattr(session, 'expires_at') and session.expires_at < time.time() + 60:
            try:
                # Attempt to refresh the session using the refresh_token
                refresh_res = client.auth.refresh_session(session.refresh_token)
                st.session_state["supabase_session"] = refresh_res.session
                st.session_state["user_session"] = refresh_res.user
                session = refresh_res.session
            except Exception:
                # If refresh fails (e.g. refresh token also expired), force a logout
                st.session_state.clear()
                st.rerun()

        client.postgrest.auth(session.access_token)

    return client

@st.cache_resource
def _create_base_client(url, key):
    """Internal cached helper to maintain a single connection pool."""
    return create_client(url, key, options=ClientOptions(postgrest_client_timeout=60))

@st.cache_resource
def get_admin_supabase():
    """Returns a Supabase client initialized with the Service Role Key for administrative tasks."""
    url = st.secrets.get("connections", {}).get("supabase", {}).get("PROJECT_URL")
    key = st.secrets.get("connections", {}).get("supabase", {}).get("SERVICE_ROLE_KEY")
    
    if not url or not key:
        st.error("SERVICE_ROLE_KEY is missing from secrets! This is required for admin tasks.")
        st.stop()
        
    return create_client(url, key, options=ClientOptions(postgrest_client_timeout=60))

def get_user_role(user_id):
    # Use the admin client to bypass RLS policies when checking user roles.
    # This ensures the login process can always identify if a user is an admin or assessor.
    supabase = get_admin_supabase()
    try:
        # Fetch the role from the profile table
        response = supabase.table("user_profiles").select("role").eq("id", user_id).execute()
        if response.data and len(response.data) > 0:
            return response.data[0].get("role", "assessor")
        return "assessor"
    except Exception as e:
        print(f"Role fetch error: {e}")
        return "assessor"


def check_auth():
    return st.session_state.get('user_session', None)

def login_form():
    st.title("🔐 Login to NSQ Portal")
    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_password")
    
    if st.button("Login"):
        supabase = get_supabase()
        try:
            # 1. Sign In
            auth_res = get_supabase().auth.sign_in_with_password({"email": email, "password": password})
            
            # 2. Set Session
            st.session_state['user_session'] = auth_res.user
            st.session_state['supabase_session'] = auth_res.session
            
            # 3. Fetch Role (using the debug-friendly version above)
            st.session_state['user_role'] = get_user_role(auth_res.user.id)
            
            # Fetch full name and store it in session state
            admin_client = get_admin_supabase() # Use admin client to bypass RLS for profile fetch
            profile_response = admin_client.table("user_profiles").select("full_name").eq("id", auth_res.user.id).execute()
            if profile_response.data and len(profile_response.data) > 0:
                st.session_state['assessor_full_name'] = profile_response.data[0].get("full_name")
            else:
                st.session_state['assessor_full_name'] = "Assessor" # Default if not found
            
            st.success("Login successful!")

            st.rerun()
            
        except Exception as e:
            st.error(f"Login failed: {e}")
