"""纯原生 urllib Gemini HTTP 客户端，零 SDK 依赖"""
import os
import json
import urllib.request
import urllib.error


class NativeGeminiClient:
    def __init__(self, model: str = None):
        self.api_key = os.environ.get("GEMINI_API_KEY", "").strip()
        if len(self.api_key) < 10:
            raise ValueError(
                "[NativeGeminiClient] GEMINI_API_KEY 未设置或无效。"
                "请通过环境变量传入：export GEMINI_API_KEY=your_key"
            )
        _model = model or os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
        self.endpoint = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{_model}:generateContent?key={self.api_key}"
        )

    def generate_content(self, system_instruction, user_prompt):
        payload = {
            "system_instruction": {
                "parts": [{"text": system_instruction}]
            },
            "contents": [{
                "parts": [{"text": user_prompt}]
            }],
            "generationConfig": {
                "temperature": 0.7,
                "response_mime_type": "application/json"
            }
        }

        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            self.endpoint, data=data,
            headers={'Content-Type': 'application/json'}
        )

        try:
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                text = result['candidates'][0]['content']['parts'][0]['text']
                return text, "SUCCESS"
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            return None, f"HTTP_ERROR_{e.code}: {error_body}"
        except Exception as e:
            return None, f"NETWORK_ERROR: {str(e)}"
