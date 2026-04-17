#!/usr/bin/env python3
"""Knowledge base maintenance utilities for ai-knowledge-vault."""

from __future__ import annotations

import argparse
import os
import re
from collections import Counter, OrderedDict, defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import yaml


def _find_repo_root() -> Path:
    current = Path(__file__).resolve().parent
    for _ in range(10):
        if (current / "knowledge").is_dir():
            return current
        current = current.parent

    env_root = os.environ.get("KB_ROOT")
    if env_root:
        return Path(env_root).expanduser().resolve()

    raise RuntimeError(
        "无法定位仓库根目录。请确保父目录中存在 knowledge/，或设置 KB_ROOT 环境变量。"
    )


REPO_ROOT = _find_repo_root()
KNOWLEDGE_DIR = REPO_ROOT / "knowledge"
CONCEPTS_DIR = KNOWLEDGE_DIR / "concepts"
REPORTS_DIR = KNOWLEDGE_DIR / "reports"
PROCESSED_DIR = KNOWLEDGE_DIR / "inbox" / "manual" / "processed"
KB_SKILL_DIR = REPO_ROOT / ".claude" / "skills" / "kb"
CONTROL_FILES = {"CLAUDE.md", "AGENTS.md", "_index.md"}
SECTION_PATTERN = r"(^##\s*{name}\s*\n)([\s\S]*?)(?=^##\s+|\Z)"
RAW_LINK_ONLY_RE = re.compile(
    r"^\s*>\s*原文见：\[\[(?P<target>[^\]]+)\]\]\s*$",
    flags=re.MULTILINE,
)
YEAR_PREFIX_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-")
GENERIC_GAP_TAGS = {
    "AI学习",
    "工作流",
    "Agent",
    "Claude Code",
    "Obsidian",
    "第二大脑",
}
TAG_ALIASES = {
    "Prompt": "Prompt Engineering",
    "Skills": "Claude Code Skills",
    "skill": "Claude Code Skills",
}


@dataclass
class ConceptSpec:
    name: str
    aliases: list[str]
    keywords: list[str]
    tags: list[str]
    definition: str
    open_question: str
    related_concepts: list[str]


CONCEPT_SPECS = [
    ConceptSpec(
        name="第二大脑",
        aliases=["Second Brain", "知识操作系统", "Memory Stack"],
        keywords=["第二大脑", "knowledge base", "memory stack", "知识操作系统"],
        tags=["第二大脑"],
        definition="把知识、任务与产出沉淀为可被 AI 长期读取、更新和复用的文件系统，而不是一次性聊天记录。",
        open_question="哪些高频查询最值得沉淀成 reports/，让知识库真正形成复利？",
        related_concepts=["Obsidian知识管理", "Agent记忆架构", "个人AI操作系统"],
    ),
    ConceptSpec(
        name="上下文工程",
        aliases=["Context Engineering", "上下文管理"],
        keywords=["上下文", "context engineering", "context", "CLAUDE.md", "about-me"],
        tags=["Context Engineering", "上下文"],
        definition="围绕选择、组织、压缩和治理上下文的系统化方法，目标是让模型在有限窗口内读到最对的材料。",
        open_question="目前哪些上下文仍停留在隐性经验，没有被编译成稳定文件？",
        related_concepts=["Agent记忆架构", "Claude协作工作流", "Claude Code Skills"],
    ),
    ConceptSpec(
        name="Agent记忆架构",
        aliases=["Agent Memory", "Memory Architecture"],
        keywords=["记忆", "memory", "长期事实", "RAG", "三层记忆"],
        tags=["RAG"],
        definition="把当前上下文、长期事实、近期脉络和历史案例拆成不同层级，分别用匹配的存储与读取策略管理。",
        open_question="哪些信息应继续结构化存储，哪些更适合摘要或语义检索？",
        related_concepts=["上下文工程", "第二大脑", "OpenClaw与Agent编排"],
    ),
    ConceptSpec(
        name="Claude Code Skills",
        aliases=["Skills", "Agent Skills"],
        keywords=["skills", "skill", "SKILL.md", "技能"],
        tags=["Skills", "技能"],
        definition="把可复用工作流封装成目录化技能，连同脚本、素材和约束一起交给 Agent 按需执行。",
        open_question="哪些重复出现的知识整理动作应该继续沉淀成新 skill，而不是留在临时对话里？",
        related_concepts=["Claude协作工作流", "上下文工程", "第二大脑"],
    ),
    ConceptSpec(
        name="Obsidian知识管理",
        aliases=["Obsidian PKM", "Vault Workflow"],
        keywords=["obsidian", "vault", "bases", "markdown", "图谱"],
        tags=["Obsidian"],
        definition="以 Obsidian 作为本地优先的知识底座，用链接、属性和视图把静态 Markdown 组织成可导航的知识网络。",
        open_question="除了 concepts/ 之外，哪些导航层最值得补成 Bases 或 Dataview 视图？",
        related_concepts=["第二大脑", "上下文工程", "Claude协作工作流"],
    ),
    ConceptSpec(
        name="Claude协作工作流",
        aliases=["Claude Cowork", "AI 协作"],
        keywords=["cowork", "思维搭档", "协作", "workflow", "工作流"],
        tags=["工作流"],
        definition="把 Claude 从一次性问答工具变成长期协作者，关键在于先提供稳定上下文，再围绕任务持续迭代。",
        open_question="哪些启动提示和协作约束已经稳定，适合固化为团队通用模板？",
        related_concepts=["上下文工程", "Claude Code Skills", "个人AI操作系统"],
    ),
    ConceptSpec(
        name="个人AI操作系统",
        aliases=["Personal OS", "Hyper-personalization"],
        keywords=["personal os", "个人os", "hyper-personalization", "USER.md", "family/"],
        tags=["个人OS", "个人助手"],
        definition="围绕个人生活与工作的长期上下文，把 AI 配置成真正了解你、能持续执行日常流程的操作系统。",
        open_question="个人上下文与知识条目之间，哪些内容应该共享，哪些必须隔离？",
        related_concepts=["第二大脑", "Claude协作工作流", "OpenClaw与Agent编排"],
    ),
    ConceptSpec(
        name="OpenClaw与Agent编排",
        aliases=["OpenClaw", "Agent Orchestration"],
        keywords=["openclaw", "gateway", "cli", "编排", "orchestr"],
        tags=["OpenClaw", "CLI"],
        definition="围绕多 Agent 的连接、调度和执行，把上下文、工具和外部系统编排成可持续运转的自动化流程。",
        open_question="哪些 OpenClaw 经验已经上升为通用编排原则，值得抽象到概念层？",
        related_concepts=["Agent记忆架构", "个人AI操作系统", "Claude Code Skills"],
    ),
]


@dataclass
class Entry:
    path: Path
    metadata: OrderedDict[str, Any]
    body: str
    title: str
    summary: str
    raw_content: str
    concepts: list[str]

    @property
    def date(self) -> str:
        return str(self.metadata.get("date", "1970-01-01"))

    @property
    def tags(self) -> list[str]:
        tags = self.metadata.get("tags") or []
        return [str(tag) for tag in tags]

    @property
    def source(self) -> str:
        return str(self.metadata.get("source", "未知来源"))

    @property
    def confidence(self) -> str:
        return str(self.metadata.get("confidence", "processed"))

    @property
    def source_type(self) -> str:
        return str(self.metadata.get("source_type", ""))


def split_frontmatter(text: str) -> tuple[OrderedDict[str, Any], str]:
    match = re.match(r"^---\n(.*?)\n---\n?", text, flags=re.DOTALL)
    if not match:
        return OrderedDict(), text
    frontmatter_raw = match.group(1)
    body = text[match.end() :]
    data = yaml.safe_load(frontmatter_raw) or {}
    if not isinstance(data, dict):
        data = {}
    ordered = OrderedDict()
    for key, value in data.items():
        ordered[str(key)] = value
    return ordered, body


def dump_frontmatter(metadata: OrderedDict[str, Any]) -> str:
    ordered = OrderedDict()
    preferred_keys = [
        "date",
        "source",
        "source_type",
        "source_url",
        "author",
        "tags",
        "concepts",
        "related",
        "confidence",
    ]
    for key in preferred_keys:
        if key in metadata:
            ordered[key] = metadata[key]
    for key, value in metadata.items():
        if key not in ordered:
            ordered[key] = value
    rendered = yaml.safe_dump(
        dict(ordered),
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
        width=1000,
    ).strip()
    return f"---\n{rendered}\n---\n"


def replace_frontmatter(text: str, metadata: OrderedDict[str, Any]) -> str:
    fm, body = split_frontmatter(text)
    del fm  # only used to confirm there is frontmatter
    return dump_frontmatter(metadata) + body.lstrip("\n")


def section_regex(name: str) -> re.Pattern[str]:
    return re.compile(SECTION_PATTERN.format(name=re.escape(name)), flags=re.MULTILINE)


def get_section(body: str, name: str) -> str:
    match = section_regex(name).search(body)
    if not match:
        return ""
    return match.group(2).strip()


def replace_section(body: str, name: str, new_content: str) -> str:
    pattern = section_regex(name)
    match = pattern.search(body)
    replacement = f"## {name}\n{new_content.strip()}\n"
    if not match:
        trimmed = body.rstrip()
        spacer = "\n\n" if trimmed else ""
        return f"{trimmed}{spacer}{replacement}\n"
    start, end = match.span()
    return f"{body[:start]}{replacement}\n{body[end:]}".rstrip() + "\n"


def extract_title(body: str, fallback: str) -> str:
    match = re.search(r"^#\s+(.+)$", body, flags=re.MULTILINE)
    return match.group(1).strip() if match else fallback


def summarize_core_points(body: str) -> str:
    core = get_section(body, "核心观点")
    if not core:
        return "（待当前Agent提炼）"
    bullet_points: list[str] = []
    for line in core.splitlines():
        match = re.match(r"^\s*(?:[-*]|\d+\.)\s*(.+?)\s*$", line)
        if match:
            bullet_points.append(match.group(1).strip())
    summary = bullet_points[0] if bullet_points else re.sub(r"\s+", " ", core).strip()
    summary = clean_summary_text(summary)
    return summary[:180] + ("…" if len(summary) > 180 else "")


def clean_summary_text(text: str) -> str:
    cleaned = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", text)
    cleaned = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", cleaned)
    cleaned = re.sub(r"`([^`]+)`", r"\1", cleaned)
    cleaned = cleaned.replace("**", "").replace("*", "")
    cleaned = re.sub(r"^#+\s*", "", cleaned)
    cleaned = re.sub(r"^\d+\.\s*", "", cleaned)
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip(" -–—•")


def list_entry_paths() -> list[Path]:
    paths = []
    for path in sorted(KNOWLEDGE_DIR.glob("*.md")):
        if path.name in CONTROL_FILES or path.name.startswith("."):
            continue
        if not YEAR_PREFIX_RE.match(path.name):
            continue
        paths.append(path)
    return paths


def load_entries() -> list[Entry]:
    entries: list[Entry] = []
    for path in list_entry_paths():
        text = path.read_text(encoding="utf-8")
        metadata, body = split_frontmatter(text)
        title = extract_title(body, path.stem)
        entries.append(
            Entry(
                path=path,
                metadata=metadata,
                body=body,
                title=title,
                summary=summarize_core_points(body),
                raw_content=get_section(body, "原始内容"),
                concepts=[],
            )
        )
    entries.sort(key=lambda entry: (entry.date, entry.path.name), reverse=True)
    return entries


def update_entry_metadata(path: Path, updates: dict[str, Any]) -> None:
    original_text = path.read_text(encoding="utf-8")
    metadata, _ = split_frontmatter(original_text)
    for key, value in updates.items():
        metadata[key] = value
    path.write_text(replace_frontmatter(original_text, metadata), encoding="utf-8")


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().lower()


def slugify_text(value: str) -> str:
    slug = re.sub(r"[^\w\u4e00-\u9fff-]+", "-", value, flags=re.UNICODE)
    slug = re.sub(r"-{2,}", "-", slug).strip("-")
    return slug or "report"


def tokenize_query(query: str) -> list[str]:
    parts = re.split(r"[\s,，、/]+", query.strip())
    return [part.lower() for part in parts if part.strip()]


def query_terms(query: str) -> list[str]:
    base_terms = tokenize_query(query)
    collapsed = re.sub(r"[\s,，、/]+", "", query.strip().lower())
    extra_terms: list[str] = []
    if collapsed and collapsed not in base_terms:
        extra_terms.append(collapsed)
    if len(collapsed) >= 2:
        extra_terms.extend(collapsed[i : i + 2] for i in range(len(collapsed) - 1))
    if len(collapsed) >= 3:
        extra_terms.extend(collapsed[i : i + 3] for i in range(len(collapsed) - 2))
    ordered = []
    seen = set()
    for term in [*base_terms, *extra_terms]:
        term = term.strip()
        if not term or term in seen:
            continue
        seen.add(term)
        ordered.append(term)
    return ordered


def concept_search_text(spec: ConceptSpec) -> str:
    concept_path = CONCEPTS_DIR / f"{spec.name}.md"
    if concept_path.exists():
        return normalize_text(concept_path.read_text(encoding="utf-8"))
    return normalize_text(" ".join([spec.name, *spec.aliases, *spec.keywords, spec.definition, spec.open_question]))


def normalize_tags(tags: list[str]) -> list[str]:
    normalized = []
    seen = set()
    for tag in tags:
        mapped = TAG_ALIASES.get(tag, tag)
        if mapped in seen:
            continue
        seen.add(mapped)
        normalized.append(mapped)
    return normalized


def entry_search_text(entry: Entry) -> str:
    parts = [entry.title, entry.summary, " ".join(entry.tags)]
    core = get_section(entry.body, "核心观点")
    if core:
        parts.append(core)
    return normalize_text(" ".join(parts))


def detect_concepts(entries: list[Entry]) -> dict[str, list[Entry]]:
    concept_map: dict[str, list[Entry]] = defaultdict(list)
    for entry in entries:
        text = entry_search_text(entry)
        entry.concepts = []
        for spec in CONCEPT_SPECS:
            tag_hit = any(tag in entry.tags for tag in spec.tags)
            keyword_hit = any(keyword.lower() in text for keyword in spec.keywords)
            if tag_hit or keyword_hit:
                concept_map[spec.name].append(entry)
                entry.concepts.append(spec.name)
    return concept_map


def peer_related_links(entry: Entry, entries: list[Entry]) -> list[str]:
    scored: list[tuple[int, str, Entry]] = []
    for candidate in entries:
        if candidate.path == entry.path:
            continue
        concept_overlap = len(set(entry.concepts) & set(candidate.concepts))
        tag_overlap = len(set(entry.tags) & set(candidate.tags))
        if concept_overlap == 0 and tag_overlap == 0:
            continue
        score = concept_overlap * 3 + tag_overlap
        scored.append((score, candidate.date, candidate))
    scored.sort(key=lambda item: (item[0], item[1], item[2].path.name), reverse=True)
    links: list[str] = []
    for _, _, candidate in scored[:2]:
        links.append(f"[[{candidate.path.stem}]]")
    return links


def render_concept_page(spec: ConceptSpec, entries: list[Entry]) -> str:
    insights = []
    for entry in entries[:4]:
        insights.append(f"- {entry.summary}（来源：[[{entry.path.stem}]])")
    related = [f"- [[concepts/{name}]]" for name in spec.related_concepts if name != spec.name]
    representatives = [f"- [[{entry.path.stem}|{entry.title}]]" for entry in entries[:6]]
    lines = [
        "---",
        f"concept: {spec.name}",
        "aliases:",
    ]
    for alias in spec.aliases:
        lines.append(f"  - {alias}")
    lines += [
        "---",
        "",
        f"# {spec.name}",
        "",
        "## 定义",
        spec.definition,
        "",
        "## 关键洞见",
        *(insights or ["- 待补充。"]),
        "",
        "## 代表条目",
        *(representatives or ["- 待补充。"]),
        "",
        "## 相关概念",
        *(related or ["- 待补充。"]),
        "",
        "## 开放问题",
        f"- {spec.open_question}",
        "",
        "## Dataview",
        "```dataview",
        "TABLE date, source, tags, confidence",
        'FROM "knowledge"',
        'WHERE file.folder = "knowledge" AND contains(concepts, this.file.link)',
        "SORT date DESC",
        "```",
        "",
    ]
    return "\n".join(lines)


def rebuild_index(entries: list[Entry], concept_map: dict[str, list[Entry]]) -> None:
    lines = [
        "# 知识库索引",
        "",
        f"> 最后更新：{date.today().isoformat()} | 条目数：{len(entries)} | 概念页数：{len([name for name, items in concept_map.items() if items])}",
        "> 检索入口：优先从概念页进入，再按需打开具体知识条目的 `原始内容`。",
        "",
        "## 概念导航",
        "",
    ]
    for spec in CONCEPT_SPECS:
        matched = concept_map.get(spec.name, [])
        if not matched:
            continue
        lines.append(f"### {spec.name}")
        lines.append(
            f"- [[concepts/{spec.name}|{spec.name}]]"
            f"（关联 {len(matched)} 条，别名：{', '.join(spec.aliases[:2])}）"
        )
        lines.append(f"- 聚焦主题：{spec.definition}")
        lines.append("")
    lines += [
        "## 最近收录",
        "",
        "| 日期 | 标题 | 来源 | 关联概念 | 摘要 |",
        "|------|------|------|----------|------|",
    ]
    for entry in entries[:50]:
        concepts = ", ".join(entry.concepts) if entry.concepts else "待归类"
        lines.append(
            f"| {entry.date} | {entry.title.replace('|', '\\|')} | {entry.source.replace('|', '\\|')} | "
            f"{concepts.replace('|', '\\|')} | {entry.summary.replace('|', '\\|')} |"
        )
    INDEX_PATH = KNOWLEDGE_DIR / "_index.md"
    INDEX_PATH.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def strip_processed_frontmatter(text: str) -> str:
    _, body = split_frontmatter(text)
    return body.strip() if body.strip() else text.strip()


def processed_lookup() -> dict[str, Path]:
    return {path.stem: path for path in PROCESSED_DIR.glob("*.md")}


def resolve_processed_path(target: str, lookup: dict[str, Path]) -> Path | None:
    normalized = target.strip().removesuffix(".md")
    direct = REPO_ROOT / f"{normalized}.md"
    if direct.exists():
        return direct
    alt = normalized.replace("/pending/", "/processed/")
    direct_alt = REPO_ROOT / f"{alt}.md"
    if direct_alt.exists():
        return direct_alt
    stem = Path(normalized).name
    return lookup.get(stem)


def repair_link_only_entries() -> list[Path]:
    lookup = processed_lookup()
    changed: list[Path] = []
    for path in list_entry_paths():
        text = path.read_text(encoding="utf-8")
        _, body = split_frontmatter(text)
        raw_section = get_section(body, "原始内容")
        match = RAW_LINK_ONLY_RE.match(raw_section.strip())
        if not match:
            continue
        source_path = resolve_processed_path(match.group("target"), lookup)
        if source_path is None:
            continue
        processed_body = strip_processed_frontmatter(source_path.read_text(encoding="utf-8"))
        updated_body = replace_section(body, "原始内容", processed_body)
        path.write_text(dump_frontmatter(split_frontmatter(text)[0]) + updated_body.lstrip("\n"), encoding="utf-8")
        changed.append(path)
    return changed


def tidy_entries() -> list[Path]:
    changed: list[Path] = []
    for path in list_entry_paths():
        original_text = path.read_text(encoding="utf-8")
        metadata, _ = split_frontmatter(original_text)
        tags = metadata.get("tags") or []
        if not isinstance(tags, list):
            continue
        normalized_tags = normalize_tags([str(tag) for tag in tags])
        if normalized_tags != [str(tag) for tag in tags]:
            metadata["tags"] = normalized_tags
            path.write_text(replace_frontmatter(original_text, metadata), encoding="utf-8")
            changed.append(path)
    return changed


def compile_concepts(write_related: bool = True) -> tuple[list[Entry], dict[str, list[Entry]]]:
    entries = load_entries()
    concept_map = detect_concepts(entries)
    CONCEPTS_DIR.mkdir(parents=True, exist_ok=True)
    for spec in CONCEPT_SPECS:
        matched = concept_map.get(spec.name, [])
        if not matched:
            continue
        concept_path = CONCEPTS_DIR / f"{spec.name}.md"
        concept_path.write_text(render_concept_page(spec, matched), encoding="utf-8")

    if write_related:
        for entry in entries:
            metadata = OrderedDict(entry.metadata)
            metadata["concepts"] = [f"[[concepts/{concept}]]" for concept in entry.concepts]
            related = [f"[[concepts/{concept}]]" for concept in entry.concepts]
            related.extend(peer_related_links(entry, entries))
            deduped = []
            seen = set()
            for item in related:
                if item in seen:
                    continue
                seen.add(item)
                deduped.append(item)
            metadata["related"] = deduped
            original_text = entry.path.read_text(encoding="utf-8")
            entry.path.write_text(replace_frontmatter(original_text, metadata), encoding="utf-8")

    entries = load_entries()
    concept_map = detect_concepts(entries)
    rebuild_index(entries, concept_map)
    return entries, concept_map


def search_entries(query: str, entries: list[Entry], concept_map: dict[str, list[Entry]], limit: int = 8) -> tuple[list[Entry], list[str]]:
    terms = query_terms(query)
    if not terms:
        return [], []
    scores: list[tuple[int, Entry]] = []
    concept_scores: dict[str, int] = {}
    for spec in CONCEPT_SPECS:
        haystack = concept_search_text(spec)
        score = 0
        for term in terms:
            if term in normalize_text(spec.name):
                score += 8
            if term in haystack:
                score += 3 if len(term) >= 3 else 1
        if score:
            concept_scores[spec.name] = score

    concept_hits = [
        name
        for name, _ in sorted(
            concept_scores.items(),
            key=lambda item: (item[1], item[0]),
            reverse=True,
        )
    ]

    for entry in entries:
        haystack = normalize_text(" ".join([entry_search_text(entry), entry.raw_content[:3000]]))
        score = 0
        for term in terms:
            if term in normalize_text(entry.title):
                score += 6
            if term in normalize_text(" ".join(entry.tags)):
                score += 4
            if any(term in normalize_text(concept) for concept in entry.concepts):
                score += 5
            if term in normalize_text(entry.summary):
                score += 4
            if term in haystack:
                score += 2 if len(term) >= 3 else 1
        for concept in entry.concepts:
            score += concept_scores.get(concept, 0) * 2
        if score:
            scores.append((score, entry))
    scores.sort(key=lambda item: (item[0], item[1].date, item[1].path.name), reverse=True)
    matched_entries = [entry for _, entry in scores[:limit]]

    if not matched_entries and concept_hits:
        bridge_entries: list[Entry] = []
        seen_paths = set()
        for concept in concept_hits[:3]:
            for entry in concept_map.get(concept, [])[:3]:
                if entry.path in seen_paths:
                    continue
                seen_paths.add(entry.path)
                bridge_entries.append(entry)
        matched_entries = bridge_entries[:limit]

    return matched_entries, list(OrderedDict.fromkeys(concept_hits[:5]))


def create_query_report(query: str, matched_entries: list[Entry], matched_concepts: list[str]) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS_DIR / f"{date.today().isoformat()}-{slugify_text(query)}.md"
    lines = [
        "# Knowledge Query Report",
        "",
        f"> 查询：{query}",
        f"> 生成日期：{date.today().isoformat()}",
        "",
        "## 命中概念",
    ]
    if matched_concepts:
        lines.extend(f"- [[concepts/{concept}|{concept}]]" for concept in matched_concepts)
    else:
        lines.append("- 暂无明确概念命中。")
    lines += [
        "",
        "## 命中条目",
    ]
    if matched_entries:
        for entry in matched_entries:
            lines.append(
                f"- [[{entry.path.stem}|{entry.title}]]"
                f" `来源: {entry.source}` `概念: {', '.join(entry.concepts) or '待归类'}`"
            )
    else:
        lines.append("- 暂无命中条目。")

    lines += [
        "",
        "## 组合判断",
    ]
    if matched_entries:
        if matched_concepts:
            lines.append(f"- 这个主题当前主要由 `{ ' + '.join(matched_concepts[:3]) }` 这几层知识组合支撑。")
        lines.append("- 以下命中不要求条目标题直接等于查询词，只要它们能共同回答这个主题，就会被纳入。")
    else:
        lines.append("- 当前知识库里还没有足够材料支撑这个主题。")

    lines += [
        "",
        "## 关键观点",
    ]
    if matched_entries:
        for entry in matched_entries[:5]:
            lines.append(f"- {entry.summary}（来源：[[{entry.path.stem}]])")
    else:
        lines.append("- 暂无可提炼观点。")

    lines += [
        "",
        "## 建议延伸阅读",
    ]
    if matched_entries:
        seen = set()
        suggestions = []
        for entry in matched_entries:
            for related in entry.metadata.get("related", []) or []:
                related_str = str(related)
                if related_str in seen or related_str.startswith("[[reports/"):
                    continue
                seen.add(related_str)
                suggestions.append(f"- {related_str}")
        lines.extend(suggestions[:8] or ["- 暂无。"])
    else:
        lines.append("- 暂无。")

    report_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return report_path


def create_health_report(entries: list[Entry], concept_map: dict[str, list[Entry]]) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    report_path = REPORTS_DIR / f"{today}-knowledge-health.md"

    isolated = [entry for entry in entries if not entry.concepts]
    tag_counter = Counter(tag for entry in entries for tag in entry.tags if tag not in GENERIC_GAP_TAGS)
    covered_keywords = {tag for spec in CONCEPT_SPECS for tag in spec.tags}
    concept_gaps = [(tag, count) for tag, count in tag_counter.items() if count >= 2 and tag not in covered_keywords]

    stale_cutoff = date.today() - timedelta(days=90)
    stale_entries = []
    for entry in entries:
        try:
            entry_date = datetime.strptime(entry.date, "%Y-%m-%d").date()
        except ValueError:
            continue
        if entry.confidence == "raw" and entry_date <= stale_cutoff:
            stale_entries.append(entry)

    potential_conflicts = []
    for spec in CONCEPT_SPECS:
        matched = concept_map.get(spec.name, [])
        if len(matched) >= 4:
            potential_conflicts.append((spec.name, len(matched)))

    conceptless_reports = []
    for candidate_report in sorted(REPORTS_DIR.glob("*.md")):
        text = candidate_report.read_text(encoding="utf-8")
        if "[[concepts/" not in text:
            conceptless_reports.append(candidate_report)

    lines = [
        "# Knowledge Health Report",
        "",
        f"> 生成日期：{today}",
        f"> 条目数：{len(entries)} | 概念页数：{len([name for name, items in concept_map.items() if items])}",
        "",
        "## 孤立条目",
    ]
    if isolated:
        lines.extend(f"- [[{entry.path.stem}|{entry.title}]]" for entry in isolated)
    else:
        lines.append("- 无。")

    lines += [
        "",
        "## 概念空白",
    ]
    if concept_gaps:
        lines.extend(f"- `{tag}`：出现 {count} 次，建议评估是否升级为概念页。" for tag, count in concept_gaps[:10])
    else:
        lines.append("- 暂未发现明显空白。")

    lines += [
        "",
        "## 过时条目",
    ]
    if stale_entries:
        lines.extend(f"- [[{entry.path.stem}|{entry.title}]]（confidence: raw）" for entry in stale_entries)
    else:
        lines.append("- 暂未发现超过 90 天仍为 raw 的条目。")

    lines += [
        "",
        "## 查询回流检查",
    ]
    if conceptless_reports:
        lines.extend(f"- [[reports/{path.stem}|{path.stem}]] 尚未链接到概念页。" for path in conceptless_reports)
    else:
        lines.append("- 当前 reports/ 均已包含概念链接，或尚无查询报告。")

    lines += [
        "",
        "## 待人工复核的高密度概念",
        "- 这部分用于提示“可能存在观点冲突或定义漂移”的主题，当前仅做启发式标记。",
    ]
    if potential_conflicts:
        lines.extend(f"- [[concepts/{name}|{name}]]：关联 {count} 条，可人工检查是否存在定义冲突。" for name, count in potential_conflicts)
    else:
        lines.append("- 暂无。")

    report_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return report_path


def add_processed_entry(
    source_path: Path,
    *,
    entry_date: str,
    title: str,
    slug: str,
    source_type: str,
    tags: list[str],
    summary: str,
    thought: str,
) -> Path:
    text = source_path.read_text(encoding="utf-8")
    source_meta, body = split_frontmatter(text)
    source = str(source_meta.get("source", source_path.name))
    source_url = str(source_meta.get("source_url", ""))
    entry_path = KNOWLEDGE_DIR / f"{entry_date}-{slug}.md"
    metadata = OrderedDict(
        [
            ("date", entry_date),
            ("source", source),
            ("source_type", source_type),
            ("source_url", source_url),
            ("tags", tags),
            ("confidence", "processed"),
        ]
    )
    content = [
        dump_frontmatter(metadata).rstrip(),
        "",
        f"# {title}",
        "",
        "## 核心观点",
        summary.strip(),
        "",
        "## 我的思考",
        thought.strip(),
        "",
        "## 原始内容",
        strip_processed_frontmatter(text),
        "",
    ]
    entry_path.write_text("\n".join(content), encoding="utf-8")
    return entry_path


def render_knowledge_base(entries: list[Entry]) -> str:
    del entries
    base = {
        "filters": {
            "and": [
                'file.inFolder("knowledge")',
                'file.folder == "knowledge"',
                'file.name != "_index.md"',
                'file.name != "CLAUDE.md"',
                'file.name != "AGENTS.md"',
            ]
        },
        "formulas": {
            "tag_count": "list(tags).length",
            "concept_count": "list(concepts).length",
            "related_count": "list(related).length",
            "days_since_capture": '(today() - date(date)).days',
        },
        "properties": {
            "date": {"displayName": "Date"},
            "source": {"displayName": "Source"},
            "source_type": {"displayName": "Type"},
            "tags": {"displayName": "Tags"},
            "concepts": {"displayName": "Concepts"},
            "confidence": {"displayName": "Confidence"},
            "formula.tag_count": {"displayName": "Tag Count"},
            "formula.concept_count": {"displayName": "Concept Count"},
            "formula.related_count": {"displayName": "Related Count"},
            "formula.days_since_capture": {"displayName": "Days Since Capture"},
        },
        "views": [
            {
                "type": "table",
                "name": "Knowledge Entries",
                "order": [
                    "date",
                    "file.name",
                    "source",
                    "source_type",
                    "tags",
                    "concepts",
                    "confidence",
                ],
                "summaries": {
                    "formula.tag_count": "Average",
                    "formula.concept_count": "Average",
                    "formula.related_count": "Average",
                },
            },
            {
                "type": "cards",
                "name": "By Concept",
                "groupBy": {
                    "property": "concepts",
                    "direction": "ASC",
                },
                "order": [
                    "file.name",
                    "concepts",
                    "source",
                    "tags",
                    "confidence",
                ],
            },
            {
                "type": "list",
                "name": "Recent Processed",
                "filters": {
                    "and": [
                        'confidence == "processed"',
                    ]
                },
                "order": [
                    "date",
                    "file.name",
                    "concepts",
                ],
            },
        ],
    }
    return yaml.safe_dump(base, allow_unicode=True, sort_keys=False, width=1000)


def write_knowledge_base(entries: list[Entry]) -> Path:
    base_path = KNOWLEDGE_DIR / "knowledge-base.base"
    base_path.write_text(render_knowledge_base(entries), encoding="utf-8")
    return base_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Knowledge maintenance utilities.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("repair", help="补全仅链接原文的知识条目。")

    compile_parser = subparsers.add_parser("compile", help="生成 concepts 层、related 字段与新版索引。")
    compile_parser.add_argument("--skip-related", action="store_true", help="只生成 concepts 和索引，不写 related。")

    find_parser = subparsers.add_parser("find", help="搜索知识条目并把结果沉淀为 report。")
    find_parser.add_argument("query", help="检索关键词")
    find_parser.add_argument("--limit", type=int, default=8, help="返回条目数量上限")
    find_parser.add_argument("--no-report", action="store_true", help="只打印结果，不写入 reports/")

    subparsers.add_parser("health", help="输出知识库健康报告。")
    subparsers.add_parser("tidy", help="整理标签后重新编译 concepts 和索引。")
    subparsers.add_parser("base", help="生成 knowledge-base.base 视图文件。")

    upgrade_parser = subparsers.add_parser("upgrade", help="执行 repair + compile + health。")
    upgrade_parser.add_argument("--skip-related", action="store_true", help="只生成 concepts 和索引，不写 related。")

    add_processed = subparsers.add_parser("add-processed", help="从 processed 原文创建知识条目。")
    add_processed.add_argument("source_path", help="processed 原文路径")
    add_processed.add_argument("--date", required=True, dest="entry_date", help="条目日期，格式 YYYY-MM-DD")
    add_processed.add_argument("--title", required=True, help="知识条目标题")
    add_processed.add_argument("--slug", required=True, help="输出文件名 slug，不含日期和扩展名")
    add_processed.add_argument("--source-type", default="article", help="source_type 值")
    add_processed.add_argument("--tags", required=True, help="逗号分隔标签")
    add_processed.add_argument("--summary", required=True, help="核心观点内容")
    add_processed.add_argument("--thought", default="- 待补充。", help="我的思考内容")

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.command == "repair":
        changed = repair_link_only_entries()
        print(f"repaired_entries={len(changed)}")
        for path in changed:
            print(path.relative_to(REPO_ROOT))
        return

    if args.command == "compile":
        entries, concept_map = compile_concepts(write_related=not args.skip_related)
        print(f"entries={len(entries)} concepts={len([name for name, items in concept_map.items() if items])}")
        return

    if args.command == "find":
        entries = load_entries()
        concept_map = detect_concepts(entries)
        matched_entries, matched_concepts = search_entries(args.query, entries, concept_map, limit=args.limit)
        if args.no_report:
            for entry in matched_entries:
                print(f"{entry.path.relative_to(REPO_ROOT)}\t{entry.summary}")
        else:
            report = create_query_report(args.query, matched_entries, matched_concepts)
            print(report.relative_to(REPO_ROOT))
        return

    if args.command == "health":
        entries = load_entries()
        concept_map = detect_concepts(entries)
        report = create_health_report(entries, concept_map)
        print(report.relative_to(REPO_ROOT))
        return

    if args.command == "tidy":
        changed = tidy_entries()
        entries, concept_map = compile_concepts(write_related=True)
        report = create_health_report(entries, concept_map)
        print(f"tidied_entries={len(changed)} entries={len(entries)} report={report.relative_to(REPO_ROOT)}")
        return

    if args.command == "base":
        entries = load_entries()
        base_path = write_knowledge_base(entries)
        print(base_path.relative_to(REPO_ROOT))
        return

    if args.command == "upgrade":
        changed = repair_link_only_entries()
        entries, concept_map = compile_concepts(write_related=not args.skip_related)
        report = create_health_report(entries, concept_map)
        base_path = write_knowledge_base(entries)
        print(
            f"repaired_entries={len(changed)} entries={len(entries)} "
            f"report={report.relative_to(REPO_ROOT)} base={base_path.relative_to(REPO_ROOT)}"
        )
        return

    if args.command == "add-processed":
        entry_path = add_processed_entry(
            Path(args.source_path),
            entry_date=args.entry_date,
            title=args.title,
            slug=args.slug,
            source_type=args.source_type,
            tags=[item.strip() for item in args.tags.split(",") if item.strip()],
            summary=args.summary,
            thought=args.thought,
        )
        print(entry_path.relative_to(REPO_ROOT))
        return


if __name__ == "__main__":
    main()
