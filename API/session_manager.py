import os
import json
import uuid
import time
import redis
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from dotenv import load_dotenv

# --- Load environment variables ---
load_dotenv()

SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")
BACKEND_TEAM_EMAIL = os.getenv("BACKEND_TEAM_EMAIL", RECIPIENT_EMAIL)
PDF_OUTPUT_DIR = os.getenv("PDF_OUTPUT_DIR", "/tmp")

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
SESSION_TTL = int(os.getenv("SESSION_TTL_SECONDS", 300))

r = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)


# --- Create a new chat session ---
def create_session(user_data: dict):
    session_id = str(uuid.uuid4())
    r.setex(f"session:{session_id}:info", SESSION_TTL, json.dumps(user_data))
    r.expire(f"session:{session_id}:chat", SESSION_TTL)
    r.expire(f"session:{session_id}:server", SESSION_TTL)
    return session_id


# --- Save user message ---
def save_user_message(session_id: str, message: str):
    entry = {
        "sender": "User",
        "message": message,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    r.rpush(f"session:{session_id}:chat", json.dumps(entry))
    r.expire(f"session:{session_id}:chat", SESSION_TTL)


# --- Save bot message ---
def save_bot_message(session_id: str, message: str, metadata=None):
    entry = {
        "sender": "Bot",
        "message": message,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "metadata": metadata or {}
    }
    r.rpush(f"session:{session_id}:chat", json.dumps(entry))
    r.expire(f"session:{session_id}:chat", SESSION_TTL)


# --- Save server log ---
def save_server_log(session_id: str, event: str, level="info", data=None):
    entry = {
        "level": level,
        "event": event,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "data": data or {}
    }
    r.rpush(f"session:{session_id}:server", json.dumps(entry))
    r.expire(f"session:{session_id}:server", SESSION_TTL)


# --- Generate PDF report from session data ---
def generate_pdf(session_id: str):
    info_json = r.get(f"session:{session_id}:info")
    if not info_json:
        return None

    info = json.loads(info_json)
    messages = r.lrange(f"session:{session_id}:chat", 0, -1)
    server_logs = r.lrange(f"session:{session_id}:server", 0, -1)

    pdf_filename = os.path.join(PDF_OUTPUT_DIR, f"session_{session_id}.pdf")
    c = canvas.Canvas(pdf_filename, pagesize=A4)
    width, height = A4
    y = height - 50

    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, "EPR Chatbot Session Report")
    y -= 30

    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "User Info:")
    y -= 20
    c.setFont("Helvetica", 10)
    for k, v in info.items():
        c.drawString(60, y, f"{k}: {v}")
        y -= 14

    y -= 20
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Conversation:")
    y -= 20

    for msg_raw in messages:
        msg = json.loads(msg_raw)
        text = f"[{msg['timestamp']}] {msg['sender']}: {msg['message']}"
        c.setFont("Helvetica", 9)
        c.drawString(60, y, text[:1000])  # prevent overflow
        y -= 12
        if y < 80:
            c.showPage()
            y = height - 50

    y -= 20
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Server Logs:")
    y -= 20

    for log_raw in server_logs:
        log = json.loads(log_raw)
        text = f"[{log['timestamp']}] {log['level'].upper()}: {log['event']}"
        c.setFont("Helvetica", 9)
        c.drawString(60, y, text[:1000])
        y -= 12
        if y < 80:
            c.showPage()
            y = height - 50

    c.save()
    return pdf_filename


# --- Send PDF to backend team via email ---
def send_pdf_to_backend(session_id: str):
    pdf_file = generate_pdf(session_id)
    if not pdf_file:
        return {"status": "error", "detail": "No data found for session"}

    info_json = r.get(f"session:{session_id}:info")
    info = json.loads(info_json) if info_json else {}

    msg = MIMEMultipart()
    msg["From"] = SMTP_USERNAME
    msg["To"] = BACKEND_TEAM_EMAIL
    msg["Subject"] = f"EPR Chatbot Conversation Report – {info.get('name', 'User')}"

    body = f"""
Hello Backend Team,

Attached is the EPR Chatbot conversation summary for {info.get('name', 'Unknown')} ({info.get('email', '')}).

Regards,
EPR Chatbot System
"""
    msg.attach(MIMEText(body, "plain"))

    with open(pdf_file, "rb") as f:
        part = MIMEApplication(f.read(), Name=os.path.basename(pdf_file))
        part["Content-Disposition"] = f'attachment; filename="{os.path.basename(pdf_file)}"'
        msg.attach(part)

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(msg)

    return {"status": "sent", "pdf": pdf_file}


# --- Finalize session ---
def finalize_session(session_id: str):
    result = send_pdf_to_backend(session_id)
    r.delete(f"session:{session_id}:info")
    r.delete(f"session:{session_id}:chat")
    r.delete(f"session:{session_id}:server")
    return result
