import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

response = client.chat.completions.create(
    messages=[
        {"role": "system", "content": "Return a JSON object with key 'test'."},
        {"role": "user", "content": "hi"}
    ],
    model="allam-2-7b",
    response_format={"type": "json_object"}
)
print(response.choices[0].message.content)
