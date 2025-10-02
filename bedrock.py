import boto3
import json

# No session/profile needed
runtime = boto3.client(service_name="bedrock-runtime", region_name="us-west-2")

model_id = "openai.gpt-oss-120b-1:0"   # example
prompt = "You are a helpful assistant. What's the capital of France?"

response = runtime.invoke_model(
    modelId=model_id,
    body=json.dumps({
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 200,
        "temperature": 0.7
    })
)

result = json.loads(response["body"].read())
answer = result["choices"][0]["message"]["content"]
print(answer)
