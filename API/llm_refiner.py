from google import genai
from google.genai import types

phone_number = "9004240004"
email = "info@recircle.in"

# Initialize Gemini client
client = genai.Client(
    vertexai=True,
    project="grant-ai-writer",
    location="global",
)

model = "gemini-2.5-flash-lite-preview-06-17"

def refine_with_gemini(query: str, raw_answer: str) -> str:
    prompt_text = (
        f'{query}\n\n'
        f'Information:\n---\n{raw_answer}\n\n'
        f'If someone asks how to reach ReCircle, share the official phone number ({phone_number}) or email ({email}) — never invent other contact details.\n'
        'Only answer questions that are related to plastic waste, Extended Producer Responsibility (EPR), or ReCircle’s work. '
        'If the question is not related to these, respond politely and suggest asking something relevant.\n\n'
        'Keep your reply short, clear, and friendly.'
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
