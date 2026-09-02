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
*   [x] **Auth Synchronicity:** (Optional) Use Supabase JS on the landing page to toggle "Login" vs "Dashboard" buttons based on session.
    *   [x] **SEO & Metadata:** Align OpenGraph tags and canonical URLs across both the landing page and the app.

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

### Phase 5: Small and New Features
These improvements should be implemented as lightweight, query-driven features that do not increase the app memory footprint on Railway or the Streamlit dashboard.

* [x] Add the assessor name to report expander titles for admin views of multiple assessors.
* [x] Add a `Sort By` dropdown to the History page with `Date`, `Student Name`, and `Assessor`; apply sorting at the query level.
* [defer] Add a `Reports generated today` metric on the User Management page using a date-filtered database query.
* [x] Add History filters for `Unit Code` and `Trade Name` without loading all records into memory.
* [defer] Add a report status badge in the history list (e.g. Draft, Finalized) using a compact status field.
* [defer] Add `Word Count` and `Paragraph Count` to report metadata in history results, computed from report text or stored as lightweight fields.
* [x] Add a progress bar for the current unit showing percentage of PCs selected, based on selected count versus total available.
* [x] Add a subscription progress bar on the `My Subscription` page showing days remaining for `platform_pass` users using expiry date math.
* [defer] Add a `Check Payment Status` button that refreshes webhook/payment state from Supabase rather than holding extra session state.
* [defer] Add a sidebar `Help` button linking to WhatsApp support as a simple external action. Existing Support links already cover this.
* [x] Refactor session state initialization into a single helper and shared key manager so app state stays consistent and minimal.
* [x] Encapsulate top-level `main.py` UI logic in a single entrypoint function to avoid accidental re-execution.
* [x] Add a stateless retry decorator for DB calls to handle transient connection resets without preserving retry state in memory.

> **Phase 5 Design Notes:**
> - Keep DB indexes: `idx_reports_created_by` on `assessment_reports(created_by)`, `idx_reports_created_at` on `assessment_reports(created_at DESC)`
> - Prioritize lightweight queries, minimal `st.session_state`, explicit DB sorting/filtering, no large in-process caches, no persistent binary state
> - **Deferred (heavy state / background workflows):** Monnify webhook automation, subscription expiry emails, API usage dashboards, webhook origin verification


### Security Verification
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

---

### Phase 6: QA Assessor Growth & Retention
These features target Quality Assurance Assessors (QAA, IQA, EQA) to make the tool indispensable and attract more users in the NSQ ecosystem.

#### Tier 1 — High Impact / Doable with Current Stack

*   [x] **Photo & Video Evidence Attachments** — (Deferred: requires Supabase Storage setup)
*   [x] **Student Portfolio / Progress Tracker**
    *   ✅ `student_portfolios` and `student_pc_progress` tables with admin-only RLS
    *   ✅ `student_portfolio.py` page with portfolio dashboard, PC progress matrix, create/delete
    *   ✅ Admin-only via `_admin_gate()`
*   [x] **Voice Dictation for Observation Notes**
    *   ✅ `st.audio_input` integrated in dashboard Step 3 (admin-only)
    *   ✅ Gemini transcription pipeline (admin-only expander)
*   [x] **Evidence Matrix Auto-Mapper**
    *   ✅ "Suggest PCs from Notes" button (admin-only)
    *   ✅ AI prompt scans notes + available PCs, returns JSON array
    *   ✅ Auto pre-selects suggested PCs in selection interface
*   [x] **Assessment Templates / Quick Start**
    *   ✅ `assessment_templates` table with admin-only RLS
    *   ✅ Save current PC selection as template (admin-only)
    *   ✅ Load template to pre-fill PC selections (admin-only)

#### Tier 2 — Medium Impact

*   [x] **PWA / Mobile-Optimized Layout**
    *   ✅ Responsive mobile CSS in `main.py` (full-width buttons, stackable columns, touch-friendly inputs)
    *   ✅ Landing page is now an installable PWA (`landing/manifest.json` + `landing/sw.js` + 192/512 icons)
    *   ✅ Service worker uses network-first for navigations + stale-while-revalidate for assets
    *   ⚠️ PWA scope is `nsqassessment.com.ng` only — `app.nsqassessment.com.ng` is a separate origin and remains a normal web app (Option 3 decision; not extending PWA to subdomain for now)

*   [x] **Bulk CSV Import for Cohorts**
    *   ✅ `bulk_csv_import.py` page (admin-only)
    *   ✅ CSV upload + preview + batch-create student portfolios
    *   ✅ Error reporting per row

*   [ ] **IQA / EQA Review Workflow**
    *   Internal/External Quality Assurers can review submitted reports.
    *   Leave comments, approve/reject with feedback, track review status per report.
    *   Database: New `report_reviews` table with reviewer ID, status, timestamp, comments.
    *   **Why:** Adds a second user persona (IQA/EQA) and makes the tool essential across the entire quality assurance chain.

*   [ ] **Export to PDF (in addition to Word)**
    *   Many organizations and accreditation bodies require PDF format.
    *   Implement with `reportlab` or headless browser rendering.
    *   **Why:** Removes a blocker for orgs that mandate PDF submissions.

#### Tier 3 — Big Swing / Long-Term

*   [ ] **Offline-First Mode**
    *   IndexedDB + service worker for offline form filling.
    *   Assessors work in remote sites with no connectivity → sync when back online.
    *   **Why:** Opens up rural and remote assessment centers that currently have no digital tooling.

*   [ ] **QR Code Student ID Integration**
    *   Print a QR code on a physical student badge.
    *   Assessor scans with phone camera → pulls up student portfolio → starts new assessment.
    *   **Why:** Eliminates manual student lookup. Especially powerful in high-volume testing centers.

---

### Phase 7: Sustainable AI Monetization & Cost Recovery

> [!WARNING]
> **Critical driver:** The Google Cloud $300 trial credit is exhausted, which kills the Vertex AI platform key for free users. We must stop subsidizing unlimited free AI and build a self-funding model before the provider cutover.

#### Tier 1 — Emergency Fix (Revenue Gate + Provider Cutover)

*   [x] **Decouple Free Tier from Vertex AI**
    *   [x] Removed Vertex AI as the free-tier default in `ai_policy.py`.
    *   [x] Free tier routes through platform Gemini (`INTERNAL_AI_KEY`) with Groq/OpenRouter fallback.
    *   [x] Free tier keeps strict 5-credit cap, then hard paywall.
    *   [x] Paid tiers (`platform_pass`, `lifetime`, `enterprise`) now BYOK-only — zero platform AI cost.

*   [x] **AI Credit Packs (fastest path to revenue)**
    *   [x] Selar products configured (20/150/400 reports).
    *   [x] "Buy AI Credits" buttons wired in dashboard paywall and subscription page.
    *   [x] `ai_credits_purchased` / `monthly_ai_quota` columns added to `organizations`.
    *   [x] Manual credit-pack top-up via admin panel (`top_up_org_credits`).
    *   [ ] Selar webhook auto-credit (deferred — Gmail bridge already relays sales).

*   [x] **Paywall Enforcement**
    *   [x] Free credits hit 0 → paywall with "Buy Credits" + "Upgrade" paths.
    *   [x] Existing `st.dialog` UX retained so users don't lose typed notes.

#### Tier 2 — Paid Tier AI Quotas (bundle AI into subscriptions)

*   [x] **Attach AI quotas to paid tiers**
    *   [x] `platform_pass`: BYOK-only — **no bundled platform quota** (reverted from 100/month).
    *   [x] `lifetime`: unlimited platform fallback (`platform_quota = None`) + BYOK.
    *   [x] `enterprise`: unlimited platform fallback + BYOK (org-level quota deferred).
    *   [x] `free`: weekly `credits_balance` (5/week), not the monthly quota path.
    *   [x] Unified consumption via `consume_ai_credit(org_id, tier, using_byok)`.

*   [x] **BYOK as the scalable "free" path for heavy users**
    *   [x] Paid users can paste their own Gemini/Groq/OpenRouter key.
    *   [x] Zero platform AI cost when BYOK is used.
    *   [x] `ai_policy.py` prefers BYOK keys when present; platform fallback is tier-dependent.

*   [x] **Quota tracking columns**
    *   [x] `ai_quota_used` + `ai_quota_reset_at` on `organizations` (migration-safe).

*   [x] **Platform Pass current entitlements (2026-09-02)**
    *   [x] BYOK only — must supply their own Gemini/Groq/OpenRouter key to generate.
    *   [x] No platform AI fallback and no bundled monthly reports.
    *   [x] Credit packs are **hidden** for Platform Pass users (prepaid platform reports are meaningless under BYOK-only).
    *   [ ] **Future option:** reintroduce a bundled platform quota or re-enable credit-pack redemption for Platform Pass if we later want to offer platform AI as an add-on.

*   [x] **Credit pack visibility**
    *   [x] Credit packs show for Free and Lifetime users; hidden for Platform Pass (BYOK-only).

#### Tier 3 — Landing Page & Pricing Alignment

*   [x] **Update landing page (`landing/index.html`)**
    *   [x] Replace "Platform AI (Gemini Flash) - Free Forever" framing with a capped free tier.
    *   [x] Surface the AI Credit Pack products next to Platform Pass and Lifetime.
    *   [x] Update the savings calculator to reflect credit-pack pricing and provider costs.
    *   [x] Update FAQ to explain the new credit/quota model (free ≠ unlimited).
    *   [x] Update meta description/keywords to de-emphasize unlimited platform AI.

*   [x] **Update in-app subscription page (`subscription_page.py`)**
    *   [x] Show AI credit balance/quota separately from platform access.
    *   [x] Add "Buy AI Credits" links alongside upgrade/downgrade controls.

*   [x] **Weekly free-credit renewal (Python-side)**
    *   [x] Refill free tier to 5 credits on login after 7 days from `last_credit_depletion`.
    *   [x] Wired in `finalize_session()`; no pg_cron extension required.

*   [x] **Provider cost documentation**
    *   [x] Free Gemini key → platform model `gemini-3.5-flash`.
    *   [x] Paid OpenRouter key → platform fallback `google/gemini-3.5-flash-lite`.
    *   [x] OpenRouter pricing (per 1M tokens): Flash Lite $0.30 input / $2.50 output; Flash $1.50 input / $9.00 output.
    *   [x] Estimated report cost (~3.5k input / 2k output tokens): Flash Lite ≈ ₦9, Flash ≈ ₦35 (at ₦1,500/USD).
    *   [x] Target margin confirmed: all credit packs stay profitable with Flash Lite (₦50/33/25 vs ≈₦9 cost).

#### Tier 4 — Automation (post-revenue)

*   [ ] **Selar webhook integration**
    *   [ ] Auto-credit organizations when a credit-pack or subscription payment clears.
    *   [ ] Store transaction reference for reconciliation.
    *   [ ] Handle refunds/chargebacks gracefully.

*   [ ] **Usage analytics & alerts**
    *   [ ] Track per-org AI spend.
    *   [ ] Alert before a paid quota is exhausted.
    *   [ ] Notify before provider free-tier rate limits are hit.

---

### Phase 8 — NOS Assessment Workbook & Instructor Guide Generator

Generate, from any NOS trade JSON, a **Student Workbook** (questions only) and an **Instructor Guide** (questions + ideal answers + marking schemes), downloadable as Word documents for assessors to share with students.

*   [ ] **Input**
    *   [ ] Accept a NOS trade JSON object (`trade_name`, `level`, `units → learning_outcomes → performance_criteria`).
    *   [ ] Let assessors upload/paste JSON or select an existing course/trade from the app.

*   [ ] **Generation**
    *   [ ] One assessment item per `performance_criteria` (`pc_code`).
    *   [ ] Vary question types: Direct, Scenario-Based, Step-by-Step Procedure, Labeled Diagram, Narrative Explanation.
    *   [ ] Align language/complexity to `level` (Level 2 = foundational; Level 3 = analytical).
    *   [ ] Produce the identical question set in both documents.

*   [ ] **Output documents**
    *   [ ] Student Workbook: questions only, with `Question Type` and `Weight` per PC.
    *   [ ] Instructor Guide: identical questions + comprehensive ideal answers + bulleted grading rubrics.
    *   [ ] Export both as `.docx` (Word) for download/sharing.

*   [ ] **Constraints**
    *   [ ] Never skip a PC.
    *   [ ] Answers must be specific (real standards, pin-outs, safety acts) — no generic "accept any valid answer."
    *   [ ] Student and Instructor question text must match exactly.

#### Sample Generation Prompt

> You are an expert curriculum developer and instructional designer specializing in vocational and technical education. Your task is to ingest a National Occupational Standards (NOS) JSON object and generate two distinct documents: a **Student Workbook (Questions Only)** and an **Instructor Guide (Questions, Answers, and Marking Schemes)**.
>
> **Input schema:** `trade_name`, `level`, and `units` containing `code`, `title`, and `learning_outcomes` (each with `lo_num`, `description`, and `performance_criteria` containing `pc_code` and `description`).
>
> For every `pc_code`, generate exactly one level-appropriate assessment item, varying type by competency nature (Direct, Scenario-Based, Step-by-Step, Diagrammatic, or Narrative). Align complexity to `level` (Level 2 foundational; Level 3 analytical).
>
> **Document 1 — Student Workbook:** questions only, with `Question Type` and `Weight` per PC.
> **Document 2 — Instructor Guide:** identical questions plus comprehensive ideal answers and bulleted grading rubrics.
>
> Never skip a PC; reference real-world technologies, standards, and safety laws; and ensure the question text matches exactly across both documents.

---
### Completed Phases Summary

| Phase | Status | Description |
|-------|--------|-------------|
| Phase 1 | ✅ Complete | Infrastructure, database schema, auth, freemium model |
| Phase 2 | ✅ Complete | Production readiness, Selar integration, Vertex AI, credit guard |
| Phase 3 | ✅ Complete | Prompt engineering overhaul, Field Auditor persona |
| Phase 3.1 | ✅ Complete | Super Admin dashboard, org/user management, API controls |
| Phase 3.2 | ✅ Complete | Auto-renewing credits, bulk ZIP, AI disclaimers, feedback widget |
| Phase 5 | ✅ Complete | Small features: sorting, filters, progress bars, session refactor |
| Security | ✅ Complete | IDOR fixes, RLS policies, session isolation, auth consistency |
| Code Quality | ✅ Complete | 20 issues fixed across critical/high/medium/low (see issues.md) |
| Phase 6 | 🚧 In Progress | QA Assessor Growth & Retention features (Tier 1–2 implemented) |
| Phase 7 | 🚧 In Progress | Sustainable AI monetization (Tiers 1 & 3 implemented) |
| Phase 8 | ⏳ Planned | NOS Assessment Workbook & Instructor Guide Generator |

---
