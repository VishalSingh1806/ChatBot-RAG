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
        Hybrid search combining LLM knowledge (60%) and database search (40%)
        """
        logger.info(f"🔄 Hybrid search for: {query[:100]}...")
        
        # Add context from previous questions
        context_aware_query = self._add_conversation_context(query)
        
        # Get database results (40%)
        db_results = find_best_answer(context_aware_query, intent_result, previous_suggestions)
        
        # Get LLM knowledge (60%)
        llm_results = self._get_llm_knowledge(context_aware_query, query)
        
        # Combine results with weighted scores
        hybrid_answer = self._combine_results(db_results, llm_results, query)
        
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
        prompt = f"""
        As an EPR compliance expert, answer this query directly without introductions:
        
        {context_query if len(self.conversation_history) > 0 else f"Query: {original_query}"}
        
        Instructions:
        - Start directly with the answer - NO introductions or overviews
        - Provide specific, actionable information
        - Use proper formatting (headings, bullet points) when helpful
        - Be comprehensive but focused
        - Clean up HTML entities
        - Answer exactly what was asked
        
        Provide a direct, well-formatted answer:
        """
        
        try:
            generation_config = genai.types.GenerationConfig(
                temperature=0.1,
                top_p=0.8,
                max_output_tokens=800  # Increased for better formatted responses
            )
            response = self.model.generate_content(prompt, generation_config=generation_config)
            return response.text.strip()
        except Exception as e:
            logger.error(f"LLM knowledge generation failed: {e}")
            return "LLM knowledge unavailable for this query."
    
    def _combine_results(self, db_results: Dict, llm_knowledge: str, query: str) -> str:
        """Combine database and LLM results with 60% LLM, 40% Database"""
        db_answer = db_results.get("answer", "")
        
        # Check if query is specifically about ReCircle contact info - prioritize database
        query_lower = query.lower()
        is_contact_query = any(keyword in query_lower for keyword in 
                              ['address', 'contact', 'phone', 'email', 'office', 'location', 'visit', 'call'])
        is_recircle_mentioned = 'recircle' in query_lower
        
        # Only prioritize database for contact-specific ReCircle queries
        if is_recircle_mentioned and is_contact_query and db_answer:
            # For ReCircle contact queries, prioritize database (80%) over LLM (20%)
            combination_prompt = f"""
            Create a direct answer prioritizing DATABASE information for this ReCircle contact query:
            
            DATABASE KNOWLEDGE (Primary - 80% weight):
            {db_answer}
            
            LLM KNOWLEDGE (Secondary - 20% weight):
            {llm_knowledge}
            
            USER QUERY: {query}
            
            Instructions:
            1. Start directly with the DATABASE answer - it has accurate ReCircle information
            2. Use database information as the primary source
            3. Only supplement with LLM if database lacks specific details
            4. Clean up HTML entities (&quot; &amp; etc.)
            5. Provide specific ReCircle contact details if available
            6. Be direct and factual
            
            Provide the database answer with any necessary formatting:
            """
        else:
            # Regular 60% LLM, 40% Database for other queries
            combination_prompt = f"""
            Create a direct answer using these sources - NO introductions:
            
            LLM KNOWLEDGE (60% weight):
            {llm_knowledge}
            
            DATABASE KNOWLEDGE (40% weight):
            {db_answer}
            
            USER QUERY: {query}
            
            Instructions:
            1. Start directly with the answer - NO "Here's" or "Overview" introductions
            2. Prioritize LLM knowledge (60%) as primary source
            3. Use database information (40%) to supplement
            4. Use proper formatting (headings, bullet points) when helpful
            5. Be comprehensive but focused on the specific question
            6. Clean up HTML entities (&quot; &amp; etc.)
            7. Answer exactly what was asked
            
            Provide a direct, well-formatted answer:
            """
        
        try:
            generation_config = genai.types.GenerationConfig(
                temperature=0.1,
                top_p=0.8,
                max_output_tokens=1000  # Increased for comprehensive responses
            )
            response = self.model.generate_content(combination_prompt, generation_config=generation_config)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Result combination failed: {e}")
            return self._fallback_combination(db_answer, llm_knowledge)
    
    def _fallback_combination(self, db_answer: str, llm_knowledge: str) -> str:
        """Simple fallback combination if LLM combination fails"""
        if not db_answer and not llm_knowledge:
            return "I don't have sufficient information to answer this query."
        
        if not db_answer:
            return llm_knowledge
        
        if not llm_knowledge:
            return db_answer
        
        # Simple concatenation with priority indication
        return f"{llm_knowledge}\n\nAdditional Information: {db_answer}"

# Global instance
hybrid_search_engine = HybridSearchEngine()

def find_hybrid_answer(query: str, intent_result=None, previous_suggestions: list = None) -> Dict:
    """
    Main function to get hybrid search results
    """
    return hybrid_search_engine.search(query, intent_result, previous_suggestions)