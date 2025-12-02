<!-- .github/copilot-instructions.md -->
# Copilot / AI agent instructions — blank-app

Purpose: help an AI coding agent be immediately productive working on this Streamlit template.

- Big picture:
  - Single-process Streamlit app. Entrypoint: `streamlit_app.py`.
  - UI is split into page modules: `main_page.py`, `page_2.py`, `page_3.py`.
  - Navigation is defined programmatically in `streamlit_app.py` using `st.Page(...)` and `st.navigation([...])`, then `pg.run()` to dispatch the selected page.

- How to run locally (used by humans and CI checks):
  - Install deps: `pip install -r requirements.txt` (`requirements.txt` currently lists `streamlit`).
  - Launch: `streamlit run streamlit_app.py` (use `--server.port` or `--global` flags if needed).

- Common code patterns you should preserve or follow:
  - Pages are standalone modules that call Streamlit top-level APIs (e.g. `st.markdown`, `st.sidebar.*`) at module import time. Do not refactor pages into background-only functions without updating the navigation registration.
  - `streamlit_app.py` is the single place that wires pages into the app. To add/remove pages, edit `streamlit_app.py` to add a `st.Page("my_page.py", title=..., icon=...)` entry and include it in the `st.navigation([...])` list.
  - Session state usage: examples are present (commented) in `streamlit_app.py`. Persist user values via `st.session_state` when needed.

- Project-specific notes and examples (from repo):
  - Menu & pages: `st.sidebar.title("MENU")` in `streamlit_app.py` and page files use `st.sidebar.markdown(...)`.
  - Example registration (copy/modify):
    ```py
    main_page = st.Page("main_page.py", title="Vendas", icon="🛒")
    page_2 = st.Page("page_2.py", title="Financeiro", icon="📈")
    pg = st.navigation([main_page, page_2, page_3])
    pg.run()
    ```

- Dependencies & integrations:
  - No external services are referenced in source. All UI logic is self-contained in page modules.
  - `requirements.txt` is authoritative for runtime deps; modify it when adding packages.

- Development & debugging tips for edits made by AI:
  - Run `streamlit run streamlit_app.py` after changes to verify pages render and there are no import errors.
  - If adding heavy processing, move it behind a button or cache with `st.cache_data` / `st.cache_resource` to avoid slow page loads.
  - Keep changes to a single page per PR to make visual review quick.

- What not to change without human review:
  - The app wiring pattern in `streamlit_app.py` (page registration and `pg.run()`), unless you update all pages consistently.
  - Global import side-effects that could slow startup (e.g., large dataset loads at module import time).

If anything here is unclear or you want the instructions in Portuguese, tell me which parts to expand or adjust.
