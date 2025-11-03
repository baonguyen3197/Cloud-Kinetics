# Diagnostic script to check Bedrock availability on LocalStack
import os
import json
import boto3
from botocore.config import Config

endpoint = os.getenv("AWS_ENDPOINT_URL", "http://localhost:4566")
region = os.getenv("AWS_DEFAULT_REGION", "ap-northeast-1")

print("Using endpoint:", endpoint, "region:", region)

cfg = Config(region_name=region, retries={"max_attempts": 1})
client = boto3.client("bedrock-runtime", endpoint_url=endpoint, config=cfg)

# list available operations
ops = getattr(client.meta.service_model, "operation_names", None)
print("Client operations available:", ops)

print("Service model name:", getattr(client.meta.service_model, 'service_id', 'unknown'))

# Try a small invoke_model
model_id = os.getenv("TEST_BEDROCK_MODEL", "meta.llama3-8b-instruct-v1:0")
body = json.dumps({
    "prompt": "Say Hello!",
    "max_gen_len": 8,
    "temperature": 0.9
})

print("Attempting invoke_model with modelId:", model_id)
try:
    resp = client.invoke_model(
        modelId=model_id,
        body=body,
        contentType="application/json",
        accept="application/json"
    )
    print("invoke_model response keys:", list(resp.keys()))
    if "body" in resp and resp["body"] is not None:
        try:
            raw = resp["body"].read()
            # try decode
            try:
                print("Response body (utf-8):\n", raw.decode('utf-8'))
            except Exception:
                print("Response body (raw bytes):", raw[:200])
        except Exception as e:
            print("Could not read response body:", e)
except Exception as e:
    print("invoke_model raised:", type(e).__name__, str(e))
    try:
        import botocore
        if isinstance(e, botocore.exceptions.ClientError):
            print("ClientError response:", e.response)
    except Exception:
        pass

print("Done.")
