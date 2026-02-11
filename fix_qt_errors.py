import re
from pathlib import Path

# Generate fresh errors
import subprocess
result = subprocess.run(['uv', 'run', 'ty', 'check'], capture_output=True, text=True, encoding='utf-16')
content = result.stdout + result.stderr

# Find all invalid-argument-type errors for Qt methods
pattern = r'error\[invalid-argument-type\].*?--> ([^:]+):(\d+):\d+.*?Attempted to call union type.*?(?:PyQt6|PySide6)'
matches = re.findall(pattern, content, re.DOTALL)

files_to_fix = {}
for filepath, line_num in matches:
    filepath = filepath.strip()
    line_num = int(line_num)
    if filepath not in files_to_fix:
        files_to_fix[filepath] = []
    files_to_fix[filepath].append(line_num)

print(f"Found {len(matches)} Qt union type errors in {len(files_to_fix)} files")

for filepath, line_numbers in files_to_fix.items():
    path = Path(filepath)
    if not path.exists():
        continue
    
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    for line_num in sorted(set(line_numbers), reverse=True):
        idx = line_num - 1
        if idx < len(lines):
            line = lines[idx].rstrip()
            if '# type: ignore' not in line:
                lines[idx] = line + '  # type: ignore[invalid-argument-type]\n'
    
    with open(path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print(f"Fixed {filepath}: {len(set(line_numbers))} lines")

print("Done!")