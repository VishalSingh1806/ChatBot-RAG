import logging
import csv
import os
from typing import Dict, List

logger = logging.getLogger(__name__)

# EPR Knowledge Base - Direct answers
EPR_KNOWLEDGE = {
    "annual report filing": {
        "answer": "The annual return for EPR compliance must be filed by 31st May each year for the previous financial year (April to March). Late filing attracts penalties.",
        "keywords": ["annual", "return", "filing", "date", "deadline", "may", "31st"]
    },
    "epr registration": {
        "answer": "EPR registration is mandatory for producers, importers, and brand owners dealing with plastic packaging. Registration must be done on the CPCB portal with required documents and fees.",
        "keywords": ["registration", "register", "how to", "mandatory", "cpcb", "portal"]
    },
    "epr penalties": {
        "answer": "EPR non-compliance penalties include fines up to ₹25 lakh, closure of operations, and legal action. Penalties vary based on violation severity and company size.",
        "keywords": ["penalty", "fine", "non-compliance", "violation", "punishment"]
    },
    "epr certificates": {
        "answer": "EPR certificates are proof of plastic waste collection and recycling. They can be purchased from authorized recyclers or PROs. Validity is typically 1 year.",
        "keywords": ["certificate", "credit", "buy", "purchase", "validity", "recycler"]
    },
    "epr targets": {
        "answer": "EPR targets are based on plastic packaging quantity. For 2023-24: 60% collection target. Targets increase annually reaching 100% by 2027-28.",
        "keywords": ["target", "obligation", "percentage", "collection", "2023", "2024"]
    },
    "recircle services": {
        "answer": "ReCircle offers complete EPR compliance solutions: registration, certificate procurement, waste collection, annual returns, and compliance monitoring. Contact: 9004240004",
        "keywords": ["recircle", "service", "help", "offer", "solution", "contact"]
    }
}

def find_best_answer(user_query: str, intent_result=None, previous_suggestions: list = None) -> dict:
    """Direct knowledge base search without ChromaDB"""
    logger.info(f"🔍 Direct search for: {user_query[:100]}...")
    
    query_lower = user_query.lower()
    best_match = None
    best_score = 0
    
    # Simple keyword matching
    for topic, data in EPR_KNOWLEDGE.items():
        score = 0
        for keyword in data["keywords"]:
            if keyword in query_lower:
                score += 1
        
        if score > best_score:
            best_score = score
            best_match = data
    
    # Default answer if no match
    if not best_match or best_score == 0:
        best_match = {
            "answer": "I can help you with EPR compliance questions. Please ask about registration, annual returns, penalties, certificates, or targets."
        }
    
    # Generate suggestions
    suggestions = generate_suggestions(user_query, previous_suggestions or [])
    
    return {
        "answer": best_match["answer"],
        "suggestions": suggestions,
        "source_info": {"source": "EPR_Knowledge_Base", "confidence": best_score}
    }

def generate_suggestions(user_query: str, previous_suggestions: list) -> list:
    """Generate relevant follow-up questions"""
    base_suggestions = [
        "What is the EPR annual return filing deadline?",
        "How do I register for EPR compliance?",
        "What are EPR non-compliance penalties?",
        "Where can I buy EPR certificates?",
        "How to calculate EPR targets?",
        "What services does ReCircle offer?"
    ]
    
    # Filter out previous suggestions and current query
    query_lower = user_query.lower()
    filtered = [s for s in base_suggestions 
               if s not in previous_suggestions 
               and not any(word in s.lower() for word in query_lower.split()[:3])]
    
    # Always add ReCircle contact as 3rd option
    result = filtered[:2] + ["Connect me to ReCircle"]
    return result[:3]