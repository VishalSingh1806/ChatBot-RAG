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
        self.model = genai.GenerativeModel("gemini-2.0-flash-exp")
        self.conversation_history = []  # Store last 5 Q&A pairs
        self.udb_path = r"C:\Users\BHAKTI\OneDrive\Desktop\ReCircle\EPR ChatBot\ChatBot-RAG\UDB\Updated_DB"
    
    def search(self, query: str, intent_result=None, previous_suggestions: list = None) -> Dict:
        """Main hybrid search with DB first, then LLM formatting"""
        logger.info(f"🔄 Hybrid search for: {query[:100]}...")
        
        # Add context from previous questions
        context_aware_query = self._add_conversation_context(query)
        
        # Determine query type
        is_timeline_query = self._is_timeline_query(query)
        is_epr_recircle_query = self._is_epr_recircle_query(query)
        
        if is_timeline_query:
            # Timeline queries: UDB only, then LLM for formatting
            hybrid_answer = self._handle_timeline_query(context_aware_query, query)
        elif is_epr_recircle_query:
            # EPR/ReCircle queries: All DBs first, then LLM
            hybrid_answer = self._handle_epr_recircle_query(context_aware_query, query, intent_result, previous_suggestions)
        else:
            # Generic queries: All DBs first, then LLM
            hybrid_answer = self._handle_generic_query(context_aware_query, query, intent_result, previous_suggestions)
        
        # Store in conversation history
        self._update_conversation_history(query, hybrid_answer)
        
        # Generate suggestions
        suggestions = generate_related_questions(query, [], intent_result, previous_suggestions)
        
        return {
            "answer": hybrid_answer,
            "suggestions": suggestions,
            "source_info": {"hybrid_search": True}
        }
    
    def _is_timeline_query(self, query: str) -> bool:
        """Check if query is timeline/deadline related"""
        timeline_keywords = ['deadline', 'date', 'when', 'timeline', 'filing date', 'due date', 'last date']
        year_patterns = ['2024-25', '2025-26', '2026-27', '2023-24']
        
        # Check for timeline keywords OR year patterns (for follow-up queries)
        has_timeline_keywords = any(keyword in query.lower() for keyword in timeline_keywords)
        has_year_pattern = any(year in query.lower() for year in year_patterns)
        
        return has_timeline_keywords or has_year_pattern
    
    def _is_epr_recircle_query(self, query: str) -> bool:
        """Check if query is EPR or ReCircle related"""
        epr_keywords = ['epr', 'recircle', 'plastic', 'waste', 'packaging', 'compliance', 'registration']
        return any(keyword in query.lower() for keyword in epr_keywords)
    
    def _handle_timeline_query(self, context_query: str, original_query: str) -> str:
        """Handle timeline queries: UDB for 2024-25+, All DBs for earlier years"""
        logger.info("⏰ Timeline query detected")
        
        # Check if query is too general
        if self._is_general_timeline_query(original_query):
            return "Please specify: Which year (2024-25, 2025-26)? (Note: This chatbot focuses on plastic waste EPR only)"
        
        # Check if query is for 2024-25 or onwards
        query_lower = original_query.lower()
        is_2024_onwards = any(year in query_lower for year in ['2024-25', '2025-26', '2026-27', '202425', '202526', '202627'])
        
        if is_2024_onwards:
            # Use UDB only for 2024-25 and onwards
            logger.info("📅 Using UDB for 2024-25+ timeline query")
            udb_result = self._search_udb_only(context_query)
            
            if udb_result and len(udb_result.strip()) > 10:
                formatted_answer = self._format_timeline_answer(udb_result, original_query)
                logger.info("🗄️ Using UDB data with LLM formatting")
                return formatted_answer
            
            return "No plastic waste EPR timeline information found for this year. Please check latest CPCB notifications."
        else:
            # Use all databases for earlier years (2023-24 and before)
            logger.info("📅 Using all databases for pre-2024 timeline query")
            db_results = find_best_answer(context_query, None, None)
            db_answer = db_results.get("answer", "")
            
            if db_answer and len(db_answer.strip()) > 10:
                # Calculate relevance
                similarity = self._calculate_similarity(original_query, db_answer)
                logger.info(f"📊 DB similarity: {similarity:.2f}")
                
                if similarity >= 0.6:
                    # Use DB data with LLM formatting
                    formatted_answer = self._format_db_answer_with_llm(db_answer, original_query)
                    logger.info("🗄️ Using all DB data with LLM formatting")
                    return formatted_answer
            
            # Fallback to LLM for earlier years
            llm_answer = self._get_llm_answer(original_query)
            logger.info("🧠 Using LLM response for earlier year")
            return llm_answer
    
    def _handle_epr_recircle_query(self, context_query: str, original_query: str, intent_result, previous_suggestions) -> str:
        """Handle EPR/ReCircle queries: All DBs first, then LLM"""
        logger.info("🏢 EPR/ReCircle query - All databases first")
        
        # Search all databases first
        db_results = find_best_answer(context_query, intent_result, previous_suggestions)
        db_answer = db_results.get("answer", "")
        
        if db_answer and len(db_answer.strip()) > 10:
            # Calculate relevance
            similarity = self._calculate_similarity(original_query, db_answer)
            logger.info(f"📊 DB similarity: {similarity:.2f}")
            
            if similarity >= 0.6:
                # Use DB data with LLM formatting
                formatted_answer = self._format_db_answer_with_llm(db_answer, original_query)
                logger.info("🗄️ Using DB data (60%+ relevant) with LLM formatting")
                return formatted_answer
        
        # Fallback to LLM
        llm_answer = self._get_llm_answer(original_query)
        logger.info("🧠 Using LLM response (DB not relevant enough)")
        return llm_answer
    
    def _handle_generic_query(self, context_query: str, original_query: str, intent_result, previous_suggestions) -> str:
        """Handle generic queries: All DBs first, then LLM"""
        logger.info("❓ Generic query - All databases first")
        
        # Search all databases first
        db_results = find_best_answer(context_query, intent_result, previous_suggestions)
        db_answer = db_results.get("answer", "")
        
        if db_answer and len(db_answer.strip()) > 10:
            # Calculate relevance
            similarity = self._calculate_similarity(original_query, db_answer)
            logger.info(f"📊 DB similarity: {similarity:.2f}")
            
            if similarity >= 0.6:
                # Use DB data with LLM formatting
                formatted_answer = self._format_db_answer_with_llm(db_answer, original_query)
                logger.info("🗄️ Using DB data (60%+ relevant) with LLM formatting")
                return formatted_answer
        
        # Fallback to LLM
        llm_answer = self._get_llm_answer(original_query)
        logger.info("🧠 Using LLM response (DB not relevant enough)")
        return llm_answer
    
    def _is_general_timeline_query(self, query: str) -> bool:
        """Check if timeline query is too general and needs specificity"""
        query_lower = query.lower()
        has_specific_year = any(year in query_lower for year in ['2024-25', '2025-26', '2026-27', '2023-24'])
        has_specific_type = any(word in query_lower for word in ['plastic', 'packaging', 'state', 'pro'])
        
        return len(query.split()) <= 6 and not has_specific_year and not has_specific_type
    
    def _search_udb_only(self, query: str) -> str:
        """Search only UDB database for timeline queries"""
        logger.info(f"🔍 Searching UDB for query: {query}")
        logger.info(f"📁 UDB path: {self.udb_path}")
        
        try:
            import chromadb
            import google.generativeai as genai
            from chromadb import EmbeddingFunction
            
            class GeminiEmbeddingFunction(EmbeddingFunction):
                def __call__(self, input):
                    embeddings = []
                    for text in input:
                        result = genai.embed_content(
                            model="models/text-embedding-004",
                            content=text
                        )
                        embeddings.append(result['embedding'])
                    return embeddings
            
            client = chromadb.PersistentClient(path=self.udb_path)
            logger.info(f"✅ Connected to UDB client")
            
            collection = client.get_collection(
                name="updated_db",
                embedding_function=GeminiEmbeddingFunction()
            )
            logger.info(f"✅ Got UDB collection with {collection.count()} documents")
            
            results = collection.query(
                query_texts=[query],
                n_results=3
            )
            logger.info(f"📊 UDB query returned {len(results['documents'][0]) if results['documents'] and results['documents'][0] else 0} results")
            
            if results['documents'] and results['documents'][0]:
                # Log first result for debugging
                first_result = results['documents'][0][0][:200] if results['documents'][0] else "No results"
                logger.info(f"📄 First UDB result: {first_result}...")
                
                # Combine top results
                combined_result = " ".join(results['documents'][0][:2])
                return self._clean_text(combined_result)
            else:
                logger.warning("⚠️ No documents found in UDB results")
            
        except Exception as e:
            logger.error(f"❌ UDB search failed: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
        
        return ""
    
    def _format_timeline_answer(self, udb_data: str, query: str) -> str:
        """Use LLM to format UDB timeline data professionally"""
        requested_year = self._get_requested_year(query)
        
        # Pre-check: If asking for 2025-26 or 2026-27, return no info message directly
        if requested_year in ['2025-26', '2026-27']:
            return f"No specific filing deadline available for FY {requested_year}. Please check latest CPCB notifications."
        
        # Only process if asking for 2024-25 or if year matches data
        if requested_year == '2024-25':
            prompt = f"""
            Extract the deadline date for FY 2024-25 ONLY:
            
            Database Info: {udb_data}
            User Query: {query}
            
            Instructions:
            - Extract deadline ONLY if it's for FY 2024-25
            - Format: "The annual report filing deadline for FY 2024-25 is [DATE]."
            - If no 2024-25 deadline found, say "No specific deadline found"
            - Keep response under 20 words
            """
            
            try:
                generation_config = genai.types.GenerationConfig(
                    temperature=0.1,
                    top_p=0.8,
                    max_output_tokens=40
                )
                response = self.model.generate_content(prompt, generation_config=generation_config)
                return self._clean_text(response.text.strip())
            except Exception as e:
                logger.error(f"Timeline formatting failed: {e}")
                return self._extract_deadline_from_text(udb_data, requested_year)
        
        # For any other year, return no info message
        return f"No specific filing deadline available for FY {requested_year}. Please check latest CPCB notifications."
    
    def _format_db_answer_with_llm(self, db_answer: str, query: str) -> str:
        """Use LLM to format database answer"""
        prompt = f"""
        Format this database information into a clear, specific answer:
        
        Database Info: {db_answer}
        User Query: {query}
        
        Instructions:
        - Keep response under 100 words
        - Be specific and accurate
        - For multiple points, use numbered format: "1. Point one\n2. Point two\n3. Point three"
        - NO markdown formatting (no **, -, •)
        - Remove irrelevant information
        - Start directly with the answer
        - Use plain text with proper line breaks for readability
        """
        
        try:
            generation_config = genai.types.GenerationConfig(
                temperature=0.1,
                top_p=0.8,
                max_output_tokens=150
            )
            response = self.model.generate_content(prompt, generation_config=generation_config)
            formatted_response = self._format_for_chat_ui(response.text.strip())
            return self._clean_text(formatted_response)
        except Exception as e:
            logger.error(f"DB formatting failed: {e}")
            return self._clean_text(db_answer)[:200]
    
    def _get_llm_answer(self, query: str) -> str:
        """Get direct LLM answer for queries without relevant DB data"""
        prompt = f"""
        Answer this EPR compliance question concisely:
        
        Query: {query}
        
        Instructions:
        - Keep response under 80 words
        - Be specific and accurate
        - For multiple points, use numbered format: "1. Point one\n2. Point two\n3. Point three"
        - NO markdown formatting (no **, -, •)
        - Focus on Indian EPR regulations
        - Start directly with the answer
        - Use plain text with proper line breaks for readability
        """
        
        try:
            generation_config = genai.types.GenerationConfig(
                temperature=0.1,
                top_p=0.8,
                max_output_tokens=120
            )
            response = self.model.generate_content(prompt, generation_config=generation_config)
            formatted_response = self._format_for_chat_ui(response.text.strip())
            return self._clean_text(formatted_response)
        except Exception as e:
            logger.error(f"LLM answer failed: {e}")
            return "Unable to provide specific information. Please check official CPCB notifications."
    
    def _get_requested_year(self, query: str) -> str:
        """Extract requested year from query"""
        query_lower = query.lower()
        if '2024-25' in query_lower or '202425' in query_lower:
            return '2024-25'
        elif '2025-26' in query_lower or '202526' in query_lower:
            return '2025-26'
        elif '2026-27' in query_lower or '202627' in query_lower:
            return '2026-27'
        return None
    
    def _extract_deadline_from_text(self, text: str, requested_year: str = None) -> str:
        """Extract deadline information from text"""
        import re
        
        clean_text = self._clean_text(text)
        
        # Based on UDB analysis, only 2024-25 has a specific deadline
        if requested_year == '2025-26':
            return f"No specific filing deadline available for FY {requested_year}. Please check latest CPCB notifications."
        elif requested_year == '2026-27':
            return f"No specific filing deadline available for FY {requested_year}. Please check latest CPCB notifications."
        
        # For 2024-25, extract the deadline
        if requested_year == '2024-25':
            # Look for the specific deadline in the text
            if '31 January 2026' in clean_text:
                return "The annual report filing deadline for FY 2024-25 is 31 January 2026."
        
        # General date pattern extraction
        date_patterns = [
            r'deadline.*?is\s+([0-9]{1,2}\s+[A-Za-z]+\s+[0-9]{4})',
            r'by\s+([0-9]{1,2}\s+[A-Za-z]+\s+[0-9]{4})',
            r'([0-9]{1,2}\s+[A-Za-z]+\s+[0-9]{4})'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, clean_text, re.IGNORECASE)
            if match:
                if requested_year:
                    return f"The annual report filing deadline for FY {requested_year} is {match.group(1)}."
                else:
                    return f"The annual report filing deadline is {match.group(1)}."
        
        # If no specific date found
        if requested_year and requested_year != '2024-25':
            return f"No specific filing deadline available for FY {requested_year}. Please check latest CPCB notifications."
        
        return "No specific deadline information found."
    
    def _calculate_similarity(self, query: str, answer: str) -> float:
        """Calculate similarity between query and answer"""
        if not query or not answer:
            return 0.0
        
        query_words = set(query.lower().split())
        answer_words = set(answer.lower().split())
        
        if not query_words:
            return 0.0
        
        intersection = len(query_words.intersection(answer_words))
        union = len(query_words.union(answer_words))
        
        return intersection / union if union > 0 else 0.0
    
    def _add_conversation_context(self, query: str) -> str:
        """Add context from last 5 conversations for follow-up queries"""
        if not self.conversation_history:
            return query
        
        query_lower = query.lower().strip()
        
        # Check if this is a year follow-up (like "2024-25")
        import re
        year_pattern = r'^(202[3-9]-[0-9]{2})$'
        if re.match(year_pattern, query_lower):
            # Look for previous deadline/filing questions
            for prev_item in reversed(self.conversation_history[-3:]):
                prev_query = prev_item['question'].lower()
                if any(keyword in prev_query for keyword in ['deadline', 'filing', 'date', 'annual', 'report']):
                    # Combine with plastic waste context
                    enhanced = f"plastic waste EPR annual report filing deadline for {query}"
                    logger.info(f"🔗 Enhanced year query: '{enhanced}'")
                    return enhanced
            
            # If no previous context, still add plastic waste context for year queries
            enhanced = f"plastic waste EPR annual report filing deadline for {query}"
            logger.info(f"🔗 Added plastic waste context to year query: '{enhanced}'")
            return enhanced
        
        # For other follow-up patterns
        follow_up_patterns = [r'^for (202[3-9]-[0-9]{2})', r'^what about', r'^and (202[3-9]-[0-9]{2})']
        is_follow_up = any(re.match(pattern, query_lower) for pattern in follow_up_patterns)
        
        if is_follow_up and self.conversation_history:
            last_question = self.conversation_history[-1]['question']
            # Add plastic waste context for EPR queries
            if any(keyword in last_question.lower() for keyword in ['deadline', 'filing', 'epr']):
                combined = f"plastic waste EPR {last_question} {query}"
                logger.info(f"🔗 Enhanced follow-up: '{combined}'")
                return combined
        
        return query
    
    def _update_conversation_history(self, question: str, answer: str):
        """Maintain last 5 Q&A pairs"""
        self.conversation_history.append({
            "question": question,
            "answer": answer
        })
        
        if len(self.conversation_history) > 5:
            self.conversation_history = self.conversation_history[-5:]
    
    def _format_for_chat_ui(self, text: str) -> str:
        """Format text specifically for chat UI with proper line breaks"""
        if not text:
            return ""
        
        import re
        
        # Convert numbered lists to proper format with line breaks
        # Pattern: "1. text 2. text 3. text" -> "1. text\n2. text\n3. text"
        text = re.sub(r'(\d+\.)\s*([^\d]*?)(?=\s*\d+\.|$)', r'\1 \2\n', text)
        
        # Clean up any trailing newlines and extra spaces
        text = re.sub(r'\n+$', '', text)
        text = re.sub(r'\s+', ' ', text)
        text = text.replace('\n ', '\n')
        
        return text.strip()
    
    def _clean_text(self, text: str) -> str:
        """Clean text for chat UI display"""
        if not text:
            return ""
        
        import re
        
        # Remove HTML entities
        text = text.replace("&quot;", '"').replace("&amp;", "&")
        text = text.replace("&lt;", "<").replace("&gt;", ">")
        
        # Remove markdown formatting
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # Remove **bold**
        text = re.sub(r'\*(.*?)\*', r'\1', text)      # Remove *italic*
        text = re.sub(r'`(.*?)`', r'\1', text)        # Remove `code`
        text = re.sub(r'#{1,6}\s*', '', text)         # Remove headers
        text = re.sub(r'^[-\*\+•]\s+', '', text, flags=re.MULTILINE)  # Remove bullet points
        
        # Preserve numbered list formatting but clean up extra spaces
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)  # Remove excessive newlines
        text = re.sub(r'[ \t]+', ' ', text)          # Clean up spaces but keep newlines
        
        return text.strip()

# Global instance
hybrid_search_engine = HybridSearchEngine()

def find_hybrid_answer(query: str, intent_result=None, previous_suggestions: list = None) -> Dict:
    """Main entry point for hybrid search"""
    return hybrid_search_engine.search(query, intent_result, previous_suggestions)