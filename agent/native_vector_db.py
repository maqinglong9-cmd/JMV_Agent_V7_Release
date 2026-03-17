"""
零依赖本地语义向量数据库
================================
检索算法：字符级 TF-IDF + Bigram + 余弦相似度
- 单字 unigram：捕获精确字符匹配
- 双字 bigram ：捕获词汇上下文（如"人工智能"≠"人工"+"智能"单独出现）
- IDF 权重：降低高频字（的、了、是）的影响
- 余弦相似度：归一化后的向量夹角距离

相比纯编辑距离：
  ✅ 支持语义相近词（"你好" ≈ "您好"）
  ✅ 长文本不退化（TF 归一化）
  ✅ 高频词降权（IDF）
  ✅ 双字符上下文
"""
import os
import json
import math
import time
from collections import Counter
from typing import List, Tuple


def _tokenize(text: str) -> List[str]:
    """
    中英文混合分词：
    - 每个汉字作为 unigram token
    - 相邻两个汉字组成 bigram token
    - 英文按空格切割
    """
    chars = list(str(text))
    tokens: List[str] = []

    i = 0
    while i < len(chars):
        c = chars[i]
        if c.strip():
            # 汉字 / 字母数字 unigram
            tokens.append(c)
            # 汉字 bigram（连续两个非空字符）
            if i + 1 < len(chars) and chars[i + 1].strip():
                tokens.append(c + chars[i + 1])
        i += 1

    return tokens


def _tf(tokens: List[str]) -> dict:
    """计算词频（Term Frequency），归一化到 [0,1]"""
    if not tokens:
        return {}
    counts = Counter(tokens)
    total = len(tokens)
    return {term: count / total for term, count in counts.items()}


def _cosine(v1: dict, v2: dict, idf: dict | None = None) -> float:
    """
    计算两个 TF 向量的余弦相似度。
    可选传入 IDF 字典对 TF 进行加权（TF-IDF）。
    """
    if not v1 or not v2:
        return 0.0

    if idf:
        v1 = {k: v * idf.get(k, 1.0) for k, v in v1.items()}
        v2 = {k: v * idf.get(k, 1.0) for k, v in v2.items()}

    common = set(v1) & set(v2)
    if not common:
        return 0.0

    dot = sum(v1[k] * v2[k] for k in common)
    mag1 = math.sqrt(sum(x * x for x in v1.values()))
    mag2 = math.sqrt(sum(x * x for x in v2.values()))

    if mag1 == 0 or mag2 == 0:
        return 0.0
    return dot / (mag1 * mag2)


class NativeVectorDB:
    """
    TF-IDF 语义向量数据库，带 JSON 持久化。
    """

    def __init__(self, db_path: str, similarity_threshold: float = 0.05):
        self.db_path = db_path
        self.similarity_threshold = similarity_threshold
        self.documents: List[dict] = []
        self._idf: dict = {}
        self._load_db()

    # ── 持久化 ────────────────────────────────────────────────

    def _load_db(self) -> None:
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.documents = data.get('documents', [])
                self._idf        = data.get('idf', {})
            except Exception:
                self.documents = []
                self._idf = {}
        else:
            self.documents = []
            self._idf = {}

    def _save_db(self) -> None:
        os.makedirs(os.path.dirname(self.db_path) or '.', exist_ok=True)
        with open(self.db_path, 'w', encoding='utf-8') as f:
            json.dump(
                {'documents': self.documents, 'idf': self._idf},
                f, ensure_ascii=False, indent=2
            )

    # ── IDF 重建 ──────────────────────────────────────────────

    def _rebuild_idf(self) -> None:
        """用所有文档重建 IDF 权重表"""
        n = len(self.documents)
        if n == 0:
            self._idf = {}
            return

        # 每个 term 出现在多少文档中
        doc_freq: Counter = Counter()
        for doc in self.documents:
            for term in set(doc.get('tf', {}).keys()):
                doc_freq[term] += 1

        self._idf = {
            term: math.log((n + 1) / (df + 1)) + 1.0
            for term, df in doc_freq.items()
        }

    # ── 公共 API ─────────────────────────────────────────────

    def memorize(self, memory_text: str, tag: str = "general") -> None:
        """存入一条记忆，自动更新 IDF"""
        tokens = _tokenize(memory_text)
        doc = {
            "id":      int(time.time() * 1000),
            "content": memory_text,
            "tag":     tag,
            "tf":      _tf(tokens),
        }
        self.documents.append(doc)
        self._rebuild_idf()
        self._save_db()
        print(f"  [海马体] 已将关键信息刻入长期记忆: '{memory_text[:40]}...' " if len(memory_text) > 40
              else f"  [海马体] 已刻入长期记忆: '{memory_text}'")

    def recall(self, query: str, top_k: int = 3) -> List[str]:
        """
        语义检索：返回最相似的 top_k 条记忆内容。
        相似度低于 similarity_threshold 的结果被过滤。
        """
        if not self.documents:
            return []

        query_tf = _tf(_tokenize(query))
        scored: List[Tuple[float, str]] = []

        for doc in self.documents:
            score = _cosine(query_tf, doc.get('tf', {}), self._idf)
            if score >= self.similarity_threshold:
                scored.append((score, doc['content']))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [content for _, content in scored[:top_k]]

    def size(self) -> int:
        return len(self.documents)

    def clear(self) -> None:
        self.documents = []
        self._idf = {}
        self._save_db()
