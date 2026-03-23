"""LLM Provider 基类 —— 零依赖，纯标准库"""
import json
import os
import ssl
import sys
import urllib.request
import urllib.error


def _is_android() -> bool:
    """检测是否运行在 Android 环境（/data/data 是 Android 应用沙箱标志）"""
    return sys.platform == "linux" and os.path.exists("/data/data")


def _build_ssl_context() -> ssl.SSLContext:
    """
    根据平台构造合适的 SSL 上下文：
    - Android：关闭证书验证（无系统 CA bundle）
    - Windows / macOS / Linux 桌面：使用系统 CA bundle 进行完整验证
    """
    if _is_android():
        # Android Python 环境无系统 CA bundle，必须跳过证书验证
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            return ctx
        except Exception:
            # create_default_context 失败时用最宽松上下文兜底
            ctx = ssl._create_unverified_context()
            return ctx
    else:
        # Windows / macOS / Linux 桌面：使用系统受信 CA，保持完整验证
        try:
            return ssl.create_default_context()
        except Exception:
            # 极端情况下回退到无验证（不应发生，仅作安全兜底）
            return ssl._create_unverified_context()


_SSL_CTX: ssl.SSLContext = _build_ssl_context()


class BaseLLMProvider:
    """所有 LLM 供应商的���象基类"""

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
            with urllib.request.urlopen(req, timeout=timeout, context=_SSL_CTX) as resp:
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
