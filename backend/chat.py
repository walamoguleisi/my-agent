import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(Path(__file__).parent.parent / ".env")

client = OpenAI(
    api_key=os.environ["DEEPSEEK_API_KEY"],
    base_url=os.environ["DEEPSEEK_BASE_URL"],
)

"""
非流式输出
response = client.chat.completions.create(
    model = os.environ["DEEPSEEK_MODEL"],
    messages = [
        {"role": "system", "content": "你是一个友好的助手。"},
        {"role": "user", "content": "用一句话介绍下你自己。"},
    ],
)

print(response.choices[0].message.content)
"""

"""流式输出

stream = client.chat.completions.create(
    model = os.environ["DEEPSEEK_MODEL"],
    messages = [
        {"role": "system", "content": "你是一个友好的助手。"},
        {"role": "user", "content": "用三句话介绍下你自己。"},
    ],
    stream = True,
)

for chunk in stream:
    delta = chunk.choices[0].delta
    if delta.content:
        print(delta.content, end="", flush=True)

print("\n")
"""

"""chat with cycle"""
messages = [
    {"role": "system", "content": "你是一个友好的助手，用简介的中文回答。"},
]

print("跟 DeepSeek聊天。输入 exit 退出。\n")

while True:
    user_input = input("你：").strip()
    if user_input.lower() in ("exit", "quit"):
        break
    if not user_input:   
        continue   
    
    messages.append(
        {"role": "user", "content": user_input}
    )

    stream = client.chat.completions.create(
        model = os.environ["DEEPSEEK_MODEL"],
        messages = messages,
        stream = True,
    )

    print("AI: ", end="", flush=True)
    reply_chunks = []
    for chunk in stream:
        delta = chunk.choices[0].delta
        if delta.content:
            print(delta.content, end="", flush=True)
            reply_chunks.append(delta.content)
    print("\n")

    messages.append(
        {"role": "assistant", "content": "".join(reply_chunks)}
    )
