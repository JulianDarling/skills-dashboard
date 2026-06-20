"""Skills Dashboard Generator — scans installed skills, reads usage log, outputs HTML."""

import sys
import json
import re
from pathlib import Path
from datetime import datetime, timedelta, timezone
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")

COMMANDS_DIR = Path(r"F:\_环境\claude\commands")
USAGE_LOG = Path(r"F:\04_利安工坊\repos\skills-dashboard\data\usage.jsonl")
OUTPUT_FILE = Path(r"F:\04_利安工坊\output\skills-dashboard.html")

CATEGORIES = {
    "research-plan": "Research & Analysis",
    "survey-data-analysis": "Research & Analysis",
    "in-app-research": "Research & Analysis",
    "candidate-eval": "Research & Analysis",
    "competitor-questionnaire": "Research & Analysis",
    "survey-localization-qa": "Research & Analysis",
    "FTUE": "Research & Analysis",
    "meeting-minutes": "Research & Analysis",
    "book-distill": "Knowledge & Learning",
    "knowledge-base-check": "Knowledge & Learning",
    "knowledge-base-qa": "Knowledge & Learning",
    "aihot": "Knowledge & Learning",
    "docx": "Documents & Output",
    "pdf": "Documents & Output",
    "pptx": "Documents & Output",
    "xlsx": "Documents & Output",
    "doc-coauthoring": "Documents & Output",
    "internal-comms": "Documents & Output",
    "persuasion-proposal": "Documents & Output",
    "purchase-request": "Documents & Output",
    "frontend-design": "Creative & Design",
    "canvas-design": "Creative & Design",
    "algorithmic-art": "Creative & Design",
    "slack-gif-creator": "Creative & Design",
    "theme-factory": "Creative & Design",
    "web-artifacts-builder": "Creative & Design",
    "brand-guidelines": "Creative & Design",
    "organize": "File & System",
    "desktop": "File & System",
    "duplicates": "File & System",
    "scan": "File & System",
    "setup": "File & System",
    "portable": "File & System",
    "neat-freak": "File & System",
    "skill-creator": "Developer Tools",
    "mcp-builder": "Developer Tools",
    "webapp-testing": "Developer Tools",
    "claude-api": "Developer Tools",
}

CATEGORY_COLORS = {
    "Research & Analysis": "#8B5CF6",
    "Knowledge & Learning": "#6366F1",
    "Documents & Output": "#3B82F6",
    "Creative & Design": "#EC4899",
    "File & System": "#14B8A6",
    "Developer Tools": "#64748B",
    "Uncategorized": "#9CA3AF",
}

CATEGORY_ORDER = [
    "Research & Analysis",
    "Knowledge & Learning",
    "Documents & Output",
    "Creative & Design",
    "File & System",
    "Developer Tools",
    "Uncategorized",
]


def parse_skill(filepath: Path, slug_override: str = None) -> dict:
    text = filepath.read_text(encoding="utf-8-sig")
    slug = slug_override or filepath.stem
    name = slug
    description = ""

    fm_match = re.match(r"^---\s*\n(.+?)\n---", text, re.DOTALL)
    if fm_match:
        fm_block = fm_match.group(1)
        name_match = re.search(r"^name:\s*(.+)$", fm_block, re.MULTILINE)
        if name_match:
            name = name_match.group(1).strip().strip("\"'")

        desc_match = re.search(
            r"^description:\s*[|>]?-?\s*\n((?:\s+.+\n)+)", fm_block, re.MULTILINE
        )
        if desc_match:
            description = " ".join(
                line.strip() for line in desc_match.group(1).strip().split("\n")
            )
        else:
            desc_match = re.search(
                r'^description:\s*["\']?(.+?)["\']?\s*$', fm_block, re.MULTILINE
            )
            if desc_match:
                description = desc_match.group(1)
    else:
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        if lines:
            first = lines[0].lstrip("# ")
            description = first

    return {
        "slug": slug,
        "name": name,
        "description": description,
        "category": CATEGORIES.get(slug, "Uncategorized"),
    }


def read_usage_stats() -> dict:
    total = Counter()
    last_7d = Counter()
    last_used = {}

    if not USAGE_LOG.exists():
        return {"total": total, "last_7d": last_7d, "last_used": last_used}

    cutoff = datetime.now(timezone.utc) - timedelta(days=7)

    for line in USAGE_LOG.read_text(encoding="utf-8").strip().split("\n"):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        skill = record.get("skill", "")
        ts_str = record.get("timestamp", "")
        if not skill or not ts_str:
            continue
        try:
            ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        except ValueError:
            continue
        total[skill] += 1
        if ts > cutoff:
            last_7d[skill] += 1
        if skill not in last_used or ts > last_used[skill]:
            last_used[skill] = ts

    return {"total": total, "last_7d": last_7d, "last_used": last_used}


def truncate(text: str, length: int = 120) -> str:
    if len(text) <= length:
        return text
    return text[: length - 1] + "…"


def escape_html(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def frequency_class(count_7d: int) -> str:
    if count_7d == 0:
        return "idle"
    if count_7d <= 3:
        return "low"
    if count_7d <= 10:
        return "mid"
    return "high"


def generate_html(skills: list, stats: dict) -> str:
    now = datetime.now()
    total_installed = len(skills)
    active_7d = sum(1 for s in skills if stats["last_7d"].get(s["slug"], 0) > 0)
    total_invocations = sum(stats["total"].values())

    grouped = {}
    for s in skills:
        cat = s["category"]
        grouped.setdefault(cat, []).append(s)

    for cat in grouped:
        grouped[cat].sort(key=lambda x: -stats["last_7d"].get(x["slug"], 0))

    cards_html = ""
    for cat in CATEGORY_ORDER:
        if cat not in grouped:
            continue
        color = CATEGORY_COLORS[cat]
        cards_html += f'<section class="category"><h2 style="border-color:{color}"><span class="cat-dot" style="background:{color}"></span>{escape_html(cat)}</h2><div class="grid">\n'
        for s in grouped[cat]:
            slug = s["slug"]
            freq = frequency_class(stats["last_7d"].get(slug, 0))
            count_total = stats["total"].get(slug, 0)
            count_7d = stats["last_7d"].get(slug, 0)
            desc_short = escape_html(truncate(s["description"]))
            desc_full = escape_html(s["description"])
            cards_html += f'''<article class="skill-card freq-{freq}" title="{desc_full}">
<div class="signal-bar" style="--cat-color:{color}"></div>
<div class="card-body">
<div class="card-header">
<code class="slug">/{escape_html(slug)}</code>
<button class="copy-btn" onclick="copySlug(this, '/{escape_html(slug)}')" title="Copy to clipboard">
<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>
</button>
</div>
<p class="desc">{desc_short}</p>
<div class="usage-line">
<span class="count-total">{count_total} total</span>
<span class="count-7d">{count_7d} / 7d</span>
</div>
</div>
</article>\n'''
        cards_html += "</div></section>\n"

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Skills Dashboard</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
:root {{
  --bg: #FAFAFA;
  --ink: #1A1A2E;
  --muted: #6B7280;
  --signal: #3B82F6;
  --idle: #D1D5DB;
  --pulse: #10B981;
  --warm: #F59E0B;
  --card-bg: #FFFFFF;
  --border: #E5E7EB;
}}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
  font-family: 'Inter', -apple-system, sans-serif;
  background: var(--bg);
  color: var(--ink);
  padding: 40px 48px;
  max-width: 1400px;
  margin: 0 auto;
  line-height: 1.5;
}}
header {{
  margin-bottom: 48px;
  padding-bottom: 24px;
  border-bottom: 1px solid var(--border);
}}
h1 {{
  font-family: 'JetBrains Mono', monospace;
  font-size: 24px;
  font-weight: 500;
  letter-spacing: -0.5px;
  margin-bottom: 12px;
}}
.stats-bar {{
  display: flex;
  gap: 24px;
  font-size: 13px;
  color: var(--muted);
}}
.stats-bar .stat-value {{
  font-weight: 600;
  color: var(--ink);
}}
.category {{
  margin-bottom: 40px;
}}
.category h2 {{
  font-size: 14px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--muted);
  margin-bottom: 16px;
  padding-left: 20px;
  border-left: 3px solid;
  display: flex;
  align-items: center;
  gap: 8px;
}}
.cat-dot {{
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
}}
.grid {{
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 12px;
}}
.skill-card {{
  position: relative;
  background: var(--card-bg);
  border: 1px solid var(--border);
  padding: 16px 16px 16px 20px;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
  overflow: hidden;
}}
.skill-card:hover {{
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.06);
}}
.signal-bar {{
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background: var(--idle);
  transition: background 0.3s;
}}
.freq-low .signal-bar {{
  background: var(--signal);
  height: 40%;
  bottom: auto;
  top: 30%;
}}
.freq-mid .signal-bar {{
  background: var(--warm);
  height: 70%;
  bottom: auto;
  top: 15%;
}}
.freq-high .signal-bar {{
  background: var(--pulse);
  animation: pulse 2s ease-in-out infinite;
}}
@keyframes pulse {{
  0%, 100% {{ opacity: 1; }}
  50% {{ opacity: 0.5; }}
}}
.freq-idle {{ opacity: 0.75; }}
.freq-idle:hover {{ opacity: 1; }}
.card-body {{ position: relative; }}
.slug {{
  font-family: 'JetBrains Mono', monospace;
  font-size: 14px;
  font-weight: 500;
  color: var(--ink);
  display: block;
  margin-bottom: 6px;
}}
.desc {{
  font-size: 12px;
  color: var(--muted);
  line-height: 1.6;
  margin-bottom: 10px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}}
.usage-line {{
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  font-family: 'JetBrains Mono', monospace;
}}
.card-header {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}}
.card-header .slug {{ margin-bottom: 0; }}
.copy-btn {{
  background: none;
  border: 1px solid var(--border);
  cursor: pointer;
  padding: 4px 6px;
  color: var(--muted);
  transition: color 0.15s, border-color 0.15s;
  display: flex;
  align-items: center;
}}
.copy-btn:hover {{ color: var(--ink); border-color: var(--ink); }}
.copy-btn.copied {{ color: var(--pulse); border-color: var(--pulse); }}
.count-total {{ color: var(--muted); }}
.count-7d {{ color: var(--signal); font-weight: 500; }}
.freq-idle .count-7d {{ color: var(--idle); }}
footer {{
  margin-top: 48px;
  padding-top: 16px;
  border-top: 1px solid var(--border);
  font-size: 11px;
  color: var(--muted);
}}
@media (max-width: 768px) {{
  body {{ padding: 24px 16px; }}
  .grid {{ grid-template-columns: 1fr; }}
}}
</style>
</head>
<body>
<header>
<h1>SKILLS DASHBOARD</h1>
<div class="stats-bar">
<span><span class="stat-value">{total_installed}</span> installed</span>
<span><span class="stat-value">{active_7d}</span> active this week</span>
<span><span class="stat-value">{total_invocations}</span> total invocations</span>
<span>Generated: {now.strftime("%Y-%m-%d %H:%M")}</span>
</div>
</header>
<main>
{cards_html}
</main>
<footer>
Skills Dashboard &mdash; scanned from F:\\_环境\\claude\\commands\\
</footer>
<script>
function copySlug(btn, text) {{
  navigator.clipboard.writeText(text).then(function() {{
    btn.classList.add('copied');
    setTimeout(function() {{ btn.classList.remove('copied'); }}, 1200);
  }});
}}
</script>
</body>
</html>"""
    return html


def main():
    skills = []

    for f in sorted(COMMANDS_DIR.glob("*.md")):
        skills.append(parse_skill(f))

    for d in sorted(COMMANDS_DIR.iterdir()):
        if d.is_dir() and (d / "SKILL.md").exists():
            skills.append(parse_skill(d / "SKILL.md", slug_override=d.name))

    stats = read_usage_stats()
    html = generate_html(skills, stats)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(html, encoding="utf-8")
    print(f"Generated: {OUTPUT_FILE}")
    print(f"  {len(skills)} skills, {sum(stats['total'].values())} total invocations logged")


if __name__ == "__main__":
    main()
