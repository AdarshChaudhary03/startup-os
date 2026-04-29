from openai import OpenAI

client = OpenAI(
    api_key="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",
    base_url="https://openrouter.ai/api/v1",
)

# FREE models — use the ":free" suffix
FREE_MODELS = [
    "meta-llama/llama-3.3-70b-instruct:free",
    "mistralai/mistral-7b-instruct:free",
    "deepseek/deepseek-r1:free",          # Reasoning
    "google/gemma-2-9b-it:free",
]

def query_model(model, prompt, system="You are helpful."):
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": prompt},
        ],
    )
    return resp.choices[0].message.content

# Document creation example
doc = query_model(
    model="meta-llama/llama-3.3-70b-instruct:free",
    system="You are a professional technical writer.",
    prompt="Write a 500-word executive summary about AI adoption in 2026.",
)
print(doc)

# Reasoning example — use DeepSeek R1
answer = query_model(
    model="deepseek/deepseek-r1:free",
    prompt="Solve: If 3x + 7 = 22, find x. Show all steps.",
)
print(answer)