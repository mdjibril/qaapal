# Transition QAAPAL to Freemium SaaS + BYOK Model

This document outlines the technical implementation plan to transition the QAAPAL Streamlit application into a scalable SaaS product. The plan introduces a Freemium model with a BYOK (Bring Your Own Key) upgrade path, while future-proofing the database to support B2B Enterprise organizations later.

## Phase 1 Conclusion: Infrastructure & UI Ready - **MERGE TO MAIN**

> [!TIP]
> **Free Tier & Exemptions**
> 1. New users get **10 free reports**. - **DONE**
> 2. `admin` roles have unlimited generations. - **DONE**
>
> **Landing Page Platform**
> **pure HTML/CSS will be use for the landing page**.
>
> **Paywall UX**
> We will use **`st.dialog`** when a user clicks "Generate" with 0 credits. This prevents them from losing the text they just typed via Session State persistence. - **DONE**
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
    *   `id` (UUID, Primary Key) - **DONE**
    *   `name` (Text) - **DONE**
    *   `subscription_tier` (Enum: 'free', 'pro', 'enterprise', 'platform_pass') - **DONE**
    *   `master_api_key` (Text, Nullable - for B2B schools paying the AI costs) - **DONE**
    *   `credits_balance` (Int, Default: 5 - for Freemium users) - **DONE**
*   **Update Table: `user_profiles`**
    *   Add `org_id` (UUID, Foreign Key to `organizations`) - **DONE**
    *   Add `org_role` (Enum: 'member', 'admin') - **DONE**
*   **Database Triggers:**
    *   Write a SQL Trigger: When a new user signs up, automatically create a "Personal Organization" for them, set `subscription_tier = 'free'`, grant them 5 `credits_balance`, and link their `org_id`. - **DONE**

*   **Row Level Security (RLS) Policies:**
    *   **Organizations:**
        *   `SELECT`: Users can only view the organization linked to their profile (`id = user_profiles.org_id`). App Superadmins bypass this check. - **DONE**
        *   `UPDATE`: Restricted to Organization Admins or App Superadmins. - **DONE**

---

### Authentication & Onboarding

We have modified the login system to allow frictionless, self-serve sign-ups so users can immediately test the app.

#### [MODIFY] `auth_utils.py`
*   Refactor `login_form()` to use `st.tabs(["Login", "Sign Up"])`. - **DONE**
*   Implement `supabase.auth.sign_up()` in the "Sign Up" tab. - **DONE**
*   Ensure new sign-ups automatically fetch their newly created `org_id` and role into `st.session_state` so they can bypass the admin approval process. - **DONE**

---

### Application Logic & UI

We have updated the sidebar to reflect the new billing states and implemented the API Key "Inheritance" logic.

#### [MODIFY] `main.py`
*   **Sidebar Billing Widget:** Add a visual indicator at the top of the sidebar showing the user's plan and remaining credits. - **DONE**
*   **API Key Inheritance Logic:** 
    *   Hide the "📡 AI Provider Settings" by default. - **DONE**
    *   Check `subscription_tier`. If the user is on the 'free' tier, use the platform's default API key (stored securely in Streamlit secrets). - **DONE**
    *   If the user upgrades to the 'platform_pass', unhide the BYOK inputs in the sidebar. - **DONE**
    *   If `org.master_api_key` exists, hide BYOK inputs and use the master key. - **DONE**

#### [MODIFY] `dashboard.py` (and statement pages)
*   **Paywall / Generation Block:**
    *   Intercept the "Generate & Finalize Report" button click.
    *   Query the user's `credits_balance` and `subscription_tier`. - **DONE**
    *   If `credits_balance == 0` and `subscription_tier == 'free'`, disable generation and trigger an `st.error` or `st.dialog` prompting them to upgrade to a paid plan. - **DONE**
    *   If successful, deduct 1 credit from `organizations.credits_balance`. - **DONE**

#### [NEW] `subscription_page.py`
*   **Subscription Management:** Added a dedicated page for users to view expiry dates, renewal status, and credit balance. - **DONE**

---

### Phase 2: Production Readiness (Next Branch)
*   **Environment Variables:** Configure Monnify API keys in Streamlit Secrets/Railway.
*   **API Key Rotation:** Implement a simple rotation logic for platform AI keys to mitigate rate limits. - **DONE**
*   **Live Webhooks:** Implement real payment validation and callback handling.
*   **Domain Mapping:** Finalize the link between the landing page and the app subdomain.

## Verification Plan

### Manual Verification
1.  **Sign-up Flow:** Register a new user from the UI. Verify that a Personal Organization is created in Supabase with 5 credits and the 'free' tier.
2.  **Freemium Limits:** Generate 5 reports. Ensure the 6th attempt is successfully blocked by the paywall UI.
3.  **BYOK Unlock:** Simulate a Stripe upgrade to 'platform_pass'. Verify the sidebar reveals the API key inputs and allows generation without deducting credits.
4.  **B2B Override (Test):** Manually insert a `master_api_key` for the organization in Supabase. Verify the UI hides personal API key inputs and uses the master key successfully.
