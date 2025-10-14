import chromadb
import google.generativeai as genai
import os
import logging
from dotenv import load_dotenv
from config import CHROMA_DB_PATH, COLLECTIONS

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set up Google Cloud credentials (only if available)
credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
if credentials_path:
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path

# Initialize ChromaDB client
client = chromadb.PersistentClient(path=CHROMA_DB_PATH)

# Configure Gemini - same as Langflow
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

def get_collections():
    """Get all available collections"""
    collections = {}
    for collection_name in COLLECTIONS:
        try:
            collections[collection_name] = client.get_collection(name=collection_name)
        except Exception as e:
            logger.warning(f"Collection '{collection_name}' not found: {e}")
    
    if not collections:
        logger.error("No collections found. Run gemini_pdf_processor.py first.")
    
    return collections

def get_recircle_info(query: str) -> str:
    """Get ReCircle company information based on query"""
    query_lower = query.lower()
    
    if any(word in query_lower for word in ["contact", "details", "phone", "email", "reach"]):
        return "ReCircle Contact Details:\n\n• Mumbai Office: 3rd Floor, APML Tower, Vishveshwar Nagar Rd, Yashodham, Goregaon, Mumbai, Maharashtra 400063\n• Phone: 9004240004\n• Email: info@recircle.in\n\nFor personalized EPR compliance assistance and expert consultation, contact us today!"
    elif any(word in query_lower for word in ["office", "location", "address", "mumbai", "where"]):
        return "ReCircle Office Location:\n• Mumbai: 3rd Floor, APML Tower, Vishveshwar Nagar Rd, Yashodham, Goregaon, Mumbai, Maharashtra 400063\n• Phone: 9004240004\n• Email: info@recircle.in\n• For office visits or meetings, please call ahead to schedule an appointment."
    elif any(word in query_lower for word in ["cto", "chief technology officer", "technology head"]):
        return "ReCircle's Chief Technology Officer (CTO) leads our technology initiatives in EPR compliance and waste management solutions. For technical partnerships or technology-related inquiries, contact us at info@recircle.in or 9004240004."
    elif any(word in query_lower for word in ["founder", "ceo", "leadership", "team"]):
        return "ReCircle is led by experienced professionals in sustainability and waste management. Our leadership team drives innovation in EPR compliance and circular economy solutions. Contact info@recircle.in for leadership inquiries."
    elif any(word in query_lower for word in ["help", "assistance", "support"]) and "recircle" in query_lower:
        return "ReCircle provides comprehensive EPR compliance and waste management support. Our team, including our CTO for technical matters, is ready to assist you. Contact us at info@recircle.in or 9004240004 for personalized assistance."
    elif any(word in query_lower for word in ["company", "about", "recircle"]):
        return "ReCircle is India's leading Extended Producer Responsibility (EPR) compliance and plastic waste management company. We help businesses achieve plastic neutrality through comprehensive waste collection, recycling, and compliance solutions."
    else:
        return "ReCircle specializes in EPR compliance, plastic waste management, and sustainability solutions for businesses across India."

def generate_related_questions(user_query: str, search_results: list = None) -> list:
    """Generate 3 highly relevant questions based on user query"""
    query_lower = user_query.lower()
    
    # Generate questions based on specific query patterns with more variety
    if "what is epr" in query_lower:
        return ["Who needs to comply with EPR rules?", "How much does EPR registration cost?", "What are the EPR compliance deadlines?"]
    
    elif "producer" in query_lower and ("help" in query_lower or "waste" in query_lower or "dispose" in query_lower):
        return ["What is the EPR registration process for producers?", "How much are EPR compliance costs?", "What happens if I don't comply with EPR?"]
    
    elif "producer responsibilities" in query_lower or "producer responsibility" in query_lower:
        return ["How much does producer EPR registration cost?", "What are the penalties for non-compliance?", "How can ReCircle help with EPR compliance?"]
    
    elif "how do producers register" in query_lower or "producer register" in query_lower:
        return ["What documents do I need for EPR registration?", "How long does the EPR registration process take?", "Can ReCircle help me with EPR registration?"]
    
    elif "registration" in query_lower or "register" in query_lower:
        return ["What documents are required for EPR registration?", "How much does EPR registration cost?", "How can ReCircle assist with registration?"]
    
    elif "penalty" in query_lower or "fine" in query_lower:
        return ["How much are EPR violation penalties?", "How can I avoid EPR fines?", "What are the consequences of non-compliance?"]
    
    elif "certificate" in query_lower:
        return ["How do I obtain EPR certificates?", "What is the validity period of EPR certificates?", "How do I renew my EPR certificates?"]
    
    elif "importer" in query_lower:
        return ["What are importer EPR obligations?", "How do importers register for EPR?", "What documents do importers need for EPR?"]
    
    elif "credit" in query_lower or "calculate" in query_lower:
        return ["How are EPR credits calculated?", "Where can I purchase EPR credits?", "What factors determine EPR credit pricing?"]
    
    elif "recircle" in query_lower:
        return ["What EPR services does ReCircle provide?", "How can ReCircle help with compliance?", "What are ReCircle's contact details?"]
    
    # Default varied questions
    else:
        return ["What are the key EPR compliance requirements?", "How much does EPR registration typically cost?", "How can ReCircle help with my EPR needs?"]

def find_best_answer(user_query: str) -> dict:
    logger.info(f"🔍 Searching for query: {user_query[:100]}...")
    
    collections = get_collections()
    if not collections:
        logger.warning("No collections available")
        return {
            "answer": "Database not ready. Please process PDFs first using gemini_pdf_processor.py.",
            "suggestions": [],
            "source_info": {}
        }
    
    # Generate query embedding using Gemini text-embedding-004 (same as Langflow)
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
    
    # Query all collections using embedding
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
                        if collection_name == 'EPR-chatbot':
                            source = 'EPR_Knowledge_Base'
                        elif collection_name == 'producer':
                            source = 'Producer_Guidelines'
                        elif collection_name == 'importer':
                            source = 'Importer_Rules'
                        elif collection_name == 'branc_owner':
                            source = 'Brand_Owner_Manual'
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
    distance_threshold = 5.0  # Increased for better coverage
    
    # Filter results by confidence threshold
    filtered_results = [r for r in all_results if r['distance'] <= distance_threshold]
    
    # If no results with threshold, use best available results
    if not filtered_results and all_results:
        logger.warning(f"⚠️ Using best available results (distance: {all_results[0]['distance']:.4f})")
        filtered_results = all_results[:3]
    
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
    
    # Check for ReCircle-specific queries only
    query_lower = user_query.lower()
    if any(word in query_lower for word in ["recircle", "contact details", "contact"]):
        recircle_info = get_recircle_info(user_query)
        answer = recircle_info
    
    # Generate suggestions
    suggestions = generate_related_questions(user_query, filtered_results)
    
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
