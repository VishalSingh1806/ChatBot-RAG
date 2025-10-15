# System Flow - PDF Report Generation

## 📊 Complete Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERACTION                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  1. User fills form (name, email, phone, organization)          │
│     → Saved to Redis: session:{id}                              │
│     → user_data_collected = true                                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  2. User sends messages                                          │
│     → Each message logged to Redis: session:{id}:chat           │
│     → Format: "User: {message}" and "Bot: {response}"           │
│     → last_interaction timestamp updated                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  3. Lead scoring happens in real-time                            │
│     → Intent detection                                           │
│     → Engagement scoring                                         │
│     → Priority calculation (low/medium/high/critical)           │
│     → Saved to Redis: lead:{id}                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    BACKGROUND MONITOR                            │
│  (Runs every 60 seconds checking all sessions)                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  4. Check inactivity                                             │
│     → Get last_interaction timestamp                            │
│     → Calculate time difference                                 │
│     → If >= 5 minutes → Trigger PDF generation                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  5. Fetch session data from Redis                                │
│     ✓ session:{id} → User info                                  │
│     ✓ lead:{id} → Lead scoring data                             │
│     ✓ session:{id}:chat → Full conversation                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  6. Generate PDF using ReportLab                                 │
│     ┌─────────────────────────────────────────┐                │
│     │ EPR Chatbot - Session Report            │                │
│     │ Session ID: {id}                        │                │
│     │ Generated: {timestamp}                  │                │
│     │                                         │                │
│     │ User Information                        │                │
│     │ • Name: {name}                          │                │
│     │ • Email: {email}                        │                │
│     │ • Phone: {phone}                        │                │
│     │ • Organization: {org}                   │                │
│     │                                         │                │
│     │ Lead Information                        │                │
│     │ • Priority: {HIGH/MEDIUM/LOW}           │                │
│     │ • First Interaction: {timestamp}        │                │
│     │ • Last Interaction: {timestamp}         │                │
│     │                                         │                │
│     │ Conversation Transcript                 │                │
│     │ User: {message 1}                       │                │
│     │ Bot: {response 1}                       │                │
│     │ User: {message 2}                       │                │
│     │ Bot: {response 2}                       │                │
│     │ ...                                     │                │
│     └─────────────────────────────────────────┘                │
│     → Saved to: reports/session_{id}.pdf                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  7. Send email via SMTP                                          │
│     From: bhaktipatil.tech@gmail.com                            │
│     To: bhakti.patil@recircle.in                                │
│     Subject: EPR Chatbot Session Report - {User Name}           │
│     Body: User summary + lead priority                          │
│     Attachment: session_{id}.pdf                                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  8. Mark session as finalized                                    │
│     → Set Redis key: session:{id}:finalized = true              │
│     → Prevents duplicate PDF generation                         │
│     → Expires after 7 days                                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                         ✅ COMPLETE
```

## 🔄 Alternative Triggers

### Manual Trigger (Frontend)
```
User clicks "End Chat" 
    → POST /end_session
    → Immediately generates PDF
    → Sends email
    → No 5-minute wait
```

### API Endpoint
```
POST /end_session
Headers: Cookie with session_id
Response: {"status": "success", "message": "PDF generated"}
```

## 📦 Redis Data Structure

```
Redis Keys:
├── session:{session_id}
│   ├── user_data_collected: "true"
│   ├── user_name: "Chinmay"
│   ├── email: "chinmay123@gmail.com"
│   ├── phone: "9865342187"
│   ├── organization: "Cog"
│   └── last_interaction: "2025-01-14T12:07:33.495792"
│
├── lead:{session_id}
│   ├── lead_score: "15"
│   ├── priority: "high"
│   ├── engagement_score: "6.5"
│   ├── total_queries: "4"
│   ├── first_interaction: "2025-01-14T12:06:00"
│   └── last_interaction: "2025-01-14T12:07:33"
│
├── session:{session_id}:chat
│   ├── [0] "User: I am producer i need help..."
│   ├── [1] "Bot: As a producer, you need..."
│   ├── [2] "User: How to calculate EPR target"
│   └── [3] "Bot: EPR targets are generated..."
│
└── session:{session_id}:finalized
    └── "true" (expires after 7 days)
```

## ⏱️ Timing

- **Session check interval**: Every 60 seconds
- **Inactivity threshold**: 5 minutes
- **Redis TTL**: 7 days for finalized sessions
- **Email timeout**: 30 seconds

## 🎯 Key Features

✅ **Real-time logging** - Every message logged immediately  
✅ **Automatic detection** - No manual intervention needed  
✅ **Duplicate prevention** - Finalization flag prevents re-sending  
✅ **Comprehensive data** - User info + lead data + full chat  
✅ **Professional format** - Clean PDF with proper sections  
✅ **Email delivery** - Automatic SMTP sending  
✅ **Error handling** - Graceful failures with logging  

## 🔍 Monitoring Points

Watch these logs to track the flow:
1. `🔍 Session monitor started` - Background task running
2. `⏰ Session {id} inactive` - Inactivity detected
3. `📥 Fetching session data` - Data retrieval started
4. `📄 Generating PDF report` - PDF creation in progress
5. `📧 Sending PDF report` - Email sending started
6. `✅ PDF successfully emailed` - Complete success
