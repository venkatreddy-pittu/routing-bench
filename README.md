# routing-bench: when does a small local model stop being worth it?

**Question:** on code-repair tasks, at what difficulty does a local model (Gemma 4 E4B via Ollama) plus a validator retry loop become worse than paying for a cloud model (AWS Bedrock), and does a hybrid router beat both?

Results: *not run yet. Fill this section only with measured numbers.*

## Four configs (same loop, same prompts, same tasks; only the plan differs)

| Config | Plan |
|---|---|
| 1_local_single | local, 1 try |
| 2_local_loop | local, up to 3 tries with pytest feedback |
| 3_cloud_single | cloud, 1 try |
| 4_hybrid | local up to 2 tries, then escalate to cloud. Early escalation if the reply has no code block (`format_error`) or repeats its previous patch (`repeated_patch`) |

Each task gives the model a spec, the buggy `solution.py`, and the initial CI failure output. Pass = all pytest tests pass.

## Run it

```bash
pip install -r requirements.txt
cp .env.example .env            # fill in model id + prices; export the vars (set -a; source .env; set +a)
ollama pull gemma4:e4b          # check the exact tag with `ollama list`
python -m bench.validate_tasks  # every buggy file must fail, every reference fix must pass
python -m bench.run --fake      # self-test of the harness, numbers are meaningless
python -m bench.run --runs 3    # the real benchmark
```

Raw per-task results go to `results/*.jsonl`; the tables print at the end.

## Rules that keep it honest
1. **Freeze the task set before the first real run.** Never edit tasks after seeing results.
2. Starter set is 9 tasks; grow to 45 (15 per tier). Write them yourself, don't copy public benchmarks.
3. Report ranges across runs, not single numbers. With 45 tasks one task is ~2 points; small gaps are noise.
4. Local cost is not zero: report your hardware and say the table counts marginal cost only.
5. Cloud cost comes from real token counts x the pricing you looked up (note the date).
6. Sandbox: `bench/sandbox.py` limits time/memory and strips AWS credentials, but is **not** a security boundary. Run in Docker without network for anything serious.

## Hardware / versions (fill in)
- Machine:
- Ollama + model tag:
- Bedrock model id + pricing date:
