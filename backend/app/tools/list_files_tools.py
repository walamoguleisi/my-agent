# backend/app/tools/list_files_tools.py
# Define seperate tool function: list files tool

from pathlib import Path

WORKSPACE = Path(__file__).parent.parent.parent.parent / "workspace" / "files"

WORKSPACE.mkdir(parents=True, exist_ok=True)

DEFINITION = {
    "id": "list_files",
    "name": "list_files",
    "description": "列出工作目录下所有文件的相对路径",
    "parameters": {
        "type": "object",
        "properties": {},
    },
}

def execute(args: dict, **kwargs) -> str:
    files = [str(p.relative_to(WORKSPACE)) for p in WORKSPACE.rglob("*") if p.is_file()]
    return "\n".join(files) if files else "(目录为空)" 
