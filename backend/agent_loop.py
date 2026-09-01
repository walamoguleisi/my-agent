# backend/agent_loop.py
# 3rd simple test of LLM API, with tool_call and agent loop
# define some tools and tools description

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

# 所有文件操作都限定在WORKSPACE目录下
WORKSPACE = Path(__file__).parent.parent / "workspace" / "files"
WORKSPACE.mkdir(parents=True, exist_ok=True)

MAX_ITERATIONS = 20     #限制loop的最大循环次数是20

# === 工具定义 ===

def tool_list_files() -> str:
    """这里不需要传入参数，就是直接列出WORKSPACE下的所有文件。"""
    files = [str(p.relative_to(WORKSPACE)) for p in WORKSPACE.rglob("*") if p.is_file()]
    if not files:
        return "（目录为空）"
    return "\n".join(files)

def tool_read_file(path: str) -> str:
    """读取WORKSPACE下某个文件的内容。"""
    target = (WORKSPACE / path).resolve()          #得到一个标准绝对路径
    if not str(target).startswith(str(WORKSPACE.resolve())):    # 如果path是个类似../../etc/password之类的路径
        return f"Error: 不允许越权访问！"       # tools中所有的错误没有使用raise Exception，而是返回一个Error开头的字符串给模型。
    if not target.exists():
        return f"Error: 文件不存在:{path}"
    return target.read_text(encoding="utf-8")

def tool_write_file(path: str, content: str) -> str:
    """ 写入WORKSPACE下某个文件。"""
    target = (WORKSPACE / path).resolve()
    if not str(target).startswith(str(WORKSPACE.resolve())):
        return f"Error: 不允许越权访问！"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return f"已写入: {path}（{len(content)}字符）"

TOOL_FUNCTIONS = {
    "list_files": tool_list_files,
    "read_file": tool_read_file,
    "write_file": tool_write_file,
}

# === 工具描述（给模型看）===
# 每个工具调用都对应上面一个函数实现。name字段比较关键，模型生成tool_call时会用这个名字，我们再用这个名字去TOOL_FUNCTIONS里找到对应的实现

tools = [
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "列出工作目录下所有文件的路径，用换行分隔",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "读取工作目录下某个文件的完整内容",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "相对于工作目录的文件路径",
                    },
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "写入或覆盖工作目录下的某个文件",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "相对于工作目录的文件路径",
                    },
                    "content": {
                        "type": "string",
                        "description": "要写入的内容",
                    },
                },
                "required": ["path", "content"],
            },
        },
    },
]

def run_agent(user_input: str) -> None:
    messages = [
        {
            "role": "system",
            "content": "你是一个能操作本地文件的助手。需要文件操作时使用提供的工具",
        },
        {
            "role": "user",
            "content": user_input,
        },
    ]

    for iteration in range(MAX_ITERATIONS):
        print(f"messages长度: {len(messages)}")
        print(f"\n--- 第{iteration +1} 轮 ---")

        stream = client.chat.completions.create(
            model = os.environ["DEEPSEEK_MODEL"],
            messages = messages,
            tools = tools,
            stream = True,
        )

        # 累计本轮的输出，针对LLM返回的assistant message，从流中逐步收取contents和tool_calls.
        content_chunks: list[str] = []
        tool_calls_acc: dict[int, dict] = {}

        for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta

            # 1) 累计普通文字
            if delta.content:
                print(delta.content, end="", flush=True)
                content_chunks.append(delta.content)
            
            # 2) 累计tool calls（按index分组）
            if delta.tool_calls:
                for tc_delta in delta.tool_calls:
                    idx = tc_delta.index
                    if idx not in tool_calls_acc:
                        tool_calls_acc[idx] = {
                            "id": "",
                            "name": "",
                            "arguments":""
                        }
                    entry = tool_calls_acc[idx]
                    if tc_delta.id:
                        entry["id"] += tc_delta.id
                    if tc_delta.function:
                        if tc_delta.function.name:
                            entry["name"] += tc_delta.function.name
                        if tc_delta.function.arguments:
                            entry["arguments"] += tc_delta.function.arguments
            # 把本轮 assistant消息追加到messages
        assistant_msg: dict = {"role": "assistant"}
        if content_chunks:
            assistant_msg["content"] = "".join(content_chunks)
        if tool_calls_acc:
            assistant_msg["tool_calls"] = [
                {
                    "id": tc["id"],
                    "type": "function",
                    "function": {
                        "name": tc["name"],
                        "arguments": tc["arguments"]
                    }
                }
                for tc in tool_calls_acc.values()
            ]
        
        messages.append(assistant_msg)

        # 没有tool calss，循环结束
        if not tool_calls_acc:
            print()
            return
            
        # 执行每个tool call
        for tc in tool_calls_acc.values():
            func_name = tc["name"]
            args = json.loads(tc["arguments"]) if tc["arguments"] else {}
            print(f"\n>>> 调用{func_name}({args})")

            func = TOOL_FUNCTIONS.get(func_name)
            if not func:
                result = f"Error：未知函数{func_name}"
            else:
                try:
                    result = func(**args)
                except Exception as e:
                    result = f"Error： 工具执行异常：{e}"
                
            print(f"<<< {result[:200]}{'...' if len(result) > 200 else ''}")

            messages.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": result,
            })
    print(f"\n达到最大论述{MAX_ITERATIONS}，强制结束。")

if __name__ == "__main__":
    print("简易 Agent。输入 exit 退出。\n")
    while True:
        line = input("你：").strip()
        if line.lower() in ("exit", "quit"):
            break
        if not line:
            continue
        run_agent(line)
        print()
