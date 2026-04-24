import vertexai
from vertexai.generative_models import GenerativeModel
import os, logging

PROJECT_ID = os.environ.get("PROJECT_ID", "your-project-id")
vertexai.init(project=PROJECT_ID, location="us-central1")
model = GenerativeModel("gemini-1.5-flash")

def generate_friendly_response(kb_context: str, user_query: str) -> str:
    try:
        prompt = f"""You are a helpful telecom customer support assistant.
A customer asked: "{user_query}"

Here is the relevant information from our knowledge base:
{kb_context}

Respond in 2-3 friendly, conversational sentences. Be concise and accurate.
Do not add information not in the context above."""
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logging.error(f"gemini_error: {e}")
        return kb_context  # fallback to raw KB answer