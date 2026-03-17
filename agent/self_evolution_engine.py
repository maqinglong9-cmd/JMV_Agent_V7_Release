"""
AI 自我进化引擎（SelfEvolutionEngine）
========================================
实现真正的 AI 驱动代码迭代升级循环：

  [用户交互] → [记录交互日志+评分]
      ↓
  [累积到阈值] → [调用 LLM 分析失败模式]
      ↓
  [生成结构化改进方案 JSON]
      ↓
  [写入新规则到元认知持久化存储]
      ↓
  [注册新工具到 ToolRegistry（动态加载）]
      ↓
  [版本号 PATCH 递增] → [更新 latest.json]

零外部依赖，全部使用标准库 + 项目已有模块。
"""
import os
import json
import time
import py_compile
import tempfile
import importlib
import importlib.util
from typing import Callable, Optional

# 路径常量
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_WORKSPACE = os.path.join(_ROOT, 'jmv_workspace')
_EVOLUTION_LOG = os.path.join(_WORKSPACE, 'evolution_log.jsonl')
_DYNAMIC_TOOLS  = os.path.join(_WORKSPACE, 'dynamic_tools.py')
_LATEST_JSON    = os.path.join(_ROOT, 'latest.json')
_VERSION_FILE   = os.path.join(_ROOT, 'version.py')

# 触发 AI 分析的最小交互次数（可配置）
_ANALYSIS_THRESHOLD = 20


class SelfEvolutionEngine:
    """
    AI 自我进化引擎：记录→分析→改进→升级 完整闭环。
    """

    def __init__(self, tool_registry=None, metacognition=None):
        """
        参数:
          tool_registry   -- ToolRegistry 实例，用于动态注册新工具
          metacognition   -- MetacognitionComponent 实例，用于写入新规则
        """
        self._tool_registry   = tool_registry
        self._metacognition   = metacognition
        self._interaction_count = 0
        os.makedirs(_WORKSPACE, exist_ok=True)

    # ── 1. 交互日志记录 ───────────────────────────────────────

    def log_interaction(
        self,
        user_input: str,
        agent_output: str,
        success: bool,
        score: float = 1.0,
        tool_used: str = '',
        error_msg: str = '',
    ) -> None:
        """
        记录一次交互到 JSONL 日志文件（每行一条 JSON）。
        score: 0.0（完全失败）~ 1.0（完全成功）
        """
        entry = {
            'ts':          time.strftime('%Y-%m-%d %H:%M:%S'),
            'input':       user_input[:500],
            'output':      agent_output[:500],
            'success':     success,
            'score':       round(score, 3),
            'tool_used':   tool_used,
            'error':       error_msg[:200],
        }
        try:
            with open(_EVOLUTION_LOG, 'a', encoding='utf-8') as f:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        except Exception as e:
            print(f"  [进化引擎] 日志写入失败: {e}")

        self._interaction_count += 1
        if self._interaction_count >= _ANALYSIS_THRESHOLD:
            self._interaction_count = 0  # 重置计数器
            # 触发后台分析（不阻塞当前线程）
            import threading
            threading.Thread(target=self._auto_analyze, daemon=True).start()

    # ── 2. 失败模式分析 ──────────────────────────────────────

    def read_recent_log(self, n: int = 50) -> list:
        """读取最近 n 条交互日志"""
        if not os.path.exists(_EVOLUTION_LOG):
            return []
        entries = []
        try:
            with open(_EVOLUTION_LOG, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            entries.append(json.loads(line))
                        except json.JSONDecodeError:
                            pass
        except Exception:
            return []
        return entries[-n:]

    def analyze_failures(self, llm_client=None, progress_cb: Optional[Callable[[str], None]] = None) -> dict:
        """
        分析最近的交互日志，识别失败模式并生成改进方案。

        参数:
          llm_client  -- UniversalLLMClient 实例（可选）
          progress_cb -- 进度回调函数，接收状态字符串

        返回改进方案 dict，格式：
        {
          "analysis_summary": "...",
          "new_rules": [{"trigger": "...", "action": "..."}],
          "new_tool_code": "...",  # 可选，Python 函数代码
          "new_tool_name": "...",  # 可选，工具注册名
          "patch_version": true    # 是否递增版本号
        }
        """
        _cb = progress_cb or (lambda msg: print(f"  [进化分析] {msg}"))

        entries = self.read_recent_log(50)
        if not entries:
            _cb("日志为空，无法分析。")
            return {"analysis_summary": "日志为空", "new_rules": []}

        failed    = [e for e in entries if not e.get('success', True)]
        total     = len(entries)
        fail_rate = len(failed) / total if total > 0 else 0

        _cb(f"分析 {total} 条记录，失败率 {fail_rate:.1%}...")

        # 统计失败的工具调用
        from collections import Counter
        fail_tools = Counter(e.get('tool_used', '') for e in failed if e.get('tool_used'))

        # 统计失败的输入模式（取前 3 条）
        fail_inputs = [e['input'] for e in failed[:3]]

        # 构建分析摘要（本地统计，不依赖 LLM）
        local_summary = (
            f"总交互 {total} 次，失败 {len(failed)} 次（{fail_rate:.1%}）。"
            f"问题工具：{dict(fail_tools.most_common(3))}。"
            f"失败输入样例：{fail_inputs[:2]}"
        )

        patch = {
            "analysis_summary": local_summary,
            "new_rules":        [],
            "new_tool_code":    None,
            "new_tool_name":    None,
            "patch_version":    fail_rate > 0.1,  # 失败率超 10% 则升版
        }

        # 尝试用 LLM 生成更深入的分析和新规则
        if llm_client and fail_inputs:
            _cb("调用 LLM 生成改进方案...")
            patch = self._llm_analyze(llm_client, local_summary, fail_inputs, patch, _cb)
        else:
            _cb("无 LLM 连接，使用本地规则推断。")
            # 本地推断：失败工具 → 规则
            for tool_name, count in fail_tools.most_common(2):
                if tool_name:
                    patch["new_rules"].append({
                        "trigger": f"类似导致{tool_name}失败的输入",
                        "action":  "CALL_TOOL_SEARCH"  # 降级到搜索
                    })

        _cb(f"分析完成：{patch['analysis_summary'][:80]}...")
        return patch

    def _llm_analyze(self, client, local_summary: str, fail_inputs: list,
                     patch: dict, cb: Callable) -> dict:
        """调用 LLM 生成改进方案，解析失败时返回原始 patch"""
        system_prompt = """你是AI自我优化专家。分析以下交互失败案例，输出JSON改进方案。
必须严格输出以下JSON格式（不要任何其他内容）：
{
  "analysis_summary": "问题根因简述（50字内）",
  "new_rules": [
    {"trigger": "触发条件关键词", "action": "CALL_TOOL_XXX"}
  ],
  "patch_version": true
}
可用工具名称：CALL_TOOL_SEARCH, CALL_TOOL_CALCULATOR, CALL_TOOL_CODER,
CALL_TOOL_TRANSLATE, CALL_TOOL_SUMMARIZE, CALL_TOOL_FILE_WRITE, CALL_TOOL_PAINTER"""

        user_msg = (
            f"本地分析结果：{local_summary}\n"
            f"失败输入样例：{fail_inputs}\n"
            f"请生成改进方案JSON："
        )

        try:
            response, status = client.chat(system_prompt, user_msg)
            if status != 'SUCCESS' or not response:
                return patch

            # 提取 JSON（容忍 LLM 输出的 markdown 包装）
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if not json_match:
                return patch

            data = json.loads(json_match.group())
            patch["analysis_summary"] = data.get("analysis_summary", patch["analysis_summary"])
            patch["new_rules"]        = data.get("new_rules", [])
            patch["patch_version"]    = data.get("patch_version", patch["patch_version"])

        except Exception as e:
            cb(f"LLM 分析解析失败: {e}，使用本地结果。")

        return patch

    # ── 3. 应用改进方案 ──────────────────────────────────────

    def apply_patch(self, patch: dict, progress_cb: Optional[Callable[[str], None]] = None) -> bool:
        """
        应用分析结果：写入新规则、注册新工具、递增版本号。
        返回 True 表示至少一项改进被成功应用。
        """
        _cb = progress_cb or (lambda msg: print(f"  [进化应用] {msg}"))
        applied = False

        # 写入新规则到元认知
        new_rules = patch.get("new_rules", [])
        if new_rules and self._metacognition:
            for rule in new_rules:
                trigger = rule.get("trigger", "")
                action  = rule.get("action", "")
                if trigger and action:
                    self._metacognition.reflect_and_upgrade(trigger, action)
                    _cb(f"新规则已写入：{trigger[:30]} → {action}")
                    applied = True

        # 注册新工具（如果 LLM 生成了工具代码）
        tool_code = patch.get("new_tool_code", "")
        tool_name = patch.get("new_tool_name", "")
        if tool_code and tool_name and self._tool_registry:
            if self._register_dynamic_tool(tool_name, tool_code, _cb):
                applied = True

        # 递增版本号
        if patch.get("patch_version") and applied:
            new_ver = self.bump_patch_version()
            if new_ver:
                _cb(f"版本号已更新至 {new_ver}")
                self.export_latest_json(new_ver)

        return applied

    def _register_dynamic_tool(self, tool_name: str, tool_code: str,
                                cb: Callable) -> bool:
        """语法检查后写入 dynamic_tools.py，并动态注册到 ToolRegistry"""
        # 语法检查（防止崩溃）
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py',
                                        delete=False, encoding='utf-8') as tmp:
            tmp.write(tool_code)
            tmp_path = tmp.name

        try:
            py_compile.compile(tmp_path, doraise=True)
        except py_compile.PyCompileError as e:
            cb(f"工具代码语法错误，跳过: {e}")
            os.unlink(tmp_path)
            return False
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

        # 追加到 dynamic_tools.py
        try:
            with open(_DYNAMIC_TOOLS, 'a', encoding='utf-8') as f:
                f.write(f"\n# === 自动生成工具: {tool_name} ===\n")
                f.write(tool_code)
                f.write('\n')
        except Exception as e:
            cb(f"写入工具文件失败: {e}")
            return False

        # 动态加载并注册
        try:
            spec   = importlib.util.spec_from_file_location("dynamic_tools", _DYNAMIC_TOOLS)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            fn_name = tool_name.lower().replace('call_tool_', '_tool_')
            fn = getattr(module, fn_name, None)
            if fn and callable(fn) and self._tool_registry:
                self._tool_registry.register(tool_name, fn)
                cb(f"新工具 {tool_name} 已注册并可立即使用。")
                return True
        except Exception as e:
            cb(f"动态加载工具失败: {e}")

        return False

    # ── 4. 版本号管理 ────────────────────────────────────────

    def bump_patch_version(self) -> str | None:
        """
        读取 version.py，将 patch 号加 1，写回文件。
        例如 "1.1.0" → "1.1.1"
        返回新版本号字符串，失败返回 None。
        """
        if not os.path.exists(_VERSION_FILE):
            return None
        try:
            with open(_VERSION_FILE, 'r', encoding='utf-8') as f:
                content = f.read()

            import re
            match = re.search(r'__version__\s*=\s*["\'](\d+)\.(\d+)\.(\d+)["\']', content)
            if not match:
                return None

            major, minor, patch = int(match.group(1)), int(match.group(2)), int(match.group(3))
            new_ver = f"{major}.{minor}.{patch + 1}"
            new_content = re.sub(
                r'(__version__\s*=\s*["\'])\d+\.\d+\.\d+(["\'])',
                f'\\g<1>{new_ver}\\g<2>',
                content
            )
            with open(_VERSION_FILE, 'w', encoding='utf-8') as f:
                f.write(new_content)

            print(f"  [进化引擎] 版本号已更新：{major}.{minor}.{patch} → {new_ver}")
            return new_ver
        except Exception as e:
            print(f"  [进化引擎] 版本号更新失败: {e}")
            return None

    def export_latest_json(self, version: str) -> None:
        """更新 latest.json 中的版本号（保留其他字段）"""
        try:
            data: dict = {}
            if os.path.exists(_LATEST_JSON):
                with open(_LATEST_JSON, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            data['version'] = version
            data['release_notes'] = f"JMV智伴 {version}（AI自动进化版本）"
            with open(_LATEST_JSON, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"  [进化引擎] latest.json 更新失败: {e}")

    def get_evolution_stats(self) -> dict:
        """返回进化统计数据，供 UI 展示"""
        entries = self.read_recent_log(100)
        total   = len(entries)
        failed  = sum(1 for e in entries if not e.get('success', True))
        rules_count = self._metacognition.rule_count() if self._metacognition else 0

        # 读取当前版本号
        current_version = "未知"
        try:
            from version import __version__
            current_version = __version__
        except Exception:
            pass

        return {
            "current_version": current_version,
            "total_interactions": total,
            "failed_interactions": failed,
            "fail_rate": f"{failed/total:.1%}" if total else "0%",
            "learned_rules": rules_count,
            "log_file": _EVOLUTION_LOG,
        }

    # ── 5. 自动触发 ──────────────────────────────────────────

    def _auto_analyze(self) -> None:
        """后台自动分析（达到交互阈值时触发），无 LLM 时仍可执行本地分析"""
        print(f"  [进化引擎] 达到 {_ANALYSIS_THRESHOLD} 次交互阈值，触发自动分析...")
        patch = self.analyze_failures()
        if patch.get("new_rules") or patch.get("patch_version"):
            self.apply_patch(patch)
