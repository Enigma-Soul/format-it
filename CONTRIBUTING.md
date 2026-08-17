# 贡献指南

感谢参与 format-it!提交前请阅读以下约定。

## 开发环境

需要 [uv](https://docs.astral.sh/uv/) 与 Python >= 3.12:

```bash
uv sync
uv run python main.py        # 启动 Web UI 调试
```

## 分支与合并

- **禁止直接向 `main` 提交,禁止强制推送(force push)`main`**
- **`main` 只能通过 `develop -> main` 的 Pull Request 更新**,合并后 CI 自动打包发版
- 功能 / 修复在 `feat/*`、`fix/*` 等分支开发,先合入 `develop` 验证,再由 `develop` 统一发 PR 到 `main`

## 代码风格

统一使用 [ruff](https://docs.astral.sh/ruff/) 格式化与检查,配置见 `pyproject.toml` 的 `[tool.ruff]`:

```bash
uv run ruff format .
uv run ruff check --fix .
```

提交前保证两条命令均无改动、无告警。

## 版本与更新日志

每次合并到 `develop`(即每个 PR)必须:

1. **更新 [CHANGELOG.md](CHANGELOG.md)**:为本次变更对应的版本新增条目,按 `### Feat / Fix / Chore(范围)` 分组
2. **更新 `pyproject.toml` 的 `version`**:按语义化版本递增 -- 破坏性变更升主版本,新功能升次版本,修复升修订版本

> [!IMPORTANT]
> CI 发版完全依赖这两处:`pyproject.toml` 的版本号决定 tag(vX.Y.Z),CHANGELOG 对应版本条目作为 Release 说明。缺少条目时 Release 说明将为空。

## 提交信息

约定式提交(`feat` / `fix` / `docs` / `refactor` / `chore` / `ci`),一行简述,例如:`feat: 支持多文件标签页`。
