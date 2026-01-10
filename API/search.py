import chromadb
import google.generativeai as genai
import os
import logging
import csv
import random
from dotenv import load_dotenv
from config import CHROMA_DB_PATHS, COLLECTIONS

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize ChromaDB clients for ALL 5 databases
clients = {}
for db_path in CHROMA_DB_PATHS:
    try:
        clients[db_path] = chromadb.PersistentClient(path=db_path)
        logger.info(f"✅ Connected to ChromaDB at {db_path}")
    except Exception as e:
        logger.error(f"❌ Failed to connect to ChromaDB at {db_path}: {e}")

# Configure Gemini
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

def get_collections():
    """Get all available collections from all 5 databases"""
    all_collections = {}
    for db_path, client in clients.items():
        for collection_name in COLLECTIONS.get(db_path, []):
            try:
                collection = client.get_collection(name=collection_name)
                all_collections[f"{collection_name}@{db_path}"] = collection
                logger.info(f"✅ Found collection '{collection_name}' with {collection.count()} documents from {db_path}")
            except Exception as e:
                logger.warning(f"Collection '{collection_name}' not found in {db_path}: {e}")

    if not all_collections:
        logger.error("No collections found. ChromaDB databases may be empty.")

    return all_collections

def get_recircle_info(query: str) -> str:
    """Get ReCircle company information based on query"""
    query_lower = query.lower()
    
    if any(word in query_lower for word in ["contact", "details", "phone", "email", "reach"]):
        contact_email = os.getenv("CONTACT_EMAIL", "info@recircle.in")
        return f"📍 Mumbai Office: 3rd Floor, APML Tower, Vishveshwar Nagar Rd, Yashodham, Goregaon, Mumbai, Maharashtra 400063\n\n📞 Phone: 9004240004\n📧 Email: {contact_email}"
    elif any(word in query_lower for word in ["office", "location", "address", "mumbai", "where"]):
        contact_email = os.getenv("CONTACT_EMAIL", "info@recircle.in")
        return f"📍 Mumbai Office: 3rd Floor, APML Tower, Vishveshwar Nagar Rd, Yashodham, Goregaon, Mumbai, Maharashtra 400063\n\n📞 Phone: 9004240004\n📧 Email: {contact_email}"
    elif any(word in query_lower for word in ["participate", "join", "benefit", "work with", "partner"]):
        contact_email = os.getenv("CONTACT_EMAIL", "info@recircle.in")
        return f"ReCircle is India's leading EPR compliance and plastic waste management company. We help businesses achieve plastic neutrality through:\n\n• Complete EPR registration and compliance management\n• Plastic waste collection and recycling solutions\n• EPR certificate procurement\n• Annual return filing and documentation\n• Customized sustainability programs\n\nTo discuss how ReCircle can help your company, contact us at:\n📞 9004240004\n📧 {contact_email}"
    elif any(word in query_lower for word in ["service", "offer", "provide", "do"]):
        contact_email = os.getenv("CONTACT_EMAIL", "info@recircle.in")
        return f"ReCircle offers comprehensive EPR compliance solutions:\n\n• EPR Registration & Licensing\n• Plastic Waste Collection & Recycling\n• EPR Certificate Management\n• Annual Return Filing\n• Compliance Monitoring & Reporting\n• Sustainability Consulting\n\nWe help businesses meet their Extended Producer Responsibility obligations efficiently and cost-effectively.\n\nContact: 9004240004 | {contact_email}"
    elif any(word in query_lower for word in ["help", "assistance", "support"]):
        contact_email = os.getenv("CONTACT_EMAIL", "info@recircle.in")
        return f"Our ReCircle team is ready to provide personalized EPR solutions tailored to your business needs.\n\nContact: 9004240004 | {contact_email}"
    elif any(word in query_lower for word in ["what is", "who is", "about", "company"]):
        contact_email = os.getenv("CONTACT_EMAIL", "info@recircle.in")
        return f"ReCircle is India's leading Extended Producer Responsibility (EPR) compliance and plastic waste management company. We help businesses achieve plastic neutrality through comprehensive waste collection, recycling, and compliance solutions.\n\nOur services include EPR registration, certificate management, waste collection infrastructure, and complete compliance support.\n\nGet in touch: 📞 9004240004 | 📧 {contact_email}"
    else:
        contact_email = os.getenv("CONTACT_EMAIL", "info@recircle.in")
        return f"ReCircle specializes in EPR compliance, plastic waste management, and sustainability solutions for businesses across India.\n\nContact us: 9004240004 | {contact_email}"

def generate_related_questions(user_query: str, search_results: list = None, intent_result=None, previous_suggestions: list = None) -> list:
    """Generate 2 dynamic questions + 1 static ReCircle contact question"""
    query_lower = user_query.lower()
    previous_suggestions = previous_suggestions or []
    
    # Static 3rd question - always about ReCircle contact
    static_contact_question = "Connect me to ReCircle"
    
    # Get 2 dynamic questions from FAQ
    dynamic_questions = []
    
    # Try FAQ questions first
    faq_questions = get_faq_questions(user_query, previous_suggestions)
    dynamic_questions.extend(faq_questions[:2])
    
    # If we don't have 2 dynamic questions, add fallback questions
    if len(dynamic_questions) < 2:
        fallback_questions = get_fallback_questions(user_query, previous_suggestions)
        # Add fallback questions that aren't already in dynamic_questions
        for q in fallback_questions:
            if q not in dynamic_questions and len(dynamic_questions) < 2:
                dynamic_questions.append(q)
    
    # Ensure we have exactly 2 dynamic questions
    if len(dynamic_questions) < 2:
        # Add default questions if still not enough
        default_questions = [
            "What is EPR and who needs to comply?",
            "How do I get started with EPR compliance?"
        ]
        for q in default_questions:
            if q not in dynamic_questions and len(dynamic_questions) < 2:
                dynamic_questions.append(q)
    
    # Return exactly 3 questions: 2 dynamic + 1 static
    return dynamic_questions[:2] + [static_contact_question]

def get_faq_questions(user_query: str, previous_suggestions: list = None) -> list:
    """Get related questions from FAQ CSV based on user query, excluding previous suggestions"""
    try:
        faq_path = os.path.join(os.path.dirname(__file__), 'data', 'epr_faqs.csv')
        if not os.path.exists(faq_path):
            logger.warning(f"FAQ file not found: {faq_path}")
            return []
        
        previous_suggestions = previous_suggestions or []
        query_lower = user_query.lower()
        query_words = set(query_lower.split())
        
        # Score each FAQ question based on keyword matches
        scored_questions = []
        
        with open(faq_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                keywords = row.get('keywords', '').lower()
                question = row.get('question', '')
                
                # Skip if question is same as user query or was previously suggested
                if question.lower().strip() == query_lower.strip():
                    continue
                if question in previous_suggestions:
                    continue
                
                # Calculate match score
                keyword_words = set(keywords.split())
                common_words = query_words.intersection(keyword_words)
                score = len(common_words)
                
                if score > 0:
                    scored_questions.append((question, score))
        
        # Sort by score (highest first) and get top 2 unique questions
        scored_questions.sort(key=lambda x: x[1], reverse=True)
        top_questions = [q[0] for q in scored_questions[:2]]
        
        if len(top_questions) >= 2:
            return top_questions
        
        # If not enough matches, add high priority questions
        with open(faq_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            high_priority = [row['question'] for row in reader 
                           if row.get('priority') == 'high' 
                           and row['question'] not in top_questions
                           and row['question'] not in previous_suggestions
                           and row['question'].lower().strip() != query_lower.strip()]
            
            needed = 2 - len(top_questions)
            return top_questions + high_priority[:needed]
    
    except Exception as e:
        logger.error(f"Error reading FAQ CSV: {e}")
        return []

def get_fallback_questions(user_query: str, previous_suggestions: list = None) -> list:
    """Generate contextual fallback questions based on user query, excluding previous suggestions"""
    previous_suggestions = previous_suggestions or []
    query_lower = user_query.lower()
    
    # Extract key topics from query
    if any(word in query_lower for word in ['register', 'registration', 'how to register']):
        questions = [
            "What documents are needed for EPR registration?",
            "How long does EPR registration take?",
            "Who can help me with EPR registration?"
        ]
        filtered = [q for q in questions if q not in previous_suggestions]
        return filtered[:3] if filtered else questions[:2]
    elif any(word in query_lower for word in ['penalty', 'fine', 'non-compliance', 'violation']):
        questions = [
            "What are EPR non-compliance penalties?",
            "How can I avoid EPR fines?",
            "How do I resolve penalty notices?"
        ]
        return [q for q in questions if q not in previous_suggestions][:3]
    elif any(word in query_lower for word in ['certificate', 'credit', 'epr certificate']):
        questions = [
            "Where can I buy EPR certificates?",
            "What is the validity of EPR certificates?",
            "What is the cost of EPR certificates?"
        ]
        return [q for q in questions if q not in previous_suggestions][:3]
    elif any(word in query_lower for word in ['target', 'obligation', 'fulfill', 'achieve']):
        questions = [
            "How to calculate my EPR target?",
            "Who will help me fulfill my EPR target?",
            "What happens if I don't meet EPR targets?"
        ]
        return [q for q in questions if q not in previous_suggestions][:3]
    elif any(word in query_lower for word in ['deadline', 'timeline', 'when', 'date']):
        questions = [
            "What are the key EPR deadlines?",
            "When is the EPR annual return due?",
            "How often do I need to report under EPR?"
        ]
        return [q for q in questions if q not in previous_suggestions][:3]
    elif any(word in query_lower for word in ['cost', 'price', 'fee', 'expensive']):
        questions = [
            "How much does EPR compliance cost?",
            "What are the EPR registration fees?",
            "How can I reduce EPR compliance costs?"
        ]
        return [q for q in questions if q not in previous_suggestions][:3]
    elif any(word in query_lower for word in ['recircle', 'help', 'service provider', 'pro']):
        questions = [
            "What services does ReCircle offer?",
            "How can ReCircle help with EPR compliance?",
            "Can ReCircle manage my entire EPR process?"
        ]
        return [q for q in questions if q not in previous_suggestions][:3]
    elif any(word in query_lower for word in ['document', 'paperwork', 'proof']):
        questions = [
            "What documents do I need for EPR registration?",
            "What proof is required for EPR compliance?",
            "How long should I keep EPR records?"
        ]
        return [q for q in questions if q not in previous_suggestions][:3]
    else:
        # Generic relevant questions
        questions = [
            "What is EPR and who needs to comply?",
            "How do I get started with EPR compliance?",
            "Who can help me with EPR compliance?"
        ]
        filtered = [q for q in questions if q not in previous_suggestions]
        return filtered[:3] if filtered else questions[:2]

def find_best_answer(user_query: str, intent_result=None, previous_suggestions: list = None) -> dict:
    logger.info(f"🔍 Searching ALL 5 DATABASES for query: {user_query[:100]}...")
    previous_suggestions = previous_suggestions or []

    collections = get_collections()
    if not collections:
        logger.warning("No collections available")
        return {
            "answer": "Database not ready. Please process PDFs first using gemini_pdf_processor.py.",
            "suggestions": [],
            "source_info": {}
        }

    # Generate query embedding using Gemini
    try:
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=user_query,
            task_type="retrieval_query"
        )
        query_embedding = result['embedding']
        logger.info(f"📊 Generated query embedding (dim: {len(query_embedding)})")
    except Exception as e:
        logger.error(f"Error generating query embedding: {e}")
        return {
            "answer": "Error processing your query. Please try again.",
            "suggestions": [],
            "source_info": {}
        }

    all_results = []

    # Query ALL collections from all 5 databases using embedding
    for collection_name, collection in collections.items():
        try:
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=10  # Get more results for better matching
            )

            if results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    metadata = results['metadatas'][0][i] if results['metadatas'] else {}
                    # Fix source fallback
                    source = metadata.get('source', 'unknown')
                    if source == 'unknown' or not source:
                        # Try to extract from collection name or use fallback
                        if 'EPR-chatbot' in collection_name:
                            source = 'EPR_Knowledge_Base'
                        elif 'EPRChatbot-1' in collection_name:
                            source = 'EPR_Regulations'
                        elif 'FinalDB' in collection_name:
                            source = 'EPR_Comprehensive_Database'
                        else:
                            source = f'{collection_name}_documents'

                    all_results.append({
                        'document': doc,
                        'distance': results['distances'][0][i] if results['distances'] else 0,
                        'collection': collection_name,
                        'metadata': metadata,
                        'chunk_id': metadata.get('chunk_id', i),
                        'source': source,
                        'pdf_index': metadata.get('pdf_index', 0)
                    })

                logger.info(f"📚 Found {len(results['documents'][0])} results from '{collection_name}' collection")
                for i, doc in enumerate(results['documents'][0]):
                    metadata = results['metadatas'][0][i] if results['metadatas'] else {}
                    distance = results['distances'][0][i] if results['distances'] else 0
                    logger.info(f"  - Chunk {metadata.get('chunk_id', i)}: distance={distance:.4f}, source={metadata.get('source', 'unknown')}")
        except Exception as e:
            logger.error(f"Error querying collection '{collection_name}': {e}")
    
    if not all_results:
        logger.warning("No results found for query")
        return {
            "answer": "I don't have information about that topic.",
            "suggestions": [],
            "source_info": {}
        }
    
    # Sort by distance (lower is better)
    all_results.sort(key=lambda x: x['distance'])
    
    # Apply very low confidence threshold for Langflow compatibility
    confidence_threshold = 0.001
    distance_threshold = 1.5  # Reduced from 5.0 for better relevance
    
    # Filter results by distance threshold
    filtered_results = [r for r in all_results if r['distance'] <= distance_threshold]
    
    # If no results with threshold, use best available results
    if not filtered_results and all_results:
        logger.warning(f"⚠️ Using best available results (distance: {all_results[0]['distance']:.4f})")
        filtered_results = all_results[:5]  # Increased from 3 to 5
    
    if not filtered_results:
        return {
            "answer": "I don't have information about that topic.",
            "suggestions": generate_related_questions(user_query),
            "source_info": {}
        }
    
    # Get best result
    best_result = filtered_results[0]
    
    # Combine top results for comprehensive answer
    combined_text = ""
    for result in filtered_results[:3]:
        doc = result['document']
        if len(doc) > 30:
            if combined_text:
                combined_text += "\n\n"
            combined_text += doc.strip()
    
    answer = combined_text if combined_text else filtered_results[0]['document']
    
    # Check for ReCircle-specific queries
    query_lower = user_query.lower()
    is_recircle_query = "recircle" in query_lower or "re-circle" in query_lower or "re circle" in query_lower
    
    if is_recircle_query:
        recircle_info = get_recircle_info(user_query)
        answer = recircle_info
    
    # Generate suggestions with exclusion of previous suggestions
    suggestions = generate_related_questions(user_query, filtered_results, intent_result, previous_suggestions)
    
    return {
        "answer": answer,
        "suggestions": suggestions,
        "source_info": {
            "collection_name": best_result['collection'],
            "chunk_id": best_result['chunk_id'],
            "source_document": best_result['source'],
            "confidence_score": round(1 - best_result['distance'], 4)
        }
    }
