# backend/app/tools.py
# 4th simple test of LLM API, only define tools function and tool description

from pathlib import Path

WORKSPACE = Path(__file__).parent.parent.parent / "workspace" / "files"
WORKSPACE.mkdir(parents=True, exist_ok=True)

def tool_list_files() -> str:
    """这里不需要传入参数，就是直接列出WORKSPACE下的所有文件。"""
    files = [str(p.relative_to(WORKSPACE)) for p in WORKSPACE.rglob("*") if p.is_file()]
    return "\n".join(files) if files else "（目录为空）"

def tool_read_file(path: str) -> str:
    """读取WORKSPACE下某个文件的内容。"""
    target = (WORKSPACE / path).resolve()          #得到一个标准绝对路径
    if not str(target).startswith(str(WORKSPACE.resolve())):    # 如果path是个类似../../etc/password之类的路径
        return f"Error: 不允许越权访问！"       # tools中所有的错误没有使用raise Exception，而是返回一个Error开头的字符串给模型。
    if not target.exists():
        return f"Error: 文件不存在:{path}"
    if target.is_dir():
        return f"Error: 路径是一个目录:{path}"
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

TOOL_DEFINITIONS = [
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
            "description": "读取工作目录下某个文件的内容",
            "parameters": {
                "type": "object", 
                "properties": {"path": {"type": "string", "description": "文件路径"}},
                "required": ["path"],
              },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "写入工作目录下某个文件",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "文件路径"}, 
                    "content": {"type": "string", "description": "文件内容"}
                    },
                "required": ["path", "content"],
            },
        },
    },
]
