# format-it

将 Word 文档按 GB/T 9704 国家公文标准进行格式化。

## 功能

- 读取 Word 文档，自动检测标题级别（字体大小 / 序号格式 / 行内字数）
- 自动格式化标题序号（`一、` / `（二）` / `3.` / `（4）`）
- 导出为 Markdown 供用户检查编辑
- 按公文标准回写为格式化 Word 文件（页边距、字体、字号、行距、缩进）
- Web UI 在线编辑 Markdown，支持暗色模式
- 无交互命令行模式，支持自动化批处理

## 目录结构

```
format-it/
├── main.py              # Web UI 入口
├── cli.py               # 命令行入口（无交互）
├── libs/                # 核心库
│   ├── config.py            # TOML 配置（GB/T 9704 默认值）
│   ├── converter.py         # 主转换类，编排流水线
│   ├── heading_detector.py  # 标题检测 + 序号格式化
│   ├── word_reader.py       # Word 读取
│   ├── word_writer.py       # Word 写入
│   ├── md_writer.py         # Markdown 写入
│   ├── md_reader.py         # Markdown 读取
│   ├── user_interaction.py  # 交互接口 + 自动/静默/打印实现
│   ├── fonts.py             # 中文字体映射
│   └── models.py            # 数据模型
├── web/                 # Web UI
│   ├── app.py               # FastAPI 应用工厂
│   ├── routes.py            # API 路由
│   ├── sessions.py          # 会话管理
│   └── static/              # 前端静态文件
│       ├── index.html
│       ├── css/style.css
│       └── js/app.js
├── configs/             # 配置文件（TOML）
└── .github/workflows/   # CI/CD
```

## 安装

需要 [uv](https://docs.astral.sh/uv/) 和 Python >= 3.12。

```bash
uv sync
```

## 使用

### Web UI（默认）

```bash
uv run python main.py                    # 启动 http://127.0.0.1:8000
uv run python main.py --public           # 监听所有接口
uv run python main.py --port 9000        # 自定义端口
```

在浏览器中上传 `.docx` 文件，编辑生成的 Markdown，点击生成并下载格式化文档。

### 命令行

```bash
uv run python cli.py input.docx              # 全流程自动
uv run python cli.py --md-only input.docx    # 仅生成 Markdown
uv run python cli.py --from-md edited.md     # 从 Markdown 生成 Word
uv run python cli.py -c custom.toml input.docx  # 指定配置
uv run python cli.py --init-config           # 生成默认配置
```

## 配置

配置文件位于 `configs/`，首次使用可通过 `--init-config` 生成。默认配置遵循 GB/T 9704：

| 项目 | 默认值 |
|------|--------|
| 纸张 | A4 (210mm × 297mm) |
| 上/下/左/右边距 | 37mm / 35mm / 28mm / 26mm |
| 标题字体 | 方正小标宋简体 22pt (2号) |
| 正文字体 | 仿宋_GB2312 16pt (3号) |
| 每行字数 | 28 |
| 每页行数 | 22 |
| 行距 | 28.9pt 固定值 |
| 一级标题 | 黑体 16pt，序号 `一、` |
| 二级标题 | 楷体_GB2312 16pt，序号 `（二）` |
| 三级标题 | 仿宋_GB2312 16pt，序号 `3.` |
| 四级标题 | 仿宋_GB2312 16pt，序号 `（4）` |
| 数字字体 | Times New Roman |

## 流水线

```
Word 文档
  ↓ WordReader（提取段落、字体、图片）
  ↓ HeadingDetector（三种策略检测标题）
  ↓ 序号格式化（一、/（二）/3./（4））
  ↓ MarkdownWriter → .md 文件
  ↓ 用户检查编辑（Web UI 或外部编辑器）
  ↓ MarkdownReader
  ↓ WordWriter（应用 GB/T 9704 格式）
  ↓ 格式化 .docx
```

## License

MIT License

Copyright (c) 2026 Enigma_Soul. All rights reserved.
