# Skills Dashboard

Skills 清单可视化 + 使用频次追踪。扫描 `F:\_环境\claude\commands\` 下所有已安装 skill，读取使用日志，生成自包含 HTML dashboard。

## 结构

```
generate.py          # 主脚本：扫描 → 解析 frontmatter → 输出 HTML（统计由前端 JS 实时计算）
usage-log-hook.sh    # PostToolUse 钩子，每次 Skill 调用追加一行 JSON
```

输出位置：`F:\04_利安工坊\output\skills-dashboard.html`
使用日志：`F:\04_利安工坊\output\usage.jsonl`（与 HTML 同目录，前端 fetch 读取）

## 运行

```bash
python generate.py
```

纯 stdlib，无外部依赖。

## 使用统计

需要在 `~/.claude/settings.json` 的 `hooks` 中配置 PostToolUse：

```json
"PostToolUse": [
  {
    "matcher": "Skill",
    "hooks": [{
      "type": "command",
      "command": "bash \"F:/04_利安工坊/repos/skills-dashboard/usage-log-hook.sh\"",
      "async": true
    }]
  }
]
```

## 设计

Patch Bay 风格：JetBrains Mono + Inter，信号条编码 7 天使用频率，按 6 个分类分组展示。

分类优先读 SKILL.md frontmatter 中的 `category` 字段，缺失时 fallback 到 generate.py 的 `CATEGORIES_FALLBACK` dict。新增 skill 推荐在 frontmatter 加 `category: <类别名>`。

统计由前端 JS 实时从同目录 `usage.jsonl` fetch 计算，打开 HTML 即为最新数据。generate.py 只负责 skill 清单（skill 列表变化时才需重新运行）。
