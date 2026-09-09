import os
import json
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()
url = os.environ.get("VITE_SUPABASE_URL")
key = os.environ.get("SUPABASE_SECRET_KEY")

supabase = create_client(url, key)

starter_codes = {
    "python": "def twoSum(nums, target):\n    # Write your Python code here\n    pass",
    "javascript": "function twoSum(nums, target) {\n    // Write your JS code here\n}",
    "cpp": "#include <iostream>\n#include <vector>\nusing namespace std;\n\nvector<int> twoSum(vector<int>& nums, int target) {\n    // Write your C++ code here\n    return {};\n}"
}

res = supabase.table("dsa_problems").update({"starter_code": json.dumps(starter_codes)}).eq("title", "Two Sum").execute()
print("Updated starter code for Two Sum!")
