from google import genai
from google.genai import types
from typing import List, Dict, Optional
import os
from dotenv import load_dotenv

load_dotenv()

phone_number = "9004240004"
email = "info@recircle.in"

# Initialize Gemini client
client = genai.Client(
    vertexai=True,
    project=os.getenv("GOOGLE_PROJECT_ID", "epr-chatbot-443706"),
    location=os.getenv("GOOGLE_LOCATION", "global"),
)

model = "gemini-2.5-flash-lite-preview-06-17"

bot_name = "ReBot"
def refine_with_gemini(
    user_name: Optional[str],
    query: str,
    raw_answer: str,
    history: List[Dict[str, str]],
    is_first_message: bool = False,
) -> str:
    # Build a history string for the prompt
    history_str = ""
    for message in history:
        role = "User" if message.get("role") == "user" else "Assistant"
        history_str += f'{role}: {message.get("text", "")}\n'

    # Greeting prefix if it's the first message and we have a name
    greeting_prefix = f"Start your answer with: 'Hi {user_name},'\n" if is_first_message and user_name else ""

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
       f'6. If the user asks your name or identity (e.g., "What is your name?", "Who are you?"), reply clearly: "I\'m {bot_name}, your assistant from ReCircle."'
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
        thinking_config=types.ThinkingConfig(thinking_budget=0),
    )

    result = ""
    for chunk in client.models.generate_content_stream(
        model=model, contents=contents, config=config
    ):
        result += chunk.text

    return result.strip()
