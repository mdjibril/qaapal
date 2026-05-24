import streamlit as st
from auth_utils import check_auth, login_form
import dashboard, history, admin_nos, admin_users, personal_statement, witness_statement, subscription_page, database as db
from datetime import datetime, timedelta
import google.generativeai as genai
import time
from groq import Groq
import requests, json
import google.api_core.exceptions
from ai_utils import validate_and_generate

st.set_page_config(page_title="NSQ Portal", layout="wide")

# Callback function for API key inputs
def update_api_key_session(key_name):
    """Callback to update st.session_state.target_key when an API key input changes."""
    st.session_state.target_key = st.session_state[key_name]

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

@st.dialog("💳 Monnify Payment Portal")
def mock_payment_dialog(org_id):
    st.write("### Upgrade to Platform Pass")
    st.write("Process your payment securely using Monnify.")
    
    u_session = st.session_state.get('user_session')
    email = u_session.email if u_session else "user@example.com"
    # Mock Naira amount for Platform Pass (approx $5 equivalent)
    amount_naira = 7500
    
    with st.container(border=True):
        st.caption("Order Summary")
        st.write(f"**Plan:** Platform Pass (Monthly)")
        st.write(f"**Amount:** ₦{amount_naira:,}.00")
        st.write(f"**Customer:** {email}")

    st.info("💡 In test mode, clicking 'Pay' simulates a successful response from the Monnify SDK.")
    
    if st.button("Pay with Monnify", type="primary", use_container_width=True):
        with st.spinner("Initializing Monnify Checkout..."):
            time.sleep(1.5) # Simulate SDK initialization
            
            # Simulate the callback/webhook logic from Monnify
            success, err = db.upgrade_org_tier(org_id)
            if success:
                st.success("✅ Payment Successful!")
                st.toast("Monnify Reference: MNFY-TEST-998877")
                st.session_state['subscription_tier'] = 'platform_pass'
                st.session_state['subscription_start_date'] = datetime.now().isoformat()
                time.sleep(1)
                st.rerun()
            else:
                st.error(f"Monnify Error: {err}")

def check_platform_pass_expiry():
    """Checks if the platform_pass subscription has expired."""
    tier = st.session_state.get('subscription_tier', 'free')
    start_date_str = st.session_state.get('subscription_start_date')

    if tier == 'platform_pass' and start_date_str:
        # Parse the date string (e.g., '2024-05-21T12:00:00+00:00')
        # Handle potential timezone info if present, or assume UTC
        try:
            start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
        except ValueError:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%dT%H:%M:%S.%f%z')
        
        # Check if one month has passed (using 30 days as a proxy for a month)
        if datetime.now(start_date.tzinfo) > start_date + timedelta(days=30):
            return True
    return False

# Define cached functions at the top level to avoid re-definition issues
@st.cache_data(ttl=600)
def get_cached_trades():
    return db.fetch_trades()

if not check_auth():
    login_form()
else:
    role = st.session_state.get('user_role', 'assessor')
    tier = st.session_state.get('subscription_tier', 'free')
    credits = st.session_state.get('credits_balance', 0)
    is_superadmin = (role == 'admin')
    is_platform_pass_expired = check_platform_pass_expiry()

    # If platform_pass is expired, treat them as free tier for UI/logic purposes
    if tier == 'platform_pass' and is_platform_pass_expired:
        st.session_state['subscription_tier'] = 'free'
        tier = 'free' # Update local variable for immediate use
        st.session_state['credits_balance'] = 0 # Ensure no credits are shown
        credits = 0 # Update local variable
    
    # --- CENTRALIZED SIDEBAR ---
    st.sidebar.title(f"🚀 NSQ Portal v1.0.3")
    
    # Sidebar Billing Widget
    with st.sidebar.container(border=True):
        if is_platform_pass_expired:
            st.error("Platform Pass Expired! Please renew.")
            if st.button("Renew Platform Pass", use_container_width=True):
                mock_payment_dialog(st.session_state.org_id)
        else:
            col_plan, col_cred = st.columns(2)
            plan_display = "SUPERADMIN" if is_superadmin else tier.upper()
            col_plan.caption(f"**Plan:** {plan_display}")
            
            credit_display = "∞" if (is_superadmin or tier != 'free') else credits
            col_cred.caption(f"**Credits:** {credit_display}")
            
            if not is_superadmin and tier == 'free' and credits == 0:
                st.error("Out of credits! Upgrade to Platform Pass.")
                if st.button("🚀 Upgrade Now", use_container_width=True):
                    mock_payment_dialog(st.session_state.org_id)

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
            # Use .get() to avoid KeyError if the secret is missing
            key_val = st.secrets.get("INTERNAL_AI_KEY")
            st.session_state.target_key = key_val.strip() if key_val else ""
            
            if not st.session_state.target_key:
                st.sidebar.error("⚠️ Platform AI Key (INTERNAL_AI_KEY) is missing from secrets.toml!")
            else:
                st.sidebar.info(f"Using Platform AI ({tier.capitalize()} Tier)")
            
            st.session_state.ai_provider = st.secrets.get("INTERNAL_AI_PROVIDER", "Gemini").strip()
            st.session_state.target_model = st.secrets.get("INTERNAL_AI_MODEL", "gemini-1.5-flash").strip()
        elif tier == 'enterprise' and st.session_state.get('master_api_key'):
            m_key = st.session_state.get('master_api_key')
            st.session_state.target_key = m_key.strip() if m_key else ""
            st.sidebar.info("Using Organization Master Key")
            st.session_state.ai_provider = "Gemini"
            st.session_state.target_model = "gemini-1.5-flash"

    if show_byok:
        with st.sidebar.expander("📡 AI Provider Settings", expanded=False):
            st.session_state.ai_provider = st.selectbox("Provider", ["Gemini", "Groq", "OpenRouter"])

            # Initialize target_key to empty string if not already set, or if provider changes
            if 'target_key' not in st.session_state or st.session_state.get('last_provider') != st.session_state.ai_provider:
                st.session_state.target_key = ""
                st.session_state.last_verified_key = ""
                st.session_state.last_provider = st.session_state.ai_provider

            if st.session_state.ai_provider == "Gemini":
                st.text_input("Gemini API Key", type="password", key="gemini_api_key_input", on_change=update_api_key_session, args=("gemini_api_key_input",))
                # Ensure target_key is set even if no change event fired yet (e.g., initial load)
                if st.session_state.target_key == "" and "gemini_api_key_input" in st.session_state:
                    st.session_state.target_key = st.session_state.gemini_api_key_input
                # We list simple names; the Router will find the 'models/xxx' version
                st.session_state.target_model = st.selectbox("Gemini Preference", ["gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-2-flash", "gemini-2-flash-lite", "gemini-1.5-flash", "gemini-1.5-flash-lite"])
            elif st.session_state.ai_provider == "Groq":
                st.text_input("Groq API Key", type="password", key="groq_api_key_input", on_change=update_api_key_session, args=("groq_api_key_input",))
                if st.session_state.target_key == "" and "groq_api_key_input" in st.session_state:
                    st.session_state.target_key = st.session_state.groq_api_key_input
                st.session_state.target_model = st.selectbox("Groq Model", ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"])
            elif st.session_state.ai_provider == "OpenRouter":
                st.text_input("OpenRouter Key", type="password", key="openrouter_api_key_input", on_change=update_api_key_session, args=("openrouter_api_key_input",))
                if st.session_state.target_key == "" and "openrouter_api_key_input" in st.session_state:
                    st.session_state.target_key = st.session_state.openrouter_api_key_input
                st.session_state.target_model = st.selectbox("Model", ["z-ai/glm-4.5-air:free", "poolside/laguna-m.1:free", "nvidia/nemotron-3-super-120b-a12b:free", "baidu/qianfan-ocr-fast:free"])

            # --- AUTOMATED VERIFICATION FLOW ---
            curr_key = st.session_state.get('target_key', '').strip()
            if curr_key:
                # Check if key changed or hasn't been verified yet
                if curr_key != st.session_state.get('last_verified_key'):
                    with st.spinner("Verifying connection..."):
                        res = validate_and_generate(st.session_state.ai_provider, st.session_state.target_model, curr_key)
                        st.session_state.last_verified_key = curr_key
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
        st.session_state.clear()
        st.rerun()

    pages[selection]()
