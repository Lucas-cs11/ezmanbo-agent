# 研电赛技术论文 LaTeX 模板

面向 eZ-PLM 的电子元器件智能选型与风险评估 Agent 系统

## Overleaf 上传指南

1. 将整个 `latex-paper/` 目录打包为 `.zip`
2. 在 Overleaf 中创建新项目 → 上传 zip
3. 编译器选择 **XeLaTeX**
4. 主文档设为 `main.tex`

## 编译步骤

```bash
# 本地编译（需安装 TeX Live 或 MacTeX）
xelatex main.tex
bibtex main
xelatex main.tex
xelatex main.tex
```

## 文件结构

```
latex-paper/
├── main.tex                 # 主文档（封面/目录/摘要/正文/参考文献）
├── references.bib           # BibTeX 参考文献
├── figures/                 # 图片目录（架构图、截图放入此目录）
├── chapters/
│   ├── abstract-cn.tex      # 中文摘要
│   ├── abstract-en.tex      # 英文摘要
│   ├── chapter1.tex         # 第1章：作品难点与创新
│   ├── chapter2.tex         # 第2章：方案论证与设计
│   ├── chapter3.tex         # 第3章：原理分析与硬件电路图
│   ├── chapter4.tex         # 第4章：软件设计与流程
│   ├── chapter5.tex         # 第5章：系统测试与分析
│   └── chapter6.tex         # 第6章：总结
└── README.md                # 本文件
```

## 格式规范（对照研电赛模板）

| 要素 | 格式 | 实现 |
|------|------|------|
| 封面 | 比赛名称一号黑体，题目小二号黑体 | `\zihao{1}` `\zihao{-2}` |
| 目录 | 三号黑体居中，三级标题 | ctexbook 自动生成 |
| 章标题 | 黑体小二号18pt居中 | `\CTEXsetup[format={\centering\heiti\zihao{-2}}]{chapter}` |
| 节标题 | 黑体小三号14pt | `\CTEXsetup[format={\heiti\zihao{-3}}]{section}` |
| 正文 | 宋体小四号12pt，固定行距20pt | `\setlength{\baselineskip}{20pt}` |
| 页眉 | 竞赛名称 + 论文题目 | fancyhdr 双行居中 |
| 页码 | 正文从1开始 | `\pagenumbering{arabic}` |
| 图表编号 | 章内重新编号（图1-1、表2-1） | `\renewcommand{\thefigure}{\thechapter-\arabic{figure}}` |
| 脚注 | 页底连续编号 | `\footnote{}` |
| 参考文献 | 无数量要求 | gbt7714-2005 格式 |

## 待完善项

1. **封面信息**：将参赛单位、队伍名称、指导老师、队员姓名替换为实际信息
2. **架构图**：将 `figures/` 中的占位图替换为实际系统截图
3. **图表编号**：确认所有 `\ref{}` 引用正确
4. **页数检查**：全文约 6000-8000 字（当前各章总约 ~7500 字，含摘要）

## 协作建议

- 队长（陆杰）：负责第1/2/3/6章和第4章Agent/数据模型部分的撰写
- 队员：负责第4章Streamlit前端、第5章评测部分的补充
- 所有 `XXXXX` 占位符需替换为实际内容
