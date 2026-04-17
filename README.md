# ai-knowledge-vault

`ai-knowledge-vault` 是一个面向 Obsidian + Claude Code 的本地优先 AI 知识库模板。  
它要解决的不是“记更多笔记”，而是把原始资料、结构化知识、检索问答和持续体检串成可积累的系统。

英文说明见 [README.en.md](./README.en.md)。

## 这是什么（2.0 定位）

这个仓库是你在个人 AI 知识库实践上的 **2.0 升级**：  
方法论上受 Andrej Karpathy 的个人知识库工作流启发，工程化上落地为可复用目录规范、CLI 命令和 Obsidian 可视化前端。

简化理解：

- 1.0：能用的个人流程和脚本
- 2.0：可复用的知识库模板 + 明确的输入/处理/输出闭环 + 持续健康检查机制

## 为什么值得用

- **更高检索效率**：先查索引和概念层，再按需读原文，降低大模型全量扫描成本。
- **更强可追溯性**：知识条目保留完整 `原始内容`，结论可以回溯到来源证据。
- **更可持续维护**：`compile/find/health/tidy` 让知识网络能持续进化，而不是越积越乱。

## 方法来源与本项目映射

Karpathy 提到的 `raw -> LLM compile wiki -> Q&A -> 输出回灌 -> health checks`，在本项目中对应为：

- `raw 数据收集` -> `knowledge/inbox/manual/pending/` 和 `knowledge/inbox/video/raw/`
- `LLM 编译 wiki` -> `python3 .claude/skills/kb/scripts/knowledge_ops.py compile`
- `Q&A against wiki` -> `python3 .claude/skills/kb/scripts/knowledge_ops.py find "query"`
- `输出回灌知识库` -> 查询/分析产物沉淀到 `knowledge/reports/`，并可继续纳入知识条目
- `linting / health checks` -> `python3 .claude/skills/kb/scripts/knowledge_ops.py health` 与 `tidy`

## 系统逻辑闭环

```mermaid
flowchart LR
    rawInput["RawInput: manualOrMedia"] --> ingest["Ingest: kbAddOrAddVideo"]
    ingest --> entries["Entries: knowledgeMd"]
    entries --> compile["Compile: knowledgeOpsCompile"]
    compile --> concepts["Concepts: knowledgeConcepts"]
    compile --> indexNode["Index: knowledge_index"]
    entries --> query["Query: knowledgeOpsFind"]
    concepts --> query
    query --> reports["Reports: knowledgeReports"]
    entries --> healthNode["Health: knowledgeOpsHealthOrTidy"]
    healthNode --> reports
```



三条常用流：

1. **入库流**：原始资料进入 `inbox`，形成 `knowledge/*.md` 知识条目
2. **编译流**：`compile` 生成概念层与索引，形成导航网络
3. **查询与体检流**：`find/health/tidy` 产出报告并反哺知识库质量

## 分层架构

- **内容层（Source of Truth）**：`knowledge/`
  - `knowledge/*.md`：时间线知识条目（原始内容 + 核心观点）
  - `knowledge/concepts/`：编译后的概念导航层
  - `knowledge/reports/`：查询报告与健康检查报告
- **自动化层（Automation）**：`.claude/skills/kb/`
  - `SKILL.md`：`/kb` 命令约定
  - `scripts/knowledge_ops.py`：`find/compile/health/tidy`
  - `scripts/video_ingest.py`：音视频入库与转写
- **消费层（Frontend & Agent）**：Obsidian + Claude Code
  - Obsidian 用于浏览、链接、可视化
  - Claude Code 负责增量维护和问答研究

## 5 分钟快速跑通（最小闭环）

### 1) 安装

```bash
git clone https://github.com/dingshuxin353/ai-knowledge-vault.git
cd ai-knowledge-vault
pip3 install -r requirements.txt
```

### 2) 准备一条待处理素材

把任意 Markdown 放到 `knowledge/inbox/manual/pending/`，或在 Claude Code 里使用 `/kb add`。
如果你已经批量放入了 `pending/`，可继续在 Claude Code 中执行 `/kb process-pending` 进行入库整理。

### 3) 编译概念层与索引

```bash
python3 .claude/skills/kb/scripts/knowledge_ops.py compile
```

### 4) 做一次查询并沉淀报告

```bash
python3 .claude/skills/kb/scripts/knowledge_ops.py find "你的主题关键词"
```

### 5) 做一次健康检查

```bash
python3 .claude/skills/kb/scripts/knowledge_ops.py health
```

你应当看到的产物：

- 知识条目：`knowledge/*.md`
- 概念层：`knowledge/concepts/*.md`
- 索引入口：`knowledge/_index.md`
- 报告输出：`knowledge/reports/*.md`

## 两层检索机制（为什么它在小中规模很实用）

- 第一层：读取 `knowledge/_index.md` + `knowledge/concepts/*.md`，先定位主题和范围
- 第二层：按需展开具体条目的 `## 原始内容`，只在必要时读取细节证据

这种分层可以在不引入复杂 RAG 工程的前提下，在个人知识库规模内保持较好的查询质量与响应效率。

## 目录地图（关键部分）

```text
knowledge/
  _index.md
  concepts/
  reports/
  inbox/
    manual/
      pending/
      processed/
      review/
    video/
      raw/
      transcripts/
      logs/
.claude/skills/kb/
docs/
```

说明：本仓库是模板形态，`knowledge/concepts/` 的完整内容通常由你运行 `compile` 后逐步生成。

## 可选能力：视频/音频转写

需要：

- `pip3 install dashscope`
- 已安装 `ffmpeg` 与 `ffprobe`
- 配置 `.claude/skills/kb/config.local.json`（或 `DASHSCOPE_API_KEY`）

运行：

```bash
python3 .claude/skills/kb/scripts/video_ingest.py
```

更多细节见 [`docs/video-transcription.md`](./docs/video-transcription.md)。

## 适合谁 / 不适合谁

适合：

- 想把长期研究资料沉淀为可被 AI 持续操作的知识系统
- 想在本地 Markdown 上构建可迁移、可追溯的个人 wiki
- 想让每次问答结果都“累积进知识库”而非一次性对话

不适合：

- 只需要临时笔记，不需要结构化维护
- 期望零配置云托管 SaaS 体验，不想维护本地文件与脚本

## 文档入口

- 架构说明：[`docs/architecture.md`](./docs/architecture.md)
- 安装指南：[`docs/installation.md`](./docs/installation.md)
- 视频转写说明：[`docs/video-transcription.md`](./docs/video-transcription.md)
- 概念层目录说明：[`knowledge/concepts/README.md`](./knowledge/concepts/README.md)
- 报告目录说明：[`knowledge/reports/README.md`](./knowledge/reports/README.md)
- 手动入库目录说明：[`knowledge/inbox/manual/README.md`](./knowledge/inbox/manual/README.md)
- 视频入库目录说明：[`knowledge/inbox/video/README.md`](./knowledge/inbox/video/README.md)

## 下一步建议

- 先放 5-10 篇原始材料到 `knowledge/inbox/manual/pending/`
- 跑一次 `compile + find + health` 看概念层和报告如何联动
- 根据你的研究主题扩展 `.claude/skills/kb/scripts/` 的处理策略

## 开源许可

MIT License