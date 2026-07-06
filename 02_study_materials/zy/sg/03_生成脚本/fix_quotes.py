"""Fix string quoting in build_review_answer_analysis.py"""
import re

path = "build_review_answer_analysis.py"
content = open(path, encoding="utf-8").read()

# Replace curly/smart quotes with straight quotes first (safety net)
content = content.replace("“", '"').replace("”", '"')

lines = content.split("\n")
fixed = []
for line in lines:
    stripped = line.lstrip()
    indent = line[: len(line) - len(stripped)]

    # Match dictionary value lines: N: "..."  or  N: "...",
    m = re.match(r'^(\d+):\s+"(.*)"(,?)$', stripped)
    if m:
        key, body, comma = m.group(1), m.group(2), m.group(3)
        # Use single quotes to avoid embedded double-quote issues
        body = body.replace("'", "\\'")
        fixed.append(f"{indent}{key}: '{body}'{comma}")
    else:
        fixed.append(line)

with open(path, "w", encoding="utf-8") as f:
    f.write("\n".join(fixed))

print("Done - fixed string quoting")
