import os
from openai import OpenAI
from dotenv import load_dotenv # Import load_dotenv

# Load environment variables
load_dotenv()

# Use your OpenRouter API key from environment variables
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY environment variable not set. Please set it in your .env file.")

client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1"
)

def summarize_document(file_name: str, text: str) -> dict:
    """
    Summarizes the given text using the OpenAI GPT model via OpenRouter.
    """
    if not text.strip():
        return {"file_name": file_name, "summary": "No readable text found for summarization."}

    # Truncate text to avoid exceeding model's context window. 
    # 5000 characters is a reasonable limit for a short summary, 
    # but adjust based on the specific model and your needs.
    text_to_summarize = text[:5000] 

    try:
        response = client.chat.completions.create(
            model="openai/gpt-4o",  # or "openai/gpt-4o-mini" for faster/lighter responses
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes documents concisely."},
                {"role": "user", "content": f"Summarize the following document in 5-10 sentences, focusing on key information:\n\n{text_to_summarize}"}
            ],
            temperature=0.5, # Adjust creativity; lower for more factual, higher for more creative
            max_tokens=400 # Max tokens for the summary itself
        )

        summary = response.choices[0].message.content.strip()

    except Exception as e:
        summary = f"Error generating summary for '{file_name}': {e}"
        print(f"Summarization error for {file_name}: {e}") # Print error to console for debugging

    return {"file_name": file_name, "summary": summary}
