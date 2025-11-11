\
        # server.py
        import os
        import smtplib
        from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Header
        from pydantic import BaseModel, EmailStr
        from typing import List, Optional
        from detectors import detect_phone_numbers, detect_currency_numbers, detect_numbers_in_words, analyze_attachments
        from email.message import EmailMessage

        app = FastAPI(title="Email Simulator Server")

        MAILBOX = []
        MANAGER_EMAIL = os.getenv("MANAGER_EMAIL", "")
        MANAGER_WEBHOOK = os.getenv("MANAGER_WEBHOOK", "")
        SMTP_HOST = os.getenv("SMTP_HOST")
        SMTP_PORT = int(os.getenv("SMTP_PORT") or 0)
        SMTP_USER = os.getenv("SMTP_USER")
        SMTP_PASS = os.getenv("SMTP_PASS")
        API_KEY = os.getenv("API_KEY", "changeme")

        class AttachmentMeta(BaseModel):
            filename: str
            content_type: Optional[str] = None
            size: int

        class PrepareEmailRequest(BaseModel):
            sender: EmailStr
            recipients: List[EmailStr]
            subject: Optional[str] = ""
            body: Optional[str] = ""
            attachments: Optional[List[AttachmentMeta]] = []

        def _scan_email_meta(subject: str, body: str, attachments: List[dict]) -> List[str]:
            flags = []
            att_info = analyze_attachments(attachments)
            if att_info["image_attached"]:
                flags.append("image_attachment")
            if att_info["large_attachments"]:
                flags.append("large_attachment:" + ",".join(att_info["large_attachments"]))
            phones = detect_phone_numbers(body + " " + subject)
            if phones:
                flags.append("phone_numbers:" + ",".join(phones))
            money = detect_currency_numbers(body + " " + subject)
            if money:
                flags.append("financial_numbers:" + ",".join(money))
            words = detect_numbers_in_words(body + " " + subject)
            if words:
                flags.append("numbers_in_words:" + ",".join(words[:5]))
            return flags

        def _notify_manager(email_meta: dict, flags: List[str]):
            subject = f"[ALERT] Email flagged: {email_meta.get('subject','(no-subject)')}"
            body = f"An email from {email_meta['sender']} to {', '.join(email_meta['recipients'])} was flagged.\\n\\nFlags: {', '.join(flags)}\\n\\nEmail ID: {email_meta['id']}\\n(Note: body not disclosed.)"
            if MANAGER_WEBHOOK:
                try:
                    import requests
                    requests.post(MANAGER_WEBHOOK, json={"text": subject + "\\n" + body}, timeout=5)
                    return True
                except Exception as e:
                    print("Webhook notify failed:", e)
            if MANAGER_EMAIL and SMTP_HOST and SMTP_PORT:
                try:
                    msg = EmailMessage()
                    msg['Subject'] = subject
                    msg['From'] = SMTP_USER or "noreply@example.com"
                    msg['To'] = MANAGER_EMAIL
                    msg.set_content(body)
                    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as s:
                        if SMTP_USER and SMTP_PASS:
                            s.starttls()
                            s.login(SMTP_USER, SMTP_PASS)
                        s.send_message(msg)
                    return True
                except Exception as e:
                    print("SMTP notify failed:", e)
            print("Manager notification (simulated):", subject, body)
            return False

        def _check_api_key(authorization: str = Header(None)):
            if not authorization:
                raise HTTPException(status_code=401, detail="Missing API Key")
            if authorization != f"Bearer {API_KEY}":
                raise HTTPException(status_code=403, detail="Invalid API Key")

        @app.post("/prepare-email")
        async def prepare_email(req: PrepareEmailRequest, authorization: str = Header(None)):
            _check_api_key(authorization)
            attachments = [a.dict() for a in (req.attachments or [])]
            flags = _scan_email_meta(req.subject or "", req.body or "", attachments)
            flagged = len(flags) > 0
            eid = str(len(MAILBOX) + 1)
            meta = {
                "id": eid,
                "direction": "outgoing",
                "sender": req.sender,
                "recipients": req.recipients,
                "subject": req.subject,
                "attachments": attachments,
                "flags": flags,
            }
            MAILBOX.append(meta)
            if flagged:
                _notify_manager(meta, flags)
            return {"email_id": eid, "flagged": flagged, "flags": flags}

        @app.post("/ingest-incoming")
        async def ingest_incoming(
            sender: EmailStr = Form(...),
            recipients: str = Form(...),
            subject: str = Form(""),
            body: str = Form(""),
            files: Optional[List[UploadFile]] = File(None),
            authorization: str = Header(None)
        ):
            _check_api_key(authorization)
            attachments_meta = []
            if files:
                for f in files:
                    content = await f.read()
                    attachments_meta.append({
                        "filename": f.filename,
                        "content_type": f.content_type,
                        "size": len(content)
                    })
            flags = _scan_email_meta(subject or "", body or "", attachments_meta)
            eid = str(len(MAILBOX) + 1)
            meta = {
                "id": eid,
                "direction": "incoming",
                "sender": sender,
                "recipients": [r.strip() for r in recipients.split(",")],
                "subject": subject,
                "attachments": attachments_meta,
                "flags": flags
            }
            MAILBOX.append(meta)
            if flags:
                _notify_manager(meta, flags)
            return {"email_id": eid, "flagged": bool(flags), "flags": flags}

        @app.get("/mailbox")
        def get_mailbox(authorization: str = Header(None)):
            _check_api_key(authorization)
            return MAILBOX

        @app.get("/mailbox/{email_id}")
        def get_mail_meta(email_id: str, authorization: str = Header(None)):
            _check_api_key(authorization)
            for m in MAILBOX:
                if m["id"] == email_id:
                    return m
            raise HTTPException(status_code=404, detail="Email not found")
