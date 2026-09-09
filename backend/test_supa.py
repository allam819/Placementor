import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def test_supabase():
    from supabase import create_client
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    client = create_client(url, key)
    # just print client
    print(client)
    
if __name__ == "__main__":
    asyncio.run(test_supabase())
