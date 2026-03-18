"""LLM Provider 基类 —— 零依赖，纯标准库"""
import json
import urllib.request
import urllib.error


class BaseLLMProvider:
    """所有 LLM 供应商的抽象基类"""

    name: str = 'base'

    def call(self, system: str, user: str, config: dict) -> tuple:
        """
        调用 LLM 接口，返回 (response_text, status_str)。
        status_str == 'SUCCESS' 表示成功，否则为错误描述。
        """
        raise NotImplementedError

    @staticmethod
    def _post(url: str, headers: dict, payload: dict, timeout: int = 30) -> tuple:
        """
        发送 POST 请求，返回 (parsed_json_or_None, status_str)。
        纯 stdlib 实现，无第三方依赖。
        """
        req = urllib.request.Request(
            url,
            data=json.dumps(payload, ensure_ascii=False).encode('utf-8'),
            headers=headers,
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode('utf-8')), 'SUCCESS'
        except urllib.error.HTTPError as e:
            body = ''
            try:
                body = e.read().decode('utf-8')
            except Exception:
                pass
            return None, f'HTTP_{e.code}: {body[:200]}'
        except urllib.error.URLError as e:
            return None, f'URL_ERROR: {str(e.reason)}'
        except Exception as e:
            return None, f'NETWORK_ERROR: {str(e)}'
