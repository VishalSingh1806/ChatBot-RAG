from typing import Dict, List, Optional
from datetime import datetime
import json
import logging
from collect_data import redis_client

class LeadManager:
    def __init__(self):
        self.lead_scores = {
            'high_interest': 8,
            'urgent_need': 10,
            'service_specific': 7,
            'business_inquiry': 6,
            'general_inquiry': 3
        }
    
    async def track_user_intent(self, session_id: str, intent_result, query: str, user_data: Optional[Dict] = None):
        """Track user intent and build lead scoring"""
        if not redis_client:
            return
        
        try:
            lead_key = f"lead:{session_id}"
            
            # Get existing lead data
            existing_data = redis_client.hgetall(lead_key)
            
            # Initialize or update lead data
            lead_data = {
                'session_id': session_id,
                'first_interaction': existing_data.get('first_interaction', datetime.utcnow().isoformat()),
                'last_interaction': datetime.utcnow().isoformat(),
                'total_queries': int(existing_data.get('total_queries', 0)) + 1,
                'lead_score': int(existing_data.get('lead_score', 0)),
                'intents': existing_data.get('intents', '[]'),
                'high_interest_queries': int(existing_data.get('high_interest_queries', 0)),
                'connection_suggested': existing_data.get('connection_suggested', 'false')
            }
            
            # Update with user data if available
            if user_data:
                lead_data.update({
                    'user_name': user_data.get('user_name', ''),
                    'email': user_data.get('email', ''),
                    'phone': user_data.get('phone', ''),
                    'organization': user_data.get('organization', '')
                })
            
            # Add current intent
            intents_list = json.loads(lead_data['intents'])
            intents_list.append({
                'intent': intent_result.intent,
                'confidence': intent_result.confidence,
                'query': query[:100],  # Store first 100 chars
                'timestamp': datetime.utcnow().isoformat()
            })
            lead_data['intents'] = json.dumps(intents_list[-10:])  # Keep last 10 intents
            
            # Update lead score
            intent_score = self.lead_scores.get(intent_result.intent, 0)
            confidence_multiplier = intent_result.confidence
            lead_data['lead_score'] += int(intent_score * confidence_multiplier)
            
            # Track high interest queries
            if intent_result.intent in ['high_interest', 'urgent_need', 'service_specific']:
                lead_data['high_interest_queries'] += 1
            
            # Mark if connection was suggested
            if intent_result.should_connect:
                lead_data['connection_suggested'] = 'true'
            
            # Save to Redis
            redis_client.hmset(lead_key, mapping=lead_data)
            redis_client.expire(lead_key, 86400 * 30)  # Expire after 30 days
            
            # Check if this is a hot lead
            await self._check_hot_lead(lead_data)
            
        except Exception as e:
            logging.error(f"Error tracking user intent: {e}")
    
    async def _check_hot_lead(self, lead_data: Dict):
        """Check if this is a hot lead and needs immediate attention"""
        hot_lead_criteria = {
            'high_score': lead_data['lead_score'] >= 20,
            'multiple_high_interest': lead_data['high_interest_queries'] >= 3,
            'urgent_intent': any('urgent_need' in json.loads(lead_data['intents'])[-3:] for intent in json.loads(lead_data['intents'])[-3:] if isinstance(intent, dict)),
            'has_contact_info': bool(lead_data.get('email') and lead_data.get('phone'))
        }
        
        if any(hot_lead_criteria.values()):
            await self._notify_hot_lead(lead_data, hot_lead_criteria)
    
    async def _notify_hot_lead(self, lead_data: Dict, criteria: Dict):
        """Send notification for hot leads"""
        try:
            # Mark as hot lead
            lead_key = f"lead:{lead_data['session_id']}"
            redis_client.hset(lead_key, 'hot_lead', 'true')
            redis_client.hset(lead_key, 'hot_lead_timestamp', datetime.utcnow().isoformat())
            
            # Log hot lead (you can extend this to send emails/notifications)
            logging.info(f"🔥 HOT LEAD DETECTED: {lead_data.get('user_name', 'Unknown')} - Score: {lead_data['lead_score']}")
            logging.info(f"Criteria met: {[k for k, v in criteria.items() if v]}")
            
        except Exception as e:
            logging.error(f"Error notifying hot lead: {e}")
    
    async def get_lead_summary(self, session_id: str) -> Optional[Dict]:
        """Get lead summary for a session"""
        if not redis_client:
            return None
        
        try:
            lead_key = f"lead:{session_id}"
            lead_data = redis_client.hgetall(lead_key)
            
            if not lead_data:
                return None
            
            # Parse intents
            intents = json.loads(lead_data.get('intents', '[]'))
            
            return {
                'session_id': session_id,
                'user_name': lead_data.get('user_name', ''),
                'organization': lead_data.get('organization', ''),
                'email': lead_data.get('email', ''),
                'phone': lead_data.get('phone', ''),
                'lead_score': int(lead_data.get('lead_score', 0)),
                'total_queries': int(lead_data.get('total_queries', 0)),
                'high_interest_queries': int(lead_data.get('high_interest_queries', 0)),
                'connection_suggested': lead_data.get('connection_suggested') == 'true',
                'hot_lead': lead_data.get('hot_lead') == 'true',
                'first_interaction': lead_data.get('first_interaction'),
                'last_interaction': lead_data.get('last_interaction'),
                'recent_intents': intents[-5:] if intents else []
            }
            
        except Exception as e:
            logging.error(f"Error getting lead summary: {e}")
            return None

# Global instance
lead_manager = LeadManager()