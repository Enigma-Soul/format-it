# 更新日志

版本号遵循语义化版本。发版时 CI 依据 `pyproject.toml` 的版本号打 tag,并取此处对应版本条目作为 GitHub Release 内容。

# 0.3.0

### Feat(web)

- Web UI 多文件标签页、下载按钮、一键整理
- 界面重设计为「红头文件」风格:纸白 / 墨色 / 印章红色板,宋体品牌字 + 仿宋注释,页眉红色反线
- 生成成功「盖章」动效;标签页脏标记提示「有未生成的修改」
- 并行上传:每个文件即时建立「转换中」标签页,失败自动移除并提示
- 已选文件逐条列出、可移除;整窗拖放接收,自动过滤非 .docx
- 会话过期明确提示重新上传;Ctrl + Enter 快速生成;方向键切换标签
- 一键整理幂等化:统一换行、去行尾空白、收紧空行、修剪首尾

### Fix(ci)

- CI 打包修复、按钮合并、统一字体

### Chore

- 接入 ruff 格式化与检查,存量代码已按规范整理
- 新增 CHANGELOG.md 与 CONTRIBUTING.md
- CI 发版读取 `pyproject.toml` 版本号,并以 CHANGELOG 对应条目作为 Release 内容
- README 重写:徽章、印章 logo、admonition 指引

# 0.2.1

### Chore(ci)

- 版本重发,修复 v0.2.0 打包产物问题

# 0.2.0

### Feat(web)

- Web UI(FastAPI + 单页前端)替代 TUI,CI 打包改为目录(--onedir)
- 前端拆分为 html / css / js 多文件,支持暗色模式

# 0.1.1

### Feat

- 实现 GB/T 9704 公文标准 Word 格式化:标题三策略检测(字号 / 序号 / 行内字数)、序号规范化、Markdown 审校中转、标准回写(页边距 / 字体 / 字号 / 行距 / 缩进)
- 无交互命令行:全流程 / `--md-only` / `--from-md` / `-c` 自定义配置 / `--init-config`

### Chore(ci)

- GitHub Actions 自动打包发布;忽略规则完善
