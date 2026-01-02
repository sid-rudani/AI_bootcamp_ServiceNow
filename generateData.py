#Sending request to OpenAI API
import os
import openai
from dotenv import load_dotenv
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
response = openai.Completion.create(
    model=os.getenv("judgeLLM"),
    prompt="Hello, how are you?",
    max_tokens=5,
    seed=42
)
print(response.choices[0].text.strip())