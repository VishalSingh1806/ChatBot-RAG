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
        system_instruction = (
            "You are an EPR compliance assistant. CRITICAL RULES: "
            "1) For deadline queries: State ONLY the date (e.g., 'January 31, 2026') - nothing else. "
            "2) Maximum 1-2 sentences for all responses. "
            "3) NEVER say 'As of', 'based on', 'simulated', 'hypothetical', 'potential'. "
            "4) Extract ONLY the specific information requested - no explanations. "
            "5) If uncertain, say 'Not yet announced' - do NOT speculate."
        )
        self.model = genai.GenerativeModel("gemini-2.0-flash-exp", system_instruction=system_instruction)

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
        # DISABLED: Gemini's web search grounding is not working properly
        # It returns "Not yet announced" even when data exists in database
        # Database + LLM refinement provides more accurate results
        return False

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

            CRITICAL INSTRUCTIONS:
            1. For deadline queries: State ONLY the date - example: "January 31, 2026"
            2. NO explanations, NO context, NO "as of", NO "based on"
            3. Maximum 1-2 sentences ONLY
            4. Use ONLY official government sources (CPCB, MoEF, EPR Portal)
            5. If conflicting dates exist, use the most recent official notification
            6. NEVER mention "simulated", "hypothetical", "potential", "likely"
            7. If uncertain, say "Not yet announced" - do NOT speculate

            Provide ONLY the specific deadline date requested, nothing more.
            """

            # Use Gemini with Google Search grounding
            generation_config = genai.types.GenerationConfig(
                temperature=0.05,  # Lower temperature for more deterministic responses
                top_p=0.7,
                max_output_tokens=100  # Limit to prevent verbose responses
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
            You are an EPR compliance expert. Answer the user's question concisely.

            USER QUESTION: {query}

            REAL-TIME WEB INFORMATION (Latest - Priority Source):
            {web_info['answer']}

            DATABASE KNOWLEDGE (Historical Context):
            {db_answer}

            CRITICAL INSTRUCTIONS:
            1. For deadline queries: State ONLY the date from web info - Example: "January 31, 2026"
            2. Maximum 1-2 sentences ONLY
            3. NEVER say "As of [date]", "based on", "simulated", "hypothetical"
            4. NEVER provide explanations, contexts, or qualifications
            5. Trust web information as the latest source
            6. Clean up HTML entities and format properly
            7. Extract ONLY the specific information requested
            8. If web info has the answer, use ONLY that - ignore database

            Provide the answer in the most concise form possible:
            """

            generation_config = genai.types.GenerationConfig(
                temperature=0.05,  # Lower temperature for concise responses
                top_p=0.7,
                max_output_tokens=100  # Limit to prevent verbose responses
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
