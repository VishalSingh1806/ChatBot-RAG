from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json
from collect_data import redis_client

class ProactiveEngagement:
    def __init__(self):
        self.engagement_triggers = {
            'inactivity_2min': 120,  # 2 minutes
            'inactivity_5min': 300,  # 5 minutes
            'multiple_questions': 3,
            'browsing_time': 180     # 3 minutes
        }
        
        self.proactive_messages = {
            'inactivity_help': [
                "Need help with anything specific about EPR compliance?",
                "Have questions about any particular aspect of plastic waste management?",
                "Looking for information on a specific EPR service?"
            ],
            'follow_up_certificates': [
                "Based on your questions about certificates, would you like to know about our EPR registration services?",
                "Since you're interested in compliance, our team can help streamline your EPR certification process."
            ],
            'follow_up_recycling': [
                "I see you're exploring recycling options. Our network covers pan-India collection and processing.",
                "For recycling partnerships, we work with certified processors across all major cities."
            ],
            'qualification_questions': [
                "To provide better guidance, what industry is your company in?",
                "What's your approximate monthly plastic packaging usage?",
                "Are you looking for immediate compliance or planning for the future?"
            ]
        }
    
    def should_send_proactive_message(self, session_id: str, last_activity: str, message_count: int) -> Optional[Dict]:
        """Determine if proactive message should be sent"""
        if not last_activity:
            return None
        
        try:
            last_time = datetime.fromisoformat(last_activity)
            time_diff = (datetime.utcnow() - last_time).total_seconds()
            
            # 2-minute inactivity after engagement
            if time_diff >= self.engagement_triggers['inactivity_2min'] and message_count >= 2:
                return {
                    'type': 'inactivity_help',
                    'message': self._get_random_message('inactivity_help'),
                    'priority': 'medium'
                }
            
            # 5-minute inactivity for new users
            elif time_diff >= self.engagement_triggers['inactivity_5min'] and message_count == 1:
                return {
                    'type': 'qualification_questions',
                    'message': self._get_random_message('qualification_questions'),
                    'priority': 'low'
                }
            
        except Exception:
            pass
        
        return None
    
    def get_smart_follow_up(self, conversation_topics: List[str]) -> Optional[str]:
        """Generate smart follow-up based on conversation topics"""
        topics_text = ' '.join(conversation_topics).lower()
        
        if any(word in topics_text for word in ['certificate', 'registration', 'compliance']):
            return self._get_random_message('follow_up_certificates')
        elif any(word in topics_text for word in ['recycling', 'recycler', 'waste management']):
            return self._get_random_message('follow_up_recycling')
        
        return None
    
    def _get_random_message(self, category: str) -> str:
        """Get random message from category"""
        import random
        messages = self.proactive_messages.get(category, [])
        return random.choice(messages) if messages else ""
    
    def track_user_journey(self, session_id: str, query: str, intent: str):
        """Track user journey for proactive engagement"""
        if not redis_client:
            return
        
        try:
            journey_key = f"journey:{session_id}"
            existing_journey = redis_client.get(journey_key)
            
            journey_data = json.loads(existing_journey) if existing_journey else {
                'topics': [],
                'intents': [],
                'engagement_level': 0,
                'last_proactive': None
            }
            
            # Add current interaction
            journey_data['topics'].append(query[:50])  # First 50 chars
            journey_data['intents'].append(intent)
            journey_data['last_activity'] = datetime.utcnow().isoformat()
            
            # Keep last 10 interactions
            journey_data['topics'] = journey_data['topics'][-10:]
            journey_data['intents'] = journey_data['intents'][-10:]
            
            # Calculate engagement level
            business_intents = ['high_interest', 'service_specific', 'business_inquiry', 'urgent_need']
            engagement_score = sum(1 for intent in journey_data['intents'] if intent in business_intents)
            journey_data['engagement_level'] = engagement_score
            
            redis_client.setex(journey_key, 3600, json.dumps(journey_data))  # 1 hour expiry
            
        except Exception as e:
            print(f"Error tracking user journey: {e}")

proactive_engagement = ProactiveEngagement()