# AI-Assisted Security Research Framework

Local-first pipeline for AI-assisted vulnerability research where **a model
(or a rule) proposes, and a human disposes**.

## Pipeline (v1, working today — no GPU or model required)

1. **Ingestion** — walk a repo, chunk source files (`.sol .py .ts .js .rs .go .move`).
2. **Indexing** — chunks carry file + line anchors so every claim is traceable.
3. **Hypothesis seeding** — conservative starter rules (delegatecall, tx.origin,
   unchecked calls/sends, block.timestamp) produce *hypotheses*, each with a rationale.
4. **Evidence tracking** — a hypothesis can only become `verified` with a linked
   evidence artifact (test output / PoC path). Rejections require a reason, so lessons persist.
5. **Reporting** — markdown report that separates verified / investigating /
   hypothesis / rejected. Only verified items may be called findings.

## Roadmap (Phase Eight — after reputation foundations)

- Local model integration (Ollama / vLLM) on 2× RTX 3090 (main rig) for
  hypothesis generation over the chunk index; satellite 3090 nodes later.
  Exactly 4× RTX 3090 exist in this setup — no design assumes a fifth.
- Embedding retrieval over indexed chunks.
- Foundry test scaffolding generated per hypothesis for human review.

## Run

```bash
export PYTHONPATH=src
pip install pytest
PYTHONPATH=src pytest -q
```

## Non-negotiables

- No fabricated findings. No AI-generated report is submitted anywhere without
  human verification and a reproducible test.
- Testing only against local code or explicitly authorized program scope.

## License

MIT — see LICENSE. Owner-confirmed Nov 3, 2026.
