# PyInstaller spec - Linux ELF (onefile)
# 构建方式：pyinstaller brain_agent_linux.spec
#
# 在 Ubuntu/Debian 上构建前需要：
#   apt install -y libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev \
#                  libportmidi-dev libswscale-dev libavformat-dev libavcodec-dev \
#                  zlib1g-dev libgstreamer1.0-dev gstreamer1.0-plugins-base \
#                  xvfb  # 虚拟显示（headless 构建必须）
#   pip install kivy[base] pyinstaller

import os

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('jmv_workspace', 'jmv_workspace'),
        ('fonts', 'fonts/'),
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
        'core', 'core.agent', 'core.brain_regions', 'core.cells', 'core.memory',
        'ui', 'ui.brain_app', 'ui.main_screen', 'ui.brain_dashboard',
        'ui.input_panel', 'ui.log_viewer', 'ui.llm_config_ui',
        'ui.responsive', 'ui.llm_config_screen', 'ui.llm_config_data',
        'ui.chat_screen', 'ui.update_dialog', 'ui.onboarding_screen',
        'adapter', 'adapter.agent_adapter', 'adapter.event_bus', 'adapter.agent_router',
        'agent', 'agent.tool_registry', 'agent.brain_core',
        'agent.evolving_brain_core', 'agent.smart_companion_agent',
        'agent.native_os_operator', 'agent.planner_component',
        'agent.dag_planner_component', 'agent.cot_memory', 'agent.emotion_engine',
        'agent.llm_brain_core', 'agent.universal_llm_client',
        'agent.native_gemini_client', 'agent.native_vector_db',
        'agent.central_nervous_system', 'agent.cns_ear', 'agent.cns_eye',
        'agent.cns_hand', 'agent.cns_mouth', 'agent.cyborg_companion_agent',
        'agent.evolutionary_agent', 'agent.ultimate_companion_agent',
        'agent.nerve_signal', 'agent.memory_component',
        'agent.metacognition_component', 'agent.eye_component',
        'agent.ear_component', 'agent.mouth_component', 'agent.hand_component',
        'agent.foot_component', 'agent.evaluator', 'agent.evolution_evaluator',
        'agent.cyborg_evaluator', 'agent.omniscient_inspector',
        'agent.native_eye_component', 'agent.native_mouth_component',
        'agent.screenshot_tool', 'agent.voice_output',
        'agent.android_operator', 'agent.windows_operator',
        'agent.chat_agent', 'agent.self_evolution_engine',
        'agent.dynamic_tool_loader', 'agent.key_store',
        # LLM Provider 模块化包
        'agent.providers', 'agent.providers.base', 'agent.providers.openai_compat',
        'agent.providers.gemini', 'agent.providers.anthropic',
        'agent.providers.ollama', 'agent.providers.registry',
        # 更新器（全平台）
        'version', 'updater', 'updater.version_checker', 'updater.downloader',
        'updater.win_updater', 'updater.unix_updater', 'updater.android_updater',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=['winsound'],  # Windows 专属模块，Linux 排除
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
    name='BrainAgent_linux',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    target_arch=None,
)
