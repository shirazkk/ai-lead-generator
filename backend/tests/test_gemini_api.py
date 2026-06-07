import asyncio
import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv(dotenv_path="../.env")
api_key = os.getenv("GEMINI_API_KEY")
print(f"API Key (truncated): {api_key[:10] if api_key else 'None'}...")

genai.configure(api_key=api_key)

async def main():
    model_name = "gemini-3-flash-preview"
    print(f"Testing model: {model_name}")
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content("Hello, write a 1-word response.")
        print(f"Success! Response: {response.text}")
    except Exception as e:
        print(f"Error with {model_name}: {e}")
        
    fallback_model = "gemini-2.5-flash"
    print(f"Testing fallback model: {fallback_model}")
    try:
        model = genai.GenerativeModel(fallback_model)
        response = model.generate_content("Hello, write a 1-word response.")
        print(f"Success! Response: {response.text}")
    except Exception as e:
        print(f"Error with {fallback_model}: {e}")

if __name__ == "__main__":
    asyncio.run(main())
