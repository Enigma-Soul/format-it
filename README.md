# format-it

将 Word 文档按 GB/T 9704 国家公文标准进行格式化。

## 功能

- 读取 Word 文档，自动检测标题级别（字体大小 / 序号格式 / 行内字数）
- 冲突标题由用户手动确认
- 自动格式化标题序号（`一、` / `（二）` / `3.` / `（4）`）
- 导出为 Markdown 供用户检查编辑
- 按公文标准回写为格式化 Word 文件（页边距、字体、字号、行距、缩进）

## 目录结构

```
format-it/
├── main.py          # 入口
├── libs/            # 核心库
│   ├── config.py            # TOML 配置（GB/T 9704 默认值）
│   ├── converter.py         # 主转换类，编排流水线
│   ├── heading_detector.py  # 标题检测 + 序号格式化
│   ├── word_reader.py       # Word 读取
│   ├── word_writer.py       # Word 写入
│   ├── md_writer.py         # Markdown 写入
│   ├── md_reader.py         # Markdown 读取
│   ├── user_interaction.py  # 用户交互接口
│   ├── tui.py               # TUI 组件（MultiSelect / Tabs）
│   ├── fonts.py             # 中文字体映射
│   └── models.py            # 数据模型
├── input/           # 放入待处理的 .docx 文件
├── output/          # 格式化后的 .docx 输出
├── tmp/             # 中间 .md 缓存
├── config.toml      # 自动生成的配置文件
└── format.txt       # GB/T 9704 公文标准参考
```

## 安装

需要 [uv](https://docs.astral.sh/uv/) 和 Python >= 3.12。

```bash
uv sync
```

## 使用

```bash
# 交互模式 — 选择 input/ 中的文件
uv run python main.py

# 处理指定文件
uv run python main.py input/report.docx

# 仅生成 Markdown（不回写 Word）
uv run python main.py input/report.docx --md-only

# 从 Markdown 直接生成 Word
uv run python main.py --from-md tmp/report.md

# 生成默认配置文件
uv run python main.py --init-config
```

## 配置

首次运行会自动生成 `config.toml`，包含 GB/T 9704 默认值：

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
  ↓ 冲突解决（用户确认）
  ↓ 序号格式化（一、/（二）/3./（4））
  ↓ MarkdownWriter → tmp/*.md
  ↓ 用户检查编辑
  ↓ MarkdownReader
  ↓ WordWriter（应用 GB/T 9704 格式）
  ↓ output/*.docx
```

## License

MIT License

Copyright (c) 2026 Enigma_Soul. All rights reserved.
