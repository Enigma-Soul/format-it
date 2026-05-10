from __future__ import annotations

import argparse
from pathlib import Path

from libs.config import FormatConfig
from libs.converter import FormatConverter
from libs.user_interaction import TUIUserInteraction


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="format-it",
        description="将 Word 文档按 GB/T 9704 国家公文标准进行格式化",
    )
    parser.add_argument(
        "input_file",
        nargs="?",
        type=Path,
        help="输入 .docx 文件路径（留空则列出 input/ 中的文件）",
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=None,
        help="输出 .docx 路径（默认: output/{输入名}_formatted.docx）",
    )
    parser.add_argument(
        "-c", "--config",
        type=Path,
        default=Path("config.toml"),
        help="配置文件路径（默认: config.toml）",
    )
    parser.add_argument(
        "--init-config",
        action="store_true",
        help="生成默认配置文件并退出",
    )
    parser.add_argument(
        "--md-only",
        action="store_true",
        help="仅转换为 Markdown，跳过 Word 生成",
    )
    parser.add_argument(
        "--from-md",
        type=Path,
        default=None,
        help="直接从 Markdown 文件转换为 Word",
    )

    # Ensure required directories exist
    for d in (Path("input"), Path("output"), Path("tmp")):
        d.mkdir(parents=True, exist_ok=True)

    args = parser.parse_args()

    if args.init_config:
        config = FormatConfig.defaults()
        config.to_toml(args.config)
        print(f"默认配置已写入: {args.config}")
        return

    config = FormatConfig.from_toml(args.config)
    ui = TUIUserInteraction()
    converter = FormatConverter(config, ui)

    if args.from_md:
        md_path = args.from_md
        output_path = args.output or config.output_dir / f"{md_path.stem}_formatted.docx"
        converter.convert_markdown_to_word(md_path, output_path)
    elif args.input_file:
        input_path = args.input_file
        if args.md_only:
            converter.convert_word_to_markdown(input_path)
        else:
            converter.run_full_pipeline(input_path)
    else:
        converter.run_interactive()


if __name__ == "__main__":
    main()
