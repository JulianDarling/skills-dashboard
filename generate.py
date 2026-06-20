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
    "Research & Analysis": "#7C3AED",
    "Knowledge & Learning": "#4F46E5",
    "Documents & Output": "#2563EB",
    "Creative & Design": "#DB2777",
    "File & System": "#0D9488",
    "Developer Tools": "#475569",
    "Uncategorized": "#6B7280",
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

TRIGGERS = {
    "research-plan": ["调研方案", "研究设计", "用研规划", "调研怎么做"],
    "persuasion-proposal": ["提案", "申请", "buy-in", "推动", "争取", "说服老板"],
    "setup": ["部署", "环境", "新电脑", "setup"],
    "book-distill": ["提炼", "新书", "书籍提炼", "读书笔记"],
    "knowledge-base-check": ["检查知识库", "lint", "健康检查", "断链"],
    "knowledge-base-qa": ["知识库里", "哪本书讲过", "跨书", "从书里找"],
    "portable": ["我来啦", "我走啦", "插上了", "要拔了"],
    "meeting-minutes": ["会议纪要", "整理会议", "会议传达"],
    "FTUE": ["体验报告", "包体体验", "试玩记录", "FTUE"],
    "candidate-eval": ["筛人", "选人", "看简历", "评估候选人", "招聘", "笔试"],
    "organize": ["整理下载", "整理文件", "Downloads"],
    "duplicates": ["查重", "重复文件", "找重复"],
    "desktop": ["清理桌面", "桌面整理"],
    "scan": ["扫描目录", "文件索引", "目录清单"],
    "in-app-research": ["端内调研", "端内问卷", "app内研究"],
    "competitor-questionnaire": ["竞品问卷", "竞品调查问卷"],
    "survey-localization-qa": ["问卷校对", "本地化校对", "翻译校对"],
    "purchase-request": ["采购申请", "预算申请", "采购"],
    "survey-data-analysis": ["问卷数据", "数据清洗", "问卷分析"],
    "aihot": ["AI 资讯", "AI 日报", "AI 圈", "AI 热点", "AI 新闻"],
    "docx": ["Word 文档", ".docx", "报告", "memo", "letter"],
    "pdf": ["PDF", "合并PDF", "拆分PDF", "OCR"],
    "pptx": ["PPT", "幻灯片", "演示文稿", "deck", "slides"],
    "xlsx": ["Excel", ".xlsx", "电子表格", "spreadsheet"],
    "doc-coauthoring": ["写文档", "协作撰写", "PRD", "design doc", "RFC"],
    "internal-comms": ["内部沟通", "status report", "3P update", "newsletter"],
    "frontend-design": ["前端设计", "UI设计", "网页视觉", "landing page"],
    "canvas-design": ["海报", "视觉艺术", "静态设计", "poster"],
    "algorithmic-art": ["生成艺术", "算法艺术", "p5.js", "flow field"],
    "slack-gif-creator": ["Slack GIF", "动画GIF", "emoji动图"],
    "theme-factory": ["主题配色", "styling", "配色方案"],
    "web-artifacts-builder": ["React组件", "shadcn", "HTML artifact"],
    "brand-guidelines": ["品牌配色", "Anthropic风格", "brand colors"],
    "mcp-builder": ["MCP服务器", "MCP server", "tool integration"],
    "webapp-testing": ["Playwright", "浏览器测试", "UI测试"],
    "claude-api": ["Claude API", "Anthropic SDK", "model pricing"],
    "skill-creator": ["创建skill", "修改skill", "skill评估", "触发优化"],
    "neat-freak": ["同步文档", "整理记忆", "tidy up", "收尾"],
}


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
        if s["slug"] == "skill-creator":
            continue
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
            triggers = TRIGGERS.get(slug, [])
            triggers_html = "".join(f'<span class="trigger-tag">{escape_html(t)}</span>' for t in triggers)
            triggers_data = escape_html(" ".join(triggers))
            cards_html += f'''<article class="skill-card" data-slug="{escape_html(slug)}" data-triggers="{triggers_data}">
<div class="signal-bar"></div>
<div class="card-body">
<div class="card-header">
<code class="slug">/{escape_html(slug)}</code>
<button class="copy-btn" onclick="copySlug(this, '/{escape_html(slug)}')" title="Copy">
<svg class="icon-copy" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>
<svg class="icon-check" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="display:none"><polyline points="20 6 9 17 4 12"/></svg>
</button>
</div>
<div class="triggers">{triggers_html}</div>
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
<title>Skills 使用手册</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
:root {{
  --bg: #FAFAFA;
  --ink: #1A1A2E;
  --muted: #4B5563;
  --signal: #2563EB;
  --idle: #D1D5DB;
  --pulse: #059669;
  --warm: #D97706;
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
.stats-bar .stat-active {{ color: var(--pulse); font-weight: 600; }}
.stats-bar .stat-invocations {{ color: var(--signal); font-weight: 600; }}
.search-box {{
  margin-bottom: 32px;
  position: relative;
}}
#search-input {{
  width: 100%;
  font-family: 'JetBrains Mono', monospace;
  font-size: 14px;
  padding: 12px 16px;
  border: 1px solid var(--border);
  background: var(--card-bg);
  color: var(--ink);
  outline: none;
  transition: border-color 0.2s;
}}
#search-input:focus {{
  border-color: var(--signal);
}}
#search-input::placeholder {{
  color: var(--idle);
}}
.search-hint {{
  position: absolute;
  right: 16px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 12px;
  color: var(--muted);
}}
.triggers {{
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-bottom: 8px;
}}
.trigger-tag {{
  font-size: 11px;
  padding: 2px 8px;
  background: #F3F4F6;
  color: var(--muted);
  font-family: 'Inter', sans-serif;
  white-space: nowrap;
}}
.skill-card.hidden {{
  display: none;
}}
.category.hidden {{
  display: none;
}}
.guide {{
  margin-bottom: 48px;
  padding: 32px;
  background: var(--card-bg);
  border: 1px solid var(--border);
}}
.guide-title {{
  font-family: 'JetBrains Mono', monospace;
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 24px;
  color: var(--ink);
  text-transform: none;
  letter-spacing: 0;
  padding-left: 0;
  border-left: none;
}}
.guide-content {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 24px;
}}
.guide-level h3 {{
  font-size: 13px;
  font-weight: 600;
  color: var(--ink);
  margin-bottom: 8px;
}}
.guide-level p {{
  font-size: 13px;
  color: var(--muted);
  line-height: 1.7;
  margin-bottom: 8px;
}}
.guide-level code {{
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  background: #F3F4F6;
  padding: 2px 6px;
  color: var(--ink);
}}
.creator-highlight {{
  margin-bottom: 48px;
}}
.creator-highlight h2 {{
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
.skill-card.featured {{
  border-color: var(--warm);
  border-width: 1.5px;
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
  transition: color 0.15s, border-color 0.15s, background 0.15s;
  display: flex;
  align-items: center;
}}
.copy-btn:hover {{ color: var(--ink); border-color: var(--ink); }}
.copy-btn.copied {{ color: var(--pulse); border-color: var(--pulse); background: #ecfdf5; }}
.copy-btn.copied .icon-copy {{ display: none !important; }}
.copy-btn.copied .icon-check {{ display: block !important; }}
#global-toast {{
  position: fixed;
  bottom: 32px;
  left: 50%;
  transform: translateX(-50%) translateY(20px);
  font-size: 13px;
  font-family: 'JetBrains Mono', monospace;
  color: white;
  background: var(--ink);
  padding: 8px 20px;
  opacity: 0;
  transition: opacity 0.2s, transform 0.2s;
  pointer-events: none;
  z-index: 1000;
}}
#global-toast.show {{
  opacity: 1;
  transform: translateX(-50%) translateY(0);
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
<h1>SKILLS 使用手册</h1>
<div class="stats-bar">
<span><span class="stat-value">{total_installed}</span> 已安装</span>
<span><span class="stat-value stat-active" id="stat-active">—</span> 本周活跃</span>
<span><span class="stat-value stat-invocations" id="stat-total">—</span> 累计调用</span>
<span>更新于 {now.strftime("%Y-%m-%d %H:%M")}</span>
</div>
</header>

<div class="search-box">
<input type="text" id="search-input" placeholder="搜索 skill 名称或触发词..." autocomplete="off">
<span class="search-hint" id="search-hint"></span>
</div>

<section class="guide">
<h2 class="guide-title">Skill 是什么、怎么用</h2>
<div class="guide-content">
<div class="guide-level">
<h3>基础用法</h3>
<p>在 Claude Code 对话中输入 <code>/skill名称</code> 即可触发。例如输入 <code>/research-plan</code> 会启动调研方案设计流程。</p>
<p>你也可以直接用自然语言描述需求，Claude 会自动识别并触发对应 skill。例如说"帮我写个调研方案"会自动触发 <code>/research-plan</code>。</p>
</div>
<div class="guide-level">
<h3>进阶用法</h3>
<p>Skill 可以组合使用：先用 <code>/research-plan</code> 设计方案，再用 <code>/persuasion-proposal</code> 把方案包装成提案。</p>
<p>Skill 的 description 决定触发灵敏度——写得越具体，自然语言触发越精准。你可以用 <code>/skill-creator</code> 调整已有 skill 的触发词。</p>
</div>
<div class="guide-level">
<h3>高级用法：创建你自己的 Skill</h3>
<p>当你发现某个工作流反复出现（写报告、整理数据、生成特定格式的输出），就应该把它固化为 skill。</p>
<p>输入 <code>/skill-creator</code> 进入创建流程：描述意图 → 生成 SKILL.md → 测试触发 → 迭代优化。你的所有自定义 skill 存放在 <code>F:\\_环境\\claude\\commands\\</code>。</p>
</div>
</div>
</section>

<section class="creator-highlight">
<h2 style="border-color:#7C3AED"><span class="cat-dot" style="background:#7C3AED"></span>Skill 工厂</h2>
<div class="grid">
<article class="skill-card featured" data-slug="skill-creator" data-triggers="创建skill 修改skill skill评估 触发优化">
<div class="signal-bar" style="background:var(--warm)"></div>
<div class="card-body">
<div class="card-header">
<code class="slug">/skill-creator</code>
<button class="copy-btn" onclick="copySlug(this, '/skill-creator')" title="Copy">
<svg class="icon-copy" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>
<svg class="icon-check" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="display:none"><polyline points="20 6 9 17 4 12"/></svg>
</button>
</div>
<div class="triggers"><span class="trigger-tag">创建skill</span><span class="trigger-tag">修改skill</span><span class="trigger-tag">skill评估</span><span class="trigger-tag">触发优化</span></div>
<p class="desc expanded">创建新 skill、修改已有 skill、运行评估测试 skill 触发准确度。当你发现一个反复出现的工作模式，用这个 skill 把它固化下来。</p>
<div class="usage-line"></div>
</div>
</article>
</div>
</section>

<main>
{cards_html}
</main>
<footer>
Skills Dashboard &mdash; scanned from F:\\_环境\\claude\\commands\\
</footer>
<div id="global-toast"></div>
<script>
const USAGE_LOG_PATH = 'usage.jsonl';
let toastTimer = null;

function copySlug(btn, text) {{
  navigator.clipboard.writeText(text).then(function() {{
    btn.classList.add('copied');
    setTimeout(function() {{ btn.classList.remove('copied'); }}, 1200);
    const toast = document.getElementById('global-toast');
    toast.textContent = 'Copied: ' + text;
    toast.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function() {{ toast.classList.remove('show'); }}, 1500);
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

const searchInput = document.getElementById('search-input');
const searchHint = document.getElementById('search-hint');
const allCards = document.querySelectorAll('main .skill-card');
const allCategories = document.querySelectorAll('main .category');

searchInput.addEventListener('input', function() {{
  const q = this.value.trim().toLowerCase();
  if (!q) {{
    allCards.forEach(c => c.classList.remove('hidden'));
    allCategories.forEach(c => c.classList.remove('hidden'));
    searchHint.textContent = '';
    return;
  }}
  let count = 0;
  allCards.forEach(function(card) {{
    const slug = card.dataset.slug.toLowerCase();
    const triggers = (card.dataset.triggers || '').toLowerCase();
    const desc = card.querySelector('.desc').textContent.toLowerCase();
    const match = slug.includes(q) || triggers.includes(q) || desc.includes(q);
    card.classList.toggle('hidden', !match);
    if (match) count++;
  }});
  allCategories.forEach(function(sec) {{
    const visible = sec.querySelectorAll('.skill-card:not(.hidden)').length;
    sec.classList.toggle('hidden', visible === 0);
  }});
  searchHint.textContent = count + ' 个匹配';
}});
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
