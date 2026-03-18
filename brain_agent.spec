# PyInstaller spec - Windows EXE
# 使用方式：pyinstaller brain_agent.spec
#
# 修复说明：
# 1. 加入 kivy_deps SDL2 + GLEW DLL（缺少则 EXE 启动崩溃）
# 2. 加入 Kivy data 目录（字体/shader/图标，缺少则文字渲染失败）
# 3. 补充 kivy.core.window.window_sdl2 等必须的隐式导入

import os
from kivy_deps import sdl2, glew
from kivy import kivy_data_dir

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('jmv_workspace', 'jmv_workspace'),
        (kivy_data_dir, 'kivy/data/'),   # Kivy 字体/shader/图标（必须）
        ('fonts', 'fonts/'),             # CJK 中文字体（修复乱码）
    ],
    hiddenimports=[
        'kivy',
        'kivy.app',
        'kivy.clock',
        'kivy.logger',
        'kivy.core.window',
        'kivy.core.window.window_sdl2',
        'kivy.core.text',
        'kivy.core.text.text_layout',
        'kivy.core.text.markup',
        'kivy.core.image',
        'kivy.core.image.img_sdl2',
        'kivy.core.audio',
        'kivy.graphics',
        'kivy.graphics.texture',
        'kivy.graphics.context_instructions',
        'kivy.graphics.vertex_instructions',
        'kivy.graphics.fbo',
        'kivy.graphics.opengl',
        'kivy.uix.boxlayout',
        'kivy.uix.gridlayout',
        'kivy.uix.scrollview',
        'kivy.uix.textinput',
        'kivy.uix.button',
        'kivy.uix.label',
        'kivy.uix.progressbar',
        'kivy.uix.widget',
        'kivy.properties',
        # 项目自身模块
        'core',
        'core.agent',
        'core.brain_regions',
        'core.cells',
        'core.memory',
        'ui',
        'ui.brain_app',
        'ui.main_screen',
        'ui.brain_dashboard',
        'ui.input_panel',
        'ui.log_viewer',
        'ui.llm_config_ui',
        'adapter',
        'adapter.agent_adapter',
        'adapter.event_bus',
        # agent 包（全部模块）
        'agent',
        'agent.tool_registry',
        'agent.brain_core',
        'agent.evolving_brain_core',
        'agent.smart_companion_agent',
        'agent.native_os_operator',
        'agent.planner_component',
        'agent.dag_planner_component',
        'agent.cot_memory',
        'agent.emotion_engine',
        'agent.llm_brain_core',
        'agent.universal_llm_client',
        'agent.native_gemini_client',
        'agent.native_vector_db',
        'agent.central_nervous_system',
        'agent.cns_ear',
        'agent.cns_eye',
        'agent.cns_hand',
        'agent.cns_mouth',
        'agent.cyborg_companion_agent',
        'agent.evolutionary_agent',
        'agent.ultimate_companion_agent',
        # CNS 体系（间接导入，PyInstaller 静态分析不可见）
        'agent.nerve_signal',
        'agent.cns_eye',
        'agent.cns_ear',
        'agent.cns_hand',
        'agent.cns_mouth',
        'agent.central_nervous_system',
        # 其他间接导入模块
        'agent.memory_component',
        'agent.metacognition_component',
        'agent.eye_component',
        'agent.ear_component',
        'agent.mouth_component',
        'agent.hand_component',
        'agent.foot_component',
        'agent.evaluator',
        'agent.evolution_evaluator',
        'agent.cyborg_evaluator',
        'agent.omniscient_inspector',
        'agent.native_eye_component',
        'agent.native_mouth_component',
        # 自我升级模块
        'version',
        'updater',
        'updater.version_checker',
        'updater.downloader',
        'updater.win_updater',
        'updater.android_updater',
        # 升级 UI
        'ui.update_dialog',
        # 响应式设计 + 新增 UI 模块
        'ui.responsive',
        'ui.llm_config_screen',
        'ui.chat_screen',
        # 对话 Agent
        'agent.chat_agent',
        # AI 自我进化引擎
        'agent.self_evolution_engine',
        'agent.dynamic_tool_loader',
        # 元认知持久化规则
        'agent.metacognition_component',
        # 截图 + 语音输出
        'agent.screenshot_tool',
        'agent.voice_output',
        # 多 Agent 路由器
        'adapter.agent_router',
        # LLM 配置数据（无 Kivy 依赖）
        'ui.llm_config_data',
        # 模块化 LLM 供应商包（20个供应商）
        'agent.providers',
        'agent.providers.base',
        'agent.providers.openai_compat',
        'agent.providers.gemini',
        'agent.providers.anthropic',
        'agent.providers.ollama',
        'agent.providers.registry',
        # 语音播放
        'winsound',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    # SDL2 + GLEW DLL 目录整体打入 EXE（Kivy 渲染必需，缺少则无法启动）
    *[Tree(p) for p in (sdl2.dep_bins + glew.dep_bins)],
    name='BrainAgent',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    target_arch=None,
)
