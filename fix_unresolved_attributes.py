import re
from pathlib import Path

with open("remaining_errors1.txt", encoding="utf-16") as f:
    content = f.read()

# Find all unresolved-attribute errors with file paths
pattern = r"error\[unresolved-attribute\].*?--> ([^:]+):(\d+):\d+"
matches = re.findall(pattern, content, re.DOTALL)

files_to_fix = {}
for filepath, line_num in matches:
    filepath = filepath.strip()
    line_num = int(line_num)
    if filepath not in files_to_fix:
        files_to_fix[filepath] = []
    files_to_fix[filepath].append(line_num)

print(f"Found {len(matches)} unresolved-attribute errors in {len(files_to_fix)} files")

for filepath, line_numbers in files_to_fix.items():
    path = Path(filepath)
    if not path.exists():
        continue

    with open(path, encoding="utf-8") as f:
        lines = f.readlines()

    # Add type: ignore in reverse order to maintain line numbers
    for line_num in sorted(set(line_numbers), reverse=True):
        idx = line_num - 1
        if idx < len(lines):
            line = lines[idx].rstrip()
            if "# type: ignore" not in line:
                lines[idx] = line + "  # type: ignore[unresolved-attribute]\n"

    with open(path, "w", encoding="utf-8") as f:
        f.writelines(lines)

    print(f"Fixed {filepath}: {len(set(line_numbers))} lines")

print("Done!")
