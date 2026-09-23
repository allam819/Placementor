import os

def rep(file, old, new):
    with open(file, 'r', encoding='utf-8') as f:
        c = f.read()
    with open(file, 'w', encoding='utf-8') as f:
        f.write(c.replace(old, new))

rep("src/main.tsx", "import React from 'react'\n", "")
rep("src/pages/Dashboard.tsx", "goals.map(goal =>", "goals.map((goal: any) =>")
rep("src/pages/Dashboard.tsx", "learning.map(activity =>", "learning.map((activity: any) =>")
rep("src/pages/Learning.tsx", "id: str", "id: string")
rep("src/pages/Resume.tsx", "id: str", "id: string")
rep("src/pages/Resume.tsx", "cat: str", "cat: string")
