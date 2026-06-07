import streamlit as st
import datetime
from datetime import timedelta
import database as db

def main():
    st.title("💳 My Subscription")

    user_role = st.session_state.get('user_role', 'assessor')
    org_id = st.session_state.get('org_id')
    current_tier = st.session_state.get('subscription_tier', 'free')
    credits_balance = st.session_state.get('credits_balance', 0)
    subscription_start_date_str = st.session_state.get('subscription_start_date')
    
    selar_base = st.secrets.get("payments", {}).get("selar_link", "https://selar.com/nsqassessment-platformpass")
    user_email = st.session_state.user_session.email
    upgrade_link = f"{selar_base}?email={user_email}"
    
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
                
                st.write(f"**Subscription Start Date:** {start_date.strftime('%B %d, %Y')}")
                st.write(f"**Estimated Renewal Date:** {expiry_date.strftime('%B %d, %Y')}")

                is_expired = db.check_platform_pass_expiry()
                if is_expired:
                    st.error("Your Platform Pass has expired! Please renew to continue enjoying unlimited generations.")
                    st.link_button("Renew Platform Pass Now", upgrade_link, type="primary", width="stretch")
                else:
                    st.success("Your Platform Pass is active!")
                    # Calculate days left relative to the timezone of the start_date
                    now_in_tz = datetime.datetime.now(start_date.tzinfo)
                    days_left = (expiry_date - now_in_tz).days
                    if days_left > 0:
                        st.info(f"You have approximately {days_left} days left on your current subscription.")
                    else:
                        st.info("Your subscription is due to expire very soon!")

            except ValueError:
                st.warning("Could not parse subscription start date. Please contact support.")
        else:
            st.warning("Subscription start date not found. Please contact support.")
            
    elif current_tier == 'free':
        st.markdown("---")
        st.subheader("Upgrade Your Plan")
        st.info(f"You are currently on the Free plan with {credits_balance} reports remaining.")
        st.write("Upgrade to **Platform Pass** for unlimited report generations and advanced features!")
        st.link_button("🚀 Upgrade to Platform Pass (₦7,000/month)", upgrade_link, type="primary", width="stretch")
            
    st.markdown("---")
    st.caption("For enterprise solutions or custom plans, please contact sales.")