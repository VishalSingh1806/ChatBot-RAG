from typing import Dict, List, Optional
import re
from dataclasses import dataclass

@dataclass
class IntentResult:
    intent: str
    confidence: float
    indicators: List[str]
    should_connect: bool = False

class IntentDetector:
    def __init__(self):
        # Define intent patterns with keywords and phrases
        self.intent_patterns = {
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
                    'we are a', 'we manufacture', 'we import'
                ],
                'weight': 0.7
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
        """Analyze user intent from current query and conversation history"""
        query_lower = query.lower()
        
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
                    score += patterns['weight'] * 1.2  # Phrases get higher weight
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
        
        # Check if should suggest team connection
        should_connect = self._should_suggest_connection(
            query_lower, conversation_history, primary_intent, confidence
        )
        
        return IntentResult(
            intent=primary_intent,
            confidence=confidence,
            indicators=all_indicators,
            should_connect=should_connect
        )
    
    def _should_suggest_connection(self, query: str, history: List[Dict], 
                                 intent: str, confidence: float) -> bool:
        """Determine if we should suggest connecting with ReCircle team"""
        
        # Lower threshold for testing - suggest connection more frequently
        if confidence >= 0.3:  # Much lower threshold
            if intent in ['high_interest', 'urgent_need', 'service_specific', 'business_inquiry']:
                return True
        
        # Check for any business-related keywords
        business_keywords = ['company', 'business', 'organization', 'compliance', 'certificate', 
                           'registration', 'help', 'need', 'want', 'looking', 'require']
        for keyword in business_keywords:
            if keyword in query:
                return True
        
        # After 2+ messages, suggest connection
        if len(history) >= 2:
            return True
        
        return False
    
    def get_connection_message(self, intent: str, user_name: Optional[str] = None) -> str:
        """Generate appropriate connection suggestion message"""
        name_prefix = f"{user_name}, " if user_name else ""
        
        messages = {
            'high_interest': f"Hi {name_prefix}it sounds like you're looking for comprehensive EPR solutions! Our team at ReCircle specializes in helping businesses achieve full compliance. Would you like to connect with our experts for personalized guidance?",
            
            'urgent_need': f"{name_prefix}I understand this is urgent! Our ReCircle team has helped many companies handle time-sensitive compliance requirements. Let me connect you with our specialists who can provide immediate assistance.",
            
            'service_specific': f"Hi {name_prefix}for specific services like EPR certificates and compliance management, our ReCircle team can provide end-to-end solutions. Would you like to speak with our experts about your requirements?",
            
            'business_inquiry': f"{name_prefix}since you're exploring EPR solutions for your business, our ReCircle team can provide tailored compliance strategies. Would you like to schedule a consultation with our specialists?"
        }
        
        return messages.get(intent, 
            f"Hi {name_prefix}our ReCircle team would be happy to help you with personalized EPR solutions. Would you like to connect with our experts?"
        )