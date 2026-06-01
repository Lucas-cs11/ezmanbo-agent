# 分支合并报告 — 2026-05-30

**仓库**：https://github.com/Lucas-cs11/ezplm-component-risk-agent  
**执行人**：陆杰  
**最终状态**：仅保留 `main` 分支，0 个远程 feature 分支，0 个日报文件

---

## 一、合并操作记录

| 分支名 | 领先提交 | 冲突 | 合并结果 |
|--------|:--------:|:----:|:--------:|
| `feature/backend/more-mock-data` | — | 无 | ✅ 上午已合并 |
| `feature/backend/api-integration` | 10 | main.py, mock_parts.json | ✅ 已合并 |
| `feature/frontend/eval-report` | 2 | main.py, eval_report.md | ✅ 已合并（保留主分支 main.py） |
| `feature/frontend/ui-v2` | 0 | — | ✅ 已包含于 eval-report |
| `feature/backend/api-data-enrichment` | 4 | 无 | ✅ 已合并（新增 mock 数据扩充脚本） |
| `feature/frontend/eval-report`（二次） | 2 | main.py | ✅ 已合并（保留主分支 main.py） |

所有已合并分支已从 GitHub 删除。

## 二、当前 main 分支状态

| 指标 | 数值 |
|------|------|
| 总提交数 | 50+ |
| Python 模块（app/） | 16 |
| Mock 数据条目 | 209→814→1237 条 |
| RAG 知识条目 | 29 |
| 远程分支 | **仅 main** |
| 日报文件 | **已全部删除** |

## 三、最近 12 次提交

| 提交 | 说明 |
|------|------|
| `68c34f6` | 删除过往报告文件 |
| `e0d58ed` | 新增 ldo_cases.jsonl |
| `c1c02c3` | 删除无关紧要的报告文件 |
| `c94fdcb` | 补充修改内容 |
| `c54d82d` | app/__init__.py |
| `600459a` | Mock 数据 814→1237 条（API 扩充） |
| `224b369` | Streamlit 端口修复 |
| `423a3aa` | 竞赛三场景 Demo |
| `80295b0` | USB-C PD 瓦特解析 |
| `a058181` | 车规硬过滤移除 |
| `482e52b` | Agent 幻觉检测 |
| `26ad164` | RAG 知识库 12→29 条 |

## 四、清理操作

| 操作 | 说明 |
|------|------|
| 删除远程分支 | 6 个 feature 分支已从 origin 删除 |
| 删除日报 | `docs/daily/2026-05-27.md`、`2026-05-28.md`、`2026-05-28.pdf` 已删除 |
| 删除日报目录 | `docs/daily/` 已移除 |
