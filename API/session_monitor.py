import asyncio
import logging
from datetime import datetime, timedelta
from collect_data import redis_client
from session_reporter import finalize_session

logging.basicConfig(level=logging.INFO)

INACTIVITY_THRESHOLD_MINUTES = 1

async def monitor_sessions():
    """Monitor sessions and auto-generate PDF after 5 minutes of inactivity"""
    logging.info("🔍 Session monitor started - checking every 60 seconds")
    
    while True:
        try:
            await asyncio.sleep(60)  # Check every minute
            
            if not redis_client:
                continue
            
            # Get all session keys
            session_keys = redis_client.keys("session:*")
            
            for key in session_keys:
                key_str = key.decode() if isinstance(key, bytes) else key
                if ":chat" in key_str or ":finalized" in key_str or ":thankyou_sent" in key_str or ":monitor_inactivity" in key_str:
                    continue
                
                session_id = key_str.split(":")[1]
                session_data = redis_client.hgetall(key_str)
                
                if not session_data:
                    continue
                
                user_data_collected = session_data.get(b"user_data_collected") or session_data.get("user_data_collected")
                if not user_data_collected:
                    continue
                
                # Check if session has chat messages
                chat_key = f"session:{session_id}:chat"
                chat_count = redis_client.llen(chat_key)
                if chat_count == 0:
                    continue
                
                # Check if already finalized
                finalized_key = f"session:{session_id}:finalized"
                if redis_client.exists(finalized_key):
                    continue
                
                last_interaction = session_data.get(b"last_interaction") or session_data.get("last_interaction")
                if not last_interaction:
                    continue
                
                if isinstance(last_interaction, bytes):
                    last_interaction = last_interaction.decode()
                
                try:
                    last_time = datetime.fromisoformat(last_interaction)
                    time_diff = (datetime.utcnow() - last_time).total_seconds() / 60
                    
                    # Only process sessions inactive between 1-60 minutes (not old sessions)
                    if INACTIVITY_THRESHOLD_MINUTES <= time_diff <= 60:
                        logging.info(f"⏰ Session {session_id} inactive for {time_diff:.1f} minutes - generating PDF")
                        
                        # Mark as finalized FIRST to prevent duplicate processing
                        redis_client.setex(finalized_key, 86400 * 7, "true")
                        
                        # Generate and send PDF
                        finalize_session(session_id)
                        
                        logging.info(f"✅ PDF generated and sent for session {session_id}")
                    elif time_diff > 60:
                        # Mark old sessions as finalized without generating PDF
                        redis_client.setex(finalized_key, 86400 * 7, "true")
                        
                except Exception as e:
                    logging.error(f"❌ Error processing session {session_id}: {e}")
                    
        except Exception as e:
            logging.error(f"❌ Error in session monitor: {e}")

async def start_monitor():
    """Start the session monitor"""
    await monitor_sessions()
