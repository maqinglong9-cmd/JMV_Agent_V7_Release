"""异步适配器：后台线程运行 Agent，支持 LLM 增强模式（含重试）"""
import os
import json
import time
import threading
from kivy.clock import Clock
from adapter.event_bus import EventBus
from core.agent import WholeBrainAgent
from core.memory import MemoryStore

_CONFIG_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'jmv_compute_config.json'
)

# 单次 LLM 调用的 System Prompt（要求返回 9 行，每行对应一个脑区）
_LLM_SYSTEM_PROMPT = """你是一个神经科学 AI 仿真系统，负责模拟人类大脑对多模态刺激的响应。
用户输入包含：视觉刺激、听觉刺激、触觉刺激。
你必须按顺序输出恰好 9 行，每行对应一个脑区的处理结果，格式如下（行首必须保留括号标签）：
[脑脊液] ...
[脑干 (Brainstem) - 含中脑, 脑桥, 延髓] ...
[下丘脑 (Hypothalamus)] ...
[丘脑 (Thalamus)] ...
[枕叶 (Occipital Lobe)] ...
[颞叶 (Temporal Lobe)] ...
[顶叶 (Parietal Lobe)] ...
[额叶 (Frontal Lobe)] ...
[小脑 (Cerebellum)] ...

每行内容需基于用户的实际输入进行智能分析，简洁专业，50字以内。严禁输出多余内容。"""


def _load_config() -> dict:
    """读取本地 LLM 配置（文件 + 环境变量密钥），失败返回空 dict"""
    from ui.llm_config_data import _DEFAULT_CONFIG, _ENV_KEY_MAP as _DATA_ENV_MAP
    config: dict = dict(_DEFAULT_CONFIG)
    try:
        if os.path.exists(_CONFIG_FILE):
            with open(_CONFIG_FILE, 'r', encoding='utf-8') as f:
                config.update(json.load(f))
    except Exception:
        pass
    # 密钥从环境变量补充（优先级更高）
    for field, env_var in _DATA_ENV_MAP.items():
        val = os.environ.get(env_var, '')
        if val:
            config[field] = val
    # 如果没有加载到任何 active_provider 或文件不存在，返回空 dict（表示无 LLM）
    if not os.path.exists(_CONFIG_FILE):
        return {}
    return config


def _init_llm_client(config: dict):
    """初始化 LLM 客户端，失败返回 None"""
    if not config:
        return None
    try:
        from agent.universal_llm_client import UniversalLLMClient
        client = UniversalLLMClient(config)
        return client
    except Exception:
        return None


def _llm_perceive(client, visual: str, audio: str, tactile: str,
                  max_retries: int = 2) -> list:
    """
    用 LLM 生成 9 条脑区响应，解析失败时返回空列表。
    网络错误时自动重试（指数退避，最多 max_retries 次）。
    """
    user_prompt = (
        f"视觉刺激：{visual}\n"
        f"听觉刺激：{audio}\n"
        f"触觉刺激：{tactile}"
    )

    for attempt in range(max_retries + 1):
        try:
            response, status = client.chat(_LLM_SYSTEM_PROMPT, user_prompt)
            if status != 'SUCCESS' or not response:
                if attempt < max_retries:
                    time.sleep(1.5 ** attempt)
                    continue
                return []

            lines = [line.strip() for line in response.strip().splitlines()
                     if line.strip()]
            # 过滤掉非标签行，取最多 9 条
            valid = [ln for ln in lines if ln.startswith('[')][:9]
            if len(valid) >= 7:   # 至少 7 条才认为 LLM 响应合格
                return valid

            if attempt < max_retries:
                time.sleep(1.5 ** attempt)
                continue
            return []

        except Exception:
            if attempt < max_retries:
                time.sleep(1.5 ** attempt)
                continue
            return []

    return []


class BrainAgentAdapter:
    def __init__(self):
        self.agent  = WholeBrainAgent()
        self.bus    = EventBus()
        self.memory = MemoryStore()
        self._lock  = threading.Lock()

        self._config = _load_config()
        self._llm    = _init_llm_client(self._config)

        # 多 Agent 路由器（默认 basic 模式）
        try:
            from adapter.agent_router import AgentRouter
            self.router = AgentRouter(mode="basic")
        except Exception:
            self.router = None

        # 初始化 AI 自我进化引擎
        try:
            from agent.self_evolution_engine import SelfEvolutionEngine
            from agent.dynamic_tool_loader import load_dynamic_tools
            if hasattr(self.agent, 'tool_registry'):
                load_dynamic_tools(self.agent.tool_registry)
            self.evolution = SelfEvolutionEngine(
                tool_registry  = getattr(self.agent, 'tool_registry', None),
                metacognition  = getattr(self.agent, 'metacognition', None),
            )
        except Exception:
            self.evolution = None

    def set_agent_mode(self, mode: str) -> None:
        """切换 Agent 模式（basic/ultimate/cyborg/cns）"""
        if self.router:
            self.router.set_mode(mode)

    @property
    def agent_mode_label(self) -> str:
        if self.router:
            return self.router.mode_label
        return "基础脑区"

    @property
    def llm_connected(self) -> bool:
        return self._llm is not None

    @property
    def llm_provider(self) -> str:
        if not self._config:
            return ''
        return self._config.get('active_provider', '')

    def reload_llm(self):
        """配置窗口关闭后重新加载"""
        self._config = _load_config()
        self._llm    = _init_llm_client(self._config)

    def trigger_evolution(self, progress_cb=None) -> dict:
        """公开接口：触发 AI 自我进化，返回 patch dict（同步）"""
        if not self.evolution:
            return {}
        patch = self.evolution.analyze_failures(
            llm_client=self._llm,
            progress_cb=progress_cb,
        )
        if patch.get('new_rules') or patch.get('patch_version'):
            self.evolution.apply_patch(patch, progress_cb=progress_cb)
        return patch

    def run_async(self, visual: str, audio: str, tactile: str):
        """后台线程执行感知，逐步发射 step 事件"""
        if not self._lock.acquire(blocking=False):
            return

        def _worker():
            try:
                # 优先使用 LLM 增强模式
                steps = []
                if self._llm:
                    steps = _llm_perceive(self._llm, visual, audio, tactile)

                # LLM 不可用或解析失败 → 降级到 Agent 路由器（当前选定模式）
                if not steps:
                    if self.router:
                        steps = self.router.run(visual, audio, tactile)
                    else:
                        steps = self.agent.perceive_and_react(visual, audio, tactile)

                total = len(steps)
                for i, step in enumerate(steps):
                    delay = i * 0.4
                    Clock.schedule_once(
                        lambda dt, s=step, idx=i: self.bus.emit(
                            'step', {'text': s, 'index': idx, 'total': total}
                        ),
                        delay
                    )

                # 保存到记忆
                self.memory.save(visual, audio, tactile, steps)

                # 记录交互日志（供进化引擎分析）
                if self.evolution:
                    self.evolution.log_interaction(
                        user_input  = visual,
                        agent_output= '\n'.join(steps),
                        success     = bool(steps),
                        score       = 1.0 if steps else 0.0,
                    )

                Clock.schedule_once(
                    lambda dt: self.bus.emit('done', None),
                    total * 0.4
                )
            except Exception as e:
                # 记录失败交互
                if self.evolution:
                    try:
                        self.evolution.log_interaction(
                            user_input  = visual,
                            agent_output= '',
                            success     = False,
                            score       = 0.0,
                            error_msg   = str(e),
                        )
                    except Exception:
                        pass
                Clock.schedule_once(
                    lambda dt, err=e: self.bus.emit('error', str(err)), 0
                )
            finally:
                self._lock.release()

        threading.Thread(target=_worker, daemon=True).start()
