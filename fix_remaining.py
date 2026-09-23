import re
import glob

for filepath in glob.glob('frontend/src/pages/*.tsx'):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    content = re.sub(r'if\s*\(\s*res\.ok\s*\)\s*\{\s*([\s\S]*?)\s*\}\s*else\s*\{[\s\S]*?\}', r'\1', content)
    content = re.sub(r'if\s*\(\s*res\.ok\s*\)\s*\{\s*([\s\S]*?)\s*\}', r'\1', content)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

print("done")
