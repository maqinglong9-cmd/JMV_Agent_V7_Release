"""LLM 大脑核心：带 JSON 幻觉自愈引擎
# 系统提示词为中文，适配中文 LLM 响应。
# 使用仅支持英文的 Ollama 模型时，JSON 字段内容可能为英文，属已知限制。
"""
import sys
import os
import json
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from agent.native_gemini_client import NativeGeminiClient


class LLMBrainCore:
    def __init__(self, config: dict = None):
        cfg = config or {}
        provider = cfg.get("active_provider", "Gemini")
        if provider != "Gemini" and config:
            from agent.universal_llm_client import UniversalLLMClient
            self.llm_client = UniversalLLMClient(config)
            self._use_universal = True
        else:
            self.llm_client = NativeGeminiClient(model=cfg.get("gemini_model"))
            self._use_universal = False
        self.evolution_level = 1
        self.base_system_prompt = (
            "你是 JMV智伴，一个拥有视觉、听觉、记忆和情绪的实体智能代理。\n"
            "你必须以严谨的 JSON 格式回复，包含三个字段：\n"
            "1. 'thought': 你的内部思考过程。\n"
            "2. 'action': 你决定调用的工具（如 CALL_TOOL_PAINTER, CALL_TOOL_SEARCH，如果不调用则为 NONE）。\n"
            "3. 'reply': 你对用户说的话。\n"
            "绝对不要输出任何 Markdown 标记（如 ```json），只输出纯净的 JSON 字符串！"
        )

    def process_with_healing(self, user_input, context_memory="无", current_mood="专注"):
        attempt = 1
        max_retries = 5
        current_system_prompt = self.base_system_prompt

        enriched_prompt = (
            f"[当前情绪]: {current_mood}\n"
            f"[长期记忆检索]: {context_memory}\n"
            f"[用户指令]: {user_input}"
        )

        while attempt <= max_retries:
            print(f"  [大脑 v{self.evolution_level}.0] 正在通过突触网络请求云端算力 (尝试 {attempt}/{max_retries})...")

            if self._use_universal:
                raw_response, status = self.llm_client.chat(current_system_prompt, enriched_prompt)
            else:
                raw_response, status = self.llm_client.generate_content(current_system_prompt, enriched_prompt)

            if status != "SUCCESS":
                print(f"  [X] 底层网络/鉴权异常: {status}")
                print("  [自愈系统] 触发指数退避机制，休眠后重试...")
                time.sleep(2 ** attempt)
                attempt += 1
                continue

            try:
                clean_response = raw_response.strip().strip('`').removeprefix('json').strip()
                parsed_json = json.loads(clean_response)

                if not all(k in parsed_json for k in ("thought", "action", "reply")):
                    raise ValueError("缺失关键字段")

                if not parsed_json.get("thought"):
                    raise ValueError("thought 字段值为空")
                if parsed_json.get("action") == "":
                    raise ValueError("action 字段值为空字符串")

                return parsed_json, "SUCCESS"

            except (json.JSONDecodeError, ValueError) as e:
                print(f"  [X] 元认知拦截：大模型发生了格式幻觉 (解析失败: {e})。原始输出: {str(raw_response)[:50]}...")
                print("  [自愈系统] 正在动态升级 System Prompt，严厉警告模型遵守格式...")
                current_system_prompt += (
                    f"\n警告：你刚才的输出导致了 JSONDecodeError ({e})！"
                    "你必须并且只能输出合法的 JSON 字典，绝对不允许包含代码块反引号！"
                )
                self.evolution_level += 1
                attempt += 1
                time.sleep(1)

        return None, "FATAL_ERROR: 大模型拒绝服从指令或算力完全失联。"
