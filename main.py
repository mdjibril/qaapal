import streamlit as st
from auth_utils import check_auth, login_form, get_secret, reset_password_form, finalize_session
import dashboard, history, admin_nos, admin_users, personal_statement, witness_statement, subscription_page, database as db
from ai_utils import validate_and_generate

st.set_page_config(
    page_title="NSQAssessment App | AI-Powered Reports",
    page_icon="⚡", # You can use an emoji or a path to an image file
    layout="wide",
    initial_sidebar_state="expanded"
)

# Callback function for API key inputs
def update_api_key_session(key_name):
    """Callback to update st.session_state.target_key when an API key input changes."""
    if st.session_state[key_name]:
        # Split by comma to support rotation even for BYOK users
        st.session_state.target_keys = [k.strip() for k in st.session_state[key_name].split(',') if k.strip()]
    else:
        st.session_state.target_keys = []

def clear_previews_on_trade_change():
    """Clears generated statement previews and all checkbox selections when the trade changes."""
    # 1. Clear generated report/statement previews
    keys_to_clear = [
        'current_generated_statement', 
        'current_witness_statement',
        'student_selected_pcs',
        'witness_selected_pcs',
        'current_selected_pcs'
    ]
    for key in keys_to_clear:
        st.session_state.pop(key, None)
        
    # 2. Clear individual checkbox states and master unit checkboxes
    prefixes = ('stmt_chk_', 'wit_chk_', 'chk_', 'stmt_unit_all_', 'wit_unit_all_', 'unit_all_')
    keys_to_del = [k for k in st.session_state.keys() if k.startswith(prefixes)]
    for k in keys_to_del:
        del st.session_state[k]

# Define cached functions at the top level to avoid re-definition issues
@st.cache_data(ttl=600)
def get_cached_trades():
    return db.fetch_trades()

# --- DEEP LINKING LOGIC ---
if "intent" in st.query_params:
    intent = st.query_params.get("intent")
    if intent == "signup":
        st.session_state["auth_mode"] = "Sign Up"
    elif intent == "earlybird":
        st.session_state["auth_mode"] = "Sign Up"
        st.session_state["promo_code"] = "EARLYBIRD_100"
    elif intent == "recovery":
        # This is a fallback if the fragment detection isn't enough
        st.session_state["reset_mode"] = True
    # Clear params to prevent the UI from being locked to one mode on refresh
    st.query_params.clear()

# --- PASSWORD RECOVERY DETECTION ---
# When clicking a reset link, Supabase redirects with a fragment (#) or token.
# We rely on the 'intent=recovery' query parameter for explicit triggering.
# The Supabase client handles the internal token exchange automatically.
if not st.session_state.get('user_session') and not st.session_state.get('reset_mode'):
    try:
        client = db.get_supabase()
        session_res = client.auth.get_session()
        if session_res:
            finalize_session(session_res.user, session_res)
    except Exception:
        pass

if st.session_state.get("reset_mode"):
    reset_password_form()
elif not check_auth():
    login_form()
else:
    role = st.session_state.get('user_role', 'assessor')
    tier = st.session_state.get('subscription_tier', 'free')
    credits = st.session_state.get('credits_balance', 0)
    is_superadmin = (role == 'admin')
    is_platform_pass_expired = db.check_platform_pass_expiry()

    # If platform_pass is expired, treat them as free tier for UI/logic purposes
    if tier == 'platform_pass' and is_platform_pass_expired:
        st.session_state['subscription_tier'] = 'free'
        tier = 'free' # Update local variable for immediate use
        st.session_state['credits_balance'] = 0 # Ensure no credits are shown
        credits = 0 # Update local variable
    
    # --- CENTRALIZED SIDEBAR ---
    st.sidebar.title(f"🚀 NSQ Portal v1.0.5")
    
    # Sidebar Billing Widget
    with st.sidebar.container(border=True):
        if is_platform_pass_expired:
            st.error("Platform Pass Expired! Please renew.")
            if st.button("Renew Platform Pass", width="stretch"):
                db.mock_payment_dialog(st.session_state.org_id)
        else:
            col_plan, col_cred = st.columns(2)
            plan_display = "SUPERADMIN" if is_superadmin else tier.upper()
            col_plan.caption(f"**Plan:** {plan_display}")
            
            credit_display = "∞" if (is_superadmin or tier != 'free') else credits
            col_cred.caption(f"**Credits:** {credit_display}")
            
            if not is_superadmin and tier == 'free' and credits == 0:
                st.error("Out of credits! Upgrade to Platform Pass.")
                selar_base = get_secret(["payments", "selar_link"], "payments__selar_link") or "https://selar.com/nsqassessment-platformpass"
                user_email = st.session_state.user_session.email
                upgrade_link = f"{selar_base}?email={user_email}"
                st.link_button("🚀 Upgrade Now", upgrade_link, width="stretch")

    st.session_state.assessor_name = st.session_state.get('assessor_full_name', 'Jibril Dauda Muhammad')
    name = st.session_state.assessor_name
    a_id = st.session_state.get('assessor_id', 'QAA/XXXX/ICT')

    st.sidebar.caption(f"Logged in as 👤: {role.capitalize()} <<>> Name: {name.capitalize()}")
    
    # st.sidebar.caption(f"👤 Assessor: {st.session_state.assessor_name}")
    # st.sidebar.caption(f"🆔 ID: {st.session_state.assessor_id}")
    
    # Trade Selection Logic
    trades_df = get_cached_trades()

    if not trades_df.empty:
        # We use index to ensure the selector stays on the same item after refresh
        selected_name = st.sidebar.selectbox(
            "Select Trade",
            trades_df['name'],
            key="global_trade_select",
            on_change=clear_previews_on_trade_change
        )
        # Update session state
        st.session_state.selected_trade_id = trades_df.loc[
            trades_df['name'] == selected_name, 'id'
        ].iloc[0]
    else:
        st.sidebar.error("⚠️ No trades found. Check Supabase connection or table data.")

    env_options = {
        "Morning (Cool)": "The morning air was cool and the lab was quiet, providing a focused atmosphere with plenty of natural light.",
        "Afternoon (Warm)": "The lab temperature was moderate; the ceiling fans were active to maintain a comfortable working environment during the peak afternoon heat.",
        "Technical/Busy": "The lab was active with the hum of server fans and multiple workstations in use, creating a realistic, high-energy technical environment.",
        "Rainy/Overcast": "Due to the weather, the lab was lit with overhead fluorescent lights; the atmosphere was cool and calm.",
        "Custom": "" 
    }
    selected_env_preset = st.sidebar.selectbox("Choose a Preset", list(env_options.keys()))
    st.session_state.default_env_text = env_options[selected_env_preset]


    # --- AI KEY INHERITANCE ---
    # If user is on Platform Pass or Enterprise, use the master/secret key.
    # If Free, use the Platform key from Streamlit secrets.
    if is_superadmin:
        show_byok = True
        st.sidebar.info("Superadmin: Manual Key Override")
    else:
        show_byok = (tier == 'platform_pass')
        
        if tier == 'free':
            # Check if Vertex AI is configured
            sa_json_str = get_secret(["vertex_ai", "service_account_json"], "vertex_ai__service_account_json")
            if not sa_json_str:
                st.sidebar.error("⚠️ Vertex AI configuration is missing from secrets.toml!")
            else:
                st.sidebar.info("Using Platform AI (Free Tier)")
            st.session_state.ai_provider = "VertexAI"
            st.session_state.target_model = "gemini-2.5-flash"
            st.session_state.target_keys = []
        elif tier in ['pro', 'enterprise']:
            st.sidebar.info("💼 Pro/Enterprise Plan: Coming Soon! (Using Platform AI)")
            # Fall back to Platform AI to ensure app keeps functioning
            st.session_state.ai_provider = "VertexAI"
            st.session_state.target_model = "gemini-1.5-flash"
            st.session_state.target_keys = []

    if show_byok:
        with st.sidebar.expander("📡 AI Provider Settings", expanded=False):
            st.session_state.ai_provider = st.selectbox("Provider", ["Gemini", "Groq", "OpenRouter"])

            # Initialize target_keys to empty list if not already set, or if provider changes
            if 'target_keys' not in st.session_state or st.session_state.get('last_provider') != st.session_state.ai_provider:
                st.session_state.target_keys = []
                st.session_state.last_verified_key = ""
                st.session_state.last_provider = st.session_state.ai_provider

            if st.session_state.ai_provider == "Gemini":
                st.text_input("Gemini API Key", type="password", key="gemini_api_key_input", on_change=update_api_key_session, args=("gemini_api_key_input",))
                if not st.session_state.target_keys and "gemini_api_key_input" in st.session_state and st.session_state.gemini_api_key_input:
                    st.session_state.target_keys = [k.strip() for k in st.session_state.gemini_api_key_input.split(',') if k.strip()]
                st.session_state.target_model = st.selectbox("Gemini Preference", ["gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-2-flash", "gemini-2-flash-lite", "gemini-1.5-flash", "gemini-1.5-flash-lite"])
            elif st.session_state.ai_provider == "Groq":
                st.text_input("Groq API Key", type="password", key="groq_api_key_input", on_change=update_api_key_session, args=("groq_api_key_input",))
                if not st.session_state.target_keys and "groq_api_key_input" in st.session_state and st.session_state.groq_api_key_input:
                    st.session_state.target_keys = [st.session_state.groq_api_key_input.strip()]
                st.session_state.target_model = st.selectbox("Groq Model", ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"])
            elif st.session_state.ai_provider == "OpenRouter":
                st.text_input("OpenRouter API Key", type="password", key="openrouter_api_key_input", on_change=update_api_key_session, args=("openrouter_api_key_input",))
                if not st.session_state.target_keys and "openrouter_api_key_input" in st.session_state and st.session_state.openrouter_api_key_input:
                    st.session_state.target_keys = [st.session_state.openrouter_api_key_input.strip()]
                st.session_state.target_model = st.selectbox("OpenRouter Model", ["google/gemini-2.0-flash-001", "nvidia/nemotron-3-super-120b-a12b:free", "poolside/laguna-m.1:free"])

            # --- AUTOMATED VERIFICATION FLOW ---
            # For BYOK, target_keys will contain a single key. For platform, it might contain multiple.
            # We verify the first key in the list for display purposes.
            curr_keys_for_verification = st.session_state.get('target_keys', [])
            if curr_keys_for_verification:
                first_key_for_verification = curr_keys_for_verification[0]
                # Check if key changed or hasn't been verified yet
                if first_key_for_verification != st.session_state.get('last_verified_key'):
                    with st.spinner("Verifying connection..."):
                        res = validate_and_generate(st.session_state.ai_provider, st.session_state.target_model, curr_keys_for_verification)
                        st.session_state.last_verified_key = first_key_for_verification
                        st.session_state.connection_success = ("✅ Connected" in str(res))
                        st.session_state.connection_msg = res
                
                # Render the status
                if st.session_state.get('connection_success'):
                    st.success(st.session_state.connection_msg)
                else:
                    st.error(f"❌ {st.session_state.get('connection_msg')}")

    if role == 'admin':
        st.sidebar.checkbox("🛠️ Dev Mode (Skip AI)", key="dev_mode")
    
    
    # 4. Navigation
    st.sidebar.markdown("---")
    
    if role == 'student':
        pages = {
            "✍️ Student Statement": personal_statement.main,
            "📜 My History": history.main
        }
    else:
        pages = {
            "Dashboard": dashboard.main, 
            "✍️ Student Statement": personal_statement.main,
            "📑 Witness Statement": witness_statement.main,
            "📜 My History": history.main,
            "💳 My Subscription": subscription_page.main
        }
        if role == 'admin':
            pages["📚 Manage NOS"] = admin_nos.main
            pages["👥 User Management"] = admin_users.main
    
    selection = st.sidebar.radio("Navigation", list(pages.keys()))
    
    if st.sidebar.button("Logout"):
        # Explicitly sign out of Supabase to clear persistence
        db.get_supabase().auth.sign_out()
        st.session_state.clear()
        st.rerun()

    pages[selection]()
