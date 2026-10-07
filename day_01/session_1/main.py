import os
from dotenv import load_dotenv
from openai import OpenAI

# 1. Load API key from .env file
load_dotenv()

# 2. Initialize the client
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL")
)

# 3. Make chat completion call
response = client.chat.completions.create(
    model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Explain what an LLM API is in one sentence."}
    ]
)

# 4. Read and print response
print("Reply:")
print(response.choices[0].message.content)
print("\nTokens used:", response.usage.total_tokens)
