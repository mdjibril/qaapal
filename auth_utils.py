import os
import streamlit as st
import time
from supabase import create_client, ClientOptions

def get_secret(key_path, env_key):
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
            # Using direct access inside try-except to handle AttrDict behavior
            val = val[k]
        
        # Handle case where val might be an empty AttrDict/Dict
        if isinstance(val, (dict, st.runtime.secrets.AttrDict)) and not val:
            pass
        elif val is not None:
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
    url = get_secret(["connections", "supabase", "PROJECT_URL"], "connections__supabase__PROJECT_URL")
    key = get_secret(["connections", "supabase", "ANON_KEY"], "connections__supabase__ANON_KEY")
    
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
    url = get_secret(["connections", "supabase", "PROJECT_URL"], "connections__supabase__PROJECT_URL")
    key = get_secret(["connections", "supabase", "SERVICE_ROLE_KEY"], "connections__supabase__SERVICE_ROLE_KEY")
    
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

def _get_password_strength(pw):
    """Calculates password strength score and feedback."""
    if not pw: return 0.0, "Empty", "gray", []
    score = 0
    missing = []
    if len(pw) >= 8: score += 1
    else: missing.append("8+ characters")
    if any(c.isupper() for c in pw): score += 1
    else: missing.append("uppercase")
    if any(c.islower() for c in pw): score += 1
    else: missing.append("lowercase")
    if any(c.isdigit() for c in pw): score += 1
    else: missing.append("number")
    if any(not c.isalnum() for c in pw): score += 1
    else: missing.append("special character")
    
    mapping = {0: (0.05, "Very Weak", "red"), 1: (0.2, "Weak", "orange"), 2: (0.4, "Fair", "yellow"), 3: (0.6, "Good", "blue"), 4: (0.8, "Strong", "green"), 5: (1.0, "Very Strong", "green")}
    return mapping[score] + (missing,)

def login_form():
    st.title("🔐 NSQ-Assessment Portal")
    
    # Deep Linking: Check if the landing page or a reset link requested a specific mode
    modes = ["Login", "Sign Up", "Forgot Password"]
    default_mode = st.session_state.get("auth_mode", "Login")
    default_index = modes.index(default_mode) if default_mode in modes else 0

    auth_choice = st.radio("Mode", modes, index=default_index, horizontal=True, label_visibility="collapsed")

    if auth_choice == "Login":
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        if st.button("Login"):
            try:
                supabase = get_supabase()
                auth_res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                _finalize_login(auth_res)
            except Exception as e:
                st.error(f"Login failed: {e}")

    elif auth_choice == "Sign Up":
        new_email = st.text_input("Email", key="signup_email")
        new_password = st.text_input("Password", type="password", key="signup_pw")

        # Real-time Password Strength Feedback
        if new_password:
            strength, label, color, missing = _get_password_strength(new_password)
            st.progress(strength, text=f"Strength: {label}")
            if missing and strength < 0.8:
                st.caption(f"💡 Suggestion: Try adding {', '.join(missing)}")

        new_password_confirm = st.text_input("Confirm Password", type="password", key="signup_pw_confirm")
        if new_password and new_password_confirm:
            if new_password != new_password_confirm:
                st.error("⚠️ Passwords do not match")
            else:
                st.success("✅ Passwords match")

        full_name = st.text_input("Full Name (e.g. John Doe)")
        org_name = st.text_input("Organization / Assessment Center Name", help="This will be used for your workspace branding.")
        
        col_a, col_b = st.columns(2)
        with col_a:
            marketing_source = st.selectbox(
                "How did you hear about us?",
                ["Select an option", "LinkedIn", "WhatsApp Group", "NBTE/NSQ Event", "Word of Mouth", "Search Engine", "Other"]
            )
        with col_b:
            report_volume = st.selectbox(
                "Monthly report volume?",
                ["1-10 reports", "11-50 reports", "51-100 reports", "100+ reports"]
            )

        primary_trade_choice = st.text_input("Primary Trade / Sector", placeholder="e.g., ICT, Welding, Fashion Design")
        
        tos_consent = st.checkbox("I agree to the Terms of Service and Privacy Policy")
        
        # Determine the redirect URL for email confirmation
        site_url = get_secret(["connections", "supabase", "SITE_URL"], "SITE_URL") or "https://app.nsqassessment.com.ng"

        if st.button("Create Free Account"):
            # Validation Logic
            if new_password != new_password_confirm:
                st.error("Passwords do not match.")
            elif len(new_password) < 6:
                st.error("Password must be at least 6 characters.")
            elif not full_name or not org_name or marketing_source == "Select an option":
                st.error("Please fill in all required fields to help us set up your workspace.")
            elif not tos_consent:
                st.error("You must agree to the Terms of Service to continue.")
            else:
                # Proceed with Registration
                try:
                    supabase = get_supabase()
                    auth_res = supabase.auth.sign_up({
                        "email": new_email, 
                        "password": new_password,
                        "options": {
                            "data": {
                                "full_name": full_name,
                                "org_name": org_name,
                                "marketing_source": marketing_source,
                                "primary_trade": primary_trade_choice,
                                "monthly_volume": report_volume
                            },
                            "email_redirect_to": site_url
                        }
                    })
                    st.success("Registration successful! Please check your email to confirm your account before logging in.")
                except Exception as e:
                    st.error(f"Sign up failed: {e}")

    elif auth_choice == "Forgot Password":
        reset_email = st.text_input("Enter your registered email", key="reset_email_input")
        site_url = get_secret(["connections", "supabase", "SITE_URL"], "SITE_URL") or "https://app.nsqassessment.com.ng"
        
        if st.button("Send Reset Link"):
            try:
                supabase = get_supabase()
                supabase.auth.reset_password_for_email(reset_email, {"redirect_to": site_url})
                st.success(f"If an account exists for {reset_email}, a password reset link has been sent.")
            except Exception as e:
                st.error(f"Error: {e}")

def reset_password_form():
    """Specialized form shown only when a recovery session is active."""
    st.title("🔄 Reset Your Password")
    st.info("Please enter your new password below.")
    
    new_pw = st.text_input("New Password", type="password")
    confirm_pw = st.text_input("Confirm New Password", type="password")
    
    if st.button("Update Password"):
        if new_pw != confirm_pw:
            st.error("Passwords do not match.")
        elif len(new_pw) < 6:
            st.error("Password must be at least 6 characters.")
        else:
            try:
                supabase = get_supabase()
                supabase.auth.update_user({"password": new_pw})
                st.success("Password updated successfully! You can now login.")
                time.sleep(2)
                st.session_state.clear()
                st.rerun()
            except Exception as e:
                st.error(f"Failed to update password: {e}")

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
