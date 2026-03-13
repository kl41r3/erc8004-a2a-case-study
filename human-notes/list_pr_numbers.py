"""
列出 data/raw/github_comments.json 中所有出现的 PR 编号。
"""
import json
from pathlib import Path
from collections import Counter

data_path = Path(__file__).parent.parent / "data/raw/github_comments.json"
records = json.loads(data_path.read_text())

# 统计每个 PR 出现的评论数
counter = Counter(
    r["pr_number"] for r in records if r.get("pr_number") is not None
)

pr_numbers = sorted(counter)
print(f"共涉及 {len(pr_numbers)} 个 PR：\n")
print(f"{'PR #':<10} {'评论数':>6}")
print("-" * 18)
for pr in pr_numbers:
    print(f"#{pr:<9} {counter[pr]:>6}")

print(f"\n所有 PR 编号（逗号分隔）：")
print(", ".join(f"#{n}" for n in pr_numbers))
