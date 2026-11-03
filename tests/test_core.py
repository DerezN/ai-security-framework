import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ai_sec_framework.core import Hypothesis, ingest, render_report, seed_hypotheses


def test_ingest_and_seed(tmp_path):
    (tmp_path / "Vault.sol").write_text(
        "contract V {\n  function f() public { require(tx.origin == msg.sender); }\n}\n"
    )
    chunks = ingest(tmp_path)
    hyps = seed_hypotheses(chunks)
    assert any(h.rule == "tx-origin-auth" and h.line == 2 for h in hyps)


def test_verify_requires_evidence():
    h = Hypothesis("H-0001", "delegatecall", "A.sol", 1, "check")
    try:
        h.verify("")
        raise AssertionError("should have raised")
    except ValueError:
        pass
    h.verify("test/output.txt")
    assert h.status == "verified"


def test_report_separates_verified_from_hypotheses(tmp_path):
    (tmp_path / "A.sol").write_text("x.delegatecall(y);\n")
    hyps = seed_hypotheses(ingest(tmp_path))
    report = render_report(hyps)
    assert "Hypothesis (1)" in report
    assert "may be described as findings" in report
