# Email Simulator — Ready-to-push Repo

This repository provides an Email Simulator Server (FastAPI) and a Streamlit UI that
monitors incoming/outgoing emails but does NOT expose email bodies to users.
It scans metadata & attachments for phone numbers, financial numbers, numbers-in-words,
attachment sizes, and detects image attachments. Flagged emails are notified to a manager.

## Quick start (local)

1. Create virtualenv and install:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Start API server:
   ```bash
   uvicorn server:app --reload --port 8000
   ```
3. Start Streamlit UI:
   ```bash
   streamlit run streamlit_app.py
   ```
4. Open Streamlit UI at http://localhost:8501

## Files
- server.py: FastAPI server (metadata-only storage)
- detectors.py: detection utilities
- streamlit_app.py: Streamlit UI (does not show bodies)
- requirements.txt: Python dependencies
- .env.example: example environment variables
- tests/: simple unit tests for detectors
- .github/workflows/ci.yml: CI to run tests

## Notes
- This repo is a simulation starter. For production, add authentication, DB, TLS, and secure secrets.
