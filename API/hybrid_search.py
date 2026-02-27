import google.generativeai as genai
import os
import logging
import re
from typing import Dict, List, Optional
from dotenv import load_dotenv
from search import find_best_answer, generate_related_questions
from config import CHROMA_DB_PATHS, COLLECTIONS
from web_search_integration import search_with_web, web_search_engine

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

class HybridSearchEngine:
    def __init__(self):
        # Read weights from environment variables, with fallback to defaults
        self.llm_weight = float(os.getenv('LLM_WEIGHT', '0.3'))  # Default 30% LLM
        self.db_weight = float(os.getenv('DB_WEIGHT', '0.7'))    # Default 70% Database

        # Ensure weights sum to 1.0
        total_weight = self.llm_weight + self.db_weight
        if total_weight != 1.0:
            self.llm_weight = self.llm_weight / total_weight
            self.db_weight = self.db_weight / total_weight

        logger.info(f"🔧 Hybrid Search Initialized: LLM={self.llm_weight*100:.0f}%, DB={self.db_weight*100:.0f}%")

        self.model = genai.GenerativeModel("gemini-2.0-flash")
        self.conversation_history = []  # Store last 5 Q&A pairs
        self.answer_cache = {}  # Cache for consistent answers to similar questions

        # Cache configuration
        self.cache_max_size = int(os.getenv('CACHE_MAX_SIZE', '100'))  # Max cached queries
        self.cache_enabled = os.getenv('CACHE_ENABLED', 'true').lower() == 'true'
    
    def search(self, query: str, intent_result=None, previous_suggestions: list = None) -> Dict:
        """
        Hybrid search combining LLM knowledge and database search
        + Real-time web search for time-sensitive queries
        + Answer caching for consistency
        """
        logger.info(f"🔄 Hybrid search for: {query[:100]}...")

        # STEP 0: Check cache for consistent answers (only for non-time-sensitive queries)
        cache_key = query.lower().strip()
        if self.cache_enabled and cache_key in self.answer_cache:
            # Don't use cache for time-sensitive queries
            if not web_search_engine.is_time_sensitive_query(query):
                logger.info(f"✅ Cache hit for query: {query[:50]}...")
                return self.answer_cache[cache_key]

        # STEP 1: Use Gemini to understand and enhance query
        enhanced_query = self._understand_query_with_gemini(query)

        # STEP 2: Check if query requires real-time web search
        is_time_sensitive = web_search_engine.is_time_sensitive_query(enhanced_query)

        # STEP 3: Add context from previous questions
        context_aware_query = self._add_conversation_context(enhanced_query)

        # Get database results (40%)
        db_results = find_best_answer(context_aware_query, intent_result, previous_suggestions)
        db_answer = db_results.get("answer", "")

        # Check if this is a deadline/date query - these should use database directly
        is_deadline_query = any(word in query.lower() for word in ['deadline', 'last date', 'due date', 'filing date', 'when', 'arf', 'annual return'])

        # FOR DEADLINE QUERIES: Use database answer directly without LLM mixing
        if is_deadline_query and db_answer and len(db_answer) > 50:
            logger.info(f"📅 Deadline query detected - using database answer directly")
            hybrid_answer = db_answer
            source_info = {
                "hybrid_search": False,
                "database_only": True,
                "db_source": db_results.get("source_info", {})
            }
        # FOR TIME-SENSITIVE QUERIES: Use web search + database
        elif is_time_sensitive:
            logger.info(f"⏰ Time-sensitive query detected - using web search")
            web_result = search_with_web(query, db_answer)

            if web_result.get("web_search_used"):
                # Web search succeeded - use real-time answer
                hybrid_answer = web_result["answer"]
                source_info = {
                    "hybrid_search": True,
                    "web_search_enabled": True,
                    "is_real_time": True,
                    "source": web_result["source_info"]["source"],
                    "db_source": db_results.get("source_info", {})
                }
            else:
                # Web search failed - fall back to normal hybrid
                logger.warning("⚠️ Web search unavailable, using normal hybrid search")
                llm_results = self._get_llm_knowledge(context_aware_query, query)
                hybrid_answer = self._combine_results(db_results, llm_results, query)
                source_info = {
                    "hybrid_search": True,
                    "web_search_enabled": False,
                    "llm_weight": self.llm_weight,
                    "db_weight": self.db_weight,
                    "db_source": db_results.get("source_info", {})
                }
        else:
            # NORMAL HYBRID SEARCH: 60% LLM + 40% Database
            llm_results = self._get_llm_knowledge(context_aware_query, query)
            hybrid_answer = self._combine_results(db_results, llm_results, query)
            source_info = {
                "hybrid_search": True,
                "web_search_enabled": False,
                "llm_weight": self.llm_weight,
                "db_weight": self.db_weight,
                "db_source": db_results.get("source_info", {})
            }

        # GEMINI-BASED INTELLIGENT FILTERING: Remove irrelevant content
        if not is_deadline_query and len(hybrid_answer) > 150:
            logger.info(f"🤖 Using Gemini to filter response (length: {len(hybrid_answer)} chars)")

            filter_prompt = f"""You are a content filter. Your job is to remove ONLY the irrelevant parts from this answer.

User asked: "{query}"

Current answer:
{hybrid_answer}

INSTRUCTIONS:
1. Keep ONLY the information that DIRECTLY answers the user's question
2. REMOVE any information about:
   - Quarterly filing deadlines (Q1, Q2, Q3, Q4)
   - EPR certificate deadlines unless asked
   - Annual return filing dates unless asked
   - Barcode/QR code requirements unless asked
   - Any dates or deadlines unless specifically asked
3. Keep the answer SHORT - maximum 60 words
4. Return ONLY the filtered answer, nothing else

Filtered answer:"""

            try:
                filter_config = genai.types.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=100
                )
                filter_response = self.model.generate_content(filter_prompt, generation_config=filter_config)
                filtered_answer = filter_response.text.strip()

                if filtered_answer and len(filtered_answer) >= 30:
                    original_len = len(hybrid_answer)
                    hybrid_answer = filtered_answer
                    logger.info(f"✅ Gemini filtered: {original_len} → {len(hybrid_answer)} chars")
                else:
                    logger.warning(f"⚠️ Gemini filter returned too short, keeping original")
            except Exception as e:
                logger.error(f"❌ Gemini filter failed: {e}")

            # Additional cleanup patterns for any remaining fragments
            cleanup_patterns = [
                r'(?:with|and) (?:specific )?deadlines.*?(?:\.|$)',
                r'Q[1-4]\s*\([^)]+\)[:\s]*[^;\n]*',
                r'The deadline for filing.*?(?:\.|$)',
                r'Under the Plastic Waste Management Amendment Rules.*?\d{4}\)',
                r'\n\s*•\s*Q[1-4].*?(?:\n|$)',
            ]

            for pattern in cleanup_patterns:
                hybrid_answer = re.sub(pattern, '', hybrid_answer, flags=re.DOTALL | re.IGNORECASE | re.MULTILINE)

            # Final cleanup
            hybrid_answer = re.sub(r'\n\s*\n+', '\n\n', hybrid_answer)
            hybrid_answer = re.sub(r'[,;:]\s*$', '.', hybrid_answer)
            hybrid_answer = hybrid_answer.strip()

        # Store this Q&A in conversation history
        self._update_conversation_history(query, hybrid_answer)

        # Generate suggestions using the same FAQ CSV logic as main search
        suggestions = generate_related_questions(query, [], intent_result, previous_suggestions)

        result = {
            "answer": hybrid_answer,
            "suggestions": suggestions,
            "source_info": source_info
        }

        # Cache the result for non-time-sensitive queries
        if self.cache_enabled and not is_time_sensitive:
            self._cache_result(cache_key, result)

        return result

    def _understand_query_with_gemini(self, query: str) -> str:
        """Use Gemini to understand and enhance query before database search"""

        prompt = f"""Analyze this user query and rewrite it for better database search.

User Query: "{query}"

Tasks:
1. Normalize year formats (2023-2024 → 2023-24, 2024-2025 → 2024-25)
2. Add EPR/plastic waste context if missing and query is EPR-related
3. Expand abbreviations (PRO → Producer Responsibility Organization, CPCB → Central Pollution Control Board)
4. Keep the original intent and meaning
5. If query is already clear and specific, return it as-is

Return ONLY the enhanced query, nothing else. No explanations.

Examples:
Input: "what about 2023-2024"
Output: plastic waste EPR annual report filing deadline for 2023-24

Input: "deadline for 2024-25"
Output: plastic waste EPR annual report filing deadline for FY 2024-25

Input: "PRO registration process"
Output: Producer Responsibility Organization EPR registration process

Input: "What documents are needed for EPR registration?"
Output: What documents are needed for EPR registration?

Enhanced Query:"""

        try:
            generation_config = genai.types.GenerationConfig(
                temperature=0.1,  # Low temperature for consistency
                top_p=0.8,
                max_output_tokens=100
            )
            response = self.model.generate_content(prompt, generation_config=generation_config)
            enhanced_query = response.text.strip().strip('"').strip()

            logger.info(f"🧠 Query Understanding: '{query}' → '{enhanced_query}'")
            return enhanced_query
        except Exception as e:
            logger.error(f"❌ Query understanding failed: {e}")
            return query  # Fallback to original query on error

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
        As an EPR compliance expert, answer this query:

        {context_query if len(self.conversation_history) > 0 else f"Query: {original_query}"}

        RULES:
        - If you know the answer with certainty, provide it directly and concisely
        - If the question asks for specific dates, deadlines, or time-sensitive information that you're uncertain about,
          respond with: "For the latest information on [topic], please check the CPCB portal at cpcb.nic.in or contact the EPR helpline."
        - Focus ONLY on EPR plastic waste (do NOT mention e-waste, battery waste, etc.)
        - Keep answers SHORT: Maximum 100-150 words
        - Simple questions = 1-2 sentence answers ONLY
        - Start with the answer immediately (no preambles)
        - Use bullet points only if listing 3+ items
        - Be factual and helpful

        Provide a clear, concise answer:
        """
        
        try:
            generation_config = genai.types.GenerationConfig(
                temperature=0.2,
                top_p=0.85,
                max_output_tokens=80  # STRICT LIMIT: 60 words max
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
            # Regular hybrid search with configurable weights
            combination_prompt = f"""
            Create a direct answer combining these sources:

            LLM KNOWLEDGE ({int(self.llm_weight*100)}% weight):
            {llm_knowledge}

            DATABASE KNOWLEDGE ({int(self.db_weight*100)}% weight):
            {db_answer}

            USER QUERY: {query}

            CRITICAL INSTRUCTION - READ CAREFULLY:
            The database contains extra information that is NOT relevant to the user's question.
            Your job is to extract ONLY what answers the question and IGNORE everything else.

            USER QUESTION: {query}

            RULES:
            1. Answer in MAXIMUM 50 words - be extremely concise
            2. If user asks "what is EPR" or "what is C1" - give ONLY the definition, nothing else
            3. DO NOT include:
               - Quarterly deadlines (Q1, Q2, Q3, Q4)
               - EPR certificate filing dates
               - Annual return deadlines
               - Barcode/QR requirements
               - Registration deadlines
               UNLESS the user specifically asks about deadlines/dates
            4. If database includes deadlines but user didn't ask - COMPLETELY IGNORE THEM
            5. Think: "Did the user ask for this specific piece of information?" If NO, don't include it
            6. Simple definition questions should get 1-2 sentence answers ONLY

            EXAMPLES:
            - User: "what is EPR" → Answer: "EPR is Extended Producer Responsibility where producers manage plastic waste lifecycle." STOP
            - User: "what is C1" → Answer: "Category 1 plastic refers to rigid plastic packaging materials." STOP
            - User: "when is deadline" → Now you can include deadline info

            Extract ONLY the answer to "{query}" (max 50 words):
            """
        
        try:
            generation_config = genai.types.GenerationConfig(
                temperature=0.1,  # Lower temperature for more focused answers
                top_p=0.7,        # Lower top_p to reduce randomness
                max_output_tokens=60  # ULTRA STRICT: 45 words absolute max
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

    def _cache_result(self, cache_key: str, result: Dict):
        """Store result in cache with size limit"""
        # Implement simple LRU-like behavior: remove oldest if cache is full
        if len(self.answer_cache) >= self.cache_max_size:
            # Remove the first (oldest) entry
            oldest_key = next(iter(self.answer_cache))
            del self.answer_cache[oldest_key]
            logger.info(f"🗑️ Cache full, removed oldest entry")

        self.answer_cache[cache_key] = result
        logger.info(f"💾 Cached result for query: {cache_key[:50]}...")

    def clear_cache(self):
        """Clear the answer cache"""
        self.answer_cache.clear()
        logger.info("🧹 Answer cache cleared")

# Global instance
hybrid_search_engine = HybridSearchEngine()

def find_hybrid_answer(query: str, intent_result=None, previous_suggestions: list = None) -> Dict:
    """
    Main function to get hybrid search results
    """
    return hybrid_search_engine.search(query, intent_result, previous_suggestions)