from typing import Dict, List, Optional
import json

class LeadQualification:
    def __init__(self):
        self.qualification_questions = {
            'industry': "What industry is your company in? (Manufacturing, FMCG, E-commerce, etc.)",
            'volume': "What's your approximate monthly plastic packaging usage?",
            'timeline': "When are you looking to implement EPR compliance?",
            'budget': "Do you have a budget allocated for EPR compliance?",
            'decision_maker': "Are you the decision maker for compliance matters?",
            'current_status': "Do you currently have any EPR registrations?"
        }
        
        self.qualification_scores = {
            'industry': {'manufacturing': 10, 'fmcg': 10, 'pharma': 9, 'food': 8, 'ecommerce': 7, 'other': 5},
            'volume': {'high': 10, 'medium': 7, 'low': 4, 'unknown': 2},
            'timeline': {'immediate': 10, 'this_month': 8, 'next_quarter': 6, 'planning': 3},
            'budget': {'approved': 10, 'in_process': 7, 'planning': 4, 'unknown': 2},
            'decision_maker': {'yes': 10, 'influencer': 6, 'no': 2},
            'current_status': {'non_compliant': 10, 'partial': 8, 'compliant': 5},
            'company_size': {'enterprise': 20, 'large': 15, 'medium': 10, 'small': 5, 'startup': 3},
            'compliance_risk': {'penalty_received': 25, 'audit_scheduled': 20, 'non_compliant': 15, 'partial': 10, 'compliant': 5},
            'engagement': {'multiple_sessions': 15, 'long_conversation': 12, 'technical_questions': 18, 'shared_contact': 20}
        }
    
    def get_next_qualification_question(self, user_context: Dict, conversation_history: List[Dict]) -> Optional[str]:
        """Get next qualification question based on context"""
        asked_questions = self._extract_asked_questions(conversation_history)
        missing_info = self._identify_missing_info(user_context, asked_questions)
        
        if missing_info:
            return self.qualification_questions.get(missing_info[0])
        return None
    
    def _extract_asked_questions(self, history: List[Dict]) -> List[str]:
        """Extract what qualification questions were already asked"""
        asked = []
        for msg in history:
            if msg.get('role') == 'bot':
                text = msg.get('text', '').lower()
                if 'industry' in text and 'company' in text:
                    asked.append('industry')
                elif 'monthly' in text and 'usage' in text:
                    asked.append('volume')
                elif 'when' in text and 'implement' in text:
                    asked.append('timeline')
                elif 'budget' in text:
                    asked.append('budget')
                elif 'decision maker' in text:
                    asked.append('decision_maker')
        return asked
    
    def _identify_missing_info(self, context: Dict, asked: List[str]) -> List[str]:
        """Identify missing qualification information"""
        missing = []
        
        if not context.get('industry') and 'industry' not in asked:
            missing.append('industry')
        if not context.get('plastic_volume') and 'volume' not in asked:
            missing.append('volume')
        if context.get('urgency') == 'low' and 'timeline' not in asked:
            missing.append('timeline')
        if 'budget' not in asked and len(asked) >= 2:  # Ask after some engagement
            missing.append('budget')
        
        return missing
    
    def calculate_lead_quality_score(self, context: Dict, user_data: Dict) -> int:
        """Calculate lead quality score based on qualification"""
        score = 0
        
        # Industry scoring
        industry = context.get('industry', 'other')
        score += self.qualification_scores['industry'].get(industry, 5)
        
        # Volume scoring
        volume = self._categorize_volume(context.get('plastic_volume'))
        score += self.qualification_scores['volume'].get(volume, 2)
        
        # Timeline scoring
        urgency = context.get('urgency', 'planning')
        timeline_map = {'critical': 'immediate', 'high': 'this_month', 'medium': 'next_quarter', 'low': 'planning'}
        timeline = timeline_map.get(urgency, 'planning')
        score += self.qualification_scores['timeline'].get(timeline, 3)
        
        # Budget scoring
        score += self.qualification_scores['budget'].get(context.get('budget', 'unknown'), 2)
        
        # Decision maker scoring
        score += self.qualification_scores['decision_maker'].get(context.get('decision_maker', 'no'), 2)
        
        # Current status scoring
        score += self.qualification_scores['current_status'].get(context.get('current_status', 'compliant'), 5)
        
        # Company size scoring
        score += self.qualification_scores['company_size'].get(context.get('company_size', 'small'), 5)
        
        # Compliance risk scoring
        score += self.qualification_scores['compliance_risk'].get(context.get('compliance_risk', 'compliant'), 5)
        
        # Behavioral scoring
        engagement_behaviors = context.get('engagement_behaviors', [])
        for behavior in engagement_behaviors:
            score += self.qualification_scores['engagement'].get(behavior, 0)
        
        # Contact info bonus
        if user_data.get('email') and user_data.get('phone'):
            score += 5
        
        # Organization info bonus
        if user_data.get('organization'):
            score += 3
        
        # Apply urgency multiplier
        urgency = context.get('urgency', 'low')
        if urgency == 'critical':
            score = int(score * 2.0)
        elif urgency == 'high':
            score = int(score * 1.5)
        
        return min(score, 150)  # Cap at 150
    
    def _categorize_volume(self, volume_text: Optional[str]) -> str:
        """Categorize plastic volume"""
        if not volume_text:
            return 'unknown'
        
        volume_lower = volume_text.lower()
        if any(word in volume_lower for word in ['ton', 'tonne', 'crore', 'million']):
            return 'high'
        elif any(word in volume_lower for word in ['lakh', 'thousand', 'kg']):
            return 'medium'
        else:
            return 'low'
    
    def should_ask_qualification_question(self, message_count: int, engagement_score: float, context: Dict) -> bool:
        """Determine if we should ask a qualification question"""
        # Disabled - no automatic qualification questions
        return False

lead_qualification = LeadQualification()
