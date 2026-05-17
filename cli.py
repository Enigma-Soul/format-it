from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from libs.config import FormatConfig, _DEFAULTS_PATH
from libs.converter import FormatConverter
from libs.user_interaction import PrintUserInteraction

CONFIGS_DIR = Path("configs")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="format-it-cli",
        description="格式化公文工具 — 命令行（无交互，自动处理）",
    )
    parser.add_argument(
        "input_file",
        nargs="?",
        type=Path,
        help="输入 .docx 文件路径",
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
        default=None,
        help="配置文件路径（默认: configs/default.toml）",
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

    for d in (Path("input"), Path("output"), Path("tmp"), CONFIGS_DIR):
        d.mkdir(parents=True, exist_ok=True)

    args = parser.parse_args()

    if args.init_config:
        target = args.config or CONFIGS_DIR / "default.toml"
        shutil.copy2(_DEFAULTS_PATH, target)
        print(f"默认配置已写入: {target}")
        return

    ui = PrintUserInteraction()
    config_path = _resolve_config(args.config)
    config = FormatConfig.from_toml(config_path)
    ui.display_progress(f"使用配置: {config.name} — {config.description}")
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
        print("请指定输入文件。使用 --help 查看帮助。")
        raise SystemExit(1)


def _resolve_config(config_path: Path | None) -> Path:
    if config_path is not None:
        return config_path
    toml_files = sorted(CONFIGS_DIR.glob("*.toml"))
    if not toml_files:
        print("configs/ 目录下没有配置文件，请使用 --init-config 生成")
        raise SystemExit(1)
    return toml_files[0]


if __name__ == "__main__":
    main()
