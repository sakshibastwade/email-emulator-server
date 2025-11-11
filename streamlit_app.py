# streamlit_app.py
import streamlit as st
import requests
import os
import pandas as pd

API_BASE = os.getenv("EMAIL_SIM_API", "http://localhost:8000")
API_KEY = os.getenv("API_KEY", "changeme")

st.set_page_config(page_title="Email Simulator", layout="wide")
st.title("Email Simulator — Inbox (metadata-only)")

# --- Compose Email ---
with st.expander("Compose / Prepare Email (Outgoing)"):
    sender = st.text_input("From (email)", value="alice@example.com")
    recipients = st.text_area("To (comma separated)", value="bob@example.com")
    subject = st.text_input("Subject")
    body = st.text_area("Body (note: body will be scanned but not stored)")
    uploaded = st.file_uploader("Attachments (multiple allowed)", accept_multiple_files=True)

    if st.button("Prepare & Send"):
        atts = []
        for f in uploaded:
            atts.append({
                "filename": f.name,
                "content_type": f.type,
                "size": f.size
            })
        payload = {
            "sender": sender,
            "recipients": [r.strip() for r in recipients.split(",") if r.strip()],
            "subject": subject,
            "body": body,
            "attachments": atts
        }
        try:
            headers = {"Authorization": f"Bearer {API_KEY}"}
            r = requests.post(f"{API_BASE}/prepare-email", json=payload, headers=headers, timeout=10)
            r.raise_for_status()
            j = r.json()
            if j.get("flagged"):
                st.error(f"Email flagged: {j.get('flags')}")
            else:
                st.success("Email prepared and sent (no flags).")
        except Exception as e:
            st.error(f"API error: {e}")

# --- Inbox Table ---
st.header("Mailbox (metadata only)")
try:
    headers = {"Authorization": f"Bearer {API_KEY}"}
    r = requests.get(f"{API_BASE}/mailbox", headers=headers, timeout=5)
    r.raise_for_status()
    mailbox = r.json()
except Exception as e:
    st.error("Cannot reach server: " + str(e))
    mailbox = []

if mailbox:
    rows = []
    for m in mailbox[::-1]:
        rows.append({
            "ID": m["id"],
            "Direction": m.get("direction"),
            "From": m.get("sender"),
            "To": ", ".join(m.get("recipients", [])),
            "Subject": m.get("subject", ""),
            "Attachments": len(m.get("attachments", [])),
            "Flags": ", ".join(m.get("flags", [])) or "—"
        })
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True)

    st.markdown("**View email metadata**")
    sel = st.text_input("Enter Email ID to view metadata (no body):")
    if sel:
        try:
            res = requests.get(f"{API_BASE}/mailbox/{sel}", headers=headers, timeout=5)
            if res.status_code == 200:
                meta = res.json()
                st.json(meta)
                if meta.get("flags"):
                    st.warning("This email is flagged. Manager has been notified (if configured).")
            else:
                st.error("Email not found.")
        except Exception as e:
            st.error("Error fetching email metadata: " + str(e))
else:
    st.info("Mailbox is empty.")
