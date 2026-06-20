# Skills Dashboard

Skills 清单可视化 + 使用频次追踪。扫描 `F:\_环境\claude\commands\` 下所有已安装 skill，读取使用日志，生成自包含 HTML dashboard。

## 结构

```
generate.py          # 主脚本：扫描 → 解析 frontmatter → 读日志 → 输出 HTML
usage-log-hook.sh    # PostToolUse 钩子，每次 Skill 调用追加一行 JSON
data/usage.jsonl     # 使用日志（钩子写入，generate.py 读取）
```

输出位置：`F:\04_利安工坊\output\skills-dashboard.html`

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

Patch Bay 风格：JetBrains Mono + Inter，信号条编码 7 天使用频率，按 6 个分类分组展示。分类映射硬编码在 generate.py 的 `CATEGORIES` dict 中，新增 skill 后需手动归类。
