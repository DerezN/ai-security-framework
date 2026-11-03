"""Core pipeline v1 (no model required):

repo ingestion -> chunked code index -> rule-based hypothesis seeds ->
evidence records -> human verification states -> markdown report.

A hypothesis is NOT a finding. Status can only move to "verified" with a
linked evidence artifact (test output, PoC path) recorded by a human reviewer.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

SOURCE_SUFFIXES = {".sol", ".py", ".ts", ".js", ".rs", ".go", ".move"}

# Conservative starter rules — pattern presence is a lead, not proof.
RULES = [
    ("unchecked-external-call", re.compile(r"\.call\{[^}]*\}\(\s*\"\"\s*\)|\.call\(\)"),
     "External call without visible result handling — check reentrancy / ignored failure."),
    ("tx-origin-auth", re.compile(r"tx\.origin"),
     "tx.origin used — check whether it gates authorization (phishing-prone)."),
    ("delegatecall", re.compile(r"delegatecall"),
     "delegatecall present — check target control and storage-collision risk."),
    ("block-timestamp", re.compile(r"block\.timestamp"),
     "block.timestamp used — check for miner-influenceable logic."),
    ("unchecked-send", re.compile(r"\.send\("),
     "send() present — check ignored return value / 2300-gas assumptions."),
]


@dataclass
class Chunk:
    file: str
    start_line: int
    text: str


@dataclass
class Hypothesis:
    id: str
    rule: str
    file: str
    line: int
    rationale: str
    status: str = "hypothesis"  # hypothesis -> investigating -> verified | rejected
    evidence: list[str] = field(default_factory=list)

    def verify(self, evidence_path: str) -> None:
        if not evidence_path:
            raise ValueError("Verification requires a linked evidence artifact (test/PoC).")
        self.evidence.append(evidence_path)
        self.status = "verified"

    def reject(self, reason: str) -> None:
        if not reason:
            raise ValueError("Rejection requires a reason so the lesson is kept.")
        self.evidence.append(f"rejected: {reason}")
        self.status = "rejected"


def ingest(root: str | Path, chunk_lines: int = 120) -> list[Chunk]:
    root = Path(root)
    chunks: list[Chunk] = []
    for p in sorted(root.rglob("*")):
        if not p.is_file() or p.suffix.lower() not in SOURCE_SUFFIXES:
            continue
        if any(part in {".git", "node_modules", "out", "cache"} for part in p.parts):
            continue
        lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
        for i in range(0, len(lines), chunk_lines):
            chunks.append(Chunk(str(p.relative_to(root)), i + 1, "\n".join(lines[i:i + chunk_lines])))
    return chunks


def seed_hypotheses(chunks: list[Chunk]) -> list[Hypothesis]:
    out: list[Hypothesis] = []
    n = 0
    for ch in chunks:
        for offset, line in enumerate(ch.text.splitlines()):
            for rule_id, pattern, rationale in RULES:
                if pattern.search(line):
                    n += 1
                    out.append(Hypothesis(f"H-{n:04d}", rule_id, ch.file, ch.start_line + offset, rationale))
    return out


def render_report(hyps: list[Hypothesis], title: str = "Security Research Report") -> str:
    lines = [f"# {title}", "", f"Total hypotheses: {len(hyps)}", ""]
    for status in ("verified", "investigating", "hypothesis", "rejected"):
        group = [h for h in hyps if h.status == status]
        if not group:
            continue
        lines += [f"## {status.capitalize()} ({len(group)})", ""]
        for h in group:
            lines.append(f"- **{h.id}** [{h.rule}] `{h.file}:{h.line}` — {h.rationale}")
            for e in h.evidence:
                lines.append(f"  - evidence: {e}")
        lines.append("")
    lines.append("_Only items under Verified, each with linked evidence, may be described as findings._")
    return "\n".join(lines) + "\n"
