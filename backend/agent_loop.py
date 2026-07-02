# backend/agent_loop.py

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

MAX_ITERATION2 = 20     #限制loop的最大循环次数是20

# === 工具定义 ===

def tool_list_files() -> str:
    """列出WORKSPACE下的所有文件。"""
    files = [str(p.relative_to(WORKSPACE)) for p in WORKSPACE.rglob("*") if p.is_file()]
    if not files:
        return "（目录为空）"
    return "\n".join(files)

def tool_read_file(path: str) -> str:
    """读取WORKSPACE下某个文件的内容。"""
    target = (WORKSPACE / path).resolve()
    if not str(target).startswith(str(WORKSPACE.resolve())):
        return "不允许越权访问！"
    if not target.exists():
        return f"ERROR: 文件不存在:{path}"
    return target.read_text(encoding="utf-8")

def tool_write_file(path: str, content: str) -> str:
    """ 写入WORKSPACE下某个文件。"""
    target = (WORKSPACE / path).resolve()
    if not str(target).startswith(str(WORKSPACE.resolve())):
        return "ERROR: 不允许越权访问！"
    target.parent.mkdir(parents=True, exist_ok=True)
