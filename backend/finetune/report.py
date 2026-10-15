"""Compare result files side by side:  python -m finetune.report finetune/results/*.json"""
import json
import sys
from pathlib import Path

ROWS = [("Clean kits (no hard violation)", lambda a: f"{a['clean_kit_rate']:.0%}"),
        ("Hard violations per kit", lambda a: f"{a['hard_violations_per_kit']:.2f}"),
        ("  invalid output", lambda a: f"{a['hard_rate']['invalid_output']:.0%}"),
        ("  unsupported claims", lambda a: f"{a['hard_rate']['unsupported_claim']:.0%}"),
        ("  invented numbers", lambda a: f"{a['hard_rate']['invented_number']:.0%}"),
        ("  forbidden words", lambda a: f"{a['hard_rate']['forbidden_word']:.0%}"),
        ("  placeholders", lambda a: f"{a['hard_rate']['placeholder']:.0%}"),
        ("Missing facts flagged (recall)", lambda a: f"{a['missing_info_recall']:.0%}"),
        ("Seconds per kit", lambda a: f"{a['mean_seconds']}"),
        ("Tokens per kit", lambda a: f"{a['mean_tokens']}")]


def table(files: list[Path]) -> str:
    data = [json.loads(f.read_text()) for f in files]
    head = "| Metric | " + " | ".join(f"{d['model']} (n={d['aggregate']['n']})" for d in data) + " |"
    lines = [head, "|---|" + "---|" * len(data)]
    for label, fn in ROWS:
        lines.append(f"| {label} | " + " | ".join(fn(d["aggregate"]) for d in data) + " |")
    return "\n".join(lines)


if __name__ == "__main__":
    print(table([Path(p) for p in sys.argv[1:]]))
