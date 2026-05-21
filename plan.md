# Transition QAAPAL to Freemium SaaS + BYOK Model

This document outlines the technical implementation plan to transition the QAAPAL Streamlit application into a scalable SaaS product. The plan introduces a Freemium model with a BYOK (Bring Your Own Key) upgrade path, while future-proofing the database to support B2B Enterprise organizations later.

## Finalized Architecture Decisions

> [!TIP]
> **Free Tier & Exemptions**
> 1. New users get **10 free reports**.
> 2. `admin` roles have unlimited generations.
> 3. A hardcoded secret email account will have unlimited generations when using BYOK.
>
> **Landing Page Platform**
> We recommend **Carrd.co** for the fastest, most cost-effective landing page ($19/year), or **Framer** if you want a highly premium, animated look.
>
> **Paywall UX**
> We will use **`st.dialog`** when a user clicks "Generate" with 0 credits. This prevents them from losing the text they just typed. The dialog will contain a link to the payment processor.
>
> **Payment Processor (Nigeria/Africa)**
> We recommend **Paystack** (owned by Stripe) as it is the easiest to set up in Nigeria and accepts international cards. If you want to sell strictly to US/UK clients and avoid all tax compliance headaches, **Lemon Squeezy** or **Paddle** (Merchant of Record) are excellent alternatives that pay out globally.

## Proposed Changes

We will organize the updates into three core components: Database, Authentication, and the Application UI.

---

### Database Architecture (Supabase)

To support both individual users and future B2B Enterprise schools, we will introduce an `organizations` structure and expand user profiles.

#### [MODIFY] Supabase Database Schema
*   **New Table: `organizations`**
    *   `id` (UUID, Primary Key)
    *   `name` (Text)
    *   `subscription_tier` (Enum: 'free', 'pro', 'enterprise', 'platform_pass')
    *   `master_api_key` (Text, Nullable - for B2B schools paying the AI costs)
    *   `credits_balance` (Int, Default: 5 - for Freemium users)
*   **Update Table: `user_profiles`**
    *   Add `org_id` (UUID, Foreign Key to `organizations`)
    *   Add `org_role` (Enum: 'member', 'admin')
*   **Database Triggers:**
    *   Write a SQL Trigger: When a new user signs up, automatically create a "Personal Organization" for them, set `subscription_tier = 'free'`, grant them 5 `credits_balance`, and link their `org_id`.

---

### Authentication & Onboarding

We will modify the login system to allow frictionless, self-serve sign-ups so users can immediately test the app.

#### [MODIFY] `auth_utils.py`
*   Refactor `login_form()` to use `st.tabs(["Login", "Sign Up"])`.
*   Implement `supabase.auth.sign_up()` in the "Sign Up" tab.
*   Ensure new sign-ups automatically fetch their newly created `org_id` and role into `st.session_state` so they can bypass the admin approval process.

---

### Application Logic & UI

We will update the sidebar to reflect the new billing states and implement the API Key "Inheritance" logic.

#### [MODIFY] `main.py`
*   **Sidebar Billing Widget:** Add a visual indicator at the top of the sidebar showing the user's plan and remaining credits.
*   **API Key Inheritance Logic:** 
    *   Hide the "📡 AI Provider Settings" by default.
    *   Check `subscription_tier`. If the user is on the 'free' tier, use the platform's default API key (stored securely in Streamlit secrets).
    *   If the user upgrades to the 'platform_pass', unhide the BYOK inputs in the sidebar.
    *   *(Future B2B Check)*: If `org.master_api_key` exists, hide BYOK inputs and use the master key.

#### [MODIFY] `dashboard.py` (and statement pages)
*   **Paywall / Generation Block:**
    *   Intercept the "Generate & Finalize Report" button click.
    *   Query the user's `credits_balance` and `subscription_tier`.
    *   If `credits_balance == 0` and `subscription_tier == 'free'`, disable generation and trigger an `st.error` or `st.dialog` prompting them to upgrade to a paid plan.
    *   If successful, deduct 1 credit from `organizations.credits_balance`.

---

## Verification Plan

### Manual Verification
1.  **Sign-up Flow:** Register a new user from the UI. Verify that a Personal Organization is created in Supabase with 5 credits and the 'free' tier.
2.  **Freemium Limits:** Generate 5 reports. Ensure the 6th attempt is successfully blocked by the paywall UI.
3.  **BYOK Unlock:** Simulate a Stripe upgrade to 'platform_pass'. Verify the sidebar reveals the API key inputs and allows generation without deducting credits.
4.  **B2B Override (Test):** Manually insert a `master_api_key` for the organization in Supabase. Verify the UI hides personal API key inputs and uses the master key successfully.
