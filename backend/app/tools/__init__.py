# backend/app/tools/__init__.py
# 工具注册器+扫描器

import importlib
from pathlib import Path

_TOOLS_DIR = Path(__file__).parent
_registry: dict[str, dict] = {}  # tool_id -> {"definition": dict, "exectue": callable}

def _discover_tools() -> None:
    """ 扫描 tools/ 目录，导入所有 *_tools.py 模块。"""

    if _registry:
        return  # 已经扫描过了
    
    for py_file in sorted(_TOOLS_DIR.glob("*_tools.py")):
        module_name = f"app.tools.{py_file.stem}"

        try:
            module = importlib.import_module(module_name)
        except Exception as e:
            print(f"Warning: 导入工具模块失败：{module_name}: {e}")
            continue
        
        definition = getattr(module, "DEFINITION", None)
        execute_fn = getattr(module, "execute", None)

        if not definition or "id" not in definition:
            print(f"Warning: 工具模块 {module_name} 缺少 DEFINITION 或 DEFINITION.id, 跳过")
            continue
        
        if not execute_fn or not callable(execute_fn):
            print(f"Warning: 工具模块 {module_name} 缺少 execute 函数，跳过")
            continue

        _registry[definition["id"]] = {
            "definition": definition,
            "execute": execute_fn,
        }

        print(f"已注册工具: {definition['id']}")

def get_all_definitions() -> list[dict]:
    """返回所有工具的 DEFINITION 列表。"""
    _discover_tools()
    return [entry["definition"] for entry in _registry.values()]

def execute_tool(tool_id: str, args: dict, **kwargs) -> str:
    """按 tool_id 执行工具。任何异常都转成字符串返回，不抛。"""
    _discover_tools()
    entry = _registry.get(tool_id)
    if not entry:
        return f"Error: 未知工具 '{tool_id}'"
    
    try:
        return entry["execute"](args, **kwargs)
    except Exception as e:
        print(f"Warning: 工具 '{tool_id}' 执行异常：{e}")
        return f"Error: 工具 '{tool_id}' 执行失败：{e}"
