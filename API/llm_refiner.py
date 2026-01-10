import google.generativeai as genai
from typing import List, Dict, Optional, Tuple
import os
import logging
from dotenv import load_dotenv
from intent_detector import IntentDetector, IntentResult
from context_manager import context_manager
from proactive_engagement import proactive_engagement
from lead_qualification import lead_qualification
from contextwindow import context_window

# Setup logging
logger = logging.getLogger(__name__)

load_dotenv()

phone_number = "9004240004"
email = os.getenv("CONTACT_EMAIL", "info@recircle.in")

# Configure Gemini with API key
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

model = "gemini-2.0-flash-exp"

bot_name = "ReBot"
intent_detector = IntentDetector()
def refine_with_gemini(
    user_name: Optional[str],
    query: str,
    raw_answer: str,
    history: List[Dict[str, str]],
    is_first_message: bool = False,
    session_id: str = None,
    source_info: Dict = None,
) -> Tuple[str, IntentResult, Dict]:
    
    # Add current query to context window
    if session_id:
        context_window.add_query(session_id, query)
    # Log query processing
    logger.info(f"🤖 Processing query for session {session_id}: {query[:100]}...")
    if source_info:
        logger.info(f"📚 Using source: {source_info['collection_name']} collection, chunk {source_info['chunk_id']}, confidence: {source_info.get('confidence_score', 'N/A')}")
    
    # Analyze user intent
    intent_result = intent_detector.analyze_intent(query, history)
    
    # Extract user context
    user_context = context_manager.extract_context(query, history)
    
    # Track user journey for proactive engagement
    if session_id:
        proactive_engagement.track_user_journey(session_id, query, intent_result.intent)
    
    # Get context from context window instead of history
    context_str = ""
    if session_id:
        context_str = context_window.get_context_string(session_id)
    else:
        # Fallback to history if no session_id
        for message in history:
            role = "User" if message.get("role") == "user" else "Assistant"
            context_str += f'{role}: {message.get("text", "")}\n'

    # Greeting prefix if it's the first message and we have a name
    greeting_prefix = f"Start your answer with: 'Hi {user_name},'\n" if is_first_message and user_name else ""
    
    # Context-aware instructions
    context_instructions = ""
    if user_context.get('urgency') in ['critical', 'high']:
        context_instructions += "IMPORTANT: This user has urgent requirements. Prioritize immediate assistance and callback offers.\n"
    if user_context.get('industry'):
        context_instructions += f"NOTE: User is from {user_context['industry']} industry. Tailor response accordingly.\n"
    
    # Check lead priority and help queries for ReCircle promotion
    lead_priority = user_context.get('priority', 'low')
    is_help_query = any(word in query.lower() for word in ['help', 'who will help', 'who can help', 'assist', 'support', 'consultant', 'contact', 'approach', 'service provider', 'expert'])
    
    # For timeline date queries, check raw_answer BEFORE LLM processing
    query_lower = query.lower()
    is_date_query = any(word in query_lower for word in ['deadline', 'when', 'date', 'timeline', 'due date', 'last date'])
    is_timeline_query = any(year in query_lower for year in ['2024-25', '2024-2025', '2025-26', '2025-2026', 'fy 2024', 'fy 2025', 'fy2024', 'fy2025'])
    
    if lead_priority in ['medium', 'high'] or is_help_query:
        context_instructions += "SPECIAL: This is a priority lead or help request. Promote ReCircle as THE solution provider. Replace generic options with ReCircle-focused answers. Instead of listing multiple options, focus on how ReCircle handles all EPR requirements.\n"
    
    if is_timeline_query and is_date_query:
        context_instructions += "CRITICAL: This is a timeline/date query. Extract ONLY the date/deadline. NO explanations, NO context, NO additional information. Just the date.\n"

    # Check if valid database match was found
    valid_match = source_info.get('valid_match', True) if source_info else True
    is_timeline_llm_mode = source_info.get('is_timeline_query', False) if source_info else False
    
    # If no valid match in database, use LLM-only mode
    if not valid_match or not raw_answer or raw_answer.strip() == "":
        if is_timeline_llm_mode:
            logger.info("🤖 Timeline query: No UDB match - using LLM for most updated date")
            prompt_text = (
                f'You are {bot_name}, ReCircle\'s EPR compliance assistant.\n'
                f'USER QUESTION: {query}\n\n'
                'INSTRUCTIONS:\n'
                '1. Answer using your MOST UPDATED EPR knowledge\n'
                '2. For date queries: Provide the LATEST deadline you know\n'
                '3. Be concise - state ONLY the date\n'
                '4. If uncertain, say "Not yet announced"\n'
                f'5. For help: Contact ReCircle ({phone_number} | {email})\n'
            )
        else:
            logger.info("🤖 No valid database match - switching to LLM-only mode")
            prompt_text = (
                f'You are {bot_name}, ReCircle\'s EPR compliance assistant.\n'
                f'USER QUESTION: {query}\n\n'
                'INSTRUCTIONS:\n'
                '1. Answer using your EPR knowledge ONLY\n'
                '2. Be concise (50-60 words max)\n'
                '3. If you don\'t know, say "I don\'t have information about that"\n'
                '4. NEVER fabricate dates or deadlines\n'
                f'5. For help queries, mention: Contact ReCircle ({phone_number} | {email})\n'
            )
    else:
        # Normal mode with database context
        prompt_text = (
            f'You are {bot_name}, an EPR compliance assistant for ReCircle.\n'
            'Provide clear, professional, and CONCISE answers using the information provided.\n\n'
            f'{greeting_prefix}'
            '## CONVERSATION CONTEXT:\n'
            f'{context_str}\n\n'
            '## CURRENT USER QUESTION:\n'
            f'{query}\n\n'
            '## INFORMATION FROM DATABASE:\n'
            f'{raw_answer}\n\n'
            '## CRITICAL INSTRUCTIONS:\n'
            '1. ANSWER ONLY WHAT IS ASKED - Extract ONLY the specific information requested\n'
            '2. For date/deadline queries: State ONLY the date, nothing else\n'
            '3. If DATABASE has the answer: Use it. If DATABASE is empty/unclear: Use your EPR knowledge to answer.\n'
            '4. NEVER say "I cannot find" or "not in database" - always provide an answer using your knowledge\n'
            '5. MAXIMUM LENGTH: 50-60 words for definitions, 100 words MAX for complex topics\n'
            '6. For category questions: List ONLY the 4 categories with brief descriptions, nothing else\n'
            '7. CRITICAL: Use \n for line breaks, \n\n before list, \n between items\n'
            '8. NEVER write lists in paragraph form or repeat the same information twice\n'
            '9. Remove ALL document references, page numbers, notification numbers\n'
            '10. NEVER mention "simulated", "hypothetical", "as of [date]", "based on search results"\n'
            f'11. For help queries, start with "Contact ReCircle" ({phone_number} | {email})\n'
            '12. NEVER suggest other companies or service providers\n'
            '13. If user has typo (like "c1 platxic" for "c1 plastic"), understand and answer correctly\n'
            f'{context_instructions}'
        )
#     prompt_text = (
#     f'You are {bot_name}, a friendly and helpful AI assistant for ReCircle specializing in EPR (Extended Producer Responsibility) and plastic waste management.\n'
#     'Your expertise covers four key areas based on our knowledge base collections:\n'
#     '• PRODUCER guidance: Manufacturing, production processes, MSME producers\n'
#     '• IMPORTER regulations: Import rules, customs, foreign trade compliance\n'
#     '• BRAND OWNER responsibilities: Brand management, trademark holders, PIBOs\n'
#     '• GENERAL EPR: Rules, regulations, compliance for all stakeholders\n\n'
#     f'{greeting_prefix}'
#     '## CONVERSATION HISTORY (for context):\n'
#     f'{history_str}\n'
#     '## CURRENT USER QUESTION:\n'
#     f'{query}\n\n'
#     '## KNOWLEDGE BASE INFORMATION (This is your primary source of truth from our specialized collections):\n'
#     f'---\n{raw_answer}\n---\n\n'
#     '## RESPONSE GUIDELINES:\n'
#     '1. Base your answer STRICTLY on the KNOWLEDGE BASE INFORMATION provided above.\n'
#     '2. Use CONVERSATION HISTORY to understand context and provide personalized responses.\n'
#     '3. Identify which EPR category the question relates to (Producer/Importer/Brand Owner/General) and tailor your expertise accordingly.\n'
#     '4. Keep responses concise, actionable, and professional. Avoid repeating the user\'s name after initial greeting.\n'
#     f'5. For contact requests, provide: Phone ({phone_number}) or Email ({email}). Never invent contact details.\n'
#     '6. SCOPE: Only answer EPR, plastic waste management, or ReCircle questions. For off-topic queries, politely redirect to relevant topics.\n'
#     f'7. IDENTITY: If asked who you are, respond: "I\'m {bot_name}, your EPR compliance assistant from ReCircle."\n'
#     '8. COMPLIANCE FOCUS: Emphasize regulatory compliance, deadlines, and actionable steps when relevant.\n'
#     '9. If information is insufficient, acknowledge limitations and suggest contacting our specialists.\n'
#     f'{context_instructions}'
# )


    # Create Gemini model instance with system instruction
    system_instruction = (
        f"You are {bot_name}, ReCircle's EPR compliance assistant. "
        "CRITICAL RULES: "
        "1) For date/deadline queries: State ONLY the date. Example: 'June 30, 2026' - nothing else. "
        "2) Extract ONLY the specific information asked - NO redundant repetition. "
        "3) Answer in 50-60 words MAX. For category questions, list ONLY the 4 categories once. "
        "4) NEVER repeat the same information in different formats. "
        "5) Use \n for line breaks between numbered items. "
        "6) Remove ALL notification numbers, dates from explanations, document references."
    )
    gemini_model = genai.GenerativeModel(model, system_instruction=system_instruction)
    
    # Configure generation settings - even lower tokens for date queries
    max_tokens = 30 if (is_timeline_query and is_date_query) else 150
    generation_config = genai.types.GenerationConfig(
        temperature=0.05,
        top_p=0.7,
        max_output_tokens=max_tokens
    )
    
    # Configure safety settings
    safety_settings = [
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    ]

    result = ""
    try:
        response = gemini_model.generate_content(
            prompt_text,
            generation_config=generation_config,
            safety_settings=safety_settings,
            stream=True
        )
        
        for chunk in response:
            if chunk.text:
                result += chunk.text
    except Exception as e:
        logger.error(f"Error generating content with Gemini: {e}")
        # Fallback to non-streaming if streaming fails
        try:
            response = gemini_model.generate_content(
                prompt_text,
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            result = response.text
        except Exception as e2:
            logger.error(f"Fallback generation also failed: {e2}")
            result = "I apologize, but I'm having trouble generating a response right now. Please try again."

    refined_answer = result.strip()
    
    # No post-processing - all answers come from database + LLM refinement
    
    # Update context window with bot response
    if session_id:
        context_window.update_response(session_id, refined_answer)
    
    # Log response generation
    logger.info(f"✅ Generated response for session {session_id}, length: {len(refined_answer)} chars")
    if source_info and source_info.get('threshold_met', False):
        logger.info(f"🔍 Query satisfied with high confidence from {source_info['collection_name']} collection")
    elif source_info:
        logger.info(f"⚠️ Query answered with low confidence - may need specialist assistance")
    
    # Get lead priority from Redis directly for context
    if session_id:
        try:
            from collect_data import redis_client
            if redis_client:
                lead_key = f"lead:{session_id}"
                lead_data = redis_client.hgetall(lead_key)
                if lead_data:
                    user_context['priority'] = lead_data.get('priority', 'low')
        except:
            pass
    
    # Personalize response based on context (DISABLED - skip for all queries)
    # if not (is_simple_date_query and is_timeline_query):
    #     refined_answer = context_manager.personalize_response(refined_answer, user_context, query, user_name)
    
    # Add qualification question if appropriate (DISABLED - skip for all queries)
    # if not (is_simple_date_query and is_timeline_query):
    #     message_count = len([msg for msg in history if msg.get('role') == 'user']) + 1
    #     engagement_score = intent_detector._calculate_engagement_score(query.lower(), history)
    #     
    #     if lead_qualification.should_ask_qualification_question(message_count, engagement_score, user_context):
    #         qual_question = lead_qualification.get_next_qualification_question(user_context, history)
    #         if qual_question:
    #             refined_answer += f"\n\n{qual_question}"
    
    # Remove duplicate CTO info - it will be added in connection message if needed
    # query_lower = query.lower()
    # if any(word in query_lower for word in ["help", "assistance", "support", "contact"]) and "recircle" in query_lower:
    #     cto_info = "\n\n🔧 **Technical Support**: For advanced technical queries or partnerships, you can reach out to our CTO who leads our technology initiatives in EPR compliance and waste management solutions."
    #     refined_answer += cto_info
    
    # Modify response if connection should be suggested (DISABLED - skip for all queries)
    # is_company_query = any(word in query.lower() for word in ['what is recircle', 'about recircle', 'recircle company', 'recircle different'])
    # 
    # if intent_result.should_connect and not is_company_query and not (is_simple_date_query and is_timeline_query):
    #     connection_message = intent_detector.get_connection_message(intent_result.intent, user_name)
    #     
    #     # Add urgency-specific messaging
    #     urgency_message = ""
    #     if user_context.get('urgency') == 'critical':
    #         urgency_message = "\n⚡ **Emergency Support**: Given the critical timeline, I can arrange an immediate callback within 30 minutes."
    #     elif user_context.get('urgency') == 'high':
    #         urgency_message = "\n🚀 **Priority Support**: We can fast-track your requirements and connect you with our specialists today."
    #     
    #     refined_answer = f"{refined_answer}\n\n---\n\n{connection_message}{urgency_message}\n\n📞 Call us: {phone_number}\n📧 Email: {email}"
    
    # Add source information to user context
    if source_info:
        user_context['source_info'] = source_info
        threshold_status = "✅ PASSED" if source_info.get('threshold_met', False) else "❌ FAILED"
        logger.info(f"📊 Response sourced from: {source_info['collection_name']} collection")
        logger.info(f"   🔢 Chunk: {source_info['chunk_id']}, Confidence: {source_info['confidence_score']}, Threshold: {threshold_status}")
    
    return refined_answer, intent_result, user_context
