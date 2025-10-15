# 🚀 Deployment Checklist - PDF Report System

## ✅ Pre-Deployment Checklist

### 1. Dependencies
- [ ] Redis installed and running
- [ ] Python 3.8+ installed
- [ ] All packages in requirements.txt installed
- [ ] reportlab package installed: `pip install reportlab`

### 2. Configuration Files
- [ ] `.env` file exists in API directory
- [ ] SMTP credentials configured correctly
- [ ] Redis host/port configured
- [ ] Email recipients configured

### 3. Directory Structure
- [ ] `API/reports/` directory exists (auto-created)
- [ ] All Python files in place
- [ ] No syntax errors in code

### 4. Redis Setup
- [ ] Redis server running: `redis-cli ping` returns PONG
- [ ] Redis accessible on configured host/port
- [ ] No connection errors

### 5. SMTP Setup
- [ ] SMTP_SERVER: smtp.gmail.com
- [ ] SMTP_PORT: 587
- [ ] SMTP_USERNAME: bhaktipatil.tech@gmail.com
- [ ] SMTP_PASSWORD: Configured (app password)
- [ ] RECIPIENT_EMAIL: bhakti.patil@recircle.in

## 🧪 Testing Checklist

### 1. Basic Tests
- [ ] API starts without errors: `python main.py`
- [ ] Background monitor starts: See "✅ Background session monitor started"
- [ ] Redis connection works: No connection errors in logs
- [ ] Test script runs: `python test_pdf_generation.py`

### 2. PDF Generation Test
- [ ] PDF created in `reports/` directory
- [ ] PDF contains all sections (User Info, Lead Info, Chat)
- [ ] PDF format matches requirements
- [ ] No errors during generation

### 3. Email Test
- [ ] Email received at bhakti.patil@recircle.in
- [ ] PDF attached correctly
- [ ] Email body contains user summary
- [ ] No SMTP errors in logs

### 4. Session Monitoring Test
- [ ] Create a test chat session
- [ ] Wait 5 minutes
- [ ] PDF automatically generated
- [ ] Email automatically sent
- [ ] Session marked as finalized

### 5. Duplicate Prevention Test
- [ ] Same session doesn't generate PDF twice
- [ ] Finalization flag works correctly
- [ ] No duplicate emails sent

## 📊 Monitoring Checklist

### 1. Logs to Watch
- [ ] `🚀 Starting EPR ChatBot API`
- [ ] `✅ Background session monitor started`
- [ ] `🔍 Session monitor started - checking every 60 seconds`
- [ ] `⏰ Session {id} inactive for 5.0 minutes`
- [ ] `📥 Fetching session data`
- [ ] `📄 Generating PDF report`
- [ ] `📧 Sending PDF report via email`
- [ ] `✅ PDF successfully emailed`

### 2. Redis Keys to Monitor
- [ ] `session:*` - User session data
- [ ] `lead:*` - Lead scoring data
- [ ] `session:*:chat` - Chat logs
- [ ] `session:*:finalized` - Finalization flags

### 3. Error Handling
- [ ] No Redis connection errors
- [ ] No SMTP authentication errors
- [ ] No PDF generation errors
- [ ] Graceful error logging

## 🔧 Production Checklist

### 1. Security
- [ ] `.env` file not committed to git
- [ ] SMTP password is app-specific password
- [ ] Redis protected (if exposed)
- [ ] Sensitive data not logged

### 2. Performance
- [ ] Background monitor doesn't block API
- [ ] PDF generation is async
- [ ] Redis keys have proper TTL
- [ ] Old PDFs cleaned up periodically

### 3. Reliability
- [ ] Email retry logic (if needed)
- [ ] Error notifications configured
- [ ] Backup email recipients (if needed)
- [ ] Session data persistence

### 4. Monitoring
- [ ] Log rotation configured
- [ ] Disk space monitoring for PDFs
- [ ] Redis memory monitoring
- [ ] Email delivery monitoring

## 📝 Post-Deployment Checklist

### 1. Verification
- [ ] API running in production
- [ ] Background monitor active
- [ ] Test session created successfully
- [ ] PDF generated and emailed
- [ ] No errors in production logs

### 2. Documentation
- [ ] Team trained on system
- [ ] Documentation accessible
- [ ] Troubleshooting guide available
- [ ] Contact info for support

### 3. Maintenance
- [ ] Schedule for log cleanup
- [ ] Schedule for PDF cleanup
- [ ] Redis backup strategy
- [ ] Update procedure documented

## 🎯 Quick Verification Commands

```bash
# Check Redis
redis-cli ping

# Check Redis keys
redis-cli keys "session:*"

# Check API is running
curl http://localhost:8000/

# Check reports directory
ls -la API/reports/

# Check logs
tail -f API/logs/app.log  # if logging to file

# Test PDF generation
cd API && python test_pdf_generation.py
```

## ✅ Final Sign-Off

- [ ] All tests passed
- [ ] Production deployment successful
- [ ] Monitoring in place
- [ ] Team notified
- [ ] Documentation complete

**Deployed by:** _________________  
**Date:** _________________  
**Verified by:** _________________  

---

## 🆘 Emergency Contacts

**Technical Issues:**
- Check logs first
- Verify Redis connection
- Test SMTP manually
- Review error messages

**Quick Fixes:**
- Restart Redis: `redis-server`
- Restart API: `python main.py`
- Clear Redis: `redis-cli flushdb` (caution!)
- Check disk space: `df -h`

---

**Status:** Ready for Production ✅
