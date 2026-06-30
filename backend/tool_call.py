import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(Path(__file__).parent.parent / ".env")

client = OpenAI(
    api_key = os.environ["DEEPSEEK_API_KEY"],
    base_url = os.environ["DEEPSEEK_BASE_URL"],
)

# === 第1步：定义本地函数 ===
def get_weather(city: str) -> str:
    """模拟一个天气查询函数，真实场景下这里应该调用外部API"""
    fake_data = {
        "北京": "晴，25°C，微风",
        "上海": "多云，28°C",
        "广州": "雷阵雨，30°C",
        "深圳": "小雨，29°C",
    }
    return fake_data.get(city, f"暂时查不到{city}的天气信息。")

# === 第2步：把这个函数描述给模型听 ===
tools = [
    {
        "type": "function",
        "function":{
            "name": "get_weather",
            "description": "查询某个城市的天气情况",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名称，例如：北京、上海、广州等",
                    },
                },
                "required": ["city"],
            },
        },
    },
]

# === 第3步：第一次调用API，带上tools ===
messages = [
    {"role": "system", "content": "你是一个友好的天气助手，但只支持中国大陆的天气查询"},
    {"role": "user", "content": "What's the weather like in New York?"},
]

response = client.chat.completions.create(
    model = os.environ["DEEPSEEK_MODEL"],
    messages = messages,
    tools = tools,
)

assistant_msg = response.choices[0].message
print("=== 第一次响应 ===")
print(f"content: {assistant_msg.content}")
print(f"tool_calls:{assistant_msg.tool_calls}")

# === 第4步：根据模型要调用工具，执行并把结果回传 ===
if assistant_msg.tool_calls:
    # 把模型这条消息原样追加到messages
    messages.append(assistant_msg.model_dump(exclude_none=True))
    
    # 处理每一个工具调用 （这里先假设只有一个工具）
    for tool_call in assistant_msg.tool_calls:
        func_name = tool_call.function.name
        func_args = json.loads(tool_call.function.arguments)
        print(f"\n模型申请调用：{func_name}({func_args})")

        # 实际执行
        if func_name == "get_weather":
            result = get_weather(**func_args)
        else:
            result = f"未知函数：{func_name}"
        print(f"执行结果：{result}")

        messages.append(
            {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result,
            }
        )
    
    # === 第5步，再调一个API，让模型基于工具结果回复 ===
    response2 = client.chat.completions.create(
        model = os.environ["DEEPSEEK_MODEL"],
        messages = messages,
        tools = tools,
    )

    print("\n=== 第二次响应 ===")
    print(f"AI: {response2.choices[0].message.content}")
