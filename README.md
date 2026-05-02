# NSQ Portal v1.0.1

A professional AI-powered assessment report generator for the National Skills Qualification (NSQ) framework. This application allows assessors to select Performance Criteria (PC) from a structured database and use Generative AI (Gemini, Groq, or OpenRouter) to synthesize professional technical narratives.

## 🚀 Features

- **Multi-Provider AI Integration:** Support for Google Gemini, Groq (Llama), and OpenRouter models.
- **Structured NOS Management:** Hierarchical selection of Trades, Units, Learning Outcomes, and Performance Criteria.
- **Automated Report Generation:** Real-time synthesis of observation narratives with mapped criteria summaries.
- **History & Export:** Full history of generated reports with one-click export to professional Word (.docx) documents.
- **Role-Based Access Control (RBAC):** Distinct views and permissions for Admin and Assessor roles via Supabase Auth.

## 🛠️ Tech Stack

- **Frontend:** [Streamlit](https://streamlit.io/)
- **Database:** [Supabase](https://supabase.com/) (PostgreSQL)
- **ORM:** [SQLAlchemy](https://www.sqlalchemy.org/)
- **Document Generation:** [python-docx](https://python-docx.readthedocs.io/)
- **AI Engines:** Google Generative AI, Groq SDK, OpenRouter API

## 📁 Project Structure

- `main.py`: Central orchestration and navigation.
- `dashboard.py`: The primary report generation workspace.
- `history.py`: Database retrieval and document re-exporting.
- `auth_utils.py`: Security layer handling Supabase Auth and sessions.
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
   ```
4. **Initialize Database:**
   - Copy the contents of `setup_db_supabase.sql` and run them in the **SQL Editor** of your Supabase dashboard.
   - Enable RLS or set up policies as required.
5. **Seed Data:**
   Set your database environment variables and run the seed script to populate the NOS criteria:
   ```bash
   python seed.py
   ```
6. **Run the app:**
   ```bash
   streamlit run main.py
   ```