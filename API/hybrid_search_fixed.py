import google.generativeai as genai
import os
import logging
from typing import Dict, List, Optional
from dotenv import load_dotenv
from search import find_best_answer, get_collections, generate_related_questions
from config import CHROMA_DB_PATHS, COLLECTIONS
import re

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

class HybridSearchEngine:
    def __init__(self):
        self.llm_weight = 0.6
        self.db_weight = 0.4
        self.model = genai.GenerativeModel("gemini-2.0-flash")
        self.conversation_history = []
        self.relevance_threshold = 0.6
    
    def search(self, query: str, intent_result=None, previous_suggestions: list = None) -> Dict:
        """Enhanced hybrid search with improved accuracy"""
        logger.info(f"🔄 Processing query: {query[:100]}...")
        
        # Add context from last 5 conversations
        context_aware_query = self._add_conversation_context(query)
        
        # Detect query type
        query_type = self._detect_query_type(context_aware_query, query)
        logger.info(f"🎯 Query type: {query_type}")
        
        # Route based on query type
        if query_type == "timeline_incomplete":
            hybrid_answer = self._ask_for_year_specification(query)
            suggestions = self._generate_year_suggestions(query)
            
        elif query_type == "timeline_specific":
            hybrid_answer = self._handle_timeline_query(context_aware_query, query)
            suggestions = generate_related_questions(query, [], intent_result, previous_suggestions)
            
        elif query_type == "generic_incomplete":
            hybrid_answer = self._ask_for_specificity(query)
            suggestions = self._generate_specificity_suggestions(query)
            
        else:  # generic_complete
            hybrid_answer = self._handle_generic_query(context_aware_query, query, intent_result, previous_suggestions)
            suggestions = generate_related_questions(query, [], intent_result, previous_suggestions)
        
        # Store in conversation history
        self._update_conversation_history(query, hybrid_answer)
        
        return {
            "answer": hybrid_answer,
            "suggestions": suggestions,
            "source_info": {
                "hybrid_search": True,
                "query_type": query_type,
                "llm_weight": self.llm_weight,
                "db_weight": self.db_weight
            }
        }
    
    def _detect_query_type(self, context_query: str, original_query: str) -> str:
        """
        Detect query type:
        - timeline_incomplete: deadline query without year
        - timeline_specific: deadline query with year
        - generic_incomplete: generic query needing more details
        - generic_complete: complete generic query
        """
        context_lower = context_query.lower()
        original_lower = original_query.lower()
        
        # Timeline keywords
        timeline_keywords = [
            'deadline', 'filing date', 'due date', 'last date', 
            'when to file', 'filing deadline', 'when to submit',
            'submission date', 'reporting date', 'return date',
            'quarterly', 'annual return', 'annual report'
        ]
        
        is_timeline = any(keyword in context_lower for keyword in timeline_keywords)
        
        if is_timeline:
            # Check if year is specified
            year_pattern = r'(202[3-9]-[0-9]{2}|FY\s*202[3-9]-[0-9]{2}|202[3-9]\s*-\s*[0-9]{2})'
            has_year = bool(re.search(year_pattern, context_query, re.IGNORECASE))
            
            return "timeline_specific" if has_year else "timeline_incomplete"
        
        # Definable/conceptual queries that should be answered directly
        definable_patterns = [
            r'^what is (epr|extended producer responsibility|plastic waste|pibo|brand owner|producer|importer)',
            r'^define (epr|extended producer responsibility|plastic waste|pibo)',
            r'^explain (epr|extended producer responsibility|plastic waste)',
            r'^meaning of (epr|extended producer responsibility|plastic waste)',
            r'^epr meaning',
            r'^full form of epr'
        ]
        
        is_definable = any(re.search(pattern, original_lower) for pattern in definable_patterns)
        
        if is_definable:
            return "generic_complete"
        
        # Vague patterns that need more specificity (only for process/procedure questions)
        vague_patterns = [
            r'^what is (the\s+)?(annual|quarterly|filing|registration)\s+(deadline|process|procedure|requirement)',
            r'^how to (file|register|submit)',
            r'^tell me about (filing|registration|submission)',
            r'^(annual|quarterly|filing) (report|return|deadline)'
        ]
        
        is_vague = any(re.search(pattern, original_lower) for pattern in vague_patterns)
        
        if is_vague:
            return "generic_incomplete"
        
        return "generic_complete"
    
    def _ask_for_year_specification(self, query: str) -> str:
        """Ask user to specify the financial year for timeline queries"""
        query_lower = query.lower()
        
        # Determine query type
        if 'quarterly' in query_lower:
            subject = "quarterly filing deadlines"
        elif 'annual return' in query_lower or 'annual report' in query_lower:
            subject = "annual return filing deadline"
        elif 'registration' in query_lower:
            subject = "registration deadline"
        else:
            subject = "filing deadline"
        
        return f"""To provide accurate {subject}, please specify the financial year.

**Example:** "{query} for 2024-25"

**Available Years:** 2023-24, 2024-25, 2025-26"""
    
    def _ask_for_specificity(self, query: str) -> str:
        """Ask user for more specific details on generic queries"""
        query_lower = query.lower()
        
        if 'annual return' in query_lower or 'annual report' in query_lower:
            return """Please specify which aspect of annual return filing you'd like to know:

• **Deadline** - "What is the annual return filing deadline for 2024-25?"
• **Process** - "How to file annual return for EPR?"
• **Requirements** - "What documents are needed for annual return?"
• **Format** - "What is the format for annual return filing?"

Please provide more details."""
        
        elif 'quarterly' in query_lower:
            return """Please specify your quarterly filing question:

• **Deadlines** - "What are quarterly filing deadlines for 2024-25?"
• **Process** - "How to file quarterly returns?"
• **Requirements** - "What information is needed for quarterly filing?"

Please provide more details."""
        
        else:
            return """Please be more specific with your question.

**Examples:**
• "What is the registration deadline for 2024-25?"
• "How to calculate EPR targets?"
• "What are the categories of plastic waste?"

What specific information do you need?"""
    
    def _generate_year_suggestions(self, query: str) -> List[str]:
        """Generate year-specific suggestions for timeline queries"""
        return [
            f"{query} for 2024-25",
            f"{query} for 2025-26",
            f"{query} for 2023-24"
        ]
    
    def _generate_specificity_suggestions(self, query: str) -> List[str]:
        """Generate specific suggestions for vague queries"""
        query_lower = query.lower()
        
        if 'annual' in query_lower:
            return [
                "What is the annual return filing deadline for 2024-25?",
                "How to file annual return for EPR?",
                "What documents are needed for annual return filing?"
            ]
        elif 'quarterly' in query_lower:
            return [
                "What are quarterly filing deadlines for 2024-25?",
                "How to submit quarterly returns?",
                "What information is needed for quarterly filing?"
            ]
        else:
            return [
                "What is the EPR registration process?",
                "What are the plastic waste categories?",
                "How to calculate EPR targets?"
            ]
    
    def _handle_timeline_query(self, context_query: str, original_query: str) -> str:
        """
        Handle timeline queries:
        1. Check DB4 (Timeline DB) ONLY
        2. If DB4 has relevant info, format and return
        3. If DB4 fails, use LLM with web search
        """
        logger.info("📅 Timeline query - checking DB4 only")
        
        # Step 1: Check DB4 ONLY
        db4_result = self._search_timeline_db_only(context_query)
        db4_answer = db4_result.get("answer", "")
        
        # Calculate relevance
        relevance = self._calculate_similarity(original_query, db4_answer)
        logger.info(f"📊 DB4 relevance: {relevance:.2%}")
        
        if relevance >= 0.5 and db4_answer and len(db4_answer.strip()) > 20:
            logger.info("✅ DB4 has relevant information")
            formatted_answer = self._format_deadline_response(db4_answer, original_query)
            if formatted_answer and len(formatted_answer.strip()) > 20:
                return formatted_answer
        
        # Step 2: DB4 failed, use LLM with web search
        logger.info("⚠️ DB4 insufficient - using LLM with web search")
        llm_answer = self._get_llm_timeline_answer(context_query, original_query)
        
        return llm_answer
    
    def _handle_generic_query(self, context_query: str, original_query: str, 
                              intent_result=None, previous_suggestions: list = None) -> str:
        """
        Handle generic queries:
        1. Search ALL databases
        2. Check relevance (60% threshold)
        3. If relevant (≥60%): use DB info
        4. If not relevant (<60%): use LLM with web search directly
        """
        logger.info("📚 Generic query - checking all databases")
        
        # Step 1: Search ALL databases
        db_results = find_best_answer(context_query, intent_result, previous_suggestions)
        db_answer = db_results.get("answer", "")
        
        # Step 2: Calculate relevance
        relevance = self._calculate_similarity(original_query, db_answer)
        logger.info(f"📊 DB relevance: {relevance:.2%}")
        
        # Step 3: Decision based on 60% threshold
        if relevance >= self.relevance_threshold and db_answer and len(db_answer.strip()) > 30:
            logger.info(f"✅ High relevance ({relevance:.2%}) - using DB info")
            # Use DB answer directly with light formatting
            formatted_answer = self._format_db_answer(db_answer, original_query)
            return formatted_answer
        else:
            logger.info(f"❌ Low relevance ({relevance:.2%}) - using LLM with web search")
            # Directly use LLM with web search
            llm_answer = self._get_llm_web_answer(context_query, original_query)
            return llm_answer
    
    def _search_timeline_db_only(self, query: str) -> Dict:
        """Search ONLY DB4 (Timeline DB) for deadline queries"""
        from config import CHROMA_DB_PATH_4, COLLECTIONS
        import chromadb
        from sentence_transformers import SentenceTransformer
        
        try:
            client = chromadb.PersistentClient(path=CHROMA_DB_PATH_4)
            collection_name = COLLECTIONS[CHROMA_DB_PATH_4][0]
            collection = client.get_collection(name=collection_name)
            
            model = SentenceTransformer('all-MiniLM-L6-v2')
            query_embedding = model.encode([query]).tolist()
            
            results = collection.query(
                query_embeddings=query_embedding,
                n_results=3,  # Reduced for more precise results
                include=["documents", "metadatas"]
            )
            
            if results['documents'] and results['documents'][0]:
                best_answer = results['documents'][0][0]
                logger.info(f"📅 DB4 found: {best_answer[:80]}...")
                return {
                    "answer": best_answer,
                    "source_info": {"database": "Timeline_DB_4"}
                }
            
            return {"answer": "", "source_info": {"database": "Timeline_DB_4", "no_results": True}}
            
        except Exception as e:
            logger.error(f"❌ DB4 search failed: {e}")
            return {"answer": "", "source_info": {"error": str(e)}}
    
    def _format_deadline_response(self, db_text: str, query: str) -> str:
        """Extract and format deadline information - SHORT and SPECIFIC"""
        if not db_text or len(db_text.strip()) < 20:
            return ""
        
        clean_text = self._clean_text(db_text)
        
        # Extract financial year
        year_match = re.search(r'(202[3-9]-[0-9]{2})', query, re.IGNORECASE)
        financial_year = year_match.group(1) if year_match else None
        
        # Check if it's quarterly query
        is_quarterly = 'quarterly' in query.lower() or 'quarter' in query.lower()
        
        if is_quarterly:
            # Extract quarterly deadlines
            quarters = self._extract_quarterly_deadlines(clean_text)
            if quarters and financial_year:
                response = f"**Quarterly Deadlines for FY {financial_year}:**\n\n"
                for q, date in quarters.items():
                    response += f"• **{q}:** {date}\n"
                return response.strip()
        
        # Extract single deadline date
        date_patterns = [
            r'(?:deadline|due date|last date|filing date).*?(\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+,?\s+\d{4})',
            r'(?:before|by|till|on or before)\s+(\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+,?\s+\d{4})',
            r'(\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+,?\s+\d{4})'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, clean_text, re.IGNORECASE)
            if match:
                deadline_date = match.group(1)
                
                if financial_year:
                    return f"**Filing Deadline for FY {financial_year}:** {deadline_date}"
                else:
                    return f"**Filing Deadline:** {deadline_date}"
        
        # If no date found but text seems relevant, return concise version
        if len(clean_text) > 50 and any(word in clean_text.lower() 
                                        for word in ['deadline', 'date', 'filing', 'submit']):
            concise = clean_text[:150].strip()
            if financial_year:
                return f"**For FY {financial_year}:** {concise}"
            return concise
        
        return ""
    
    def _extract_quarterly_deadlines(self, text: str) -> Dict[str, str]:
        """Extract quarterly deadlines from text"""
        quarters = {}
        
        patterns = [
            (r'Q1.*?(\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+,?\s+\d{4})', 'Q1 (Apr-Jun)'),
            (r'Q2.*?(\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+,?\s+\d{4})', 'Q2 (Jul-Sep)'),
            (r'Q3.*?(\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+,?\s+\d{4})', 'Q3 (Oct-Dec)'),
            (r'Q4.*?(\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+,?\s+\d{4})', 'Q4 (Jan-Mar)')
        ]
        
        for pattern, label in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                quarters[label] = match.group(1)
        
        return quarters if len(quarters) > 0 else None
    
    def _format_db_answer(self, db_answer: str, query: str) -> str:
        """Format DB answer - keep it concise and specific"""
        clean = self._clean_text(db_answer)
        
        # If answer is already concise (< 200 chars), return as is
        if len(clean) < 200:
            return clean
        
        # Extract most relevant sentences (max 3)
        sentences = re.split(r'[.!?]+', clean)
        relevant_sentences = []
        
        query_words = set(re.findall(r'\w+', query.lower()))
        
        for sent in sentences[:5]:  # Check first 5 sentences
            sent = sent.strip()
            if len(sent) < 10:
                continue
            
            sent_words = set(re.findall(r'\w+', sent.lower()))
            overlap = len(query_words & sent_words)
            
            if overlap >= 2:  # At least 2 matching words
                relevant_sentences.append(sent)
            
            if len(relevant_sentences) >= 3:
                break
        
        if relevant_sentences:
            return '. '.join(relevant_sentences) + '.'
        
        # Fallback: return first 200 chars
        return clean[:200].strip() + '...'
    
    def _get_llm_timeline_answer(self, context_query: str, original_query: str) -> str:
        """Get concise timeline answer from LLM"""
        
        year_match = re.search(r'(202[3-9]-[0-9]{2})', context_query, re.IGNORECASE)
        financial_year = year_match.group(1) if year_match else None
        
        is_quarterly = 'quarterly' in original_query.lower() or 'quarter' in original_query.lower()
        
        if is_quarterly and financial_year:
            prompt = f"""Search and provide ONLY the quarterly filing deadlines for EPR Plastic for FY {financial_year}.

Format EXACTLY like this:
**Quarterly Deadlines for FY {financial_year}:**
• Q1 (Apr-Jun): [Date]
• Q2 (Jul-Sep): [Date]
• Q3 (Oct-Dec): [Date]
• Q4 (Jan-Mar): [Date]

Be CONCISE. No extra text. Just the deadlines."""
        
        elif financial_year:
            prompt = f"""Search and provide the annual return filing deadline for EPR Plastic for FY {financial_year}.

Format EXACTLY: **Filing Deadline for FY {financial_year}:** [Date]

Be SPECIFIC. One line answer only."""
        
        else:
            return "Please specify the financial year (e.g., 2024-25)"
        
        try:
            generation_config = genai.types.GenerationConfig(
                temperature=0.1,
                top_p=0.8,
                max_output_tokens=150  # Reduced for conciseness
            )
            response = self.model.generate_content(prompt, generation_config=generation_config)
            return self._clean_text(response.text.strip())
        except Exception as e:
            logger.error(f"❌ LLM failed: {e}")
            return "Unable to fetch deadline. Please check the CPCB portal."
    
    def _get_llm_web_answer(self, context_query: str, original_query: str) -> str:
        """Get concise answer from LLM with web search"""
        
        prompt = f"""You are an EPR Plastic expert. Search the web and provide a CONCISE, SPECIFIC answer.

Query: {original_query}

Requirements:
- Answer in 3-5 sentences MAX
- Be SPECIFIC and DIRECT
- No unnecessary details
- Use bullet points ONLY if listing items
- Start with the direct answer

Provide accurate, up-to-date information."""
        
        try:
            generation_config = genai.types.GenerationConfig(
                temperature=0.2,
                top_p=0.85,
                max_output_tokens=200  # Reduced for conciseness
            )
            response = self.model.generate_content(prompt, generation_config=generation_config)
            return self._clean_text(response.text.strip())
        except Exception as e:
            logger.error(f"❌ LLM failed: {e}")
            return "Unable to retrieve information. Please try rephrasing your question."
    
    def _add_conversation_context(self, query: str) -> str:
        """Add context from last 5 conversations"""
        if not self.conversation_history:
            return query
        
        query_lower = query.lower().strip()
        
        # Check for standalone year query
        year_pattern = r'^(202[3-9]-[0-9]{2})$'
        if re.match(year_pattern, query_lower):
            for prev_item in reversed(self.conversation_history[-3:]):
                prev_query = prev_item['question'].lower()
                if any(kw in prev_query for kw in ['deadline', 'filing', 'due', 'quarterly', 'annual']):
                    enhanced = f"{prev_item['question']} {query}"
                    logger.info(f"🔗 Enhanced: '{query}' -> '{enhanced}'")
                    return enhanced
        
        # Check for incomplete follow-up queries
        follow_up_patterns = [
            r'^for (202[3-9]-[0-9]{2})',
            r'^what about',
            r'^how about',
            r'^and (202[3-9]-[0-9]{2})'
        ]
        
        is_follow_up = any(re.match(pattern, query_lower) for pattern in follow_up_patterns)
        
        if is_follow_up and self.conversation_history:
            last_question = self.conversation_history[-1]['question']
            combined = f"{last_question} {query}"
            logger.info(f"🔗 Combined: '{combined}'")
            return combined
        
        return query
    
    def _update_conversation_history(self, question: str, answer: str):
        """Keep last 5 Q&A pairs"""
        self.conversation_history.append({
            "question": question,
            "answer": answer
        })
        
        if len(self.conversation_history) > 5:
            self.conversation_history = self.conversation_history[-5:]
        
        logger.info(f"💾 History: {len(self.conversation_history)} items")
    
    def _calculate_similarity(self, query: str, answer: str) -> float:
        """Calculate relevance between query and answer"""
        if not query or not answer:
            return 0.0
        
        query_words = set(re.findall(r'\w+', query.lower()))
        answer_words = set(re.findall(r'\w+', answer.lower()))
        
        # Remove stop words
        stop_words = {
            'the', 'is', 'at', 'which', 'on', 'a', 'an', 'and', 
            'or', 'but', 'in', 'with', 'to', 'for', 'of', 'as', 'by'
        }
        query_words -= stop_words
        answer_words -= stop_words
        
        if not query_words:
            return 0.0
        
        intersection = len(query_words & answer_words)
        union = len(query_words | answer_words)
        
        similarity = intersection / union if union > 0 else 0.0
        
        # Boost for key term matches
        key_terms = {
            'deadline', 'filing', 'registration', 'annual', 'quarterly',
            'report', 'epr', 'plastic', 'return', 'submit', 'date'
        }
        key_matches = len(query_words & key_terms & answer_words)
        
        if key_matches > 0:
            similarity = min(1.0, similarity + (key_matches * 0.15))
        
        return similarity
    
    def _clean_text(self, text: str) -> str:
        """Clean and format text"""
        if not text:
            return ""
        
        # HTML entities
        text = text.replace("&quot;", '"').replace("&amp;", "&")
        text = text.replace("&lt;", "<").replace("&gt;", ">")
        text = text.replace("&nbsp;", " ")
        
        # Whitespace
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s*\n+', '\n\n', text)
        
        return text.strip()

# Global instance
hybrid_search_engine = HybridSearchEngine()

def find_hybrid_answer(query: str, intent_result=None, previous_suggestions: list = None) -> Dict:
    """Main function for hybrid search"""
    return hybrid_search_engine.search(query, intent_result, previous_suggestions)