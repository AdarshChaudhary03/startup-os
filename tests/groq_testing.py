from groq import Groq

client = Groq(api_key="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")

# Text generation / reasoning
completion = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[
        {"role": "system", "content": "You are a helpful coding assistant."},
        {"role": "user",   "content": "Write a Python function to parse JSON safely."}
    ],
    temperature=0.7,
    max_tokens=1024,
)
print(completion.choices[0].message.content)

# Streaming response (great for real-time UI)
stream = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[{"role": "user", "content": "Analyze this dataset for trends."}],
    stream=True,
)
for chunk in stream:
    print(chunk.choices[0].delta.content or "", end="")