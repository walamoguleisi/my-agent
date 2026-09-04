# backend/app/tools/read_file_tools.py
# Define seperate tool function: read file tool

from pathlib import Path

WORKSPACE = Path(__file__).parent.parent.parent.parent / "workspace" / "files"

DEFINITION = {
    "id": "read_file",
    "name": "read_file",
    "description": "读取工作目录下某个文件的完整内容",
    "parameters": {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "相对于工作目录的文件路径"},
        },
        "required": ["path"],
    },
}

def execute(args: dict, **kwargs) -> str:
    path = args.get("path", "")

    if not path:
        return "Error: 缺少 path 参数"
    
    target = (WORKSPACE / path).resolve()

    if not str(target).startswith(str(WORKSPACE.resolve())):
        return "Error: 不允许越权访问！"
    if not target.exists():
        return f"Error: 文件不存在: {path}"
    if target.is_dir():
        return f"Error: 路径是一个目录: {path}"
    
    try:
        return target.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return f"Error: 文件不是有效的UTF-8文本文件: {path}"
