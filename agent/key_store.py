"""API Key 混淆存储（XOR + base64）——防止明文泄露，非加密级安全"""
import base64

_SALT = b'JMV_AGENT_2024_SALT_KEY_PROTECT_XOR'
_PREFIX = 'jmv1:'  # 标识已混淆的字符串


def encrypt(text: str) -> str:
    """混淆 API Key（XOR + base64）。已混淆的字符串直接返回。"""
    if not text or text.startswith(_PREFIX):
        return text
    data = text.encode('utf-8')
    salt = (_SALT * ((len(data) // len(_SALT)) + 1))[:len(data)]
    xored = bytes(a ^ b for a, b in zip(data, salt))
    return _PREFIX + base64.b64encode(xored).decode('ascii')


def decrypt(encoded: str) -> str:
    """解混淆 API Key。未混淆的字符串（旧格式）直接返回。"""
    if not encoded or not encoded.startswith(_PREFIX):
        return encoded  # 兼容旧版明文格式
    try:
        raw = base64.b64decode(encoded[len(_PREFIX):].encode('ascii'))
        salt = (_SALT * ((len(raw) // len(_SALT)) + 1))[:len(raw)]
        return bytes(a ^ b for a, b in zip(raw, salt)).decode('utf-8')
    except Exception:
        return encoded


def is_encrypted(text: str) -> bool:
    """判断字符串是否已经过混淆处理。"""
    return bool(text) and text.startswith(_PREFIX)


def encrypt_config(config: dict, key_fields: list) -> dict:
    """
    对 config 字典中指定字段进行混淆，返回新字典（不修改原始对象）。
    key_fields: 需要混淆的字段名列表（如 ['gemini_key', 'openai_key', ...]）
    """
    result = dict(config)
    for field in key_fields:
        if field in result and result[field]:
            result = {**result, field: encrypt(result[field])}
    return result


def decrypt_config(config: dict, key_fields: list) -> dict:
    """
    对 config 字典中指定字段进行解混淆，返回新字典（不修改原始对象）。
    """
    result = dict(config)
    for field in key_fields:
        if field in result and result[field]:
            result = {**result, field: decrypt(result[field])}
    return result
