import chromadb
import google.generativeai as genai
import os
import logging
from dotenv import load_dotenv
from config import CHROMA_DB_PATH, CHROMA_DB_PATH_LANGFLOW, COLLECTIONS, COLLECTIONS_LANGFLOW

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set up Google Cloud credentials (only if available)
credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
if credentials_path:
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path

# Initialize ChromaDB clients
client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
client_langflow = chromadb.PersistentClient(path=CHROMA_DB_PATH_LANGFLOW)

# Configure Gemini - same as Langflow
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

def get_collections():
    """Get all available collections from both ChromaDB databases"""
    collections = {}
    
    # Get collections from primary database
    for collection_name in COLLECTIONS:
        try:
            collections[collection_name] = client.get_collection(name=collection_name)
            logger.info(f"✅ Loaded collection '{collection_name}' from primary DB")
        except Exception as e:
            logger.warning(f"Collection '{collection_name}' not found in primary DB: {e}")
    
    # Get collections from Langflow database
    try:
        langflow_collections = client_langflow.list_collections()
        for collection in langflow_collections:
            collection_name = collection.name
            try:
                collections[f"langflow_{collection_name}"] = client_langflow.get_collection(name=collection_name)
                logger.info(f"✅ Loaded collection '{collection_name}' from Langflow DB")
            except Exception as e:
                logger.warning(f"Could not load Langflow collection '{collection_name}': {e}")
    except Exception as e:
        logger.warning(f"Could not access Langflow database: {e}")
    
    if not collections:
        logger.error("No collections found. Run gemini_pdf_processor.py first.")
    
    return collections

def get_recircle_info(query: str) -> str:
    """Get ReCircle company information based on query"""
    query_lower = query.lower()
    
    # Service-related queries
    if any(word in query_lower for word in ["services", "offer", "provide", "what does recircle", "what can recircle"]):
        return """ReCircle offers comprehensive EPR and sustainability services:

• EPR Registration & Compliance Management
• Plastic Waste Collection & Processing
• Recycling Partnerships & Certification
• Plastic Neutrality Programs
• Sustainability Consulting
• Compliance Reporting & Documentation
• Circular Economy Solutions

We help businesses transform their waste management approach while meeting all regulatory requirements."""
    
    # Differentiation queries
    elif any(word in query_lower for word in ["different", "better", "why recircle", "advantage", "unique"]):
        return """ReCircle stands out as India's leading EPR compliance partner through:

• End-to-end EPR compliance solutions (registration to reporting)
• Pan-India waste collection and recycling network
• Technology-driven compliance tracking platform
• Expert team with deep regulatory knowledge
• Proven track record with 500+ businesses
• Transparent pricing and process
• Dedicated account management
• Real-time compliance monitoring

We don't just help you comply - we help you build sustainable, circular business practices."""
    
    # Contact queries
    elif any(word in query_lower for word in ["contact", "details", "phone", "email", "reach"]):
        return "📍 Mumbai Office: 3rd Floor, APML Tower, Vishveshwar Nagar Rd, Yashodham, Goregaon, Mumbai, Maharashtra 400063\n\n📞 Phone: 9004240004\n📧 Email: info@recircle.in"
    
    # Location queries
    elif any(word in query_lower for word in ["office", "location", "address", "mumbai", "where"]):
        return "📍 ReCircle Office: 3rd Floor, APML Tower, Vishveshwar Nagar Rd, Yashodham, Goregaon, Mumbai, Maharashtra 400063\n\nFor office visits or meetings, please call ahead: 9004240004"
    
    # Help/assistance queries
    elif any(word in query_lower for word in ["help", "assistance", "support"]) and "recircle" in query_lower:
        return """ReCircle provides comprehensive EPR compliance and waste management support:

• Complete EPR registration and regulatory compliance
• Plastic waste collection and recycling networks
• Plastic neutrality and carbon offset programs
• Compliance reporting and documentation
• Sustainable packaging consulting
• Circular economy implementation

Our team is ready to assist you with personalized solutions tailored to your business needs."""
    
    # General company queries
    elif any(word in query_lower for word in ["company", "about", "what is recircle", "tell me about"]):
        return """ReCircle is India's leading Extended Producer Responsibility (EPR) compliance and plastic waste management company. We help businesses achieve plastic neutrality through comprehensive waste collection, recycling, and compliance solutions.

Our services include EPR registration, compliance management, plastic credit programs, and sustainable packaging solutions. We partner with businesses to create circular economy solutions, helping them meet regulatory requirements while reducing their environmental impact."""
    
    else:
        return "ReCircle specializes in EPR compliance, plastic waste management, and sustainability solutions for businesses across India."

# Track previously suggested questions per session
_suggested_questions_cache = {}

def generate_related_questions(user_query: str, search_results: list = None, intent_result=None, session_id: str = None) -> list:
    """Generate dynamic contextually relevant questions using AI"""
    query_lower = user_query.lower()
    
    # Get previously suggested questions for this session
    previous_questions = _suggested_questions_cache.get(session_id, set()) if session_id else set()
    
    # Check if user is asking for help/assistance or has high priority intent
    help_keywords = ['help', 'assist', 'support', 'guidance', 'who will help', 'can you help', 'need help']
    is_help_query = any(keyword in query_lower for keyword in help_keywords)
    
    # Check intent priority if available
    is_high_priority = False
    if intent_result:
        high_priority_intents = ['contact_intent', 'sales_opportunity', 'urgent_need', 'high_interest']
        is_high_priority = (intent_result.intent in high_priority_intents and intent_result.confidence >= 0.6) or intent_result.should_connect
    
    # If help query or high priority, include ReCircle service questions (not contact)
    if is_help_query or is_high_priority:
        recircle_questions = [
            "How can ReCircle help me with EPR compliance?",
            "What services does ReCircle offer?",
            "What makes ReCircle different from other EPR service providers?",
            "Can ReCircle handle my complete EPR compliance?",
            "What is ReCircle's process for EPR registration?"
        ]
        # Filter out previously suggested questions
        recircle_questions = [q for q in recircle_questions if q not in previous_questions]
        
        # Mix ReCircle questions with relevant ones
        try:
            context_text = ""
            if search_results:
                for result in search_results[:2]:
                    context_text += result.get('document', '')[:200] + " "
            
            avoid_list = "\n".join(list(previous_questions)[:5]) if previous_questions else "None"
            
            prompt = f"""User asked: "{user_query}"

Context: {context_text[:300]}

Previously suggested (DO NOT repeat):
{avoid_list}

Generate 1 unique, specific follow-up question that:
- Is directly related to their query
- Explores a different aspect than the original question
- Is practical and actionable
- MUST be different from previously suggested questions

Format: Return ONLY the question, ending with '?'. No numbering."""
            
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(prompt, generation_config=genai.types.GenerationConfig(temperature=1.0, max_output_tokens=80))
            
            if response and response.text:
                lines = [line.strip().lstrip('0123456789.-*• ').strip() for line in response.text.strip().split('\n')]
                ai_questions = [line for line in lines if line and '?' in line and len(line) > 10 and line not in previous_questions][:1]
                result_questions = ai_questions + recircle_questions[:2]
                result_questions = result_questions[:3]  # Limit to 3
                
                # Cache the suggestions
                if session_id:
                    _suggested_questions_cache[session_id] = previous_questions.union(set(result_questions))
                
                return result_questions
        except Exception as e:
            logger.warning(f"AI question generation failed: {e}")
        
        # Fallback: return ReCircle questions
        result = recircle_questions[:3]
        if session_id:
            _suggested_questions_cache[session_id] = previous_questions.union(set(result))
        return result
    
    # Regular AI-generated questions for other queries
    try:
        context_text = ""
        if search_results:
            for result in search_results[:3]:
                context_text += result.get('document', '')[:250] + " "
        
        # Add previously asked questions to prompt to avoid repetition
        avoid_list = "\n".join(list(previous_questions)[:10]) if previous_questions else "None"
        
        prompt = f"""User asked: "{user_query}"

Context from EPR knowledge base:
{context_text[:600]}

Previously suggested questions (DO NOT repeat these):
{avoid_list}

Generate exactly 3 unique, highly relevant follow-up questions that:
1. Are DIRECTLY related to "{user_query}" topic
2. Explore different aspects (next steps, requirements, process details)
3. Are specific and actionable (avoid generic questions)
4. Each question should be distinct and non-repetitive
5. MUST be completely different from previously suggested questions

Format: Return ONLY 3 questions, one per line, each ending with '?'. No numbering, bullets, or explanations."""
        
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=1.0,
                max_output_tokens=200,
                top_p=0.95
            )
        )
        
        if response and response.text:
            lines = response.text.strip().split('\n')
            questions = []
            for line in lines:
                line = line.strip().lstrip('0123456789.-*• ').strip()
                if line and '?' in line and len(line) > 10 and line not in previous_questions:
                    questions.append(line)
            
            if len(questions) >= 2:
                logger.info(f"✅ Generated {len(questions)} unique AI questions")
                result_questions = questions[:3]
                
                # Cache the suggestions
                if session_id:
                    _suggested_questions_cache[session_id] = previous_questions.union(set(result_questions))
                
                return result_questions
        
    except Exception as e:
        logger.warning(f"AI question generation failed: {e}")
    
    return get_fallback_questions(user_query)

def get_fallback_questions(user_query: str) -> list:
    """Generate contextual fallback questions based on user query"""
    query_lower = user_query.lower()
    
    # Extract key topics from query
    if any(word in query_lower for word in ['register', 'registration', 'how to register']):
        return [
            "What documents are needed for EPR registration?",
            "How long does EPR registration take?",
            "Who can help me with EPR registration?"
        ]
    elif any(word in query_lower for word in ['penalty', 'fine', 'non-compliance', 'violation']):
        return [
            "What are EPR non-compliance penalties?",
            "How can I avoid EPR fines?",
            "How do I resolve penalty notices?"
        ]
    elif any(word in query_lower for word in ['certificate', 'credit', 'epr certificate']):
        return [
            "Where can I buy EPR certificates?",
            "What is the validity of EPR certificates?",
            "What is the cost of EPR certificates?"
        ]
    elif any(word in query_lower for word in ['target', 'obligation', 'fulfill', 'achieve']):
        return [
            "How to calculate my EPR target?",
            "Who will help me fulfill my EPR target?",
            "What happens if I don't meet EPR targets?"
        ]
    elif any(word in query_lower for word in ['deadline', 'timeline', 'when', 'date']):
        return [
            "What are the key EPR deadlines?",
            "When is the EPR annual return due?",
            "How often do I need to report under EPR?"
        ]
    elif any(word in query_lower for word in ['cost', 'price', 'fee', 'expensive']):
        return [
            "How much does EPR compliance cost?",
            "What are the EPR registration fees?",
            "How can I reduce EPR compliance costs?"
        ]
    elif any(word in query_lower for word in ['recircle', 'help', 'service provider', 'pro']):
        return [
            "What services does ReCircle offer?",
            "How can ReCircle help with EPR compliance?",
            "Can ReCircle manage my entire EPR process?"
        ]
    elif any(word in query_lower for word in ['document', 'paperwork', 'proof']):
        return [
            "What documents do I need for EPR registration?",
            "What proof is required for EPR compliance?",
            "How long should I keep EPR records?"
        ]
    else:
        # Generic relevant questions
        return [
            "What is EPR and who needs to comply?",
            "How do I get started with EPR compliance?",
            "Who can help me with EPR compliance?"
        ]

def find_best_answer(user_query: str, intent_result=None) -> dict:
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
    
    # Check for ReCircle-specific queries
    query_lower = user_query.lower()
    is_recircle_query = "recircle" in query_lower or "re-circle" in query_lower or "re circle" in query_lower
    
    # Handle all ReCircle queries (services, differentiation, contact, etc.)
    if is_recircle_query:
        recircle_info = get_recircle_info(user_query)
        # Combine with RAG answer if available and relevant
        if answer and len(answer) > 50:
            answer = f"{recircle_info}\n\n{answer}"
        else:
            answer = recircle_info
    
    # Generate suggestions (pass session_id if available from intent_result)
    session_id = getattr(intent_result, 'session_id', None) if intent_result else None
    suggestions = generate_related_questions(user_query, filtered_results, intent_result, session_id)
    
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
