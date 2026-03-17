"""终极集成 Agent：长期记忆 + 情绪引擎"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from agent.native_vector_db import NativeVectorDB
from agent.emotion_engine import EmotionEngine

_PROJECT_ROOT = os.path.join(os.path.dirname(__file__), '..')


class UltimateCompanionAgent:
    def __init__(self):
        db_path = os.path.join(os.path.abspath(_PROJECT_ROOT), "jmv_long_term_memory.json")
        self.long_term_memory = NativeVectorDB(db_path=db_path)
        self.emotion = EmotionEngine()
        self.short_term_context = []
        self.is_ready = False

    def process_input(self, user_text):
        print(f"\n[用户]: {user_text}")
        self.emotion.tick()

        if "记住" in user_text:
            fact = user_text.replace("记住", "").strip()
            self.long_term_memory.memorize(fact)
            base_reply = "好的，我已经把它深深存入了我的底层硬盘中。"
            return self.emotion.apply_mood_modifier(base_reply)

        memories = self.long_term_memory.recall(user_text)
        if memories:
            print(f"  [闪回] 长期记忆检索到相关线索: {memories}")
            base_reply = f"根据我之前记住的信息：{memories[0]}。我以此为你提供建议。"
        else:
            base_reply = "我明白了你的意思，正在处理当前任务..."

        return self.emotion.apply_mood_modifier(base_reply)
