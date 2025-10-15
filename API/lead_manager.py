from typing import Dict, Optional
from datetime import datetime
import json
import logging
from collect_data import redis_client
from notification_system import notification_system
from backend_notifications import backend_notifications
from lead_qualification import lead_qualification


class LeadManager:
    def __init__(self):
        self.lead_scores = {
            'sales_opportunity': 9,
            'contact_intent': 10,
            'company_inquiry': 8,
            'high_interest': 8,
            'urgent_need': 10,
            'service_specific': 7,
            'business_inquiry': 8,
            'general_inquiry': 3
        }

        # Lead priority thresholds
        self.priority_thresholds = {
            'critical': 25,
            'high': 15,
            'medium': 8,
            'low': 3
        }

    async def track_user_intent(self, session_id: str, intent_result, query: str,
                                user_data: Optional[Dict] = None, engagement_score: float = 0):
        """Track user intent and update lead scoring in Redis"""
        if not redis_client:
            return

        try:
            lead_key = f"lead:{session_id}"
            existing_data = redis_client.hgetall(lead_key)

            lead_data = {
                'session_id': session_id,
                'first_interaction': existing_data.get('first_interaction', datetime.utcnow().isoformat()),
                'last_interaction': datetime.utcnow().isoformat(),
                'total_queries': int(existing_data.get('total_queries', 0)) + 1,
                'lead_score': int(existing_data.get('lead_score', 0)),
                'engagement_score': engagement_score,
                'intents': existing_data.get('intents', '[]'),
                'queries': existing_data.get('queries', '[]'),
                'high_interest_queries': int(existing_data.get('high_interest_queries', 0)),
                'connection_suggested': existing_data.get('connection_suggested', 'false'),
                'backend_notified': existing_data.get('backend_notified', 'false'),
                'priority': existing_data.get('priority', 'low')
            }

            # Update user info if available
            if user_data:
                lead_data.update({
                    'user_name': user_data.get('user_name', ''),
                    'email': user_data.get('email', ''),
                    'phone': user_data.get('phone', ''),
                    'organization': user_data.get('organization', '')
                })

            # Append query and intents
            queries_list = json.loads(lead_data['queries'])
            queries_list.append(query[:100])
            lead_data['queries'] = json.dumps(queries_list[-10:])

            intents_list = json.loads(lead_data['intents'])
            intents_list.append({
                'intent': intent_result.intent,
                'confidence': intent_result.confidence,
                'engagement_score': engagement_score,
                'timestamp': datetime.utcnow().isoformat()
            })
            lead_data['intents'] = json.dumps(intents_list[-10:])

            # Calculate new lead score
            intent_score = self.lead_scores.get(intent_result.intent, 0)
            confidence_multiplier = intent_result.confidence
            calculated_score = intent_score * confidence_multiplier
            lead_data['lead_score'] = max(1, int(calculated_score))

            # Track high-interest queries
            if intent_result.intent in ['sales_opportunity', 'contact_intent', 'high_interest',
                                        'urgent_need', 'service_specific']:
                lead_data['high_interest_queries'] += 1

            if intent_result.should_connect:
                lead_data['connection_suggested'] = 'true'

            # Update priority
            lead_data['priority'] = self._calculate_priority(lead_data['lead_score'], engagement_score)

            # Save to Redis
            redis_client.hmset(lead_key, mapping=lead_data)
            redis_client.expire(lead_key, 86400 * 30)

            # Trigger notifications only (no PDF here)
            await self._check_notifications(lead_data)

        except Exception as e:
            logging.error(f"Error tracking user intent: {e}", exc_info=True)

    def _calculate_priority(self, lead_score: int, engagement_score: float) -> str:
        combined_score = lead_score + (engagement_score * 2)
        if combined_score >= self.priority_thresholds['critical']:
            return 'critical'
        elif combined_score >= self.priority_thresholds['high']:
            return 'high'
        elif combined_score >= self.priority_thresholds['medium']:
            return 'medium'
        return 'low'

    async def _check_notifications(self, lead_data: Dict):
        """Notify backend/hot lead but do NOT generate PDF"""
        message_count = lead_data['total_queries']
        engagement_score = lead_data.get('engagement_score', 0)
        priority = lead_data.get('priority', 'low')

        if priority == 'critical' and lead_data.get('backend_notified') != 'true':
            await self._notify_critical_lead(lead_data)
            return

        primary_intent = self._get_primary_intent(lead_data)
        if primary_intent in ['contact_intent', 'sales_opportunity'] or lead_data['lead_score'] >= 9:
            await self._notify_hot_lead(lead_data, {'high_value_intent': True})
            return

        hot_lead_criteria = {
            'high_score': lead_data['lead_score'] >= 20,
            'high_engagement': engagement_score >= 5.0,
            'multiple_messages': message_count >= 5,
            'has_contact_info': bool(lead_data.get('email') and lead_data.get('phone'))
        }

        criteria_met = sum(hot_lead_criteria.values())
        if priority != 'low' and ((criteria_met >= 2) or (engagement_score >= 6.0)):
            await self._notify_hot_lead(lead_data, hot_lead_criteria)
        elif (engagement_score >= 3.0 or message_count >= 4) and lead_data.get('backend_notified') != 'true':
            await self._notify_backend_team(lead_data)

    async def _notify_critical_lead(self, lead_data: Dict):
        """Send alert for critical leads (no PDF)"""
        try:
            lead_key = f"lead:{lead_data['session_id']}"
            redis_client.hset(lead_key, 'critical_lead', 'true')
            redis_client.hset(lead_key, 'critical_timestamp', datetime.utcnow().isoformat())
            await notification_system.send_hot_lead_alert(lead_data)
        except Exception as e:
            logging.error(f"Error notifying critical lead: {e}")

    async def _notify_hot_lead(self, lead_data: Dict, criteria: Dict):
        """Notify hot leads (no PDF)"""
        try:
            lead_key = f"lead:{lead_data['session_id']}"
            redis_client.hset(lead_key, 'hot_lead', 'true')
            redis_client.hset(lead_key, 'hot_lead_timestamp', datetime.utcnow().isoformat())
            await notification_system.send_hot_lead_alert(lead_data)
        except Exception as e:
            logging.error(f"Error notifying hot lead: {e}")

    async def _notify_backend_team(self, lead_data: Dict):
        """Notify backend team about high engagement users"""
        try:
            lead_key = f"lead:{lead_data['session_id']}"
            redis_client.hset(lead_key, 'backend_notified', 'true')

            user_data = {
                'email': lead_data.get('email', ''),
                'phone': lead_data.get('phone', ''),
                'organization': lead_data.get('organization', '')
            }

            from context_manager import context_manager
            recent_queries = json.loads(lead_data.get('queries', '[]'))
            mock_history = [{'role': 'user', 'text': q} for q in recent_queries[:-1]]
            user_context = context_manager.extract_context(
                recent_queries[-1] if recent_queries else '', mock_history)

            lead_quality_score = lead_qualification.calculate_lead_quality_score(user_context, user_data)

            session_data = {
                'session_id': lead_data['session_id'],
                'user_name': lead_data.get('user_name', 'Anonymous'),
                'email': lead_data.get('email', ''),
                'phone': lead_data.get('phone', ''),
                'organization': lead_data.get('organization', ''),
                'engagement_score': lead_data.get('engagement_score', 0),
                'lead_quality_score': lead_quality_score,
                'message_count': lead_data['total_queries'],
                'primary_intent': self._get_primary_intent(lead_data),
                'priority': lead_data.get('priority', 'low'),
                'industry': user_context.get('industry', 'Unknown'),
                'urgency': user_context.get('urgency', 'low'),
                'recent_queries': recent_queries,
                'last_interaction': lead_data.get('last_interaction'),
                'session_duration': self._calculate_session_duration(lead_data)
            }

            await backend_notifications.notify_high_engagement_user(session_data)
        except Exception as e:
            logging.error(f"Error notifying backend team: {e}")

    def _get_primary_intent(self, lead_data: Dict) -> str:
        try:
            intents = json.loads(lead_data.get('intents', '[]'))
            if not intents:
                return 'unknown'
            intent_counts = {}
            for intent_data in intents:
                intent = intent_data.get('intent', 'unknown')
                intent_counts[intent] = intent_counts.get(intent, 0) + 1
            return max(intent_counts, key=intent_counts.get)
        except:
            return 'unknown'

    def _calculate_session_duration(self, lead_data: Dict) -> str:
        try:
            first = datetime.fromisoformat(lead_data.get('first_interaction', ''))
            last = datetime.fromisoformat(lead_data.get('last_interaction', ''))
            return str(last - first).split('.')[0]
        except:
            return 'Unknown'

    async def get_lead_summary(self, session_id: str) -> Optional[Dict]:
        if not redis_client:
            return None
        try:
            lead_key = f"lead:{session_id}"
            lead_data = redis_client.hgetall(lead_key)
            if not lead_data:
                return None
            intents = json.loads(lead_data.get('intents', '[]'))
            return {
                'session_id': session_id,
                'user_name': lead_data.get('user_name', ''),
                'organization': lead_data.get('organization', ''),
                'email': lead_data.get('email', ''),
                'phone': lead_data.get('phone', ''),
                'lead_score': int(lead_data.get('lead_score', 0)),
                'priority': lead_data.get('priority', 'low'),
                'total_queries': int(lead_data.get('total_queries', 0)),
                'high_interest_queries': int(lead_data.get('high_interest_queries', 0)),
                'connection_suggested': lead_data.get('connection_suggested') == 'true',
                'hot_lead': lead_data.get('hot_lead') == 'true',
                'critical_lead': lead_data.get('critical_lead') == 'true',
                'first_interaction': lead_data.get('first_interaction'),
                'last_interaction': lead_data.get('last_interaction'),
                'recent_intents': intents[-5:] if intents else []
            }
        except Exception as e:
            logging.error(f"Error getting lead summary: {e}")
            return None


# ✅ Global instance
lead_manager = LeadManager()
