"""Reproduce semantic extraction results and preserve every prediction/error."""
import argparse
from collections import Counter
import json
from pathlib import Path

from .analysis import Query, RuleAnalyzer

ROOT = Path(__file__).resolve().parents[1]


def evaluate() -> dict:
    cases = [json.loads(line) for line in (ROOT / "data/questions.jsonl").read_text("utf8").splitlines() if line.strip()]
    analyzer = RuleAnalyzer()
    categories = {}
    decisions = Counter()
    records = []
    for case in cases:
        expected = dict(case["expected"])
        expected["query"] = Query(**expected["query"]).__dict__ if expected.get("query") else None
        actual = analyzer.analyze(case["text"]).to_dict()
        correct = actual == expected
        category = categories.setdefault(case["category"], {"cases": 0, "exact_matches": 0})
        category["cases"] += 1
        category["exact_matches"] += int(correct)
        decisions[expected["decision"] + " -> " + actual["decision"]] += 1
        records.append({"id": case["id"], "text": case["text"], "category": case["category"],
                        "correct": correct, "expected": expected, "actual": actual})
    ready = [r for r in records if r["expected"]["decision"] == "ready"]
    fields = ("start_year", "end_year", "metric", "operation", "destination", "top_k")
    field_accuracy = {field: round(sum(r["actual"]["query"] is not None and
                                      r["actual"]["query"][field] == r["expected"]["query"][field]
                                      for r in ready) / len(ready), 4) for field in fields}
    return {"system": "offline rule baseline", "model_calls": 0,
            "dataset": "Sample-authored synthetic diagnostic set; not an independent test set",
            "cases": len(records), "exact_matches": sum(r["correct"] for r in records),
            "exact_match_accuracy": round(sum(r["correct"] for r in records) / len(records), 4),
            "ready_case_field_accuracy": field_accuracy,
            "decision_confusion": dict(sorted(decisions.items())), "categories": categories,
            "records": records}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Verify the saved report is reproducible")
    parser.add_argument("--output", type=Path, help="Write the complete UTF-8 evaluation report")
    args = parser.parse_args()
    report = evaluate()
    if args.check:
        saved = json.loads((ROOT / "reports/evaluation.json").read_text("utf8"))
        if saved != report:
            raise SystemExit("The saved evaluation does not match current predictions")
        print(f"Reproduced {report['cases']} cases; {report['exact_matches']} exact matches")
    elif args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf8")
        print(f"Saved {report['cases']} cases; {report['exact_matches']} exact matches")
    else:
        print(json.dumps(report, indent=2, ensure_ascii=True))
