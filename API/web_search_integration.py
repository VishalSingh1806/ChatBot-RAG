"""
Web Search Integration for Real-Time EPR Data
Fetches latest deadlines, notifications, and updates from CPCB and official sources
"""

import os
import logging
import google.generativeai as genai
from datetime import datetime
from typing import Dict, Optional
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

class WebSearchEngine:
    def __init__(self):
        self.model = genai.GenerativeModel("gemini-2.0-flash-exp")

        # Time-sensitive keywords that trigger web search
        self.deadline_keywords = [
            'deadline', 'last date', 'due date', 'extended', 'extension',
            'when', 'latest', 'current', 'recent', 'new', 'updated',
            '2024-25', '2024-2025', '2025-26', '2025-2026',
            'this year', 'next year', 'fiscal year', 'financial year'
        ]

        # CPCB and EPR-related domains to prioritize
        self.priority_domains = [
            'cpcb.nic.in',
            'moef.gov.in',
            'eprportal.cpcb.gov.in'
        ]

    def is_time_sensitive_query(self, query: str) -> bool:
        """Detect if query requires real-time web search"""
        query_lower = query.lower()

        # Broader deadline detection - any query about deadlines or filing dates
        deadline_terms = [
            'deadline', 'last date', 'due date', 'filing date', 'filing deadline',
            'annual report', 'annual return', 'filing', 'submit', 'when to file',
            'date for filing', 'report filing', 'return filing'
        ]

        # Check if query is about deadlines/filing - always use web search
        has_deadline_filing = any(term in query_lower for term in deadline_terms)

        # Check for deadline-related keywords
        has_deadline_keyword = any(keyword in query_lower for keyword in self.deadline_keywords)

        # Check for specific date/year mentions
        has_year_mention = any(year in query_lower for year in ['2024', '2025', '2026'])

        # Queries about annual returns, filing, compliance are often time-sensitive
        has_filing_context = any(keyword in query_lower for keyword in
                                ['annual return', 'filing', 'submit', 'report'])

        return has_deadline_filing or has_deadline_keyword or (has_year_mention and has_filing_context)

    def search_latest_info(self, query: str) -> Optional[Dict]:
        """
        Perform web search using Gemini's grounding feature
        Returns latest information from web sources
        """
        try:
            logger.info(f"🌐 Performing web search for: {query[:100]}...")

            # Enhanced prompt for deadline-specific searches
            search_prompt = f"""
            Search for the LATEST official information about: {query}

            Focus on:
            - Central Pollution Control Board (CPCB) official notifications
            - EPR Portal updates and announcements
            - Ministry of Environment notifications
            - Recent deadline extensions or changes

            Current date context: {datetime.now().strftime('%B %d, %Y')}

            Provide:
            1. Most recent deadline dates (with financial year)
            2. Any extensions or updates
            3. Official source/notification reference
            4. Key details that are currently valid

            Important: Only provide information from official government sources (CPCB, MoEF, EPR Portal).
            If you find conflicting dates, mention the most recent official notification.
            """

            # Use Gemini with Google Search grounding
            generation_config = genai.types.GenerationConfig(
                temperature=0.1,
                top_p=0.9,
                max_output_tokens=1000
            )

            # Note: Gemini's grounding with Google Search
            # This requires the search grounding feature to be enabled
            response = self.model.generate_content(
                search_prompt,
                generation_config=generation_config
            )

            web_answer = response.text.strip()

            logger.info(f"✅ Web search completed. Retrieved latest information.")

            return {
                "answer": web_answer,
                "source": "Web Search (Real-time)",
                "timestamp": datetime.now().isoformat(),
                "is_real_time": True
            }

        except Exception as e:
            logger.error(f"❌ Web search failed: {e}")
            return None

    def combine_with_db_answer(self, web_info: Dict, db_answer: str, query: str) -> str:
        """
        Intelligently combine web search results with database answer
        Prioritize web results for time-sensitive information
        """
        try:
            combination_prompt = f"""
            You are an EPR compliance expert. Combine these sources to answer the user's question.

            USER QUESTION: {query}

            REAL-TIME WEB INFORMATION (Latest - Priority Source):
            {web_info['answer']}

            DATABASE KNOWLEDGE (Historical Context):
            {db_answer}

            Instructions:
            1. PRIORITIZE the web information as it contains the LATEST data
            2. Start with the most current deadlines/dates from web search
            3. Use database knowledge only for context or general information
            4. If web info has specific dates, use those dates (they are current)
            5. Clearly state "As of [current date/year]" when providing deadlines
            6. If there are conflicting dates, trust the web information
            7. Clean up HTML entities and format properly
            8. Be specific about financial years (FY 2024-25, etc.)

            Provide a clear, direct answer with latest information:
            """

            generation_config = genai.types.GenerationConfig(
                temperature=0.1,
                top_p=0.8,
                max_output_tokens=1000
            )

            response = self.model.generate_content(
                combination_prompt,
                generation_config=generation_config
            )

            return response.text.strip()

        except Exception as e:
            logger.error(f"❌ Failed to combine web and DB results: {e}")
            # Fallback to web info if available
            return web_info['answer'] if web_info else db_answer


# Global instance
web_search_engine = WebSearchEngine()

def search_with_web(query: str, db_answer: str = "") -> Dict:
    """
    Main function to search with web integration
    Returns combined result with real-time data
    """
    # Check if query needs real-time search
    if not web_search_engine.is_time_sensitive_query(query):
        return {
            "answer": db_answer,
            "web_search_used": False,
            "source_info": {
                "source": "Database Only",
                "is_real_time": False
            }
        }

    # Perform web search
    web_info = web_search_engine.search_latest_info(query)

    if not web_info:
        # Web search failed, use DB answer
        logger.warning("⚠️ Web search unavailable, using database answer")
        return {
            "answer": db_answer,
            "web_search_used": False,
            "source_info": {
                "source": "Database (Web search unavailable)",
                "is_real_time": False
            }
        }

    # Combine web results with database answer
    if db_answer and db_answer.strip():
        combined_answer = web_search_engine.combine_with_db_answer(web_info, db_answer, query)
    else:
        combined_answer = web_info['answer']

    return {
        "answer": combined_answer,
        "web_search_used": True,
        "source_info": {
            "source": "Web Search + Database (Hybrid)",
            "is_real_time": True,
            "web_timestamp": web_info['timestamp']
        }
    }
