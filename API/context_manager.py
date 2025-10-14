from typing import Dict, Optional, List
import json
import re
from collect_data import redis_client

class ContextManager:
    def __init__(self):
        self.industry_keywords = {
            'manufacturing': ['manufacture', 'factory', 'production', 'plant', 'industrial'],
            'fmcg': ['fmcg', 'consumer goods', 'packaged goods', 'retail', 'brands'],
            'ecommerce': ['ecommerce', 'online', 'marketplace', 'delivery', 'shipping'],
            'pharma': ['pharmaceutical', 'medicine', 'drugs', 'healthcare', 'medical'],
            'food': ['food', 'beverage', 'restaurant', 'catering', 'dairy']
        }
        
        self.company_size_indicators = {
            'large': ['multinational', 'corporate', 'enterprise', 'group', 'limited', 'pvt ltd'],
            'medium': ['company', 'business', 'firm', 'organization'],
            'small': ['startup', 'small business', 'shop', 'store']
        }
        
        self.urgency_levels = {
            'critical': ['audit tomorrow', 'penalty notice', 'legal action', 'court'],
            'high': ['urgent', 'asap', 'deadline', 'this week', 'immediate'],
            'medium': ['soon', 'quickly', 'next month'],
            'low': ['planning', 'future', 'considering']
        }
    
    def extract_context(self, query: str, history: List[Dict]) -> Dict:
        """Extract user context from conversation"""
        all_text = query.lower()
        for msg in history:
            if msg.get('role') == 'user':
                all_text += ' ' + msg.get('text', '').lower()
        
        context = {
            'industry': self._detect_industry(all_text),
            'company_size': self._detect_company_size(all_text),
            'urgency': self._detect_urgency(all_text),
            'plastic_volume': self._extract_volume(all_text),
            'location': self._extract_location(all_text)
        }
        
        return context
    
    def _detect_industry(self, text: str) -> Optional[str]:
        for industry, keywords in self.industry_keywords.items():
            if any(keyword in text for keyword in keywords):
                return industry
        return None
    
    def _detect_company_size(self, text: str) -> Optional[str]:
        for size, indicators in self.company_size_indicators.items():
            if any(indicator in text for indicator in indicators):
                return size
        return None
    
    def _detect_urgency(self, text: str) -> str:
        for level, keywords in self.urgency_levels.items():
            if any(keyword in text for keyword in keywords):
                return level
        return 'low'
    
    def _extract_volume(self, text: str) -> Optional[str]:
        # Extract plastic volume mentions
        volume_patterns = [
            r'(\d+)\s*(tons?|tonnes?|kg|kilograms?)',
            r'(\d+)\s*(lakh|crore|million|thousand)\s*(units?|pieces?)'
        ]
        for pattern in volume_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)
        return None
    
    def _extract_location(self, text: str) -> Optional[str]:
        # Common Indian cities/states
        locations = ['mumbai', 'delhi', 'bangalore', 'chennai', 'pune', 'hyderabad', 
                    'gujarat', 'maharashtra', 'karnataka', 'tamil nadu']
        for location in locations:
            if location in text:
                return location.title()
        return None
    
    def _is_help_query(self, query: str) -> bool:
        """Check if query is asking for help/assistance vs theoretical information"""
        help_keywords = ['help', 'assist', 'support', 'guidance', 'consultation', 'advice', 'solution', 'reach out', 'contact']
        theory_keywords = ['what is', 'define', 'definition', 'meaning', 'explain', 'category', 'type']
        
        query_lower = query.lower()
        has_help = any(keyword in query_lower for keyword in help_keywords)
        has_theory = any(keyword in query_lower for keyword in theory_keywords)
        
        return has_help and not has_theory
    
    def personalize_response(self, base_response: str, context: Dict, query: str = "", user_name: str = None) -> str:
        """Personalize response based on user context"""
        if not any(context.values()):
            return base_response
        
        personalization = []
        
        # Remove company promotion - handled elsewhere
        
        # Urgency-based messaging
        if context['urgency'] == 'critical':
            personalization.append("Given the critical timeline, our emergency response team can assist you immediately.")
        elif context['urgency'] == 'high':
            personalization.append("We understand the urgency and can fast-track your compliance process.")
        
        if personalization:
            return f"{base_response}\n\n{' '.join(personalization)}"
        
        return base_response

context_manager = ContextManager()