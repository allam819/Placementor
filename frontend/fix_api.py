import os
import re

files_to_fix = [
    "src/pages/DSAInterviewWorkspace.tsx",
    "src/pages/DSAProblems.tsx",
    "src/pages/DSAWorkspace.tsx",
    "src/pages/Goals.tsx",
    "src/pages/Interviews.tsx",
    "src/pages/Learning.tsx",
    "src/pages/Resume.tsx",
    "src/pages/Settings.tsx"
]

for file_path in files_to_fix:
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    if "import { fetchApi }" not in content and "fetch(" in content:
        imports = re.findall(r'^import .+\n', content, flags=re.MULTILINE)
        if imports:
            last_import = imports[-1]
            content = content.replace(last_import, last_import + "import { fetchApi } from '../lib/api'\n")
        else:
            content = "import { fetchApi } from '../lib/api'\n" + content

    content = re.sub(
        r"await fetch\(`http://127\.0\.0\.1:8000/api(.*?)\`, \{(.*?)\}\)",
        r"await fetchApi(`\1`, {\2})",
        content,
        flags=re.DOTALL
    )
    content = re.sub(
        r"await fetch\('http://127\.0\.0\.1:8000/api(.*?)', \{(.*?)\}\)",
        r"await fetchApi('\1', {\2})",
        content,
        flags=re.DOTALL
    )
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

print("Done replacing.")
