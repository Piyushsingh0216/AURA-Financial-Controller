import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.environ.get("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

print("Fetching available models for your API key...\n")
try:
    models = client.models.list()
    for m in models.data:
        print(f"Model ID: {m.id}")
except Exception as e:
    print(f"Failed to fetch models: {e}")