"""Skills Dashboard Generator — scans installed skills, outputs HTML with live stats."""

import sys
import json
import re
from pathlib import Path
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8")

COMMANDS_DIR = Path(r"F:\_环境\claude\commands")
OUTPUT_DIR = Path(r"F:\04_利安工坊\output")
OUTPUT_FILE = OUTPUT_DIR / "skills-dashboard.html"

CATEGORIES_FALLBACK = {
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
    category = None

    fm_match = re.match(r"^---\s*\n(.+?)\n---", text, re.DOTALL)
    if fm_match:
        fm_block = fm_match.group(1)
        name_match = re.search(r"^name:\s*(.+)$", fm_block, re.MULTILINE)
        if name_match:
            name = name_match.group(1).strip().strip("\"'")

        cat_match = re.search(r"^category:\s*(.+)$", fm_block, re.MULTILINE)
        if cat_match:
            category = cat_match.group(1).strip().strip("\"'")

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

    if not category:
        category = CATEGORIES_FALLBACK.get(slug, "Uncategorized")

    return {
        "slug": slug,
        "name": name,
        "description": description,
        "category": category,
    }


def escape_html(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;").replace("'", "&#39;")


def generate_html(skills: list) -> str:
    now = datetime.now()
    total_installed = len(skills)
    skills_json = json.dumps(skills, ensure_ascii=False)

    grouped = {}
    for s in skills:
        cat = s["category"]
        grouped.setdefault(cat, []).append(s)

    cards_html = ""
    for cat in CATEGORY_ORDER:
        if cat not in grouped:
            continue
        color = CATEGORY_COLORS.get(cat, "#9CA3AF")
        cards_html += f'<section class="category" data-cat="{escape_html(cat)}"><h2 style="border-color:{color}"><span class="cat-dot" style="background:{color}"></span>{escape_html(cat)}</h2><div class="grid">\n'
        for s in grouped[cat]:
            slug = s["slug"]
            desc = escape_html(s["description"])
            cards_html += f'''<article class="skill-card" data-slug="{escape_html(slug)}">
<div class="signal-bar"></div>
<div class="card-body">
<div class="card-header">
<code class="slug">/{escape_html(slug)}</code>
<button class="copy-btn" onclick="copySlug(this, '/{escape_html(slug)}')" title="Copy">
<svg class="icon-copy" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>
<svg class="icon-check" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="display:none"><polyline points="20 6 9 17 4 12"/></svg>
</button>
</div>
<p class="desc">{desc}</p>
<div class="usage-line"></div>
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
  background: transparent;
}}
.skill-card.freq-low .signal-bar {{ background: var(--signal); }}
.skill-card.freq-mid .signal-bar {{ background: var(--warm); }}
.skill-card.freq-high .signal-bar {{ background: var(--pulse); animation: pulse 2s ease-in-out infinite; }}
@keyframes pulse {{
  0%, 100% {{ opacity: 1; }}
  50% {{ opacity: 0.5; }}
}}
.card-body {{ position: relative; }}
.card-header {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}}
.slug {{
  font-family: 'JetBrains Mono', monospace;
  font-size: 14px;
  font-weight: 500;
  color: var(--ink);
}}
.copy-btn {{
  background: none;
  border: 1px solid var(--border);
  cursor: pointer;
  padding: 4px 6px;
  color: var(--muted);
  transition: color 0.15s, border-color 0.15s;
  display: flex;
  align-items: center;
  position: relative;
}}
.copy-btn:hover {{ color: var(--ink); border-color: var(--ink); }}
.copy-btn.copied {{ color: var(--pulse); border-color: var(--pulse); }}
.copy-btn.copied .icon-copy {{ display: none !important; }}
.copy-btn.copied .icon-check {{ display: block !important; }}
.copy-toast {{
  position: absolute;
  top: -28px;
  right: 0;
  font-size: 11px;
  font-family: 'JetBrains Mono', monospace;
  color: var(--pulse);
  background: white;
  border: 1px solid var(--pulse);
  padding: 2px 8px;
  white-space: nowrap;
  animation: fadeInOut 1.2s ease forwards;
  pointer-events: none;
}}
@keyframes fadeInOut {{
  0% {{ opacity: 0; transform: translateY(4px); }}
  15% {{ opacity: 1; transform: translateY(0); }}
  75% {{ opacity: 1; }}
  100% {{ opacity: 0; }}
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
  cursor: pointer;
  transition: all 0.2s;
}}
.desc.expanded {{
  -webkit-line-clamp: unset;
  display: block;
}}
.usage-line {{
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  font-family: 'JetBrains Mono', monospace;
  min-height: 16px;
}}
.count-total {{ color: var(--muted); }}
.count-7d {{ color: var(--signal); font-weight: 500; }}
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
<span><span class="stat-value" id="stat-active">—</span> active this week</span>
<span><span class="stat-value" id="stat-total">—</span> total invocations</span>
<span>Skills scanned: {now.strftime("%Y-%m-%d %H:%M")}</span>
</div>
</header>
<main>
{cards_html}
</main>
<footer>
Skills Dashboard &mdash; scanned from F:\\_环境\\claude\\commands\\
</footer>
<script>
const USAGE_LOG_PATH = 'usage.jsonl';

function copySlug(btn, text) {{
  navigator.clipboard.writeText(text).then(function() {{
    btn.classList.add('copied');
    const toast = document.createElement('span');
    toast.className = 'copy-toast';
    toast.textContent = 'Copied!';
    btn.appendChild(toast);
    setTimeout(function() {{
      btn.classList.remove('copied');
      toast.remove();
    }}, 1200);
  }});
}}

document.querySelectorAll('.desc').forEach(function(el) {{
  el.addEventListener('click', function() {{
    this.classList.toggle('expanded');
  }});
}});

async function loadStats() {{
  let lines;
  try {{
    const resp = await fetch(USAGE_LOG_PATH);
    if (!resp.ok) return;
    const text = await resp.text();
    lines = text.trim().split('\\n').filter(Boolean);
  }} catch(e) {{ return; }}

  const now = Date.now();
  const sevenDays = 7 * 24 * 60 * 60 * 1000;
  const total = {{}};
  const last7d = {{}};

  for (const line of lines) {{
    try {{
      const rec = JSON.parse(line);
      const skill = rec.skill;
      const ts = new Date(rec.timestamp).getTime();
      total[skill] = (total[skill] || 0) + 1;
      if (now - ts < sevenDays) {{
        last7d[skill] = (last7d[skill] || 0) + 1;
      }}
    }} catch(e) {{ continue; }}
  }}

  let totalCount = 0;
  let activeCount = 0;

  document.querySelectorAll('.skill-card').forEach(function(card) {{
    const slug = card.dataset.slug;
    const t = total[slug] || 0;
    const w = last7d[slug] || 0;
    totalCount += t;
    if (w > 0) activeCount++;

    const usageLine = card.querySelector('.usage-line');
    if (t > 0) {{
      usageLine.innerHTML = '<span class="count-total">' + t + ' total</span><span class="count-7d">' + w + ' / 7d</span>';
    }}

    if (w === 0) {{
      // no signal bar, no class
    }} else if (w <= 3) {{
      card.classList.add('freq-low');
    }} else if (w <= 10) {{
      card.classList.add('freq-mid');
    }} else {{
      card.classList.add('freq-high');
    }}
  }});

  document.getElementById('stat-active').textContent = activeCount;
  document.getElementById('stat-total').textContent = totalCount;
}}

loadStats();
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

    html = generate_html(skills)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(html, encoding="utf-8")
    print(f"Generated: {OUTPUT_FILE}")
    print(f"  {len(skills)} skills")


if __name__ == "__main__":
    main()
