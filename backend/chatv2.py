import json
import os

from dotenv import load_dotenv
from pathlib import Path
from openai import OpenAI

# 加载环境变量
load_dotenv(Path(__file__).parent.parent / ".env")

# 配置文件路径
HISTORY_FILE = Path(__file__).parent.parent / "workspace" / "chat_log.json"

# 初始化客户端
client = OpenAI(
    api_key=os.environ["DEEPSEEK_API_KEY"],
    base_url=os.environ["DEEPSEEK_BASE_URL"]
)

def load_chat_history():
    """从本地JSON读取历史消息，如果文件不存在返回初始空列表"""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    # 默认携带system角色设定
    return [
        {"role": "system", "content": "你是一个乐于助人的AI助手。"}
    ]

def save_chat_history(messages):
    """把消息列表写入JSON文件"""
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)

def main():
    # 启动时加载历史对话
    messages = load_chat_history()

    print("=== 已加载历史对话，输入exit退出 ===")
    while True:
        user_input = input("\n你：").strip()
        if user_input.strip().lower() == "exit":
            print("对话结束，历史已保存！")
            break

        # 把用户消息加入上下文
        messages.append({"role": "user", "content": user_input})

        # 调用流式接口
        stream = client.chat.completions.create(
            model=os.environ["DEEPSEEK_MODEL"],
            messages=messages,
            stream=True,
        )

        full_reply = ""
        print("AI：", end="")
        for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                full_reply += delta.content
                print(delta.content, end="", flush=True)

        # 将AI完整回复加入消息上下文
        messages.append({"role": "assistant", "content": full_reply})

        # 立刻持久化保存到本地JSON
        save_chat_history(messages)

if __name__ == "__main__":
    main()
