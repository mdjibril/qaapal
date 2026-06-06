# Transition QAAPAL to Freemium SaaS + BYOK Model

This document outlines the technical implementation plan to transition the QAAPAL Streamlit application into a scalable SaaS product. The plan introduces a Freemium model with a BYOK (Bring Your Own Key) upgrade path, while future-proofing the database to support B2B Enterprise organizations later.

## Phase 1 Conclusion: Infrastructure & UI Ready - **MERGE TO MAIN**

> [!TIP]
> **Free Tier & Exemptions**
> - [x] New users get **5 free reports**.
> - [x] `admin` roles have unlimited generations.
>
> **Landing Page Platform**
> **pure HTML/CSS will be use for the landing page**.
>
> **Paywall UX**
> - [x] We will use **`st.dialog`** when a user clicks "Generate" with 0 credits. This prevents them from losing the text they just typed via Session State persistence.
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
    *   [x] `id` (UUID, Primary Key)
    *   [x] `name` (Text)
    *   [x] `subscription_tier` (Enum: 'free', 'pro', 'enterprise', 'platform_pass')
    *   [x] `master_api_key` (Text, Nullable - for B2B schools paying the AI costs)
    *   [x] `credits_balance` (Int, Default: 5 - for Freemium users)
*   **Update Table: `user_profiles`**
    *   [x] Add `org_id` (UUID, Foreign Key to `organizations`)
    *   [x] Add `org_role` (Enum: 'member', 'admin')
*   **Database Triggers:**
    *   [x] Write a SQL Trigger: When a new user signs up, automatically create a "Personal Organization" for them, set `subscription_tier = 'free'`, grant them 5 `credits_balance`, and link their `org_id`.
*   **Row Level Security (RLS) Policies:**
    *   **Organizations:**
        *   [x] `SELECT`: Users can only view the organization linked to their profile (`id = user_profiles.org_id`). App Superadmins bypass this check.
        *   [x] `UPDATE`: Restricted to Organization Admins or App Superadmins.
---

### Authentication & Onboarding

We have modified the login system to allow frictionless, self-serve sign-ups so users can immediately test the app.

#### [MODIFY] `auth_utils.py`
*   [x] Refactor `login_form()` to use `st.tabs(["Login", "Sign Up"])`.
*   [x] Implement `supabase.auth.sign_up()` in the "Sign Up" tab.
*   [x] Ensure new sign-ups automatically fetch their newly created `org_id` and role into `st.session_state` so they can bypass the admin approval process.
---

### Application Logic & UI

We have updated the sidebar to reflect the new billing states and implemented the API Key "Inheritance" logic.

#### [MODIFY] `main.py`
*   [x] **Sidebar Billing Widget:** Add a visual indicator at the top of the sidebar showing the user's plan and remaining credits.
*   **API Key Inheritance Logic:** 
    *   [x] Hide the "📡 AI Provider Settings" by default.
    *   [x] Check `subscription_tier`. If the user is on the 'free' tier, use the platform's default API key (stored securely in Streamlit secrets).
    *   [x] If the user upgrades to the 'platform_pass', unhide the BYOK inputs in the sidebar.
    *   [x] If `org.master_api_key` exists, hide BYOK inputs and use the master key.
#### [MODIFY] `dashboard.py` (and statement pages)
*   **Paywall / Generation Block:**
    *   Intercept the "Generate & Finalize Report" button click.
    *   [x] Query the user's `credits_balance` and `subscription_tier`.
    *   [x] If `credits_balance == 0` and `subscription_tier == 'free'`, disable generation and trigger an `st.error` or `st.dialog` prompting them to upgrade to a paid plan.
    *   [x] If successful, deduct 1 credit from `organizations.credits_balance`.
#### [NEW] `subscription_page.py`
*   [x] **Subscription Management:** Added a dedicated page for users to view expiry dates, renewal status, and credit balance.
---

### Phase 2: Production Readiness (Next Branch)
*   [x] **CLI Setup (Ubuntu):** Install Supabase CLI via NPM or Shell script and authenticate.
*   [x] **Project Linking:** Link local repo to Supabase Project Ref.
*   [x] **Secret Management:** Set `BRIDGE_SECRET` in Supabase using `supabase secrets set`.
*   [x] **Edge Function Deployment:** Deploy `selar-webhook` to production (using --no-verify-jwt).
*   [x] **Real Selar Integration:** Transition from mock payment dialogs to the actual Selar hosted checkout and API.
*   [x] **Vertex AI Transition:** Implement Google Cloud Vertex AI support for the Platform Tier to utilize the $300 GCP credit balance.
*   [x] **Service Account Management:** Securely store and parse GCP Service Account JSON from secrets to authorize Vertex AI calls.
*   [x] **API Key Rotation:** Implement a simple rotation logic for platform AI keys to mitigate rate limits.
*   **Payment Automation Bridge:** Create a Google Apps Script (GAS) to monitor Gmail for "New Sale" emails from Selar/Paystack.
*   **Webhook Relay:** Configure GAS to parse customer emails and relay them to the Supabase `selar-webhook` Edge Function.
*   **Payment UX:** Configure **Redirect URL** on Selar product pages to return users to `app.qaapal.com` after purchase.
*   [x] **Hybrid Provider Routing:** Ensure the AI Router supports both simple API keys (for BYOK/Groq/OpenRouter) and IAM-based auth (for Vertex AI).
*   [x] **Credit Guard UX:** Disable generation buttons and show contextual warnings for users with 0 credits.
*   [x] **AI Router Stability & Vertex AI Scope Fixes:** Ensure robust AI provider routing and correct OAuth scopes for Vertex AI.
*   [x] **UI Accessibility (Empty Labels):** Address Streamlit empty label warnings for improved accessibility.
*   [x] **Database Indexing:** Implement GIN Trigram and B-Tree indexes for high-speed search and sorting.
*   [x] **Lazy Loading & Caching:** Optimize History page by fetching metadata first and lazy-loading content with session state caching.
*   [x] **Enhanced Progress UX:** Utilize `st.status` for granular, transparent feedback during AI generation.
*   **Landing Page & App Integration:**
    *   **DNS Configuration:** Map root domain (qaapal.com) to static hosting and `app` subdomain to Railway.
    *   **CTA Implementation:** Link landing page "Get Started" buttons to the Streamlit URL with intent parameters.
    *   **Deep Linking Logic:** Update `main.py` to check `st.query_params` for `intent=signup` to auto-toggle the registration tab.
    *   **Auth Synchronicity:** (Optional) Use Supabase JS on the landing page to toggle "Login" vs "Dashboard" buttons based on session.
    *   **SEO & Metadata:** Align OpenGraph tags and canonical URLs across both the landing page and the app.

### Phase 3: Advanced Integrations
*   **Real Monnify Integration:** Transition from Selar to Monnify Web SDK/API for more advanced payment flows, once business registration is complete.


## Verification Plan

### Manual Verification
1.  **Sign-up Flow:** Register a new user. Verify organization creation in Supabase with **10 credits** and 'free' tier.
2.  **Freemium Limits & Deduction:** Generate 10 reports. Verify `credits_balance` decrements each time in both the UI and Supabase. Ensure the 11th attempt triggers the `st.dialog` paywall.
3.  **API Key Rotation:** Configure multiple Gemini keys in secrets. Simulate a `ResourceExhausted` (429) error and verify the system transparently rotates to the next key.
4.  **Multi-Provider Fallback:** Deplete or disable all Gemini keys. Verify the system automatically falls back to Groq or OpenRouter using the designated fallback models and keys.
5.  **BYOK Unlock:** Upgrade to 'platform_pass'. Verify the sidebar reveals provider settings and allows generation without credit deduction.
6.  **Subscription Lifecycle:** Manually expire a subscription in the DB (>30 days). Verify the UI reflects "Expired" and blocks generation until renewal.
7.  **Production Gate (Phase 2):** 
    *   Verify **Vertex AI** authentication using the Service Account JSON structure in secrets.
    *   Verify **Monnify** payment completion and webhook-driven credit/tier updates.