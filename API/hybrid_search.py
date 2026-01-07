import google.generativeai as genai
import os
import logging
from typing import Dict, List, Optional
from dotenv import load_dotenv
from search import find_best_answer, get_collections, generate_related_questions
from config import CHROMA_DB_PATHS, COLLECTIONS

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

class HybridSearchEngine:
    def __init__(self):
        self.llm_weight = 0.6  # 60% LLM
        self.db_weight = 0.4   # 40% Database
        self.model = genai.GenerativeModel("gemini-2.0-flash-exp")
        self.conversation_history = []  # Store last 5 Q&A pairs
    
    def search(self, query: str, intent_result=None, previous_suggestions: list = None) -> Dict:
        """
        Hybrid search - LLM FIRST for EPR queries, then supplement with database
        """
        logger.info(f"🔄 Hybrid search for: {query[:100]}...")
        
        # Add context from previous questions
        context_aware_query = self._add_conversation_context(query)
        
        # For EPR queries, get LLM knowledge FIRST (prioritize 60% weight)
        llm_results = self._get_llm_knowledge(context_aware_query, query)
        logger.info(f"📝 LLM response length: {len(llm_results) if llm_results else 0}")
        
        # Get database results (40% - supplementary)
        db_results = find_best_answer(context_aware_query, intent_result, previous_suggestions)
        
        # Combine with LLM priority
        hybrid_answer = self._combine_results_llm_first(db_results, llm_results, query)
        
        # Store this Q&A in conversation history
        self._update_conversation_history(query, hybrid_answer)
        
        # Generate suggestions using the same FAQ CSV logic as main search
        suggestions = generate_related_questions(query, [], intent_result, previous_suggestions)
        
        return {
            "answer": hybrid_answer,
            "suggestions": suggestions,
            "source_info": {
                "hybrid_search": True,
                "llm_weight": self.llm_weight,
                "db_weight": self.db_weight,
                "db_source": db_results.get("source_info", {})
            }
        }
    
    def _add_conversation_context(self, query: str) -> str:
        """Add context from previous 5 questions to current query"""
        if not self.conversation_history:
            return query
        
        context = "\n".join([f"Q: {item['question']}\nA: {item['answer'][:100]}..." 
                            for item in self.conversation_history[-3:]])  # Last 3 for brevity
        
        return f"Previous context:\n{context}\n\nCurrent question: {query}"
    
    def _update_conversation_history(self, question: str, answer: str):
        """Update conversation history, keeping only last 5 Q&A pairs"""
        self.conversation_history.append({
            "question": question,
            "answer": answer
        })
        
        # Keep only last 5 conversations
        if len(self.conversation_history) > 5:
            self.conversation_history = self.conversation_history[-5:]
    
    def _get_llm_knowledge(self, context_query: str, original_query: str) -> str:
        """Get LLM's knowledge about the query with conversation context"""
        query_lower = original_query.lower()
        
        # Check if this is a deadline-related query - DON'T process here, let _combine_results handle it
        is_deadline_query = any(keyword in query_lower for keyword in 
                               ['deadline', 'date', 'when', 'timeline', 'filing date', 'due date', 'last date'])
        
        if is_deadline_query:
            # Return placeholder - actual timeline processing happens in _combine_results_llm_first
            return "TIMELINE_QUERY_PLACEHOLDER"
        else:
            # General prompt for non-deadline queries
            prompt = f"""
            You are an EPR compliance expert with specific knowledge of Indian EPR regulations. Answer this query:
            
            Query: {original_query}
            
            SPECIFIC EPR PLASTIC WASTE CATEGORIES (if asked about categories):
            - C1: Rigid plastic packaging (bottles, containers, trays)
            - C2: Flexible plastic packaging (pouches, films, wrappers)
            - C3: Multi-layered plastic packaging (composite materials)
            - C4: Plastic sheets and carry bags
            
            Instructions:
            - Write in natural, professional language
            - Start directly with the answer - NO introductions
            - For categories/lists, use numbered format: "1. ", "2. ", etc.
            - Put each category on a new line
            - Keep each point concise and clear
            - Use normal sentence case, not ALL CAPS
            - Be specific and accurate about EPR regulations
            - Answer ONLY what is asked
            - Format as clean numbered list, not paragraphs or bullet points
            """
        
        try:
            generation_config = genai.types.GenerationConfig(
                temperature=0.1,
                top_p=0.8,
                max_output_tokens=300  # Increased for complete responses
            )
            response = self.model.generate_content(prompt, generation_config=generation_config)
            return response.text.strip()
        except Exception as e:
            logger.error(f"LLM knowledge generation failed: {e}")
            return "LLM knowledge unavailable for this query."
    
    def _get_timeline_response(self, query: str) -> str:
        """Get timeline/deadline response directly from LLM with latest info"""
        logger.info(f"🚀 CALLING _get_timeline_response with query: {query}")
        
        prompt = f"""
        You are an EPR compliance expert with access to the LATEST 2024-2025 EPR notifications and extensions. Answer this plastic waste EPR deadline query:
        
        Query: {query}
        
        IMPORTANT: Use your most recent knowledge about EPR plastic waste deadlines for 2024-25. There have been extensions beyond the standard June 30 deadline.
        
        Instructions:
        - Provide the CURRENT extended deadline for plastic waste EPR 2024-25
        - Include any recent extensions or changes from CPCB
        - Keep response SHORT (1-2 sentences maximum)
        - Focus ONLY on plastic waste EPR deadlines
        - Give the most up-to-date information available
        """
        
        try:
            logger.info(f"📤 Sending prompt to LLM: {prompt[:200]}...")
            generation_config = genai.types.GenerationConfig(
                temperature=0.1,
                top_p=0.8,
                max_output_tokens=100
            )
            response = self.model.generate_content(prompt, generation_config=generation_config)
            llm_response = response.text.strip()
            logger.info(f"📥 LLM returned: {llm_response[:200]}...")
            return llm_response
        except Exception as e:
            logger.error(f"❌ Timeline LLM response failed: {e}")
            return "Please check the latest EPR notifications for current deadline information."
    
    def _get_timeline_response_knowledge_based(self, query: str) -> str:
        """Get timeline response using LLM's training knowledge"""
        logger.info(f"🚀 CALLING knowledge-based timeline response for: {query}")
        
        prompt = f"""
        You are an EPR expert. Provide the plastic waste EPR deadline for this query:
        
        Query: {query}
        
        Based on EPR patterns:
        - 2024-25 deadline: Extended to November 30, 2025
        - 2025-26 deadline: June 30, 2026 (standard pattern)
        - 2026-27 deadline: June 30, 2027 (standard pattern)
        
        Instructions:
        - Give the specific deadline date for the year asked
        - Keep response SHORT (maximum 10 words)
        - Format: "The deadline is [DATE]"
        - Use established EPR deadline patterns
        """
        
        try:
            generation_config = genai.types.GenerationConfig(
                temperature=0.1,
                top_p=0.8,
                max_output_tokens=25
            )
            response = self.model.generate_content(prompt, generation_config=generation_config)
            return response.text.strip()
        except Exception as e:
            logger.error(f"❌ Knowledge-based timeline failed: {e}")
            return "EPR annual filing deadline is typically June 30 of the following year. Please check CPCB notifications for current extensions."
    
    def _calculate_similarity(self, query: str, db_answer: str) -> float:
        """Calculate similarity between query and database answer using Jaccard similarity"""
        if not query or not db_answer:
            return 0.0
        
        query_words = set(query.lower().split())
        answer_words = set(db_answer.lower().split())
        
        if not query_words:
            return 0.0
        
        # Calculate Jaccard similarity
        intersection = len(query_words.intersection(answer_words))
        union = len(query_words.union(answer_words))
        
        return intersection / union if union > 0 else 0.0
    
    def _combine_results_llm_first(self, db_results: Dict, llm_knowledge: str, query: str) -> str:
        """Smart combination: Use DB only if 80% similar, otherwise use LLM"""
        db_answer = db_results.get("answer", "")
        query_lower = query.lower()
        
        # Debug logging
        logger.info(f"🔍 Query: {query}")
        logger.info(f"📊 LLM response: {llm_knowledge[:100] if llm_knowledge else 'None'}...")
        logger.info(f"🗄️ DB response: {db_answer[:100] if db_answer else 'None'}...")
        
        # 1. ReCircle contact queries - DATABASE first
        is_contact_query = any(keyword in query_lower for keyword in 
                              ['address', 'contact', 'phone', 'email', 'office', 'location', 'visit', 'call'])
        is_recircle_mentioned = 'recircle' in query_lower
        
        if is_recircle_mentioned and is_contact_query:
            if db_answer and len(db_answer.strip()) > 10:
                logger.info(f"📞 Using DB for ReCircle contact")
                return self._clean_text(db_answer)
            elif llm_knowledge and len(llm_knowledge.strip()) > 5:
                logger.info(f"📞 Fallback to LLM for ReCircle contact")
                return self._clean_text(llm_knowledge)
        
        # 2. Deadline/Timeline queries - Check if specific or generic
        is_deadline_query = any(keyword in query_lower for keyword in 
                               ['deadline', 'date', 'when', 'timeline', 'filing date', 'due date', 'last date'])
        
        # Check if this is a follow-up year specification (short response like "2025-26" or "for 2024-25")
        is_year_followup = (len(query.split()) <= 3) and \
                          any(year in query_lower for year in ['2024-25', '2025-26', '2026-27', '2023-24', '2024', '2025', '2026', '2027'])
        
        # Check if query mentions specific year or is a follow-up
        has_specific_year = any(year in query_lower for year in ['2024', '2025', '2026', '2027', '2023'])
        
        # Check if any of the last 5 questions was about deadlines
        previous_was_deadline = False
        last_deadline_question = ""
        if self.conversation_history and is_year_followup:
            # Check last 5 questions for deadline context
            for i in range(min(5, len(self.conversation_history))):
                past_question = self.conversation_history[-(i+1)]['question'].lower()
                if any(keyword in past_question for keyword in 
                      ['deadline', 'date', 'when', 'timeline', 'filing date', 'due date']):
                    previous_was_deadline = True
                    last_deadline_question = self.conversation_history[-(i+1)]['question']
                    break
        
        if is_deadline_query or is_year_followup:
            # ALWAYS use LLM DIRECTLY for timeline queries - NO DB check
            logger.info(f"⏰ DETECTED timeline query - using LLM DIRECTLY (no DB check)")
            
            if is_year_followup and previous_was_deadline:
                combined_query = f"{last_deadline_question} {query}"
                logger.info(f"📅 Combined timeline query: {combined_query}")
                timeline_response = self._get_timeline_response_knowledge_based(combined_query)
            elif has_specific_year or is_deadline_query:
                logger.info(f"📅 Direct timeline query: {query}")
                timeline_response = self._get_timeline_response_knowledge_based(query)
            else:
                logger.info(f"❓ Generic deadline query - asking for specifics")
                return "Could you please specify the exact year? For example: 'What is the deadline for annual report filing for 2024-25?' This will help me provide you with the accurate date."
            
            logger.info(f"✅ Timeline response generated: {timeline_response[:100]}...")
            return self._clean_text(timeline_response)
        
        # 3. EPR queries - Check DB similarity first (80% threshold)
        is_epr_query = any(keyword in query_lower for keyword in 
                          ['epr', 'filing', 'annual', 'return', 'compliance', 'registration', 'waste', 'categories', 'plastic'])
        
        if is_epr_query and db_answer and len(db_answer.strip()) > 10:
            similarity = self._calculate_similarity(query, db_answer)
            logger.info(f"📈 DB similarity score: {similarity:.2f}")
            
            # If similarity is 80% or higher, combine DB + LLM
            if similarity >= 0.8:
                logger.info(f"🔄 Combining DB + LLM (high similarity: {similarity:.2f})")
                combined_answer = self._combine_db_and_llm(db_answer, llm_knowledge, query)
                return self._clean_text(combined_answer)
            else:
                logger.info(f"⚠️ DB similarity too low ({similarity:.2f}), using LLM only")
                if llm_knowledge and len(llm_knowledge.strip()) > 5:
                    return self._clean_text(llm_knowledge)
        
        # 4. All other queries - LLM first
        if llm_knowledge and len(llm_knowledge.strip()) > 10:
            logger.info(f"✅ Using LLM for general query")
            return self._clean_text(llm_knowledge)
        
        # Final fallback to database
        if db_answer and len(db_answer.strip()) > 10:
            logger.info(f"⚠️ Final fallback to DB")
            return self._clean_text(db_answer)
        
        return "I don't have sufficient information to answer this query."
    
    def _combine_db_and_llm(self, db_answer: str, llm_knowledge: str, query: str) -> str:
        """Combine database and LLM knowledge for comprehensive answer"""
        prompt = f"""
        Create a professional, comprehensive answer by combining these sources:
        
        DATABASE INFORMATION:
        {db_answer}
        
        LLM KNOWLEDGE:
        {llm_knowledge}
        
        USER QUERY: {query}
        
        Instructions:
        - Combine both sources to create one comprehensive answer
        - Start directly with the answer - NO introductions
        - Preserve original formatting from database (numbered lists, bullet points)
        - Keep the exact structure and formatting as provided
        - Ensure accuracy by prioritizing database facts
        - Don't modify the formatting style of structured content
        - Maintain numbered questions and detailed answers format
        """
        
        try:
            generation_config = genai.types.GenerationConfig(
                temperature=0.1,
                top_p=0.8,
                max_output_tokens=300
            )
            response = self.model.generate_content(prompt, generation_config=generation_config)
            return response.text.strip()
        except Exception as e:
            logger.error(f"DB+LLM combination failed: {e}")
            # Fallback to database answer
            return db_answer
    
    def _clean_text(self, text: str) -> str:
        """Clean HTML entities and format text professionally"""
        if not text:
            return ""
        
        # Clean HTML entities
        text = text.replace("&quot;", '"').replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
        
        # Format text professionally
        text = self._format_professional_text(text)
        
        return text.strip()
    
    def _format_professional_text(self, text: str) -> str:
        """Format text to preserve original structure while cleaning up"""
        if not text:
            return ""
        
        # Clean HTML entities but preserve structure
        text = text.replace("&amp;", "&").replace("&quot;", '"').replace("&lt;", "<").replace("&gt;", ">")
        
        # Preserve numbered lists and bullet points as they are
        # Don't modify capitalization for structured content
        return text.strip()
    
    def _fallback_combination(self, db_answer: str, llm_knowledge: str) -> str:
        """Simple fallback combination if LLM combination fails"""
        if not db_answer and not llm_knowledge:
            return "I don't have sufficient information to answer this query."
        
        # Prioritize LLM knowledge (60% weight)
        if llm_knowledge and len(llm_knowledge.strip()) > 20:
            return llm_knowledge
        
        if db_answer and len(db_answer.strip()) > 20:
            return db_answer
        
        # Return whatever we have
        return llm_knowledge or db_answer or "I don't have sufficient information to answer this query."

# Global instance
hybrid_search_engine = HybridSearchEngine()

def find_hybrid_answer(query: str, intent_result=None, previous_suggestions: list = None) -> Dict:
    """
    Main function to get hybrid search results
    """
    return hybrid_search_engine.search(query, intent_result, previous_suggestions)