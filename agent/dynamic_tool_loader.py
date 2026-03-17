"""
动态工具加载器（DynamicToolLoader）
=====================================
启动时扫描 jmv_workspace/dynamic_tools.py，
将 AI 生成的工具函数热加载到 ToolRegistry。

动态工具约定：
  - 函数名格式：_tool_<name>(params: str) -> str
  - 注册名格式：CALL_TOOL_<NAME>（大写）
"""
import os
import importlib.util
import py_compile
import tempfile
from typing import TYPE_CHECKING

_WORKSPACE    = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                              'jmv_workspace')
_DYNAMIC_FILE = os.path.join(_WORKSPACE, 'dynamic_tools.py')


def load_dynamic_tools(tool_registry) -> int:
    """
    扫描 dynamic_tools.py，将其中所有 _tool_xxx 函数注册到 tool_registry。
    返回成功注册的工具数量。
    """
    if not os.path.isfile(_DYNAMIC_FILE):
        return 0

    # 先做语法检查，有错误则跳过整个文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py',
                                     delete=False, encoding='utf-8') as tmp:
        with open(_DYNAMIC_FILE, 'r', encoding='utf-8') as src:
            tmp.write(src.read())
        tmp_path = tmp.name

    try:
        py_compile.compile(tmp_path, doraise=True)
    except py_compile.PyCompileError as e:
        print(f"  [动态加载] dynamic_tools.py 语法错误，跳过: {e}")
        os.unlink(tmp_path)
        return 0
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

    # 加载模块
    try:
        spec   = importlib.util.spec_from_file_location("jmv_dynamic_tools", _DYNAMIC_FILE)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    except Exception as e:
        print(f"  [动态加载] 模块加载失败: {e}")
        return 0

    # 扫描 _tool_xxx 函数，映射为 CALL_TOOL_XXX
    count = 0
    for attr_name in dir(module):
        if not attr_name.startswith('_tool_'):
            continue
        fn = getattr(module, attr_name, None)
        if not callable(fn):
            continue
        # _tool_translate → CALL_TOOL_TRANSLATE
        tool_name = 'CALL_TOOL_' + attr_name[6:].upper()
        tool_registry.register(tool_name, fn)
        print(f"  [动态加载] 已注册工具: {tool_name}")
        count += 1

    if count:
        print(f"  [动态加载] 共加载 {count} 个动态工具。")
    return count


def reload_dynamic_tools(tool_registry) -> int:
    """热重载动态工具（不需要重启应用）"""
    # 清除已缓存的模块
    import sys
    sys.modules.pop('jmv_dynamic_tools', None)
    return load_dynamic_tools(tool_registry)
