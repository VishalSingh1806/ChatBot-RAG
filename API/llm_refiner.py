from google import genai
from google.genai import types
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
email = "info@recircle.in"

# Initialize Gemini client
client = genai.Client(
    vertexai=True,
    project=os.getenv("GOOGLE_PROJECT_ID", "epr-chatbot-443706"),
    location=os.getenv("GOOGLE_LOCATION", "global"),
)

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
    is_help_query = any(word in query.lower() for word in ['help', 'who will help', 'who can help', 'assist', 'support'])
    
    if lead_priority in ['medium', 'high'] or is_help_query:
        context_instructions += "SPECIAL: This is a priority lead or help request. Promote ReCircle as THE solution provider. Replace generic options with ReCircle-focused answers. Instead of listing multiple options, focus on how ReCircle handles all EPR requirements.\n"

    prompt_text = (
        f'You are {bot_name}, an EPR assistant for ReCircle.\n'
        'Answer questions directly without assumptions about the user.\n\n'
        f'{greeting_prefix}'
        '## CONVERSATION CONTEXT:\n'
        f'{context_str}\n\n'
        '## CURRENT USER QUESTION:\n'
        f'{query}\n\n'
        '## INFORMATION:\n'
        f'{raw_answer}\n\n'
        '## GUIDELINES:\n'
        '1. Answer the question directly without generic prefixes\n'
        '2. For "What is EPR" questions, start with: "EPR stands for Extended Producer Responsibility"\n'
        '3. Do NOT assume user business type (FMCG, manufacturer, etc.)\n'
        '4. Do NOT add phrases like "brands like yours" or similar assumptions\n'
        '5. Use bullet points (•) for clear formatting\n'
        '6. Keep responses focused and actionable\n'
        '7. REMOVE all document references, page numbers, section numbers, and manual references\n'
        '8. Provide complete step-by-step registration process without referencing documents\n'
        '9. For producer registration, include: portal details, required documents, timeline, and fees\n'
        f'10. For contact: {phone_number} or {email}\n'
        '11. For medium/high priority leads OR help queries: Replace generic answers with ReCircle-focused solutions\n'
        '12. Do NOT add contact info in the main answer - it will be added separately\n'
        '13. For company queries (about ReCircle): Do NOT add any contact promotion\n'
        '14. Focus only on EPR and plastic waste topics\n'
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


    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=prompt_text)]
        )
    ]

    config = types.GenerateContentConfig(
        temperature=1,
        top_p=0.95,
        max_output_tokens=1024,
        safety_settings=[
            types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="OFF"),
            types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="OFF"),
            types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="OFF"),
            types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="OFF"),
        ],
        
    )

    result = ""
    for chunk in client.models.generate_content_stream(
        model=model, contents=contents, config=config
    ):
        result += chunk.text

    refined_answer = result.strip()
    
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
    
    # Personalize response based on context
    refined_answer = context_manager.personalize_response(refined_answer, user_context, query, user_name)
    
    # Add qualification question if appropriate
    message_count = len([msg for msg in history if msg.get('role') == 'user']) + 1
    engagement_score = intent_detector._calculate_engagement_score(query.lower(), history)
    
    if lead_qualification.should_ask_qualification_question(message_count, engagement_score, user_context):
        qual_question = lead_qualification.get_next_qualification_question(user_context, history)
        if qual_question:
            refined_answer += f"\n\n{qual_question}"
    
    # Remove duplicate CTO info - it will be added in connection message if needed
    # query_lower = query.lower()
    # if any(word in query_lower for word in ["help", "assistance", "support", "contact"]) and "recircle" in query_lower:
    #     cto_info = "\n\n🔧 **Technical Support**: For advanced technical queries or partnerships, you can reach out to our CTO who leads our technology initiatives in EPR compliance and waste management solutions."
    #     refined_answer += cto_info
    
    # Modify response if connection should be suggested (exclude company queries)
    is_company_query = any(word in query.lower() for word in ['what is recircle', 'about recircle', 'recircle company', 'recircle different'])
    
    if intent_result.should_connect and not is_company_query:
        connection_message = intent_detector.get_connection_message(intent_result.intent, user_name)
        
        # Add urgency-specific messaging
        urgency_message = ""
        if user_context.get('urgency') == 'critical':
            urgency_message = "\n⚡ **Emergency Support**: Given the critical timeline, I can arrange an immediate callback within 30 minutes."
        elif user_context.get('urgency') == 'high':
            urgency_message = "\n🚀 **Priority Support**: We can fast-track your requirements and connect you with our specialists today."
        
        refined_answer = f"{refined_answer}\n\n---\n\n{connection_message}{urgency_message}\n\n📞 Call us: {phone_number}\n📧 Email: {email}"
    
    # Add source information to user context
    if source_info:
        user_context['source_info'] = source_info
        threshold_status = "✅ PASSED" if source_info.get('threshold_met', False) else "❌ FAILED"
        logger.info(f"📊 Response sourced from: {source_info['collection_name']} collection")
        logger.info(f"   🔢 Chunk: {source_info['chunk_id']}, Confidence: {source_info['confidence_score']}, Threshold: {threshold_status}")
    
    return refined_answer, intent_result, user_context
