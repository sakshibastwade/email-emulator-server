# streamlit_app.py
import streamlit as st
import re
import mimetypes
import pandas as pd

st.set_page_config(page_title="Email Simulator (Offline)", layout="wide")
st.title("📧 Email Simulator — Single App Version")

# -----------------------------
# Detection Utilities
# -----------------------------
PHONE_REGEXES = [
    re.compile(r'(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{2,4}\)?[-.\s]?)?\d{6,10}'),
    re.compile(r'\b[6-9]\d{9}\b'),
]
CURRENCY_SYMBOLS = r'[\$\€\£\₹\¥]'
NUMBER_REGEX = re.compile(
    rf'\b{CURRENCY_SYMBOLS}?\s?\d{{1,3}}(?:[,\s]\d{{3}})*(?:\.\d+)?\b|\b{CURRENCY_SYMBOLS}\d+\b'
)
NUM_WORDS = [
    "zero","one","two","three","four","five","six","seven","eight","nine","ten",
    "eleven","twelve","thirteen","fourteen","fifteen","sixteen","seventeen",
    "eighteen","nineteen","twenty","thirty","forty","fifty","sixty","seventy",
    "eighty","ninety","hundred","thousand","lakh","lacs","million","billion","crore"
]
NUM_WORDS_RE = re.compile(
    r'\b(' + r'|'.join(NUM_WORDS) + r')(?:[\s-](' + r'|'.join(NUM_WORDS) + r'))*\b',
    re.IGNORECASE,
)
IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.svg'}


def detect_phone_numbers(text: str):
    found = set()
    for r in PHONE_REGEXES:
        for m in r.findall(text or ""):
            digits = re.sub(r"\D", "", m)
            if 6 <= len(digits) <= 15:
                found.add(m.strip())
    return sorted(found)


def detect_currency_numbers(text: str):
    return list(set(NUMBER_REGEX.findall(text or "")))


def detect_numbers_in_words(text: str):
    return [m.group(0) for m in NUM_WORDS_RE.finditer(text or "")]


def analyze_attachments(attachments):
    total = 0
    image_attached = False
    large = []
    for a in attachments:
        size = a.get("size", 0)
        total += size
        ctype = a.get("content_type") or mimetypes.guess_type(a.get("filename", ""))[0]
        fn = a.get("filename", "unknown")
        if ctype and ctype.startswith("image/"):
            image_attached = True
        else:
            ext = (fn and '.' in fn and fn[fn.rfind('.'):].lower()) or ''
            if ext in IMAGE_EXTS:
                image_attached = True
        if size >= 5 * 1024 * 1024:
            large.append(fn)
    return {"total_size": total, "image_attached": image_attached, "large_attachments": large}


def scan_email(subject, body, attachments):
    flags = []
    text = (subject or "") + " " + (body or "")
    if detect_phone_numbers(text):
        flags.append("phone_numbers")
    if detect_currency_numbers(text):
        flags.append("financial_numbers")
    if detect_numbers_in_words(text):
        flags.append("numbers_in_words")
    att_info = analyze_attachments(attachments)
    if att_info["image_attached"]:
        flags.append("image_attachment")
    if att_info["large_attachments"]:
        flags.append("large_attachment")
    return flags


# -----------------------------
# State storage
# -----------------------------
if "mailbox" not in st.session_state:
    st.session_state.mailbox = []

# -----------------------------
# Compose Section
# -----------------------------
with st.expander("✉️ Compose / Send Email"):
    sender = st.text_input("From", "alice@example.com")
    recipients = st.text_input("To (comma separated)", "bob@example.com")
    subject = st.text_input("Subject")
    body = st.text_area("Body (scanned but not stored)")
    uploaded = st.file_uploader("Attachments", accept_multiple_files=True)

    if st.button("Send Email"):
        attachments = [
            {"filename": f.name, "content_type": f.type, "size": f.size}
            for f in uploaded
        ]
        flags = scan_email(subject, body, attachments)
        eid = str(len(st.session_state.mailbox) + 1)
        email_meta = {
            "ID": eid,
            "Direction": "Outgoing",
            "From": sender,
            "To": recipients,
            "Subject": subject,
            "Attachments": len(attachments),
            "Flags": ", ".join(flags) if flags else "—",
        }
        st.session_state.mailbox.append(email_meta)
        if flags:
            st.error(f"⚠️ Email flagged: {', '.join(flags)}")
        else:
            st.success("✅ Email sent (no flags).")

# -----------------------------
# Simulate Incoming Email
# -----------------------------
with st.expander("📥 Simulate Incoming Email"):
    incoming_sender = st.text_input("From (incoming)", "random@external.com")
    incoming_recipients = st.text_input("To (incoming)", "me@example.com")
    incoming_subject = st.text_input("Subject (incoming)")
    incoming_body = st.text_area("Body (incoming)")
    incoming_files = st.file_uploader("Attachments (incoming)", accept_multiple_files=True, key="incoming")

    if st.button("Receive Email"):
        attachments = [
            {"filename": f.name, "content_type": f.type, "size": f.size}
            for f in incoming_files
        ]
        flags = scan_email(incoming_subject, incoming_body, attachments)
        eid = str(len(st.session_state.mailbox) + 1)
        email_meta = {
            "ID": eid,
            "Direction": "Incoming",
            "From": incoming_sender,
            "To": incoming_recipients,
            "Subject": incoming_subject,
            "Attachments": len(attachments),
            "Flags": ", ".join(flags) if flags else "—",
        }
        st.session_state.mailbox.append(email_meta)
        if flags:
            st.warning(f"⚠️ Incoming email flagged: {', '.join(flags)}")
        else:
            st.info("📩 Incoming email received (no flags).")

# -----------------------------
# Mailbox Table
# -----------------------------
st.header("📂 Mailbox (metadata only)")
if st.session_state.mailbox:
    df = pd.DataFrame(st.session_state.mailbox)
    st.dataframe(df, use_container_width=True)
else:
    st.info("No emails yet.")
