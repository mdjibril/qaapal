# Issues

## 🔴 Critical

1. [x] `file_utils.py:1` — Unused `from curses import meta` crashes on Windows
2. [x] `history.py:470` — `for...else` indentation bug causes double display
3. [x] `dashboard.py:55,79` — Redundant `fetch_nested_nos` called twice
4. [x] `admin_panel.py:63-118` — Duplicated code block

## 🟠 High

5. [x] `main.py:157` — Expired pass not persisted to DB
6. [x] `admin_panel.py:68` — Broken secret detection logic
7. [x] `database.py:286` — Falsy `0` count check
8. [x] `ai_utils.py:29` — `st.session_state` in business logic

## 🟡 Medium

9. [x] `database.py:352` — Dead mock payment dialog
10. [x] `subscription_page.py:91` vs `database.py:352` — Pricing inconsistency (₦3,500 vs ₦7,000)
11. [x] `file_utils.py:216` — Unused parameters `witness_name/role`
12. [x] `file_utils.py:304` — Typo "perfumed" → "performed"
13. [x] `security_utils.py:23` — Overly aggressive char stripping
14. [x] `components.py:72` — `st.progress(text=)` needs Streamlit ≥1.36 (verified: pinned at 1.56.0, not a bug)

## 🔵 Low

15. [x] `seed.py` — Module-level Streamlit import in CLI-only tool
16. [x] `ai_utils.py:177` — Connection test wastes API tokens
17. [x] `admin_panel.py:92` — Mock webhook data instead of real data
18. [x] `personal_statement.py:158` — Save lock without timeout
19. [x] `account_settings.py:48` — Relies on RLS for profile updates
20. [x] `history.py:153` — Unused parameters in `display_report_item`
