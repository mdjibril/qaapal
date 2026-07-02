# Transition NSQ Assessment to Freemium SaaS + BYOK Model

This document outlines the technical implementation plan to transition the NSQ Assessment Streamlit application into a scalable SaaS product. The plan introduces a Freemium model with a BYOK (Bring Your Own Key) upgrade path, while future-proofing the database to support B2B Enterprise organizations later.

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
    - [x] `subscription_tier` (Enum: 'free', 'pro', 'enterprise', 'platform_pass') - *Note: Pro and Enterprise are "Coming Soon"*
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
*   [x] **Email Confirmation Link:** Ensure `email_redirect_to` is correctly set for signup emails.
*   [x] **Enhanced Onboarding:** Added Organization Name, Marketing Source, and Sector segmentation fields.
*   [x] **Password Safety:** Added real-time Password Confirmation matching.
*   [x] **Password Strength:** Implemented a real-time visual strength meter with suggestions.
*   [x] **ToS Compliance:** Integrated mandatory Terms of Service consent checkbox.
*   [x] **Forgot Password Flow:** Implement `supabase.auth.reset_password_for_email()` and handle recovery redirects.
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
*   [x] **Payment Automation Bridge:** Create a Google Apps Script (GAS) to monitor Gmail for "New Sale" emails from Selar/Paystack.
*   [x] **Webhook Relay Debugging:** Refine GAS parsing logic for Selar Merchant Notifications and verify end-to-end fulfillment.
*   [x] **Payment UX:** Configure **Redirect URL** on Selar product pages to return users to `app.nsqassessment.com.ng` after purchase.
*   [x] **Hybrid Provider Routing:** Ensure the AI Router supports both simple API keys (for BYOK/Groq/OpenRouter) and IAM-based auth (for Vertex AI).
*   [x] **Credit Guard UX:** Disable generation buttons and show contextual warnings for users with 0 credits.
*   [x] **AI Router Stability & Vertex AI Scope Fixes:** Ensure robust AI provider routing and correct OAuth scopes for Vertex AI.
*   [x] **UI Accessibility (Empty Labels):** Address Streamlit empty label warnings for improved accessibility.
*   [x] **Database Indexing:** Implement GIN Trigram and B-Tree indexes for high-speed search and sorting.
*   [x] **Lazy Loading & Caching:** Optimize History page by fetching metadata first and lazy-loading content with session state caching.
*   [x] **Enhanced Progress UX:** Utilize `st.status` for granular, transparent feedback during AI generation.
*   **Landing Page & App Integration:**
    *   [x] **Feature Status:** Mark Pro Plan and Enterprise Plan as "Coming Soon" on Landing Page and handle interim routing in app logic.
    *   [x] **DNS Configuration:** Point DomainKing nameservers to Netlify; CNAME verified, TXT record verified by Railway.
    *   [x] **CTA Implementation:** Link landing page "Get Started" buttons to the Streamlit URL using `?intent=signup` parameters.
    *   [x] **Deep Linking Logic:** Update `main.py` to check `st.query_params` for `intent=signup` and `type=recovery` to auto-toggle the registration/reset tab.
    *   [ ] **Auth Synchronicity:** (Optional) Use Supabase JS on the landing page to toggle "Login" vs "Dashboard" buttons based on session.
    *   [ ] **SEO & Metadata:** Align OpenGraph tags and canonical URLs across both the landing page and the app.

### Phase 3: Output Refinement & Quality Assurance (User Feedback Implementation) - **COMPLETED**
*   [x] **Prompt Engineering Overhaul (System Prompt Update):** Shift the AI persona from a "storytelling mindset" to a "process-documentation mindset" to ensure reports are truly audit-ready and compliant with the NSQ framework. Implement the following step-by-step rules:
    1.  **Enforce the "HOW" (Physical Action Rule):** Mandate that every sentence mapped to a Performance Criterion (PC) contains a verb of physical action or a specific technical interaction. (e.g., instead of "The student showed safety," use "The candidate gripped the insulated handle...").
    2.  **Eliminate Assessor Bias (Silent Observer Constraint):** Forbid the AI from generating text where the assessor provides hints, asks leading questions, or offers opinions. Record only the candidate's independent decisions, actions, and corrections.
    3.  **Humanize Linguistic Patterns (Assessor Log Persona):** Shift the persona to a "Field Auditor recording a Technical Log." Add a negative constraint list to avoid AI transition words (e.g., "Moreover", "Additionally") and flowery adjectives. Keep the tone industrial, professional, brief, and factual.
    4.  **Ground in "Trade Context" (Trade-First Anchoring):** Require the AI to prioritize trade-specific nouns (e.g., RJ45, Multimeter for ICT) over general pedagogical terms. Ensure every paragraph contains trade-specific technical terms.
    5.  **Reverse-Engineer the PC (Compliance First):** Instruct the AI to look at the PC description and describe the minimum necessary action to prove that specific criteria, ensuring strict alignment with the "Audit-Ready" goal in `launch.md`.

### Phase 3.1: Super Admin UI & Controls
To effectively manage the SaaS platform and monitor system health, a dedicated Super Admin dashboard should be built. Suggested features include:
*   **System Overview Dashboard:** High-level metrics including total active users, organizations, total reports generated, and aggregated API usage.
*   **Organization & User Management:** A centralized table to view all organizations, their subscription tiers ('free', 'platform_pass'), and credit balances. Include manual controls to adjust credits, upgrade/downgrade tiers, and manage user access.
*   **API & Routing Controls:** Live monitoring of AI provider health (Gemini, Groq, OpenRouter). Include manual override toggles to switch the default global fallback models in the event of an API outage.
*   **Audit Logs & QA Viewer:** A secure interface to view recently generated observation reports (anonymized if needed) to actively QA the "Field Auditor" prompt outputs and ensure NOS alignment.
*   **Payment & Webhook Logs:** A transaction history table monitoring incoming webhooks (from Selar/Monnify) to quickly diagnose and manually resolve any stuck payment upgrades.

### Phase 3.2: User Experience & Utility Updates
*   [x] **Auto-Renewing Credits:** Update the `organizations` table to include a `last_credit_renewal_date`. Implement logic (lazy evaluation on login/generation or via cron job) to auto-replenish 5 credits for 'free' tier users every 7 days.
*   [x] **Bulk Report Download (ZIP):** Add a feature to the History/Dashboard page allowing assessors to filter reports by a specific date, select them in bulk, and download them packaged in a single ZIP file.
*   [x] **AI Disclaimer UI:** Introduce a visible disclaimer (e.g., `st.caption("⚠️ AI can make mistakes. Please verify generated reports against your field notes.")`) positioned immediately below the "Generate" button on all statement/report forms.
*   [x] **Refine Remaining System Prompts:** Extend the "Field Auditor" prompt engineering overhaul to both the **Personal Statement** and **Witness Statement** modules, ensuring they adhere strictly to the professional, trade-specific tone and eliminate conversational fluff.
*   [x] **Security & Data Integrity:** Implemented input sanitization utilities, prompt injection defenses, and added CHECK constraints to database tables for length limits and non-empty fields.
*   [x] **NSQ Role Tracking:** Added a role selection dropdown (QAA, IQA, EQA) to the sign-up form and linked it to the `user_profiles` schema for better user segmentation.
*   [x] **Product Feedback Widget:** Implemented a robust in-app feedback system (👍/👎 with optional comment box) that displays after report generation and clears appropriately for new generations.
*   [x] **Strict Pre-Generation Validation:** Enforced that all critical observation inputs (Candidate Name, Timeline, Atmospheric Details, Observation Notes) are non-empty before allowing AI generation to proceed.
### Phase 4: Advanced Integrations
*   **Real Monnify Integration:** Transition from Selar to Monnify Web SDK/API for more advanced payment flows, once business registration is complete.


## Verification Plan

### SEECURITY Verification
*   [x] **IDOR Review - History Reads:** Verified report history access paths for `assessment_reports`, `student_statements`, and `witness_statements`. Confirmed non-admin list queries are scoped by `created_by = user_id`.
*   [x] **IDOR Fix - Lazy Content Fetch:** Added ownership enforcement to the lazy report content fetch in `history.py`, so non-admin users can only load full text for records where `created_by` matches their user ID.
*   [x] **IDOR Fix - Bulk ZIP Export:** Added ownership enforcement to the bulk download query in `history.py`, so selected IDs cannot be used to export another user's reports.
*   [x] **IDOR Review - Delete Operations:** Verified single and bulk delete operations already apply `created_by = user_id` for non-admin users while allowing admin access.
*   [x] **RLS Fix - Witness Statement Inserts:** Updated `setup_full_db.sql` to replace the broad authenticated insert policy with `WITH CHECK (auth.uid() = created_by)` for `public.witness_statements`.
*   [x] **Login Page Security Review:** Reviewed login, sign-up, password reset, session finalization, and logout flow for stale user state and profile cross-reference risks.
*   [x] **Session Cross-Reference Fix:** Removed caching from the user-scoped Supabase client in `auth_utils.py` because `postgrest.auth()` mutates the client with a bearer token and cached Streamlit resources can be shared across browser sessions.
*   [x] **Session State Isolation:** Updated `finalize_session()` to clear old Streamlit session state before storing the newly authenticated user/session and loading profile/org data.
*   [x] **Auth Consistency Check:** Tightened `check_auth()` so the app only treats authentication as valid when both `user_session` and `supabase_session` exist and refer to the same Supabase user.
*   [x] **Verification Command:** Confirmed Python syntax with `python3 -m py_compile auth_utils.py main.py database.py history.py dashboard.py personal_statement.py witness_statement.py subscription_page.py`.
*   [x] **Production DB Follow-Up:** Apply the updated witness statement RLS policy from `setup_full_db.sql` in the live Supabase SQL Editor if it has not already been applied.

### Manual Verification
1.  **Sign-up Flow:** Register a new user. Verify organization creation in Supabase with **5 credits** and 'free' tier.
2.  **Freemium Limits & Deduction:** Generate 5 reports. Verify `credits_balance` decrements each time in both the UI and Supabase. Ensure the 6th attempt triggers the `st.dialog` paywall.
3.  **API Key Rotation:** Configure multiple Gemini keys in secrets. Simulate a `ResourceExhausted` (429) error and verify the system transparently rotates to the next key.
4.  **Multi-Provider Fallback:** Deplete or disable all Gemini keys. Verify the system automatically falls back to Groq or OpenRouter using the designated fallback models and keys.
5.  **BYOK Unlock:** Upgrade to 'platform_pass'. Verify the sidebar reveals provider settings and allows generation without credit deduction.
6.  **Subscription Lifecycle:** Manually expire a subscription in the DB (>30 days). Verify the UI reflects "Expired" and blocks generation until renewal.
7.  **Production Gate (Phase 2):** 
    *   Verify **Vertex AI** authentication using the Service Account JSON structure in secrets.
    *   Verify **Monnify** payment completion and webhook-driven credit/tier updates.
