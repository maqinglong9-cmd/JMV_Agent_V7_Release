"""零依赖多供应商 LLM 路由客户端"""
import json
import urllib.request
import urllib.error


class UniversalLLMClient:
    def __init__(self, config):
        self.config = config
        self.active_provider = config.get("active_provider", "Gemini")

    def _post_request(self, url, headers, payload):
        req = urllib.request.Request(
            url, data=json.dumps(payload).encode('utf-8'), headers=headers
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                return json.loads(response.read().decode('utf-8')), "SUCCESS"
        except urllib.error.HTTPError as e:
            return None, f"HTTP_{e.code}: {e.read().decode('utf-8')}"
        except Exception as e:
            return None, f"NETWORK_ERROR: {str(e)}"

    def chat(self, system_prompt, user_prompt):
        provider = self.active_provider

        if provider == "Ollama":
            url = self.config.get("ollama_endpoint", "http://localhost:11434/api/generate")
            model = self.config.get("ollama_model", "llama3")
            payload = {"model": model, "system": system_prompt, "prompt": user_prompt, "stream": False}
            res, status = self._post_request(url, {"Content-Type": "application/json"}, payload)
            if status == "SUCCESS":
                return res.get("response", ""), status
            return None, status

        elif provider in ["OpenAI", "DeepSeek"]:
            api_key = self.config.get(f"{provider.lower()}_key", "")
            url = ("https://api.openai.com/v1/chat/completions" if provider == "OpenAI"
                   else "https://api.deepseek.com/chat/completions")
            model = (self.config.get("openai_model", "gpt-3.5-turbo")
                     if provider == "OpenAI"
                     else self.config.get("deepseek_model", "deepseek-chat"))
            headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            }
            res, status = self._post_request(url, headers, payload)
            if status == "SUCCESS":
                return res["choices"][0]["message"]["content"], status
            return None, status

        elif provider == "Claude":
            api_key = self.config.get("claude_key", "")
            url = "https://api.anthropic.com/v1/messages"
            headers = {
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
            payload = {
                "model": self.config.get("claude_model", "claude-3-haiku-20240307"),
                "system": system_prompt,
                "messages": [{"role": "user", "content": user_prompt}],
                "max_tokens": 1024
            }
            res, status = self._post_request(url, headers, payload)
            if status == "SUCCESS":
                return res["content"][0]["text"], status
            return None, status

        else:  # Gemini (default)
            api_key = self.config.get("gemini_key", "")
            _model = self.config.get("gemini_model", "gemini-2.5-flash")
            url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
                   f"{_model}:generateContent?key={api_key}")
            payload = {
                "system_instruction": {"parts": [{"text": system_prompt}]},
                "contents": [{"parts": [{"text": user_prompt}]}]
            }
            res, status = self._post_request(url, {"Content-Type": "application/json"}, payload)
            if status == "SUCCESS":
                return res['candidates'][0]['content']['parts'][0]['text'], status
            return None, status
