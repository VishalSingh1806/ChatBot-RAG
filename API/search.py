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

# Set up Google Cloud credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

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
    
    if any(word in query_lower for word in ["office", "location", "address", "mumbai", "where"]):
        return "ReCircle Office Location:\n• Address: 3rd Floor, APML Tower, Vishveshwar Nagar Rd, Yashodham, Goregaon, Mumbai, Maharashtra 400063\n• Phone: 9004240004\n• Email: info@recircle.in\n• For office visits or meetings, please call ahead to schedule an appointment."
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
    """Generate contextually relevant questions based on user query and search results"""
    query_lower = user_query.lower()
    
    # Registration-related queries
    if any(word in query_lower for word in ["register", "registration", "documents", "apply"]):
        return [
            "What documents are needed for EPR registration?",
            "How long does EPR registration take?",
            "What is the EPR registration fee?",
            "How do I renew my EPR certificate?",
            "Can I register multiple brands under one EPR?"
        ]
    
    # Compliance-related queries
    elif any(word in query_lower for word in ["compliance", "target", "achieve", "meet"]):
        return [
            "How do I meet my EPR targets?",
            "What are EPR compliance requirements?",
            "How often do I need to report under EPR?",
            "What happens if I miss my EPR target?",
            "How are EPR targets calculated?"
        ]
    
    # Certificate-related queries
    elif any(word in query_lower for word in ["certificate", "validity", "renew"]):
        return [
            "How long is my EPR certificate valid?",
            "How do I renew my EPR certificate?",
            "What is a recycling certificate?",
            "How do I get a recycling certificate?",
            "Can I transfer my EPR certificate?"
        ]
    
    # Penalty-related queries
    elif any(word in query_lower for word in ["penalty", "fine", "non-compliance", "violation"]):
        return [
            "What are the penalties for EPR non-compliance?",
            "How can I avoid EPR penalties?",
            "What happens if I don't comply with EPR?",
            "Can I appeal against EPR penalties?",
            "How much are EPR fines?"
        ]
    
    # Recycling-related queries
    elif any(word in query_lower for word in ["recycle", "recycling", "waste", "disposal"]):
        return [
            "How is plastic waste recycled?",
            "What types of plastic can be recycled?",
            "How do I find authorized recyclers?",
            "What are recycling certificates?",
            "How do I dispose of non-recyclable plastic?"
        ]
    
    # Producer-specific queries
    elif any(word in query_lower for word in ["producer", "manufacturer", "production"]):
        return [
            "What are producer responsibilities under EPR?",
            "How do producers comply with EPR?",
            "What documents do producers need for EPR?",
            "How do producers calculate plastic usage?",
            "Can producers handle EPR compliance in-house?"
        ]
    
    # Importer-specific queries
    elif any(word in query_lower for word in ["import", "importer", "imported goods"]):
        return [
            "How do importers comply with EPR?",
            "Are imported goods covered under EPR?",
            "What are importer responsibilities under EPR?",
            "How do importers report plastic usage?",
            "Can exporters be exempt from EPR?"
        ]
    
    # Brand owner queries
    elif any(word in query_lower for word in ["brand", "brand owner", "pibo"]):
        return [
            "What are brand owner responsibilities under EPR?",
            "How do brand owners comply with EPR?",
            "Are brand owners responsible for third-party packaging?",
            "What is a PIBO under EPR?",
            "How do brand owners track packaging waste?"
        ]
    
    # ReCircle-specific queries - context-aware suggestions
    elif any(word in query_lower for word in ["recircle"]):
        if "contact" in query_lower or "reach" in query_lower:
            return [
                "What services does ReCircle offer?",
                "How can ReCircle help with EPR compliance?",
                "What is ReCircle's Plastic Neutral Program?",
                "Can ReCircle handle my entire EPR process?",
                "What are ReCircle's office locations?"
            ]
        elif "service" in query_lower or "offer" in query_lower:
            return [
                "How can ReCircle help with EPR compliance?",
                "What is ReCircle's Plastic Neutral Program?",
                "Can ReCircle handle my entire EPR process?",
                "How do I contact ReCircle?",
                "What are ReCircle's pricing options?"
            ]
        elif "plastic neutral" in query_lower:
            return [
                "How does plastic neutrality work?",
                "What are the benefits of plastic neutrality?",
                "How long does it take to achieve plastic neutrality?",
                "What documents are needed for plastic neutrality?",
                "How is plastic neutrality verified?"
            ]
        elif "handle" in query_lower or "process" in query_lower:
            return [
                "What is ReCircle's step-by-step EPR process?",
                "How long does EPR compliance take with ReCircle?",
                "What documents does ReCircle need from me?",
                "How does ReCircle track my EPR progress?",
                "What are ReCircle's success rates?"
            ]
        elif "what is" in query_lower or "about" in query_lower:
            return [
                "What services does ReCircle offer?",
                "How can ReCircle help with EPR compliance?",
                "What makes ReCircle different from competitors?",
                "How long has ReCircle been in business?",
                "What industries does ReCircle serve?"
            ]
        else:
            # Fallback for other ReCircle queries
            return [
                "What services does ReCircle offer?",
                "How can ReCircle help with EPR compliance?",
                "How do I contact ReCircle?",
                "What is ReCircle's Plastic Neutral Program?",
                "Can ReCircle handle my entire EPR process?"
            ]
    
    # Help/support queries - focus on assistance
    elif any(word in query_lower for word in ["help", "support", "assistance"]):
        return [
            "How can ReCircle help with EPR compliance?",
            "What services does ReCircle offer?",
            "How do I contact ReCircle?",
            "Can ReCircle handle my entire EPR process?",
            "What is ReCircle's emergency support?"
        ]
    
    # Plastic/category queries
    elif any(word in query_lower for word in ["plastic", "category", "c1", "c2", "c3", "c4", "c5"]):
        return [
            "What are plastic categories C1, C2, C3, C4, C5?",
            "What is rigid plastic packaging?",
            "What is flexible plastic packaging?",
            "How are plastic categories defined?",
            "Which plastic category applies to my product?"
        ]
    
    # Fee/cost queries
    elif any(word in query_lower for word in ["fee", "cost", "price", "charge", "amount"]):
        return [
            "What is the EPR registration fee?",
            "How much does EPR compliance cost?",
            "Are there annual fees for EPR?",
            "What are the penalties for non-compliance?",
            "How are EPR fees calculated?"
        ]
    
    # Timeline queries
    elif any(word in query_lower for word in ["time", "duration", "long", "when", "deadline"]):
        return [
            "How long does EPR registration take?",
            "What are EPR compliance deadlines?",
            "When do I need to submit EPR reports?",
            "How often are EPR audits conducted?",
            "What is the validity period of EPR certificate?"
        ]
    
    # Default EPR-related questions
    else:
        return [
            "What is EPR?",
            "Who needs to comply with EPR rules?",
            "How do I register for EPR?",
            "What are EPR compliance requirements?",
            "What documents are needed for EPR registration?"
        ]

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
        filtered_results = all_results[:3]  # Use top 3 results
    
    if not filtered_results:
        logger.warning("❌ No results found at all")
        return {
            "answer": "I don't have information about that topic. For personalized assistance, contact ReCircle at info@recircle.in or 9004240004.",
            "suggestions": generate_related_questions(user_query),
            "source_info": {
                "collection_name": "none",
                "chunk_id": 0,
                "source_document": "none",
                "pdf_index": 0,
                "confidence_score": 0,
                "total_results_found": len(all_results),
                "confidence_threshold": confidence_threshold,
                "threshold_met": False
            }
        }
    
    # Get best result from filtered results
    best_result = filtered_results[0]
    
    # Log the best match with detailed info
    logger.info(f"✅ Best match from '{best_result['collection']}' collection")
    logger.info(f"   📄 Source: {best_result['source']}")
    logger.info(f"   🔢 Chunk ID: {best_result['chunk_id']}")
    logger.info(f"   📊 Distance: {best_result['distance']:.4f}")
    logger.info(f"   🎯 Confidence: {round(1 - best_result['distance'], 4)}")
    
    # Combine top 3 relevant chunks for comprehensive answer
    top_chunks = filtered_results[:3]
    combined_text = ""
    
    for i, result in enumerate(top_chunks):
        doc = result['document']
        # Clean up text and add if it's quality content
        if len(doc) > 30 and doc.count('uni') < 5:
            if combined_text:
                combined_text += "\n\n"
            combined_text += doc.strip()
    
    # Check for ReCircle-specific queries
    query_lower = user_query.lower()
    if any(word in query_lower for word in ["recircle", "company", "cto", "team", "leadership"]):
        # ReCircle-specific queries
        recircle_info = get_recircle_info(user_query)
        answer = recircle_info
    else:
        # Use combined text if available, otherwise use best single result
        answer = combined_text if combined_text else filtered_results[0]['document']
        
        # Add ReCircle info for help/assistance queries or when answer is short
        if any(word in query_lower for word in ["help", "assistance", "support", "contact", "reach out"]) or len(answer) < 100:
            if not answer.endswith("."):
                answer += "."
            answer += "\n\nFor personalized assistance and expert consultation, contact ReCircle at info@recircle.in or 9004240004."
    
    # Generate contextually relevant suggestions
    suggestions = generate_related_questions(user_query, filtered_results)
    
    # Prepare source information
    source_info = {
        "collection_name": best_result['collection'],
        "chunk_id": best_result['chunk_id'],
        "source_document": best_result['source'],
        "pdf_index": best_result['pdf_index'],
        "confidence_score": round(1 - best_result['distance'], 4),  # Convert distance to confidence
        "total_results_found": len(all_results),
        "filtered_results_count": len(filtered_results),
        "confidence_threshold": confidence_threshold,
        "threshold_met": True
    }
    
    return {
        "answer": answer,
        "suggestions": suggestions,
        "source_info": source_info
    }
