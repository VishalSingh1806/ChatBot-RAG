from typing import Dict, List, Optional
import re
from dataclasses import dataclass
import json

@dataclass
class IntentResult:
    intent: str
    confidence: float
    indicators: List[str]
    should_connect: bool = False

class IntentDetector:
    def __init__(self):
        # Enhanced engagement tracking
        self.engagement_indicators = {
            'question_depth': ['how to', 'what is the process', 'can you explain', 'tell me more', 'step by step', 'detailed'],
            'business_context': ['our company', 'we need', 'my business', 'our organization', 'we are', 'we have', 'our team', 'my company'],
            'urgency_signals': ['urgent', 'deadline', 'soon', 'quickly', 'asap', 'immediate', 'today', 'this week'],
            'service_interest': ['help us', 'assist', 'support', 'guidance', 'consultation', 'quote', 'pricing', 'cost'],
            'compliance_focus': ['compliance', 'certificate', 'registration', 'audit', 'penalty', 'fine', 'legal'],
            'decision_signals': ['budget', 'approve', 'decision', 'purchase', 'implement', 'start', 'begin'],
            'technical_questions': ['implementation', 'process', 'requirements', 'documentation', 'procedure'],
            'risk_indicators': ['penalty', 'fine', 'audit', 'non-compliant', 'violation', 'notice']
        }
        
        # Define intent patterns with keywords and phrases
        self.intent_patterns = {
            'sales_opportunity': {
                'keywords': [
                    'i am', 'we are', 'our company', 'my business', 'my organization',
                    'looking for', 'searching for', 'need solution', 'want solution',
                    'planning to', 'thinking about', 'considering', 'exploring options',
                    'budget for', 'cost for', 'price for', 'quote for', 'estimate for'
                ],
                'phrases': [
                    'i am producer', 'i am importer', 'i am manufacturer', 'i am brand owner',
                    'we are producer', 'we are importer', 'we are manufacturer',
                    'our company is', 'my business is', 'we manufacture', 'we import',
                    'we produce', 'we sell', 'we distribute', 'looking for epr',
                    'need epr compliance', 'want epr help', 'epr solution for us'
                ],
                'weight': 0.95
            },
            'contact_intent': {
                'keywords': [
                    'contact', 'call', 'phone', 'email', 'reach out', 'get in touch',
                    'speak to', 'talk to', 'connect with', 'meeting', 'consultation',
                    'help me', 'assist me', 'need help', 'want help', 'require help',
                    'want to discuss', 'need assistance', 'require assistance'
                ],
                'phrases': [
                    'how to contact', 'want to contact', 'need to contact',
                    'can you help me', 'i need help', 'i want help', 'want to speak',
                    'schedule a call', 'book a meeting', 'get assistance',
                    'talk to someone', 'connect me with', 'reach your team',
                    'want help for', 'need help with', 'require help with'
                ],
                'weight': 1.0
            },
            'company_inquiry': {
                'keywords': [
                    'recircle', 'company', 'about recircle', 'what is recircle',
                    'recircle services', 'different from competitors', 'why recircle',
                    'what makes recircle', 'recircle different', 'about company'
                ],
                'phrases': [
                    'what is recircle', 'about recircle', 'recircle company',
                    'what makes recircle', 'recircle different', 'why choose recircle'
                ],
                'weight': 0.9
            },
            'high_interest': {
                'keywords': [
                    'need help', 'want to implement', 'looking for solution', 'interested in',
                    'how to start', 'get started', 'need assistance', 'require support',
                    'want to comply', 'need compliance', 'looking for partner',
                    'cost of', 'pricing', 'quote', 'proposal', 'consultation'
                ],
                'phrases': [
                    'can you help us', 'we need to', 'our company needs',
                    'looking for a partner', 'want to work with', 'need professional help',
                    'require expert guidance', 'seeking assistance'
                ],
                'weight': 0.8
            },
            'business_inquiry': {
                'keywords': [
                    'business', 'company', 'organization', 'enterprise', 'firm',
                    'manufacturer', 'producer', 'importer', 'brand owner',
                    'compliance officer', 'sustainability manager'
                ],
                'phrases': [
                    'for our business', 'our organization', 'my company',
                    'we are a', 'we manufacture', 'we import', 'i am importer',
                    'i am producer', 'i am manufacturer'
                ],
                'weight': 0.8
            },
            'urgent_need': {
                'keywords': [
                    'urgent', 'asap', 'immediately', 'deadline', 'penalty',
                    'non-compliance', 'audit', 'inspection', 'fine'
                ],
                'phrases': [
                    'need it urgently', 'facing penalty', 'audit coming up',
                    'deadline approaching', 'immediate help needed'
                ],
                'weight': 0.9
            },
            'service_specific': {
                'keywords': [
                    'certificate', 'registration', 'PRO services', 'recycling partner',
                    'waste management', 'plastic neutral', 'EPR compliance',
                    'collection network', 'reporting'
                ],
                'phrases': [
                    'need EPR certificate', 'want to register', 'looking for PRO',
                    'need recycling partner', 'plastic neutrality program'
                ],
                'weight': 0.8
            }
        }
        
        # Connection triggers - when to suggest team connection
        self.connection_triggers = {
            'multiple_business_queries': 3,  # 3+ business-related queries
            'high_confidence_threshold': 0.7,
            'urgent_keywords': ['urgent', 'deadline', 'penalty', 'audit'],
            'service_requests': ['certificate', 'registration', 'consultation', 'quote']
        }
    
    def analyze_intent(self, query: str, conversation_history: List[Dict]) -> IntentResult:
        """Analyze user intent with enhanced engagement tracking"""
        query_lower = query.lower()
        
        # Calculate engagement score from conversation
        engagement_score = self._calculate_engagement_score(query_lower, conversation_history)
        
        # Calculate intent scores
        intent_scores = {}
        all_indicators = []
        
        for intent_type, patterns in self.intent_patterns.items():
            score = 0
            indicators = []
            
            # Check keywords
            for keyword in patterns['keywords']:
                if keyword in query_lower:
                    score += patterns['weight']
                    indicators.append(f"keyword: {keyword}")
            
            # Check phrases
            for phrase in patterns['phrases']:
                if phrase in query_lower:
                    score += patterns['weight'] * 1.2
                    indicators.append(f"phrase: {phrase}")
            
            if score > 0:
                intent_scores[intent_type] = score
                all_indicators.extend(indicators)
        
        # Determine primary intent
        if intent_scores:
            primary_intent = max(intent_scores, key=intent_scores.get)
            confidence = min(intent_scores[primary_intent], 1.0)
        else:
            primary_intent = 'general_inquiry'
            confidence = 0.3
        
        # Enhanced connection logic
        should_connect = self._should_suggest_connection(
            query_lower, conversation_history, engagement_score, primary_intent, confidence
        )
        
        return IntentResult(
            intent=primary_intent,
            confidence=confidence,
            indicators=all_indicators,
            should_connect=should_connect
        )
    
    def _calculate_engagement_score(self, current_query: str, history: List[Dict]) -> float:
        """Calculate user engagement score with behavioral tracking"""
        score = 0
        user_messages = [msg for msg in history if msg.get('role') == 'user']
        
        # Add current query to analysis
        all_queries = [msg.get('text', '').lower() for msg in user_messages] + [current_query]
        
        # Track engagement behaviors
        engagement_behaviors = []
        
        for query in all_queries:
            # Check engagement indicators
            for category, indicators in self.engagement_indicators.items():
                for indicator in indicators:
                    if indicator in query:
                        if category == 'business_context':
                            score += 2.0
                        elif category == 'urgency_signals':
                            score += 1.5
                        elif category == 'service_interest':
                            score += 1.8
                        elif category == 'compliance_focus':
                            score += 1.6
                        elif category == 'decision_signals':
                            score += 2.5
                        elif category == 'technical_questions':
                            score += 2.0
                            engagement_behaviors.append('technical_questions')
                        elif category == 'risk_indicators':
                            score += 3.0
                        else:
                            score += 1.0
        
        # Behavioral bonuses
        if len(user_messages) >= 5:
            engagement_behaviors.append('long_conversation')
        
        return min(score, 10.0)  # Cap at 10
    
    def _should_suggest_connection(self, query: str, history: List[Dict], 
                                 engagement_score: float, intent: str, confidence: float) -> bool:
        """Enhanced connection suggestion logic"""
        user_message_count = len([msg for msg in history if msg.get('role') == 'user']) + 1
        
        # Immediate connection for high-risk situations
        risk_keywords = ['penalty', 'fine', 'audit', 'legal action', 'court']
        if any(keyword in query for keyword in risk_keywords):
            return True
        
        # Immediate connection for high-value intents
        if intent in ['urgent_need'] and confidence > 0.5:
            return True
        
        # Exclude definition questions and registration info from triggering company info
        definition_keywords = ['what is', 'what are', 'define', 'definition', 'meaning of', 'explain']
        registration_info_keywords = ['how to register', 'how do i register', 'register for', 'registration process']
        
        if any(keyword in query for keyword in definition_keywords + registration_info_keywords):
            return False
        
        # Help requests and service inquiries only
        help_keywords = ['help', 'assist', 'support', 'guidance', 'who will help', 'can you help', 'need help']
        service_keywords = ['consultation', 'quote', 'pricing', 'cost of service']
        
        if any(keyword in query for keyword in help_keywords + service_keywords):
            return True
        
        # Progressive engagement-based connection
        if user_message_count >= 3 and engagement_score >= 4.0:
            return True
        elif user_message_count >= 4 and engagement_score >= 2.5:
            return True
        elif user_message_count >= 2 and engagement_score >= 6.0:
            return True
        
        # High engagement users
        if engagement_score >= 5.0:
            return True
        
        return False
    
    def get_connection_message(self, intent: str, user_name: Optional[str] = None) -> str:
        """Generate appropriate connection suggestion message"""
        return "Our ReCircle team would be happy to help you with personalized EPR solutions. Would you like to connect with our experts?"

# Global instance
intent_detector = IntentDetector()
