#!/usr/bin/env python3
"""Check that the data, the scripts and the prose still agree.

findings.jsonl is the source of truth. PAPER.md and AGENTS.md are prose written
over it, which means there are three copies of every number in this repo and
three copies of anything diverge the moment one is edited. This script is the
cheap defence: structure and cross-references are hard failures, and every
measured value that no longer appears verbatim in the paper is printed for a
human to look at.

    python check_bundle.py        # exit 0 if clean, 1 on any FAIL
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent
REQUIRED = ["id", "intent", "hypothesis", "method", "measurement", "verdict",
            "mechanism", "generalizes_to", "if_you_were_about_to", "script"]

fails: list[str] = []
reviews: list[str] = []


def fail(msg: str) -> None:
    fails.append(msg)
    print(f"FAIL   {msg}")


def review(msg: str) -> None:
    reviews.append(msg)
    print(f"REVIEW {msg}")


schema = json.loads((ROOT / "findings.schema.json").read_text())
declared = set(schema["properties"])
if declared != set(REQUIRED):
    fail(f"schema fields {sorted(declared)} != checker fields {sorted(REQUIRED)}")

findings = []
for n, line in enumerate(
        (ROOT / "findings.jsonl").read_text().splitlines(), start=1):
    if not line.strip():
        continue
    try:
        findings.append(json.loads(line))
    except json.JSONDecodeError as e:
        fail(f"findings.jsonl line {n} is not valid JSON: {e}")

paper = (ROOT / "PAPER.md").read_text()
agents = (ROOT / "AGENTS.md").read_text()


def numbers(obj) -> list[str]:
    """Every measured scalar, as it would be written in prose."""
    out = []
    if isinstance(obj, dict):
        for v in obj.values():
            out += numbers(v)
    elif isinstance(obj, list):
        for v in obj:
            out += numbers(v)
    elif isinstance(obj, bool):
        pass
    elif isinstance(obj, (int, float)):
        out.append(obj)
    return out


def in_paper(value) -> bool:
    """Does this number appear in the paper, allowing for trailing zeros and
    thousands separators? 0.6 in the data may be written 0.60 in a table."""
    s = repr(value)
    cands = {s, s.rstrip("0").rstrip(".") if "." in s else s}
    if isinstance(value, float):
        cands |= {f"{value:.1f}", f"{value:.2f}", f"{value:.3f}"}
    if isinstance(value, int) and abs(value) >= 1000:
        cands.add(f"{value:,}")
    return any(re.search(rf"(?<![\d.]){re.escape(c)}(?![\d])", paper)
               for c in cands)


seen_ids = set()
for f in findings:
    fid = f.get("id", "<no id>")
    if fid in seen_ids:
        fail(f"{fid}: duplicate id")
    seen_ids.add(fid)
    for k in REQUIRED:
        if k not in f:
            fail(f"{fid}: missing field '{k}'")
    for k in f:
        if k not in declared:
            fail(f"{fid}: field '{k}' is not in findings.schema.json")
    if not isinstance(f.get("intent"), list) or not f.get("intent"):
        fail(f"{fid}: 'intent' must be a non-empty list — it is the lookup key")
    if not isinstance(f.get("measurement"), dict) or not f.get("measurement"):
        fail(f"{fid}: 'measurement' must be a non-empty object")

    script = ROOT / f.get("script", "")
    if not script.is_file():
        fail(f"{fid}: script {f.get('script')} does not exist")
    else:
        try:
            compile(script.read_text(), str(script), "exec")
        except SyntaxError as e:
            fail(f"{fid}: {f['script']} does not compile: {e}")

    if fid not in agents:
        fail(f"{fid}: not cited in AGENTS.md — an agent cannot find it")

    orphans = [v for v in numbers(f["measurement"]) if not in_paper(v)]
    if orphans:
        review(f"{fid}: measured {orphans} not quoted in PAPER.md")

for script in sorted((ROOT / "scripts").glob("[0-9]*.py")):
    rel = f"scripts/{script.name}"
    if not any(f.get("script") == rel for f in findings):
        fail(f"{rel} is not claimed by any finding")

print(f"\n{len(findings)} findings · {len(fails)} failures · "
      f"{len(reviews)} to review")
sys.exit(1 if fails else 0)
