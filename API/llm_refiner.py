from google import genai
from google.genai import types
from typing import List, Dict, Optional, Tuple
import os
from dotenv import load_dotenv
from intent_detector import IntentDetector, IntentResult
from context_manager import context_manager
from proactive_engagement import proactive_engagement
from lead_qualification import lead_qualification

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
) -> Tuple[str, IntentResult, Dict]:
    # Analyze user intent
    intent_result = intent_detector.analyze_intent(query, history)
    
    # Extract user context
    user_context = context_manager.extract_context(query, history)
    
    # Track user journey for proactive engagement
    if session_id:
        proactive_engagement.track_user_journey(session_id, query, intent_result.intent)
    
    # Build a history string for the prompt
    history_str = ""
    for message in history:
        role = "User" if message.get("role") == "user" else "Assistant"
        history_str += f'{role}: {message.get("text", "")}\n'

    # Greeting prefix if it's the first message and we have a name
    greeting_prefix = f"Start your answer with: 'Hi {user_name},'\n" if is_first_message and user_name else ""
    
    # Context-aware instructions
    context_instructions = ""
    if user_context.get('urgency') in ['critical', 'high']:
        context_instructions += "IMPORTANT: This user has urgent requirements. Prioritize immediate assistance and callback offers.\n"
    if user_context.get('industry'):
        context_instructions += f"NOTE: User is from {user_context['industry']} industry. Tailor response accordingly.\n"

    prompt_text = (
        f'You are {bot_name}, a friendly and helpful AI assistant for ReCircle.\n'
        'Your primary goal is to provide clear and concise answers based on the information provided.\n\n'
        f'{greeting_prefix}'
        '## CONVERSATION HISTORY (for context):\n'
        f'{history_str}\n'
        '## CURRENT USER QUESTION:\n'
        f'{query}\n\n'
        '## KNOWLEDGE BASE INFORMATION (This is your primary source of truth. Base your answer on this):\n'
        f'---\n{raw_answer}\n---\n\n'
        '## INSTRUCTIONS:\n'
        '1. Based on the KNOWLEDGE BASE INFORMATION, answer the CURRENT USER QUESTION.\n'
        '2. Use the CONVERSATION HISTORY to understand the context of the question.\n'
        '3. Keep your reply short, clear, and friendly. Do not repeat the user\'s name after the initial greeting.\n'
        f'4. If asked for contact details, provide the official phone number ({phone_number}) or email ({email}). Do not invent contact details.\n'
       '5. Only answer questions about plastic waste, EPR, or ReCircle. For unrelated questions, politely decline and steer the conversation back to relevant topics.\n'
       f'6. If the user asks your name or identity (e.g., "What is your name?", "Who are you?"), reply clearly: "I\'m {bot_name}, your assistant from ReCircle."\n'
        f'{context_instructions}'
    )

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
    
    # Personalize response based on context
    refined_answer = context_manager.personalize_response(refined_answer, user_context, user_name)
    
    # Add qualification question if appropriate
    message_count = len([msg for msg in history if msg.get('role') == 'user']) + 1
    engagement_score = intent_detector._calculate_engagement_score(query.lower(), history)
    
    if lead_qualification.should_ask_qualification_question(message_count, engagement_score, user_context):
        qual_question = lead_qualification.get_next_qualification_question(user_context, history)
        if qual_question:
            refined_answer += f"\n\n{qual_question}"
    
    # Modify response if connection should be suggested
    if intent_result.should_connect:
        connection_message = intent_detector.get_connection_message(intent_result.intent, user_name)
        
        # Add urgency-specific messaging
        urgency_message = ""
        if user_context.get('urgency') == 'critical':
            urgency_message = "\n⚡ **Emergency Support**: Given the critical timeline, I can arrange an immediate callback within 30 minutes."
        elif user_context.get('urgency') == 'high':
            urgency_message = "\n🚀 **Priority Support**: We can fast-track your requirements and connect you with our specialists today."
        
        refined_answer = f"{connection_message}{urgency_message}\n\nFor immediate assistance:\n📞 Call us: {phone_number}\n📧 Email: {email}\n\n---\n\nAdditional Information:\n{refined_answer}"
    
    return refined_answer, intent_result, user_context
