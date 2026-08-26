"""Direct Bedrock Runtime client, bypassing the local llm.py proxy.

Used because the proxy sends a `temperature` param that Claude Opus 5 rejects
(deprecated for that model). Mirrors llm.Client's interface: Client(model).send(message)
-> {"response": "<text>"}.
"""
import json

import boto3

DEFAULT_PROFILE = "core-services-staging"
DEFAULT_REGION = "us-east-1"


class Client:
    def __init__(self, model, profile_name=DEFAULT_PROFILE, region_name=DEFAULT_REGION, max_tokens=4096):
        self.model = model
        self.max_tokens = max_tokens
        session = boto3.Session(profile_name=profile_name)
        self._brt = session.client("bedrock-runtime", region_name=region_name)

    def send(self, message):
        model_id = self.model if self.model.startswith("us.") else "us." + self.model
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": self.max_tokens,
            "messages": [{"role": "user", "content": message}],
        }
        try:
            resp = self._brt.invoke_model(modelId=model_id, body=json.dumps(body))
        except Exception as exc:
            raise Exception(f"Error invoking Bedrock model {model_id}: {exc}") from exc

        payload = json.loads(resp["body"].read())
        content = payload.get("content", [])
        text = "".join(block.get("text", "") for block in content if block.get("type") == "text")
        return {"response": text}
