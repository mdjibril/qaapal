# NSQ Portal v1.1.0

A professional AI-powered assessment report generator for the National Skills Qualification (NSQ) framework. This application allows assessors to select Performance Criteria (PC) from a structured database and use Generative AI (Gemini, Groq, or OpenRouter) to synthesize professional technical narratives..

## 🚀 Features

- **Multi-Provider AI Integration:** Support for Google Gemini, Groq (Llama), and OpenRouter models.
- **Structured NOS Management:** Hierarchical selection of Trades, Units, Learning Outcomes, and Performance Criteria.
- **Automated Report Generation:** Real-time synthesis of observation narratives with mapped criteria summaries.
- **History & Export:** Full history of generated reports with one-click export to professional Word (.docx) documents.
- **Role-Based Access Control (RBAC):** Distinct views and permissions for Admin and Assessor roles via Supabase Auth.

### 🛠️ Assessment Tools
- **Observation Reports:** Synthesis of professional technical narratives from assessor notes and selected Performance Criteria (PC).
- **Personal Statements:** Student-focused tool to convert self-reflections into formal first-person statements of competence.
- **Witness Testimonies:** Formal validation tool for supervisors and expert witnesses to provide evidence of candidate performance.
- **Word Export:** One-click generation of standardized NSQ forms (CPN-ARF-02) using `python-docx`.

### 🤖 AI Intelligence & Routing
- **Hybrid AI Engine:** Seamlessly switches between **Google Vertex AI** (Platform tier) and **BYOK (Bring Your Own Key)** for Pro users.
- **Multi-Provider Support:** Native integration with Gemini 2.0/1.5, Groq (Llama 3.3), and OpenRouter.
- **Smart Mapping:** Proprietary prompting logic ensures inline mapping of Unit codes and PCs within the narrative.

### 💳 SaaS & Billing Logic
- **Freemium Model:** New users start with 5 free credits.
- **Platform Pass:** Monthly subscription via **Selar** integration for unlimited generations.
- **Credit Guard:** Automatic credit deduction and paywall intercepts to prevent data loss.
- **Automated Provisioning:** Webhook-driven (Edge Functions) subscription upgrades upon successful payment.

### 🔐 Security & Management
- **RBAC (Role-Based Access Control):** Granular permissions for Admins, Assessors, and Students.
- **Self-Healing Profiles:** Automatic initialization of user profiles and organization workspaces during first-time login.
- **Session Persistence:** Intelligent session restoration that recovers user roles and organization data even after server restarts.

## 🏷️ Release Notes

- **Current version:** `v1.1.0`
- **Highlights:** Fish farming NOS export parsing now supports mixed-case codes like `AqCS/FFA/007/L3`, the seed script supports `--file`, `--trade`, and `--level`, and history rows now display the report level next to the trade name.

## 🛠️ Tech Stack

- **Frontend:** [Streamlit](https://streamlit.io/)
- **Backend/DB:** Supabase (PostgreSQL, Edge Functions, Auth)
- **Document Generation:** [python-docx](https://python-docx.readthedocs.io/)
- **AI Engines:** Google Vertex AI, Gemini API, Groq SDK, OpenRouter

## 📁 Project Structure

- `main.py`: Central orchestration and navigation.
- `dashboard.py`: Assessor observation workspace.
- `personal_statement.py` / `witness_statement.py`: Specialized statement generation modules.
- `subscription_page.py`: Billing and plan management UI.
- `history.py`: Database retrieval and document re-exporting.
- `auth_utils.py`: Authentication, session finalization, and secret management.
- `database.py`: Data access layer for trade and NOS data.
- `ai_utils.py`: Modular router for different AI providers.
- `file_utils.py`: Standardized Word document formatting logic.

## ⚙️ Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/mdjibril/qaapal.git
   ```
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure Secrets:**
   Create a `.streamlit/secrets.toml` file with your Supabase credentials:
   ```toml
   [connections.supabase]
   PROJECT_URL = "https://your-project-id.supabase.co"
   ANON_KEY = "your_supabase_anon_key"
   SERVICE_ROLE_KEY = "your_supabase_service_role_key"
   
   [vertex_ai]
   service_account_json = '{"your": "json_here"}'
   
   [payments]
   selar_link = "https://selar.co/your-link"
   selar_lifetime_link = "https://selar.co/your-lifetime-link"
   
   [SITE_URL]
   "https://app.nsqassessment.com.ng"
   ```
4. **Initialize Database:**
   - Copy the contents of `setup_db_supabase.sql` and run them in the **SQL Editor** of your Supabase dashboard.
   - Enable RLS or set up policies as required.
5. **Seed Data:**
   Set your database environment variables and run the seed script to populate the NOS criteria:
   ```bash
   python seed.py
   ```
   Useful targeted seeding commands:
   ```bash
   python3 seed.py --file "data/level-3/NOS ICT Web Development L3.json"  # Seed one exact NOS file
   python3 seed.py --trade "ICT Web Development"  # Seed every NOS file for one trade
   python3 seed.py --trade "ICT Web Development" --level 3  # Seed only Level 3 for that trade
   ```
6. **Run the app:**
   ```bash
   streamlit run main.py
   ```

## 🛠️ Database Maintenance

- If signup marketing fields are not showing up in `user_profiles`, verify the `on_auth_user_created` trigger in the Supabase SQL Editor.
- The trigger function should store `marketing_source`, `primary_trade`, `monthly_report_volume`, and `assessor_role` from `auth.users.raw_user_meta_data`.
- If the trigger looks outdated, re-run the patched function and trigger definition from the SQL Editor instead of re-running the full database setup script.
- When seeding a specific NOS file, use `--file`; when you want a whole trade, use `--trade`; when you want one level, add `--level`.

## 🚂 Deployment on Railway.io

1. **Create a new Project:** Link your GitHub repository to Railway.
2. **Configure Variables:** Add the following environment variables in the Railway dashboard. Note the use of `__` to match Streamlit's secrets structure:
   - `connections__supabase__PROJECT_URL`
   - `connections__supabase__ANON_KEY`
   - `connections__supabase__SERVICE_ROLE_KEY`
   - `vertex_ai__service_account_json`
   - `payments__selar_link`
   - `payments__selar_lifetime_link`
   - `BRIDGE_SECRET` (For webhook security)
3. **Start Command:** Railway should detect the `requirements.txt` and python environment. Ensure your start command is:
   ```bash
   streamlit run main.py --server.port $PORT --server.address 0.0.0.0
   ```
4. **Networking:** Railway will automatically provide a public URL once the build is complete.

### 💡 Tips for Production
- Ensure the `SERVICE_ROLE_KEY` is kept private and only used on the server side.
- Configure the `SITE_URL` in Supabase Auth settings to match your production domain for correct password reset and email confirmation redirects.
- Keep the `BRIDGE_SECRET` synced between Railway and your Payment Webhook (GAS or Supabase Edge Function).
