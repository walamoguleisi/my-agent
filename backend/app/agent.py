# backend/app/agent.py
# 5th simple test of LLM API, define tool call parse funciton, tool call arguments parse function, and agent event generator

import json
import os
from pathlib import Path
from typing import Generator

from dotenv import load_dotenv
from openai import OpenAI

from app.tools import TOOL_FUNCTIONS, TOOL_DEFINITIONS

load_dotenv(Path(__file__).parent.parent.parent / ".env")

client = OpenAI(
    api_key = os.environ["MINIMAX_API_KEY"],
    base_url = os.environ["MINIMAX_BASE_URL"],
)

MAX_ITERATIONS = 20

def append_tool_call_delta(acc: dict[int, dict], tc_delta) -> None:
    idx = tc_delta.index           # 数据结构中是index，存储对应工具调用的编号，是整型，仅在stream中出现
    if idx not in acc:
        acc[idx] = {
            "id": "",
            "name": "",
            "arguments": ""
        }
    
    entry = acc[idx]

    if tc_delta.id:
        entry["id"] += tc_delta.id      # 数据结构中是id，对应大模型返回的tool call，它和index是平级的
    if tc_delta.function:
        if tc_delta.function.name:
            entry["name"] += tc_delta.function.name
        if tc_delta.function.arguments:
            entry["arguments"] += tc_delta.function.arguments

""" 需要返回一个字典型，用于func(**args)，另外加上对JSON字符串结构的检测
这个函数返回了四种场景：
1. 正常返回字典参数
2. 返回空，传入的原始工具参数就是空
3. 返回{"_raw", raw_arguments}，传入的JSON字符串无法解析
4. 返回{"_value", value}，最后解析的JSON字符串不是字典类型
"""
def parse_tool_args(raw_arguments: str) -> dict:       
    if not raw_arguments:
        return {}
    try:
        value = json.loads(raw_arguments)
    except json.JSONDecodeError:
        return {"_raw", raw_arguments}         
    
    if isinstance(value, dict):
        return value
    
    return {"_value", value}

def run_agent_events(user_message: str) -> Generator[dict, None, None]:
    # messages 是给模型的上下文
    # 事件是给外部看的执行过程，两条线都要维护

    messages = [
        {
            "role": "system",
            "content": "你是一个能操作本地文件的助手，需要文件操作时使用提供的工具",
        },
        {
            "role": "user",
            "content": user_message,
        },
    ]

    for iteration in range(MAX_ITERATIONS):
        # 每一轮模型调用开始前，先把轮数交出去
        yield {"type": "iteration_start", "iteration": iteration+1}

        try:
            stream = client.chat.completions.create(
                model = os.environ["MINIMAX_MODEL"],
                messages = messages,
                tools = TOOL_DEFINITIONS,
                stream = True,
            )
        except Exception as e:
            # 模型API调用失败，这是系统级错误，直接结束本次任务
            yield {"type": "error", "message": str(e)}
            return
        
        content_chunk: list[str] = []
        tool_calls_acc: dict[int, dict] = {}

        for chunk in stream:
            if not chunk.choices:
                continue
            
            delta = chunk.choices[0].delta

            if delta.content:
                content_chunk.append(delta.content)
                # 文本token可以立刻交出去，CLI会实时打印
                yield {"type": "token", "content": delta.content}
            
            if delta.tool_calls:
                for tc_delta in delta.tool_calls:
                    # tool_call是流式增量，先按index累积，等这一轮结束后再执行
                    append_tool_call_delta(tool_calls_acc, tc_delta)
        
        # 把这一轮assistant message输出放回messages
        # 如果这一轮有tool_calls, 这条assistant message里必须带上tool_calls

        assistant_message = {"role": "assistant"}

        if content_chunk:
            assistant_message["content"] = "".join(content_chunk)
        
        if tool_calls_acc:
            assistant_message["tool_calls"] = [
                {
                    "id": tc["id"],
                    "type": "function",
                    "function": {
                        "name": tc["name"],
                        "arguments": tc["arguments"],
                    },
                }
                for tc in tool_calls_acc.values()
            ]
        
        messages.append(assistant_message)

        # 如果没有工具调用，说明模型已经给出最终回答，任务结束
        if not tool_calls_acc:
            yield {"type": "done", "content": "".join(content_chunk)}
            return
        
        # 有工具调用，就逐个执行
        for tc in tool_calls_acc.values():
            func_name = tc["name"]          # func_name就是tool name，不是函数的名称
            args = parse_tool_args(tc["arguments"])

            # 工具执行前， 先把工具名和参数交出去
            yield {
                "type": "tool_start", 
                "tool_call_id": tc["id"],
                "name": func_name,
                "args": args,
            }

            func = TOOL_FUNCTIONS.get(func_name)

            try:
                if func is None:
                    result = f"Error: 未知函数 {func_name}"
                elif "_raw" in args:
                    result = f"Error: 工具参数不是合法JSON: {args['_raw']}"
                else:
                    result = func(**args)
            except Exception as e:
                result = f"Error: 工具执行异常：{e}"

            is_error = isinstance(result, str) and result.startswith("Error:")   #is_error表示的是工具执行是否返回错误

            # 工具执行后，把结果交出去
            yield {
                "type": "tool_result",
                "tool_call_id": tc["id"],
                "name": func_name,
                "output": result,
                "is_error": is_error,
            }

            # 工具执行结果放回到message， 下一轮模型才能看到。每执行一个工具，就将执行结果的tool message放到message队列中。
            messages.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": result,
            })

    # 跑完最大轮数还没结束，说明任务失控了， 兜底结束
    yield {"type": "error", "message": f"达到最大轮数{MAX_ITERATIONS}"}
