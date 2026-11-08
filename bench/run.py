"""Usage: python -m bench.run --runs 3            (real models: Ollama + Bedrock)
          python -m bench.run --fake --runs 1     (harness self-test, no models, numbers are meaningless)"""
import argparse
import json
import os
import time
from collections import Counter
from pathlib import Path

from .agent import solve
from .models import BedrockModel, FakeModel, OllamaModel
from .sandbox import run_tests
from .tasks import TASKS

PLANS = {
    "1_local_single": [("local", 1)],
    "2_local_loop": [("local", 3)],
    "3_cloud_single": [("cloud", 1)],
    "4_hybrid": [("local", 2), ("cloud", 1)],  # escalation rule lives in agent.py (ESCALATE_ON) + the 2-try cap here
}


def cloud_cost(usage):
    pin = float(os.getenv("BEDROCK_IN_PER_1M") or "nan")
    pout = float(os.getenv("BEDROCK_OUT_PER_1M") or "nan")
    tin, tout = usage.get("cloud", [0, 0])
    return (tin * pin + tout * pout) / 1e6


def pct(rs):
    return 100 * sum(r["passed"] for r in rs) / len(rs) if rs else float("nan")


def report(recs):
    cfgs = sorted({r["config"] for r in recs})
    runs = sorted({r["run"] for r in recs})
    print("\n| Config | Pass % (mean [min-max over runs]) | Avg latency (s) | Cloud $ / 1,000 tasks | Local tokens / task | Escalated % | Top failure mode |")
    print("|---|---|---|---|---|---|---|")
    for c in cfgs:
        rs = [r for r in recs if r["config"] == c]
        per_run = [pct([r for r in rs if r["run"] == k]) for k in runs]
        cost = sum(cloud_cost(r["usage"]) for r in rs) / len(rs) * 1000
        cost_s = "n/a (set BEDROCK_*_PER_1M)" if cost != cost else f"${cost:,.2f}"
        local_tok = sum(sum(r["usage"].get("local", [0, 0])) for r in rs) / len(rs)
        fails = Counter(r["failure"] for r in rs if not r["passed"])
        top = fails.most_common(1)[0][0] if fails else "-"
        esc = 100 * sum(r["escalated"] for r in rs) / len(rs)
        print(f"| {c} | {pct(rs):.0f} [{min(per_run):.0f}-{max(per_run):.0f}] | {sum(r['latency'] for r in rs) / len(rs):.1f} | {cost_s} | {local_tok:.0f} | {esc:.0f} | {top} |")
    print("\nPass % by difficulty tier (this is where the break point shows up):\n")
    print("| Config | Tier 1 | Tier 2 | Tier 3 |")
    print("|---|---|---|---|")
    for c in cfgs:
        cells = [f"{pct([r for r in recs if r['config'] == c and r['tier'] == t]):.0f}" for t in (1, 2, 3)]
        print(f"| {c} | " + " | ".join(cells) + " |")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--configs", nargs="*", default=list(PLANS))
    ap.add_argument("--fake", action="store_true")
    args = ap.parse_args()

    if args.fake:
        models = {"local": FakeModel(TASKS, succeed_on=2), "cloud": FakeModel(TASKS, succeed_on=1)}
    else:
        models = {"local": OllamaModel()}
        if any(k == "cloud" for c in args.configs for k, _ in PLANS[c]):
            models["cloud"] = BedrockModel()

    first_failure = {t["id"]: run_tests(t["buggy"], t["tests"])[1] for t in TASKS}
    Path("results").mkdir(exist_ok=True)
    out_path = Path("results") / f"{'fake_' if args.fake else ''}{time.strftime('%Y%m%d_%H%M%S')}.jsonl"
    recs = []
    with open(out_path, "w") as f:
        for run in range(args.runs):
            for cfg in args.configs:
                for t in TASKS:
                    res = solve(t, models, PLANS[cfg], first_failure[t["id"]])
                    rec = dict(run=run, config=cfg, task=t["id"], tier=t["tier"], **res)
                    recs.append(rec)
                    f.write(json.dumps(rec) + "\n")
                    print(f"run{run} {cfg:<15} {t['id']:<20} {'PASS' if res['passed'] else 'FAIL'} tries={res['tries']} {res['latency']:.1f}s")
    report(recs)
    print(f"\nraw results: {out_path}")


if __name__ == "__main__":
    main()
