# ai-knowledge-vault

`ai-knowledge-vault` 是一个面向 Obsidian 和 Claude Code 的本地优先知识库模板。

它的目标不是“多记几篇笔记”，而是让知识条目、概念页、查询报告和待处理素材形成一套可持续维护、可被 AI 直接利用的文件系统。

## 适合谁

- 想用 Obsidian 管理长期知识的人
- 想让 Claude Code 直接使用知识库的人
- 想把“收藏内容”整理成可复用知识网络的人
- 想保留原始材料，同时让 AI 参与编译和体检的人

## 核心能力

- `knowledge/_index.md` 作为主索引入口
- `knowledge/concepts/` 作为概念导航层
- `knowledge/reports/` 沉淀查询结果与健康检查
- `knowledge/inbox/manual/` 处理手动收集的待入库材料
- `knowledge/inbox/video/` 处理视频或音频转写素材
- `.claude/skills/kb/` 提供 Claude Code 可调用的知识库技能

## 推荐工作流

1. 把原始内容放进 `knowledge/inbox/manual/pending/`，或用 `/kb add` 直接收录。
2. 用 `/kb process-pending` 或人工整理，生成规范知识条目。
3. 运行 `/kb compile`，把时间线条目编译成概念页和 related 链接。
4. 用 `/kb find` 检索知识，并把重要查询沉淀到 `reports/`。
5. 定期运行 `/kb health` 与 `/kb tidy`，检查知识库结构质量。

## 两层检索机制

这个项目默认采用“两层检索”：

- 第一层：读取 `knowledge/_index.md` 和 `knowledge/concepts/*.md`
  这里解决“去哪里找”和“主题范围是什么”
- 第二层：按需打开具体知识条目的 `## 原始内容`
  这里解决“细节证据是什么”

这样做的好处是：

- 减少 AI 每次全量扫描全文的成本
- 让概念导航与原始材料分层管理
- 保留完整来源，同时又方便快速检索

## 安装方式

### 作为 Obsidian 知识库

直接用 Obsidian 打开本仓库即可。

### 作为 Claude Code skill

将 `.claude/skills/kb/` 复制或链接到你的 Claude Code skills 目录，然后在会话中使用 `/kb ...`。

## 视频转写

可选开启。需要：

- `pip3 install dashscope`
- 安装 `ffmpeg`
- 配置 `.claude/skills/kb/config.local.json`

配置完成后，可使用：

```bash
python3 .claude/skills/kb/scripts/video_ingest.py
```

## 文档

- 架构说明：`docs/architecture.md`
- 安装指南：`docs/installation.md`
- 视频转写说明：`docs/video-transcription.md`

## 开源许可

MIT License
