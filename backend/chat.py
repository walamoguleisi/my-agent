import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(Path(__file__).parent.parent / ".env")

client = OpenAI(
    api_key=os.environ["DEEPSEEK_API_KEY"],
    base_url=os.environ["DEEPSEEK_BASE_URL"],
)

response = client.chat.completions.create(
    model = os.environ["DEEPSEEK_MODEL"],
    messages = [
        {"role": "system", "content": "你是一个友好的助手。"},
        {"role": "user", "content": "用一句话介绍下你自己。"},
    ],
)

print(response.choices[0].message.content)
