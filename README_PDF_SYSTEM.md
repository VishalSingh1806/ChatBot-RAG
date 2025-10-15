# 📄 PDF Report System - Complete Documentation

## 🎯 Overview

Your EPR ChatBot now has a fully automated PDF report generation system that:
- **Logs all conversations** to backend server (Redis)
- **Monitors sessions** for inactivity
- **Generates professional PDFs** after 5 minutes
- **Emails reports** to bhakti.patil@recircle.in

## ✅ Files Modified/Created

### Modified Files:
1. **`API/session_reporter.py`** - Enhanced logging and PDF generation
2. **`API/main.py`** - Added background monitor startup
3. **`API/.env`** - Added Redis configuration
4. **`API/requirements.txt`** - Added reportlab dependency

### New Files:
1. **`API/session_monitor.py`** - Background task for monitoring sessions
2. **`API/test_pdf_generation.py`** - Test script
3. **`IMPLEMENTATION_SUMMARY.md`** - Technical summary
4. **`QUICK_START.md`** - Quick start guide
5. **`SYSTEM_FLOW.md`** - Visual flow diagram
6. **`README_PDF_SYSTEM.md`** - This file

## 🚀 Quick Start

```bash
# 1. Start Redis
redis-server

# 2. Install dependencies
cd API
pip install reportlab

# 3. Start API
python main.py
```

**Expected output:**
```
🚀 Starting EPR ChatBot API
✅ Background session monitor started
🔍 Session monitor started - checking every 60 seconds
```

## 📊 PDF Format

Your PDFs match the exact format you specified:

```
EPR Chatbot - Session Report
Session ID: 535b2e50-9c73-4163-9953-d4c03931c59d
Generated: 2025-01-14T12:07:33.495792 UTC

User Information
Name: Chinmay
Email: chinmay123@gmail.com
Phone: 9865342187
Organization: Cog

Lead Information
Priority: High

First Interaction: 2025-01-14T12:06:00
Last Interaction: 2025-01-14T12:07:33

Conversation Transcript
User: I am producer i need help to collect my plastic waste
Bot: As a producer, you need to establish a system...
User: How to calculate EPR target
Bot: EPR targets are generated on the EPR Portal...
...
```

## 📧 Email Configuration

**Current Settings (from .env):**
- **SMTP Server:** smtp.gmail.com
- **Port:** 587
- **From:** bhaktipatil.tech@gmail.com
- **To:** bhakti.patil@recircle.in
- **Password:** Configured in .env

## ⏱️ Automatic Trigger

**When PDF is generated:**
1. User becomes inactive for **5 minutes**
2. Background monitor detects inactivity
3. Fetches all session data from Redis
4. Generates PDF with complete conversation
5. Sends email with PDF attachment
6. Marks session as finalized (prevents duplicates)

## 🔍 Logging

All operations are logged with detailed information:

```
📥 Fetching session data for: {session_id}
👤 User: Chinmay
📧 Email: chinmay123@gmail.com
📞 Phone: 9865342187
🏢 Organization: Cog
🎯 Lead Score: 15
⭐ Priority: high
💬 Chat messages: 8
📄 Generating PDF report...
📧 Sending PDF report via email...
✅ PDF successfully emailed to bhakti.patil@recircle.in
```

## 🧪 Testing

### Test with existing session:
```bash
cd API
python test_pdf_generation.py
```

### Test with new chat:
1. Open frontend: http://localhost:5173
2. Fill form and chat
3. Wait 5 minutes or close chat
4. Check email for PDF

## 📁 File Locations

- **PDFs saved:** `API/reports/session_{id}.pdf`
- **Logs:** Console output
- **Session data:** Redis (keys: `session:*`, `lead:*`)

## ⚙️ Configuration

### Change inactivity timeout:
Edit `API/session_monitor.py`:
```python
INACTIVITY_THRESHOLD_MINUTES = 5  # Change this
```

### Change email recipient:
Edit `API/.env`:
```env
BACKEND_TEAM_EMAIL=your-email@example.com
```

### Change check interval:
Edit `API/session_monitor.py`:
```python
await asyncio.sleep(60)  # Check every 60 seconds
```

## 🔧 Troubleshooting

### Issue: PDF not generating
**Solution:**
- Verify Redis is running: `redis-cli ping`
- Check session has user data: `redis-cli hgetall session:{id}`
- Look for errors in console logs

### Issue: Email not sending
**Solution:**
- Verify SMTP credentials in `.env`
- Check spam/junk folder
- Test SMTP connection manually
- Review email errors in logs

### Issue: Session not detected
**Solution:**
- Ensure form was submitted (user_data_collected = true)
- Check last_interaction timestamp is updating
- Verify session exists: `redis-cli keys "session:*"`

## 📊 Monitoring

### Check active sessions:
```bash
redis-cli keys "session:*"
```

### View session data:
```bash
redis-cli hgetall session:{session_id}
```

### View chat logs:
```bash
redis-cli lrange session:{session_id}:chat 0 -1
```

### Check if finalized:
```bash
redis-cli exists session:{session_id}:finalized
```

## 🎯 Success Indicators

✅ Background monitor starts on API launch  
✅ Sessions checked every 60 seconds  
✅ Inactivity detected after 5 minutes  
✅ PDF generated with all data  
✅ Email sent successfully  
✅ Session marked as finalized  

## 📞 Support

For issues or questions:
1. Check console logs for errors
2. Verify Redis connection
3. Test SMTP settings
4. Review this documentation
5. Run test script: `python test_pdf_generation.py`

## 🎉 Summary

Your system now:
- ✅ Logs all data to backend (Redis)
- ✅ Monitors sessions automatically
- ✅ Generates PDFs after 5 minutes
- ✅ Emails to bhakti.patil@recircle.in
- ✅ Prevents duplicate PDFs
- ✅ Includes user info, lead data, and full chat
- ✅ Professional PDF format
- ✅ Comprehensive logging

**Everything is ready to use! Just start the API and it works automatically.** 🚀
