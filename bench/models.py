"""Model adapters. Each .chat(system, messages) returns (text, tokens_in, tokens_out)."""
import json
import os
import re
import urllib.request


class OllamaModel:
    def __init__(self, model=None, host=None, temperature=0.2):
        self.model = model or os.getenv("OLLAMA_MODEL", "gemma4:e4b")
        self.host = (host or os.getenv("OLLAMA_HOST", "http://localhost:11434")).rstrip("/")
        self.temperature = temperature

    def chat(self, system, messages):
        body = {
            "model": self.model,
            "stream": False,
            "options": {"temperature": self.temperature},
            "messages": [{"role": "system", "content": system}] + messages,
        }
        req = urllib.request.Request(
            f"{self.host}/api/chat",
            data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=600) as r:
            data = json.load(r)
        return data["message"]["content"], data.get("prompt_eval_count", 0), data.get("eval_count", 0)


class BedrockModel:
    def __init__(self, model_id=None, region=None, temperature=0.2):
        import boto3  # imported here so local-only runs don't need it

        self.model_id = model_id or os.environ["BEDROCK_MODEL_ID"]
        self.temperature = temperature
        self.client = boto3.client("bedrock-runtime", region_name=region or os.getenv("AWS_REGION", "us-east-1"))

    def chat(self, system, messages):
        resp = self.client.converse(
            modelId=self.model_id,
            system=[{"text": system}],
            messages=[{"role": m["role"], "content": [{"text": m["content"]}]} for m in messages],
            inferenceConfig={"temperature": self.temperature, "maxTokens": 2048},
        )
        text = "".join(b.get("text", "") for b in resp["output"]["message"]["content"])
        usage = resp["usage"]
        return text, usage["inputTokens"], usage["outputTokens"]


class FakeModel:
    """Harness self-test only. Returns the buggy code until attempt `succeed_on`, then the reference fix."""

    def __init__(self, tasks, succeed_on):
        self.tasks = {t["id"]: t for t in tasks}
        self.succeed_on = succeed_on

    def chat(self, system, messages):
        task_id = re.search(r"Task: (\S+)", messages[0]["content"]).group(1)
        attempt = sum(1 for m in messages if m["role"] == "assistant") + 1
        t = self.tasks[task_id]
        code = t["ref"] if attempt >= self.succeed_on else t["buggy"]
        return f"```python\n{code}\n```", 100, 50
