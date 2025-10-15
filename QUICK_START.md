# Quick Start Guide - PDF Report System

## ✅ What Was Implemented

Your EPR ChatBot now automatically:
1. **Logs all chat data** to Redis in real-time
2. **Monitors sessions** in the background
3. **Generates PDF reports** after 5 minutes of inactivity
4. **Emails PDFs** to bhakti.patil@recircle.in

## 🚀 How to Start

### 1. Make sure Redis is running:
```bash
redis-server
```

### 2. Install new dependency (if needed):
```bash
cd API
pip install reportlab
```

### 3. Start the API:
```bash
cd API
python main.py
```

You should see:
```
🚀 Starting EPR ChatBot API
✅ Background session monitor started
🔍 Session monitor started - checking every 60 seconds
```

## 📊 What Happens Automatically

### When User Chats:
- Every message is logged to Redis
- Session data is updated with timestamps
- Lead scoring happens in real-time

### After 5 Minutes of Inactivity:
```
⏰ Session {id} inactive for 5.0 minutes - generating PDF
📥 Fetching session data for: {id}
👤 User: {name}
📧 Email: {email}
📞 Phone: {phone}
🏢 Organization: {org}
🎯 Lead Score: {score}
⭐ Priority: {priority}
💬 Chat messages: {count}
📄 Generating PDF report...
📧 Sending PDF report via email...
📤 Sending email to bhakti.patil@recircle.in
✅ PDF successfully emailed
✅ Session finalization completed
```

## 📁 Where PDFs Are Saved

PDFs are saved in: `API/reports/session_{session_id}.pdf`

## 📧 Email Details

**From:** bhaktipatil.tech@gmail.com  
**To:** bhakti.patil@recircle.in  
**Subject:** EPR Chatbot Session Report - {User Name}

**Email includes:**
- User details (name, email, phone, organization)
- Lead priority (HIGH/MEDIUM/LOW)
- Total queries count
- PDF attachment with full conversation

## 🧪 Test It Now

### Option 1: Test with existing session
```bash
cd API
python test_pdf_generation.py
```

### Option 2: Create a new chat session
1. Open frontend: http://localhost:5173
2. Fill the form and chat
3. Wait 5 minutes (or close the chat)
4. Check your email for the PDF!

## 📝 Monitor Logs

Watch the console for real-time updates:
- 🔍 = Session monitoring
- ⏰ = Inactivity detected
- 📥 = Fetching data
- 📄 = Generating PDF
- 📧 = Sending email
- ✅ = Success
- ❌ = Error

## ⚙️ Configuration

### Change inactivity timeout:
Edit `API/session_monitor.py`:
```python
INACTIVITY_THRESHOLD_MINUTES = 5  # Change to 3, 10, etc.
```

### Change email recipients:
Edit `API/.env`:
```
BACKEND_TEAM_EMAIL=your-email@example.com
```

## 🔧 Troubleshooting

### PDF not generating?
- Check Redis is running: `redis-cli ping` (should return PONG)
- Check logs for errors
- Verify session has user data collected

### Email not sending?
- Verify SMTP credentials in `.env`
- Check spam folder
- Look for email errors in logs

### Session not detected?
- Ensure user filled the form (user_data_collected = true)
- Check Redis: `redis-cli keys "session:*"`
- Verify last_interaction timestamp is updating

## 📞 Support

If you encounter issues:
1. Check the logs in console
2. Verify Redis connection
3. Test SMTP settings
4. Run test_pdf_generation.py

## 🎉 Success Indicators

You'll know it's working when you see:
1. ✅ Background session monitor started (on API startup)
2. 🔍 Session monitor checking every 60 seconds
3. ⏰ Inactivity detected after 5 minutes
4. ✅ PDF successfully emailed

That's it! Your system is now automatically generating and emailing PDF reports! 🚀
