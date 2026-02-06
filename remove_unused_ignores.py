import re
from pathlib import Path

with open('errors.txt', 'r', encoding='utf-16') as f:
    content = f.read()

pattern = r'warning\[unused-type-ignore-comment\].*?--> ([^:]+):(\d+):\d+'
matches = re.findall(pattern, content, re.DOTALL)

files_to_fix = {}
for filepath, line_num in matches:
    filepath = filepath.strip()
    line_num = int(line_num)
    if filepath not in files_to_fix:
        files_to_fix[filepath] = []
    files_to_fix[filepath].append(line_num)

print(f"Found {len(matches)} unused comments in {len(files_to_fix)} files")

for filepath, line_numbers in files_to_fix.items():
    path = Path(filepath)
    if not path.exists():
        continue
    
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    for line_num in sorted(line_numbers, reverse=True):
        idx = line_num - 1
        if idx < len(lines):
            # Remove entire # type: ignore comment including brackets
            lines[idx] = re.sub(r'\s*#\s*type:\s*ignore(\[[\w-]+\])?', '', lines[idx])
            # If line is now empty or just whitespace, remove it
            if lines[idx].strip() == '':
                lines[idx] = '\n'
    
    with open(path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print(f"Fixed {filepath}")

print("Done!")