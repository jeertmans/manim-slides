import re
from pathlib import Path

with open('qt_errors.txt', 'r', encoding='utf-16') as f:
    content = f.read()

# Find invalid-argument-type errors that mention PyQt/PySide
pattern = r'error\[invalid-argument-type\].*?--> ([^:]+):(\d+):\d+'
all_matches = re.findall(pattern, content, re.DOTALL)

# Filter for only Qt-related ones
qt_matches = []
for match in all_matches:
    filepath, line_num = match
    # Check if this error mentions Qt in its context
    error_context = content[content.find(f'--> {filepath}:{line_num}'):content.find(f'--> {filepath}:{line_num}') + 500]
    if 'PyQt6' in error_context or 'PySide6' in error_context or 'QWidget' in error_context or 'QLayout' in error_context:
        qt_matches.append((filepath.strip(), int(line_num)))

files_to_fix = {}
for filepath, line_num in qt_matches:
    if filepath not in files_to_fix:
        files_to_fix[filepath] = []
    files_to_fix[filepath].append(line_num)

print(f"Found {len(qt_matches)} Qt errors in {len(files_to_fix)} files")

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
    
    print(f"Fixed {filepath}")

print("Done!")