<div align="center">

<img src="docs/logo.svg" width="80" alt="format-it">

# format-it

**将 Word 公文一键格式化为 GB/T 9704 国家标准**

[![Python](https://img.shields.io/badge/python-3.12%2B-3776ab.svg)](pyproject.toml)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Release](https://img.shields.io/github/v/release/Enigma-Soul/format-it?include_prereleases)](https://github.com/Enigma-Soul/format-it/releases)

Word → Markdown 审校 → 规范 Word：先转换为可读的 Markdown 供人工检查修订，再按公文标准回写为格式化文档。

</div>

## 特性

- **标题自动检测**：综合字体大小、序号格式（`一、` / `（二）` / `3.` / `（4）`）、行内字数三种策略判定标题级别，并自动规范化序号
- **GB/T 9704 全要素回写**：页边距、字体字号、行距、缩进、奇偶页页码一次到位
- **Web UI 在线审校**：多文件标签页、拖拽上传、暗色模式、一键整理、`Ctrl + Enter` 快速生成
- **无交互命令行**：一条命令完成全流程，可接入批处理脚本
- **格式可配置**：TOML 配置文件，内置公文默认值，可按单位自定义

> [!TIP]
> 不想装 Python？到 [Releases](https://github.com/Enigma-Soul/format-it/releases) 下载免安装 zip（Windows，CI 自动构建），解压即用。

## 快速开始

需要 [uv](https://docs.astral.sh/uv/) 和 Python >= 3.12。

```bash
git clone https://github.com/Enigma-Soul/format-it.git
cd format-it
uv sync
uv run python main.py          # 打开 http://127.0.0.1:8000
```

Web UI 三步完成格式化：

1. 选择配置，拖入一个或多个 `.docx` 文件，点击 **转换为 Markdown**
2. 在编辑器中检查修订标题级别与正文（对照：`#` 总标题 · `##` 一级 · `###` 二级 · `####` 三级 · `#####` 四级）
3. 点击 **生成并下载**，得到符合标准的 `.docx`

> [!WARNING]
> `--public` 会监听所有网络接口，仅限可信内网使用，默认仅绑定本机。

## 命令行

```bash
uv run python cli.py input.docx               # 全流程自动
uv run python cli.py --md-only input.docx     # 仅 Word -> Markdown
uv run python cli.py --from-md edited.md      # 仅 Markdown -> Word
uv run python cli.py -c custom.toml in.docx   # 指定配置文件
uv run python cli.py --init-config            # 生成默认配置模板
```

服务端口与监听地址：

```bash
uv run python main.py --port 9000             # 自定义端口
uv run python main.py --public                # 监听 0.0.0.0
```

> [!NOTE]
> 转换得到的 Markdown 顶部有 `<!-- format-it-meta ... -->` JSON 块，用于回写时还原字体信息，请勿删除。Web UI 会自动剥离和回填；使用 `--from-md` 时需连同元数据一起保存。

## 配置

配置文件位于 [`configs/`](configs/)（TOML），首次使用可 `--init-config` 生成模板。默认值遵循 GB/T 9704：

| 项目 | 默认值 |
|------|--------|
| 纸张 | A4 (210mm × 297mm) |
| 页边距（上/下/左/右） | 37mm / 35mm / 28mm / 26mm |
| 标题字体 | 方正小标宋简体 22pt（2号） |
| 正文字体 | 仿宋_GB2312 16pt（3号） |
| 一级标题 | 黑体 16pt，序号 `一、` |
| 二级标题 | 楷体_GB2312 16pt，序号 `（二）` |
| 三级标题 | 仿宋_GB2312 16pt，序号 `3.` |
| 四级标题 | 仿宋_GB2312 16pt，序号 `（4）` |
| 版面 | 每行 28 字，每页 22 行，行距 28.9pt 固定值 |

## 工作原理

```
Word 文档
  ↓ WordReader       提取段落、字体、图片
  ↓ HeadingDetector  三策略检测标题，规范化序号
  ↓ MarkdownWriter   输出 .md（附字体元数据）
  ↓ 人工审校          Web UI 或任意编辑器
  ↓ MarkdownReader   还原结构与字体
  ↓ WordWriter       应用 GB/T 9704 格式
  → 格式化 .docx
```

数字与西文按公文惯例自动改用 Times New Roman，与中文分别设字体；表格以 Markdown 管道表中转，图片提取后按 156mm 版心宽度重新嵌入。

## 项目结构

```
format-it/
├── main.py               # Web UI 入口
├── cli.py                # 命令行入口（无交互）
├── libs/                 # 核心库
│   ├── config.py             # TOML 配置（GB/T 9704 默认值）
│   ├── converter.py          # 流水线编排
│   ├── heading_detector.py   # 标题检测 + 序号格式化
│   ├── word_reader.py        # Word 读取
│   ├── word_writer.py        # Word 写入
│   ├── md_writer.py          # Markdown 写入
│   ├── md_reader.py          # Markdown 读取
│   ├── user_interaction.py   # 交互抽象（自动/静默/打印）
│   ├── fonts.py              # 中文字体映射
│   └── models.py             # 数据模型
├── web/                  # Web UI（FastAPI + 原生前端）
│   ├── app.py                # 应用工厂
│   ├── routes.py             # API 路由
│   ├── sessions.py           # 会话管理（30 分钟过期）
│   └── static/               # index.html / css / js
├── configs/              # TOML 配置
└── .github/workflows/    # CI：版本号变更时自动打包发布
```
