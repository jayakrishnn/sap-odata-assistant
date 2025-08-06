# test_llm.py

from dotenv import load_dotenv
from pathlib import Path
from google import genai

# 1) Load your .env
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

# 2) Instantiate the client with your key
client = genai.Client(api_key=None)  # let it auto-pick GEMINI_API_KEY

# 3) Send a very simple prompt
resp = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Hello, world!"
)

print("RAW RESPONSE OBJECT:")
print(resp)
print("\nRESPONSE.TEXT:")
print(repr(resp.text))
