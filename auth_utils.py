import os
import streamlit as st
import time
from supabase import create_client, ClientOptions

def _get_secret(key_path, env_key):
    """
    Helper to fetch configuration. 
    1. Tries Streamlit Secrets (for local & Streamlit Cloud)
    2. Falls back to OS Environment Variables (for Railway/Docker)
    """
    try:
        # We use a nested get to avoid triggering the StreamlitSecretNotFoundError 
        # that occurs when using square bracket [k] access on an empty secrets object.
        val = st.secrets
        for k in key_path:
            val = val.get(k)
            if val is None:
                break
        if val is not None:
            return val
    except Exception:
        # If st.secrets fails for any reason (missing file, etc.), we fall back
        pass

    # Fallback to OS Environment Variables (Railway/Docker)
    raw_val = os.environ.get(env_key) or os.environ.get(env_key.upper())
    if raw_val and isinstance(raw_val, str):
        # Strip whitespace and any accidental wrapping quotes added by UI
        return raw_val.strip().strip('"').strip("'")
    return raw_val

def get_supabase():
    url = _get_secret(["connections", "supabase", "PROJECT_URL"], "connections__supabase__PROJECT_URL")
    key = _get_secret(["connections", "supabase", "ANON_KEY"], "connections__supabase__ANON_KEY")
    
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
    url = _get_secret(["connections", "supabase", "PROJECT_URL"], "connections__supabase__PROJECT_URL")
    key = _get_secret(["connections", "supabase", "SERVICE_ROLE_KEY"], "connections__supabase__SERVICE_ROLE_KEY")
    
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
    st.title("🔐 QAAPAL Portal")
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        if st.button("Login"):
            try:
                supabase = get_supabase()
                auth_res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                _finalize_login(auth_res)
            except Exception as e:
                st.error(f"Login failed: {e}")

    with tab2:
        new_email = st.text_input("Email", key="signup_email")
        new_password = st.text_input("Password", type="password", key="signup_pw")
        full_name = st.text_input("Full Name (e.g. John Doe)")
        if st.button("Create Free Account"):
            try:
                supabase = get_supabase()
                auth_res = supabase.auth.sign_up({
                    "email": new_email, 
                    "password": new_password,
                    "options": {"data": {"full_name": full_name}}
                })
                st.success("Registration successful! You can now login.")
            except Exception as e:
                st.error(f"Sign up failed: {e}")

def _finalize_login(auth_res):
    st.session_state['user_session'] = auth_res.user
    st.session_state['supabase_session'] = auth_res.session
    
    admin_client = get_admin_supabase()
    # Fetch profile and organization data
    profile_res = admin_client.table("user_profiles")\
        .select("role, org_role, full_name, organizations(id, subscription_tier, credits_balance, master_api_key, subscription_start_date)")\
        .eq("id", auth_res.user.id).execute()
    
    # If profile is missing (e.g., trigger failed or delayed), attempt to initialize it (Self-Healing)
    if not profile_res.data:
        try:
            # metadata is stored in user_metadata for the authenticated user object
            meta = getattr(auth_res.user, 'user_metadata', {}) or {}
            full_name = meta.get('full_name', 'New User')
            
            admin_client.table("user_profiles").upsert({
                "id": auth_res.user.id,
                "email": auth_res.user.email,
                "full_name": full_name,
                "role": "assessor"
            }).execute()
            
            # Re-fetch to include data potentially added by the trigger in the background
            profile_res = admin_client.table("user_profiles")\
                .select("role, org_role, full_name, organizations(id, subscription_tier, credits_balance, master_api_key)")\
                .eq("id", auth_res.user.id).execute()
        except Exception as e:
            st.error(f"Login error: Could not initialize user profile. {e}")
            return

    if not profile_res.data:
        st.error("Login failed: Profile data is unavailable.")
        return

    prof = profile_res.data[0]
    # Handle case where organizations join might be None
    org = prof.get('organizations') or {}
    
    st.session_state['user_role'] = prof.get('role', 'assessor') # App Superadmin check
    st.session_state['org_role'] = prof.get('org_role', 'member') # Org level role
    st.session_state['assessor_full_name'] = prof.get('full_name')
    st.session_state['org_id'] = org.get('id', None)
    st.session_state['subscription_tier'] = org.get('subscription_tier', 'free')
    st.session_state['credits_balance'] = org.get('credits_balance', 0)
    st.session_state['master_api_key'] = org.get('master_api_key')
    st.session_state['subscription_start_date'] = org.get('subscription_start_date')
    
    st.rerun()
