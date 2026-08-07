import streamlit as st
import datetime
from datetime import timedelta
import database as db
from auth_utils import get_secret
from app_state import ensure_session_defaults

def main():
    ensure_session_defaults(
        {
            "subscription_progress_hint": "",
        }
    )

    st.title("💳 My Subscription")

    user_role = st.session_state.get('user_role', 'assessor')
    assessor_name = st.session_state.get('assessor_full_name', 'Jibril Dauda Muhammad')
    org_id = st.session_state.get('org_id')
    current_tier = st.session_state.get('subscription_tier', 'free')
    credits_balance = st.session_state.get('credits_balance', 0)
    subscription_start_date_str = st.session_state.get('subscription_start_date')
    
    selar_base = get_secret(["payments", "selar_link"], "payments__selar_link") or "https://selar.com/nsqassessment-platformpass"
    selar_lifetime_base = get_secret(["payments", "selar_lifetime_link"], "payments__selar_lifetime_link") or "https://selar.com/nsqassessment-lifetime"
    user_email = st.session_state.user_session.email
    upgrade_link = f"{selar_base}?email={user_email}"
    lifetime_upgrade_link = f"{selar_lifetime_base}?email={user_email}"
    
    st.markdown("---")
    st.subheader("Account Summary")
    st.caption(f"{assessor_name} | {user_role.capitalize()}")

    col_a, col_b = st.columns(2)
    with col_a:
        st.metric("Current Plan", "Superadmin" if user_role == "admin" else current_tier.replace('_', ' ').title())
    with col_b:
        st.metric("Credits", "Unlimited" if user_role == "admin" or current_tier != "free" else credits_balance)

    if user_role != "admin":
        st.markdown("---")
        st.subheader("Quick Support")
        st.link_button("WhatsApp Support", "https://wa.me/2348184018469", width="stretch")
        st.link_button("Email Support", "mailto:muhammadjibrildauda@gmail.com", width="stretch")

    st.markdown("---")
    st.subheader("Current Plan Details")

    if user_role == 'admin':
        st.success("You are a **Superadmin**! You have unlimited access to all features.")
        st.info("Your plan is not subject to standard subscription tiers or credit limits.")
        return # Superadmins don't need further subscription details.

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Your Current Plan", current_tier.replace('_', ' ').title())
    with col2:
        if current_tier == 'free':
            st.metric("Remaining Credits", credits_balance)
        else:
            st.metric("Remaining Credits", "Unlimited")

    if current_tier == 'platform_pass':
        st.markdown("---")
        st.subheader("Subscription Status")
        
        if subscription_start_date_str:
            try:
                # Use the same parsing logic as in main.py's check_platform_pass_expiry
                start_date = datetime.datetime.fromisoformat(subscription_start_date_str.replace('Z', '+00:00'))
                expiry_date = start_date + timedelta(days=30) # Assuming 30 days for a month
                now_in_tz = datetime.datetime.now(start_date.tzinfo)
                total_seconds = (expiry_date - start_date).total_seconds() or 1
                elapsed_seconds = max(0, min(total_seconds, (now_in_tz - start_date).total_seconds()))
                progress = max(0.0, min(1.0, elapsed_seconds / total_seconds))

                st.write(f"**Subscription Start Date:** {start_date.strftime('%B %d, %Y')}")
                st.write(f"**Estimated Renewal Date:** {expiry_date.strftime('%B %d, %Y')}")
                st.progress(progress, text=f"{max(0, (expiry_date - now_in_tz).days)} days remaining")

                is_expired = db.check_platform_pass_expiry()
                if is_expired:
                    st.error("Your Platform Pass has expired! Please renew to continue enjoying unlimited generations.")
                    st.link_button("Renew Platform Pass Now", upgrade_link, type="primary", width="stretch")
                else:
                    st.success("Your Platform Pass is active!")
                    # Calculate days left relative to the timezone of the start_date
                    days_left = (expiry_date - now_in_tz).days
                    if days_left > 0:
                        st.info(f"You have approximately {days_left} days left on your current subscription.")
                    else:
                        st.info("Your subscription is due to expire very soon!")

            except ValueError:
                st.warning("Could not parse subscription start date. Please contact support.")
        else:
            st.warning("Subscription start date not found. Please contact support.")

    elif current_tier == 'lifetime':
        st.markdown("---")
        st.subheader("Subscription Status")
        st.success("🎉 You are on the **Lifetime Tier**! You have permanent, unlimited access to all features.")
        st.info("Your access never expires. Thank you for your one-time purchase!")

    elif current_tier == 'free':
        st.markdown("---")
        st.subheader("Upgrade Your Plan")
        
        if credits_balance <= 0:
            st.error("You have run out of free credits.")
            st.info("💡 You can wait for 7 days for your free credits to automatically renew, or upgrade now for unlimited access!")
        else:
            st.info(f"You are currently on the Free plan with {credits_balance} reports remaining.")
            
        st.write("Upgrade to **Platform Pass** or our **Lifetime Tier** for unlimited report generations and advanced features!")
        
        col_up1, col_up2 = st.columns(2)
        with col_up1:
            st.link_button("🚀 Upgrade to Platform Pass (₦3,500/mo)", upgrade_link, type="primary", width="stretch")
        with col_up2:
            st.link_button("💎 Get Lifetime Tier (₦10,000 One-time)", lifetime_upgrade_link, type="secondary", width="stretch")
            
    st.markdown("---")
    st.caption("For enterprise solutions or custom plans, please contact sales.")
