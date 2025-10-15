import os
import redis
import smtplib
import logging
import json
from datetime import datetime
from dotenv import load_dotenv
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.utils import simpleSplit

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Redis setup
redis_client = redis.StrictRedis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    db=0,
    decode_responses=True
)

# SMTP
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
BACKEND_EMAIL = os.getenv("BACKEND_TEAM_EMAIL", os.getenv("RECIPIENT_EMAIL"))
SALES_EMAIL = os.getenv("SALES_TEAM_EMAIL")

OUTPUT_DIR = os.path.join(os.getcwd(), "reports")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --------------------------------------------------------
# Fetch full session data
# --------------------------------------------------------
def fetch_full_session(session_id: str):
    session_key = f"session:{session_id}"
    lead_key = f"lead:{session_id}"
    chat_key = f"session:{session_id}:chat"
    
    session_info = redis_client.hgetall(session_key)
    lead_info = redis_client.hgetall(lead_key)
    chat_logs = redis_client.lrange(chat_key, 0, -1)
    
    # Enhanced logging
    logging.info(f"📥 Fetching session data for: {session_id}")
    logging.info(f"🔑 Session key: {session_key}, exists: {redis_client.exists(session_key)}")
    logging.info(f"🔑 Lead key: {lead_key}, exists: {redis_client.exists(lead_key)}")
    logging.info(f"🔑 Chat key: {chat_key}, exists: {redis_client.exists(chat_key)}")
    logging.info(f"👤 User: {session_info.get('user_name', 'N/A')}")
    logging.info(f"📧 Email: {session_info.get('email', 'N/A')}")
    logging.info(f"📞 Phone: {session_info.get('phone', 'N/A')}")
    logging.info(f"🏢 Organization: {session_info.get('organization', 'N/A')}")
    logging.info(f"🎯 Lead Score: {lead_info.get('lead_score', 'N/A')}")
    logging.info(f"⭐ Priority: {lead_info.get('priority', 'N/A')}")
    logging.info(f"💬 Chat messages retrieved: {len(chat_logs)}")
    
    if len(chat_logs) == 0:
        logging.warning(f"⚠️ No chat logs found for session {session_id}")
    else:
        logging.info(f"✅ First message: {chat_logs[0][:50]}...")
        logging.info(f"✅ Last message: {chat_logs[-1][:50]}...")
    
    return session_info, chat_logs, lead_info

# --------------------------------------------------------
# Generate PDF
# --------------------------------------------------------
def generate_pdf(session_id: str, session_info: dict, chat_logs: list, lead_info: dict):
    organization = session_info.get('organization', 'Company').replace(' ', '_')
    pdf_path = os.path.join(OUTPUT_DIR, f"EPR_Lead_from_{organization}.pdf")
    c = canvas.Canvas(pdf_path, pagesize=letter)
    width, height = letter
    y = height - 50

    def draw_box(title):
        nonlocal y
        c.setFillColor(colors.HexColor('#184040'))
        c.rect(40, y - 20, width - 80, 25, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 13)
        c.drawString(50, y - 10, title)
        c.setFillColor(colors.black)
        y -= 35

    def write_line(text, font="Helvetica", size=10):
        nonlocal y
        text = text.replace('•', '').replace('■', '').replace('**', '')
        c.setFont(font, size)
        wrapped = simpleSplit(text, font, size, width - 100)
        for line in wrapped:
            if y < 70:
                c.showPage()
                y = height - 50
                c.setFont(font, size)  # Reset font after new page
            c.drawString(60, y, line.strip())
            y -= 12
        y -= 3

    # Header
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(width / 2, y, "Lead Analysis and Details")
    y -= 50

    # User Info
    y -= 10
    draw_box("User Information")
    c.setFont("Helvetica-Bold", 10)
    for key, label in {
        "user_name": "Name",
        "email": "Email",
        "phone": "Phone",
        "organization": "Organization"
    }.items():
        c.drawString(60, y, f"{label}:")
        c.setFont("Helvetica", 10)
        c.drawString(150, y, session_info.get(key, 'N/A'))
        c.setFont("Helvetica-Bold", 10)
        y -= 15
    y -= 5

    # Lead Info
    y -= 10
    draw_box("Lead Information")
    priority = lead_info.get("priority", "N/A").capitalize()
    
    # Format timestamps
    first_interaction = lead_info.get('first_interaction', 'N/A')
    last_interaction = lead_info.get('last_interaction', 'N/A')
    
    if first_interaction != 'N/A':
        try:
            dt = datetime.fromisoformat(first_interaction)
            first_interaction = dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            pass
    
    if last_interaction != 'N/A':
        try:
            dt = datetime.fromisoformat(last_interaction)
            last_interaction = dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            pass
    
    c.setFont("Helvetica-Bold", 10)
    c.drawString(60, y, "Priority:")
    c.setFont("Helvetica", 10)
    c.drawString(150, y, priority)
    y -= 20
    
    c.setFont("Helvetica-Bold", 10)
    c.drawString(60, y, "First Interaction:")
    c.setFont("Helvetica", 10)
    c.drawString(150, y, first_interaction)
    y -= 15
    
    c.setFont("Helvetica-Bold", 10)
    c.drawString(60, y, "Last Interaction:")
    c.setFont("Helvetica", 10)
    c.drawString(150, y, last_interaction)
    y -= 10

    # Conversation
    y -= 10
    draw_box("Conversation Transcript")
    if not chat_logs:
        c.setFont("Helvetica", 10)
        c.drawString(60, y, "No chat messages found for this session.")
    else:
        for i, msg in enumerate(chat_logs):
            msg = msg.replace('•', '').replace('■', '').replace('**', '')
            c.setFont("Helvetica", 10)
            wrapped = simpleSplit(msg, "Helvetica", 10, width - 100)
            for line in wrapped:
                if y < 70:
                    c.showPage()
                    y = height - 50
                    c.setFont("Helvetica", 10)  # Reset font after new page
                c.drawString(60, y, line.strip())
                y -= 12
            if msg.startswith("Bot:") and i < len(chat_logs) - 1:
                y -= 10

    c.save()
    logging.info(f"✅ PDF created: {pdf_path}")
    return pdf_path

# --------------------------------------------------------
# Email PDF
# --------------------------------------------------------
def send_pdf_report(session_id: str, pdf_path: str, session_info: dict, lead_info: dict):
    logging.info(f"📧 Preparing to send PDF report for session {session_id}")
    
    msg = MIMEMultipart()
    msg["From"] = SMTP_USERNAME
    msg["To"] = BACKEND_EMAIL
    msg["Subject"] = f"EPR Chatbot Session Report - {session_info.get('user_name', 'Unknown')}"

    priority = lead_info.get('priority', 'low').upper()
    body = f"""
📄 EPR Chatbot Session Summary

👤 User: {session_info.get('user_name', 'N/A')}
📧 Email: {session_info.get('email', 'N/A')}
📞 Phone: {session_info.get('phone', 'N/A')}
🏢 Organization: {session_info.get('organization', 'N/A')}

🎯 Lead Priority: {priority}
💬 Total Queries: {lead_info.get('total_queries', 'N/A')}

🕒 Session ID: {session_id}
🗓️ Generated: {datetime.utcnow().isoformat()} UTC

Please find the detailed session report attached.
    """
    msg.attach(MIMEText(body, "plain"))

    with open(pdf_path, "rb") as f:
        part = MIMEApplication(f.read(), Name=os.path.basename(pdf_path))
    part["Content-Disposition"] = f'attachment; filename="{os.path.basename(pdf_path)}"'
    msg.attach(part)

    logging.info(f"📤 Sending email to {BACKEND_EMAIL}")
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=30) as server:
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(msg)

    logging.info(f"✅ PDF successfully emailed to {BACKEND_EMAIL}")

# --------------------------------------------------------
# Finalize session
# --------------------------------------------------------
def finalize_session(session_id: str):
    logging.info(f"🔄 Starting session finalization for: {session_id}")
    
    session_info, chat_logs, lead_info = fetch_full_session(session_id)
    
    if not session_info:
        logging.warning(f"⚠️ No session info found for {session_id}")
        return
    
    logging.info(f"📄 Generating PDF report...")
    pdf_path = generate_pdf(session_id, session_info, chat_logs, lead_info)
    
    logging.info(f"📧 Sending PDF report via email...")
    send_pdf_report(session_id, pdf_path, session_info, lead_info)
    
    logging.info(f"✅ Session finalization completed for {session_id}")
