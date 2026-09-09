import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def test():
    from supabase import create_client
    url = os.environ.get("VITE_SUPABASE_URL") or os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SECRET_KEY")
    client = create_client(url, key)
    
    # create dummy user
    import random
    email = f"test_{random.randint(1,1000)}@gmail.com"
    res = client.auth.admin.create_user({"email": email, "password": "password123", "email_confirm": True})
    
    # sign in to get token
    client = create_client(url, os.environ.get("VITE_SUPABASE_PUBLISHABLE_KEY") or os.environ.get("SUPABASE_PUBLISHABLE_KEY"))
    login = client.auth.signInWithPassword({"email": email, "password": "password123"})
    token = login.session.access_token
    
    import requests
    response = requests.post(
        "http://127.0.0.1:8000/api/learning/chat",
        json={"message": "I learned about python today"},
        headers={"Authorization": f"Bearer {token}"}
    )
    print("STATUS:", response.status_code)
    print("TEXT:", response.text)

if __name__ == "__main__":
    asyncio.run(test())
