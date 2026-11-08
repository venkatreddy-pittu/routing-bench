"""Sanity check: every buggy file must FAIL its tests and every reference fix must PASS. Run after editing tasks."""
from .sandbox import run_tests
from .tasks import TASKS

bad = 0
ids = set()
for t in TASKS:
    assert t["id"] not in ids, f"duplicate id {t['id']}"
    ids.add(t["id"])
    buggy_ok, _ = run_tests(t["buggy"], t["tests"])
    ref_ok, out = run_tests(t["ref"], t["tests"])
    status = "OK " if (not buggy_ok and ref_ok) else "BAD"
    bad += status == "BAD"
    print(f"{status} {t['id']:<22} buggy_fails={not buggy_ok} ref_passes={ref_ok}")
    if not ref_ok:
        print(out)
print(f"\n{len(TASKS)} tasks, {bad} bad")
raise SystemExit(1 if bad else 0)
