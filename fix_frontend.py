import os
import glob
import re

for filepath in glob.glob('frontend/src/pages/*.tsx'):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    original_content = content
    
    # 1. if (res.ok) setXYZ(await res.json()) -> setXYZ(res)
    content = re.sub(r'if\s*\(\s*res\.ok\s*\)\s*([a-zA-Z0-9_]+)\(\s*await\s*res\.json\(\)\s*\)', r'\1(res)', content)
    
    # 2. const data = await res.json() -> const data = res
    content = re.sub(r'const\s+([a-zA-Z0-9_]+)\s*=\s*await\s+res\.json\(\)', r'const \1 = res', content)
    
    # 3. await res.text() -> we don't have access to .text() anymore, if we get here we'll just throw it out or let the try/catch catch it.
    content = re.sub(r'await\s+res\.text\(\)', r'String(res)', content)
    
    # 4. Remove `if (res.ok) {` and corresponding `else { ... }` blocks where possible.
    # It's easier to just strip `if (res.ok) {` and the else alert, but regex is brittle. Let's do it manually for the files.

    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

print("done")
