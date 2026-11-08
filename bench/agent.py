"""One loop, four configs. A config is just a plan: a list of (model_key, max_tries) stages."""
import re
import time
from collections import defaultdict

from .sandbox import classify, run_tests

SYSTEM = (
    "You fix bugs in a single Python file. Reply with the complete corrected solution.py "
    "in ONE ```python code block and nothing else."
)
ESCALATE_ON = {"format_error", "repeated_patch"}  # stop wasting local tries; move to the next stage


def extract_code(text):
    blocks = re.findall(r"```(?:python)?\n(.*?)```", text, re.S)
    return blocks[-1] if blocks else None


def initial_prompt(task, first_failure):
    return (
        f"Task: {task['id']}\n\nSpec:\n{task['spec']}\n\nsolution.py:\n```python\n{task['buggy']}\n```\n\n"
        f"CI output:\n{first_failure}\n\nFix solution.py."
    )


def solve(task, models, plan, first_failure):
    messages = [{"role": "user", "content": initial_prompt(task, first_failure)}]
    usage = defaultdict(lambda: [0, 0])
    latency, tries, prev_code, category, escalated = 0.0, 0, None, "no_attempt", False
    for stage, (key, max_tries) in enumerate(plan):
        escalated = stage > 0
        for _ in range(max_tries):
            t0 = time.time()
            text, tin, tout = models[key].chat(SYSTEM, messages)
            latency += time.time() - t0
            usage[key][0] += tin
            usage[key][1] += tout
            tries += 1
            messages.append({"role": "assistant", "content": text})
            code = extract_code(text)
            if code is None:
                category, feedback = "format_error", "No ```python block found. Reply with the full file in one code block."
            elif code == prev_code:
                category, feedback = "repeated_patch", "That is identical to your previous attempt. Try a different fix."
            else:
                ok, out = run_tests(code, task["tests"])
                if ok:
                    return dict(passed=True, tries=tries, latency=latency, usage=dict(usage), escalated=escalated, failure=None)
                category, feedback = classify(out), f"Tests still fail:\n{out}"
            prev_code = code
            messages.append({"role": "user", "content": feedback})
            if category in ESCALATE_ON and stage < len(plan) - 1:
                break
    return dict(passed=False, tries=tries, latency=latency, usage=dict(usage), escalated=escalated, failure=category)
