import streamlit as st
from auth_utils import check_auth, login_form, get_secret, reset_password_form, finalize_session
import dashboard, history, personal_statement, witness_statement, subscription_page, account_settings, admin_panel, student_portfolio, bulk_csv_import, workbook_generator, database as db
from ai_utils import validate_and_generate
from ai_policy import get_ai_access_policy
from app_state import ensure_session_defaults

APP_VERSION = "v1.1.0"

st.set_page_config(
    page_title="NSQAssessment App | AI-Powered Reports",
    page_icon="⚡", # You can use an emoji or a path to an image file
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Mobile-optimized responsive CSS ---
st.markdown("""
<style>
/* Improve mobile responsiveness */
@media screen and (max-width: 768px) {
    /* Make buttons full-width on mobile */
    .stButton > button,
    .stDownloadButton > button,
    .stFormSubmitButton > button {
        width: 100%;
    }

    /* Reduce padding on mobile */
    .block-container {
        padding-left: 1rem;
        padding-right: 1rem;
        padding-top: 1rem;
    }

    /* Make text inputs larger touch targets */
    .stTextInput input,
    .stTextArea textarea {
        font-size: 16px !important;
    }

    /* Stack columns on mobile */
    [data-testid="column"] {
        width: 100% !important;
        min-width: 100% !important;
    }
}

/* General mobile improvements */
@media screen and (max-width: 480px) {
    .block-container {
        padding-left: 0.5rem;
        padding-right: 0.5rem;
    }
}
</style>
""", unsafe_allow_html=True)

# Callback function for API key inputs
def update_api_key_session(key_name):
    """Callback to store user-entered BYOK keys when an API key input changes."""
    if st.session_state[key_name]:
        # Split by comma to support rotation even for BYOK users
        st.session_state.byok_keys = [k.strip() for k in st.session_state[key_name].split(',') if k.strip()]
    else:
        st.session_state.byok_keys = []

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
        
    # 3. Clear persistent sets
    for persistent_set in ('persistent_selected_pcs', 'persistent_student_selected_pcs', 'persistent_witness_selected_pcs'):
        if persistent_set in st.session_state:
            st.session_state[persistent_set].clear()


def clear_nos_context():
    """Clear all NOS-related selections when trade or level changes."""
    clear_previews_on_trade_change()
    for key in (
        "global_trade_level_select",
        "selected_trade_level_id",
        "selected_trade_level",
        "selected_trade_level_name",
    ):
        st.session_state.pop(key, None)

ENV_OPTIONS = {
    "Morning (Cool)": "The morning air was cool and the lab was quiet, providing a focused atmosphere with plenty of natural light.",
    "Afternoon (Warm)": "The lab temperature was moderate; the ceiling fans were active to maintain a comfortable working environment during the peak afternoon heat.",
    "Technical/Busy": "The lab was active with the hum of server fans and multiple workstations in use, creating a realistic, high-energy technical environment.",
    "Rainy/Overcast": "Due to the weather, the lab was lit with overhead fluorescent lights; the atmosphere was cool and calm.",
    "Custom": ""
}

def update_environment_preset():
    """Apply the selected environment preset to the dashboard atmosphere field."""
    preset_text = ENV_OPTIONS[st.session_state.env_preset]
    st.session_state.default_env_text = preset_text
    st.session_state.dash_atmosphere = preset_text

# Define cached functions at the top level to avoid re-definition issues
@st.cache_data(ttl=600)
def get_cached_trades():
    return db.fetch_trades()


@st.cache_data(ttl=600)
def get_cached_trade_levels(trade_id):
    if not trade_id:
        return []
    return db.fetch_trade_levels(trade_id)

def main():
    # --- DEEP LINKING LOGIC ---
    ensure_session_defaults(
        {
            "auth_mode": "Login",
            "env_preset": "Morning (Cool)",
        }
    )

    if "intent" in st.query_params:
        intent = st.query_params.get("intent")
        if intent == "signup":
            st.session_state["auth_mode"] = "Sign Up"
        elif intent == "earlybird":
            st.session_state["auth_mode"] = "Sign Up"
            st.session_state["promo_code"] = "EARLYBIRD_100"
        elif intent == "recovery":
            st.session_state["reset_mode"] = True
        st.query_params.clear()

    update_environment_preset()

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
        return
    elif not check_auth():
        login_form()
        return

    role = st.session_state.get('user_role', 'assessor')
    tier = st.session_state.get('subscription_tier', 'free')
    credits = st.session_state.get('credits_balance', 0)
    is_superadmin = (role == 'admin')
    is_platform_pass_expired = db.check_platform_pass_expiry()

    ai_policy = get_ai_access_policy(role, tier, is_platform_pass_expired)
    st.session_state['_ai_policy'] = ai_policy
    show_byok = ai_policy["allow_byok"]
    platform_quota = ai_policy.get("platform_quota")
    using_byok = False

    if tier == 'platform_pass' and is_platform_pass_expired:
        st.session_state['subscription_tier'] = 'free'
        tier = 'free'
        st.session_state['credits_balance'] = 0
        credits = 0
        org_id = st.session_state.get('org_id')
        if org_id:
            db.upgrade_org_tier(org_id, 'free')
        ai_policy = get_ai_access_policy(role, tier, is_platform_pass_expired)
        st.session_state['_ai_policy'] = ai_policy
        show_byok = ai_policy["allow_byok"]

    st.sidebar.title(f"🚀 NSQ Portal {APP_VERSION}")

    st.session_state.assessor_name = st.session_state.get('assessor_full_name', 'Jibril Dauda Muhammad')
    name = st.session_state.assessor_name

    st.sidebar.caption(f"{name} | {role.capitalize()} | {tier.replace('_', ' ').title()}")

    trades = get_cached_trades()
    if trades:
        with st.sidebar.container(border=True):
            st.markdown("**NOS Selection**")
            sorted_trades = sorted(trades, key=lambda trade: (trade.get("name") or "").casefold())
            trade_names = [t['name'] for t in sorted_trades]
            selected_name = st.selectbox(
                "Select Trade Family",
                trade_names,
                key="global_trade_select",
                on_change=clear_nos_context
            )
            selected_trade = next((t for t in sorted_trades if t['name'] == selected_name), None)
            selected_trade_id = selected_trade['id'] if selected_trade else None
            st.session_state.selected_trade_id = selected_trade_id
            st.session_state.selected_trade_name = selected_trade['name'] if selected_trade else selected_name

            trade_levels = get_cached_trade_levels(selected_trade_id)
            if trade_levels:
                def format_level_option(level_row):
                    label = f"Level {level_row['level']}"
                    display_name = level_row.get("display_name")
                    if display_name:
                        label = f"{label} - {display_name}"
                    return label

                current_level_id = st.session_state.get("selected_trade_level_id")
                default_level_index = next(
                    (idx for idx, lvl in enumerate(trade_levels) if lvl["id"] == current_level_id),
                    0,
                )

                selected_trade_level = st.selectbox(
                    "Select Level",
                    trade_levels,
                    index=default_level_index,
                    key="global_trade_level_select",
                    on_change=clear_previews_on_trade_change,
                    format_func=format_level_option,
                )
                if selected_trade_level:
                    st.session_state.selected_trade_level_id = selected_trade_level["id"]
                    st.session_state.selected_trade_level = selected_trade_level["level"]
                    st.session_state.selected_trade_level_name = selected_trade_level.get("display_name") or f"Level {selected_trade_level['level']}"
                    st.caption(f"Current: {st.session_state.selected_trade_name} / {st.session_state.selected_trade_level_name}")
            else:
                st.session_state.pop("selected_trade_level_id", None)
                st.session_state.pop("selected_trade_level", None)
                st.session_state.pop("selected_trade_level_name", None)
                st.session_state.pop("global_trade_level_select", None)
                st.info("No levels found for this trade.")
    else:
        st.sidebar.error("⚠️ No trades found. Check Supabase connection or table data.")

    with st.sidebar.container(border=True):
        st.markdown("**Report Context**")
        selected_env_preset = st.selectbox(
            "Atmosphere",
            list(ENV_OPTIONS.keys()),
            key="env_preset",
            on_change=update_environment_preset
        )
        st.session_state.default_env_text = ENV_OPTIONS[selected_env_preset]

    if ai_policy["status_message"]:
        with st.sidebar.container(border=True):
            st.markdown("**AI Status**")
            st.info(ai_policy["status_message"])
            if not is_superadmin:
                if using_byok:
                    st.success("🔑 BYOK active — no platform quota used.")
                elif tier == "free":
                    st.caption(f"Weekly allowance: {credits} of 5 reports remaining.")
                else:
                    quota = ai_policy.get("platform_quota")
                    if quota == 0:
                        st.caption("Bring your own AI key to generate reports.")
                    elif quota is None:
                        st.caption("Platform quota: unlimited.")
                    else:
                        used = st.session_state.get("ai_quota_used", 0) or 0
                        st.caption(f"Platform quota: {used} of {quota} monthly reports used.")

    if not show_byok:
        st.session_state.ai_provider = ai_policy["default_provider"]
        st.session_state.target_model = ai_policy["default_model"]
        # Non-BYOK users use the platform OpenRouter key or its Gemini fallback.
        st.session_state.target_keys = []
        platform_key_name = "OPENROUTER_API_KEY" if st.session_state.ai_provider == "OpenRouter" else "INTERNAL_AI_KEY"
        platform_key = get_secret([platform_key_name], platform_key_name)
        if platform_key:
            st.session_state.target_keys = [k.strip() for k in str(platform_key).split(',') if k.strip()]

    if show_byok:
        with st.sidebar.expander("📡 AI Provider Settings", expanded=False):
            providers = ai_policy["provider_options"]
            if st.session_state.get("ai_provider") not in providers:
                st.session_state.ai_provider = ai_policy["default_provider"]
            st.session_state.ai_provider = st.selectbox("Provider", providers)

            if 'target_keys' not in st.session_state or st.session_state.get('last_provider') != st.session_state.ai_provider:
                st.session_state.target_keys = []
                st.session_state.byok_keys = []
                st.session_state.verification_result = None
                st.session_state.verification_fingerprint = None
                st.session_state.last_provider = st.session_state.ai_provider

            if st.session_state.ai_provider == "Gemini":
                st.text_input("Gemini API Key", type="password", key="gemini_api_key_input", on_change=update_api_key_session, args=("gemini_api_key_input",))
                byok_keys = [k.strip() for k in st.session_state.get("gemini_api_key_input", "").split(",") if k.strip()]
                gemini_model_choice = st.selectbox("Gemini Preference", ["gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-3.1-flash", "gemini-3.1-flash-lite", "Other (Custom)"])
                if gemini_model_choice == "Other (Custom)":
                    st.session_state.target_model = st.text_input("Custom Gemini Model", placeholder="e.g. gemini-3.1-pro-preview", key="gemini_custom_model")
                else:
                    st.session_state.target_model = gemini_model_choice
            else:
                st.text_input("OpenRouter API Key", type="password", key="openrouter_api_key_input", on_change=update_api_key_session, args=("openrouter_api_key_input",))
                byok_keys = [k.strip() for k in st.session_state.get("openrouter_api_key_input", "").split(",") if k.strip()]
                or_model_choice = st.selectbox("OpenRouter Model", ["google/gemini-3.5-flash", "google/gemini-3.5-flash-lite", "nvidia/nemotron-3-super-120b-a12b:free", "poolside/laguna-m.1:free", "Other (Custom)"])
                if or_model_choice == "Other (Custom)":
                    st.session_state.target_model = st.text_input("Custom OpenRouter Model", placeholder="e.g. anthropic/claude-3-haiku", key="or_custom_model")
                else:
                    st.session_state.target_model = or_model_choice

            st.session_state.byok_keys = byok_keys
            verification_fingerprint = (st.session_state.ai_provider, st.session_state.target_model, tuple(byok_keys))
            if st.button("Verify Key", key="verify_ai_key", disabled=not byok_keys):
                with st.spinner("Verifying connection..."):
                    st.session_state.verification_result = validate_and_generate(
                        st.session_state.ai_provider,
                        st.session_state.target_model,
                        byok_keys,
                    )
                    st.session_state.verification_fingerprint = verification_fingerprint

            if st.session_state.get("verification_fingerprint") == verification_fingerprint:
                verification_result = st.session_state.get("verification_result")
                if "✅ Connected" in str(verification_result):
                    st.success(verification_result)
                else:
                    st.error(f"❌ {verification_result}")

    # Phase 7 Tier 2: determine whether this generation uses BYOK or platform quota.
    # platform_quota == 0 means BYOK-only (no platform fallback).
    selected_key_name = (
        "gemini_api_key_input"
        if st.session_state.ai_provider == "Gemini"
        else "openrouter_api_key_input"
    )
    using_byok = bool(str(st.session_state.get(selected_key_name, "")).strip())
    if show_byok and using_byok:
        st.session_state.target_keys = st.session_state.get("byok_keys", [])
    if show_byok and not using_byok and platform_quota != 0:
        # Paid tier without a pasted key, with platform fallback available.
        st.session_state.ai_provider = ai_policy["default_provider"]
        st.session_state.target_model = ai_policy["default_model"]
        platform_key_name = "OPENROUTER_API_KEY" if st.session_state.ai_provider == "OpenRouter" else "INTERNAL_AI_KEY"
        platform_key = get_secret([platform_key_name], platform_key_name)
        st.session_state.target_keys = [k.strip() for k in str(platform_key).split(',') if k.strip()] if platform_key else []
        using_byok = False
    st.session_state.using_byok = using_byok

    if role == 'admin':
        with st.sidebar.expander("🛠️ Admin Tools", expanded=False):
            st.checkbox("Dev Mode (Skip AI)", key="dev_mode")

    with st.sidebar.expander("🆘 Support", expanded=False):
        st.caption("Contact support directly")
        st.link_button("WhatsApp Support", "https://wa.me/2348184018469", width="stretch")
        st.link_button("Email Support", "mailto:muhammadjibrildauda@gmail.com", width="stretch")

    with st.sidebar.container(border=True):
        st.markdown("**Navigation**")
        if role == 'student':
            pages = {
                "✍️ Student Statement": personal_statement.main,
                "📜 My History": history.main,
                "⚙️ Account Settings": account_settings.main
            }
        else:
            pages = {
                "📝 Dashboard": dashboard.main,
                "✍️ Student Statement": personal_statement.main,
                "📑 Witness Statement": witness_statement.main,
                "📚 Workbook Generator": workbook_generator.main,
                "📜 My History": history.main,
                "⚙️ Account Settings": account_settings.main,
                "💳 My Subscription": subscription_page.main
            }
            if role == 'admin':
                pages["🛡️ Super Admin Dashboard"] = admin_panel.main
                pages["🎓 Student Portfolios"] = student_portfolio.main
                pages["📋 Bulk CSV Import"] = bulk_csv_import.main

        selection = st.radio("Go to", list(pages.keys()), label_visibility="collapsed")

        if st.button("Logout"):
            db.get_supabase().auth.sign_out()
            st.session_state.clear()
            st.rerun()

    pages[selection]()


if __name__ == "__main__":
    main()
