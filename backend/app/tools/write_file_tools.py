# backend/app/tools/write_file_tools.py
# Define seperate tool function: write file tool

from pathlib import Path

WORKSPACE = Path(__file__).parent.parent.parent.parent / "workspace" / "files"

DEFINITION = {
    "id": "write_file",
    "name": "write_file",
    "description": "写入工作目录下某个文件的内容",
    "parameters": {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "相对于工作目录的文件路径"},
            "content": {"type": "string", "description": "要写入的内容"},
        },
        "required": ["path", "content"],
    },
}   


def execute(args: dict, **kwargs) -> str:
    path = args.get("path", "")
    content = args.get("content", "")

    if not path:
        return "Error: 缺少 path 参数"
    
    target = (WORKSPACE / path).resolve()

    if not str(target).startswith(str(WORKSPACE.resolve())):
        return "Error: 不允许越权访问！"
    
    target.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        target.write_text(content, encoding="utf-8")
        return f"已写入: {path}（{len(content)}字符）"
    except Exception as e:
        return f"Error: 写入文件失败: {e}"
