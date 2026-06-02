# -*- coding: utf-8 -*-
"""
Header UI 构建 — 顶部设置栏（模型选择、Provider、Web/Think 开关等）

从 ai_tab.py 中拆分出的 Mixin，所有方法通过 self 访问 AITab 实例状态。
样式由全局 style_template.qss 通过 objectName 选择器控制。
"""

from houdini_agent.qt_compat import QtWidgets, QtCore
from houdini_agent.utils.ai_client import normalize_custom_chat_url, normalize_custom_models_url
from .i18n import tr, get_language, set_language, language_changed
from .theme_engine import ThemeEngine


class HeaderMixin:
    """顶部设置栏构建与交互逻辑"""

    def _build_header(self) -> QtWidgets.QWidget:
        """顶部设置栏 — 单行：Provider + Model + keyStatus + Web + Think + ⋯ 溢出菜单"""
        header = QtWidgets.QFrame()
        header.setObjectName("headerFrame")
        
        outer = QtWidgets.QVBoxLayout(header)
        outer.setContentsMargins(8, 2, 8, 2)
        outer.setSpacing(0)
        
        # -------- 单行：Provider + Model + keyStatus + Web + Think + ⋯ --------
        row = QtWidgets.QHBoxLayout()
        row.setSpacing(4)
        
        # 提供商
        self.provider_combo = QtWidgets.QComboBox()
        self.provider_combo.setObjectName("providerCombo")
        self.provider_combo.addItem("Ollama", 'ollama')
        self.provider_combo.addItem("DeepSeek", 'deepseek')
        self.provider_combo.addItem("GLM", 'glm')
        self.provider_combo.addItem("OpenAI", 'openai')
        self.provider_combo.addItem("Duojie", 'duojie')
        self.provider_combo.addItem("OpenRouter", 'openrouter')
        self.provider_combo.addItem("Custom", 'custom')
        self.provider_combo.setMinimumWidth(70)
        self.provider_combo.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        row.addWidget(self.provider_combo)
        
        # Custom 配置按钮（仅在 Custom provider 时可见）
        self.btn_custom_config = QtWidgets.QPushButton("⚙")
        self.btn_custom_config.setObjectName("btnCustomConfig")
        self.btn_custom_config.setFixedSize(22, 22)
        self.btn_custom_config.setCursor(QtCore.Qt.PointingHandCursor)
        self.btn_custom_config.setToolTip("配置 Custom Model 的 URL、API Key 和模型名")
        self.btn_custom_config.setVisible(False)
        self.btn_custom_config.clicked.connect(self._open_custom_provider_dialog)
        row.addWidget(self.btn_custom_config)
        
        # 模型
        self.model_combo = QtWidgets.QComboBox()
        self.model_combo.setObjectName("modelCombo")
        self._model_map = {
            'ollama': ['qwen2.5:14b', 'qwen2.5:7b', 'llama3:8b', 'mistral:7b'],
            'deepseek': ['deepseek-v4-flash', 'deepseek-v4-pro', 'deepseek-chat', 'deepseek-reasoner'],
            'glm': ['glm-4.7'],
            'openai': ['gpt-5.2', 'gpt-5.3-codex'],
            'duojie': [
                'claude-opus-4-6-gemini',
                'claude-opus-4-6-max',
                'claude-sonnet-4-5',
                'claude-sonnet-4-6',
                'gemini-3-flash',
                'gemini-3.1-pro',
                'glm-5-turbo',
                'glm-5.1',
                'MiniMax-M2.7',
                'MiniMax-M2.7-highspeed',
            ],
            'openrouter': [
                'anthropic/claude-sonnet-4.6',
                'anthropic/claude-opus-4.6',
                'anthropic/claude-sonnet-4.5',
                'anthropic/claude-haiku-4.5',
                'openai/gpt-5.2',
                'openai/gpt-5.3-codex',
                'openai/o4-mini',
                'google/gemini-3-flash-preview',
                'google/gemini-2.5-pro',
                'google/gemini-2.5-flash',
                'deepseek/deepseek-v3.2',
                'deepseek/deepseek-r1',
                'x-ai/grok-4.1-fast',
                'meta-llama/llama-4-maverick',
                'qwen/qwen3-235b-a22b',
                'mistralai/mistral-large-2512',
            ],
            'custom': [],  # 由用户通过配置对话框动态填充
        }
        # Custom provider 的运行时配置（从持久化配置加载）
        self._custom_provider_config = {
            'api_url': '',
            'api_key': '',
            'models': [],           # 用户配置的模型名列表
            'context_limit': 128000,
            'supports_vision': False,
            'supports_fc': True,    # 是否支持 Function Calling
        }
        self._load_custom_provider_config()
        self._model_context_limits = {
            'qwen2.5:14b': 32000, 'qwen2.5:7b': 32000, 'llama3:8b': 8000, 'mistral:7b': 32000,
            'deepseek-v4-flash': 128000, 'deepseek-v4-pro': 128000,
            'deepseek-chat': 128000, 'deepseek-reasoner': 128000,
            'glm-4.7': 200000,
            'gpt-5.2': 128000,
            'gpt-5.3-codex': 200000,
            # Duojie 模型
            'claude-opus-4-6-gemini': 200000,
            'claude-opus-4-6-max': 200000,
            'claude-sonnet-4-5': 200000,
            'claude-sonnet-4-6': 200000,
            'gemini-3-flash': 1048576,
            'gemini-3.1-pro': 1048576,
            'glm-5-turbo': 200000,
            'glm-5.1': 200000,
            'MiniMax-M2.7': 128000,
            'MiniMax-M2.7-highspeed': 128000,
            # OpenRouter 模型
            'anthropic/claude-sonnet-4.6': 1000000,
            'anthropic/claude-opus-4.6': 1000000,
            'anthropic/claude-sonnet-4.5': 1000000,
            'anthropic/claude-haiku-4.5': 200000,
            'openai/gpt-5.2': 400000,
            'openai/gpt-5.3-codex': 400000,
            'openai/o4-mini': 200000,
            'google/gemini-3-flash-preview': 1048576,
            'google/gemini-2.5-pro': 1048576,
            'google/gemini-2.5-flash': 1048576,
            'deepseek/deepseek-v3.2': 163840,
            'deepseek/deepseek-r1': 64000,
            'x-ai/grok-4.1-fast': 2000000,
            'meta-llama/llama-4-maverick': 1048576,
            'qwen/qwen3-235b-a22b': 131072,
            'mistralai/mistral-large-2512': 262144,
        }
        # 模型特性配置
        self._model_features = {
            # Ollama
            'qwen2.5:14b':               {'supports_prompt_caching': True, 'supports_vision': False},
            'qwen2.5:7b':                {'supports_prompt_caching': True, 'supports_vision': False},
            'llama3:8b':                  {'supports_prompt_caching': True, 'supports_vision': False},
            'mistral:7b':                 {'supports_prompt_caching': True, 'supports_vision': False},
            # DeepSeek
            'deepseek-v4-flash':          {'supports_prompt_caching': True, 'supports_vision': False},
            'deepseek-v4-pro':            {'supports_prompt_caching': True, 'supports_vision': False},
            'deepseek-chat':              {'supports_prompt_caching': True, 'supports_vision': False},
            'deepseek-reasoner':          {'supports_prompt_caching': True, 'supports_vision': False},
            # GLM
            'glm-4.7':                    {'supports_prompt_caching': True, 'supports_vision': False},
            # OpenAI
            'gpt-5.2':                    {'supports_prompt_caching': True, 'supports_vision': True},
            'gpt-5.3-codex':              {'supports_prompt_caching': True, 'supports_vision': True},
            # Duojie - Claude
            'claude-opus-4-6-gemini':    {'supports_prompt_caching': True, 'supports_vision': True},
            'claude-opus-4-6-max':        {'supports_prompt_caching': True, 'supports_vision': True},
            'claude-sonnet-4-5':          {'supports_prompt_caching': True, 'supports_vision': True},
            'claude-sonnet-4-6':          {'supports_prompt_caching': True, 'supports_vision': True},
            # Duojie - Gemini
            'gemini-3-flash':             {'supports_prompt_caching': True, 'supports_vision': True},
            'gemini-3.1-pro':             {'supports_prompt_caching': True, 'supports_vision': True},
            # Duojie - GLM (Anthropic 协议)
            'glm-5-turbo':                {'supports_prompt_caching': True, 'supports_vision': False},
            'glm-5.1':                    {'supports_prompt_caching': True, 'supports_vision': False},
            # Duojie - MiniMax
            'MiniMax-M2.7':               {'supports_prompt_caching': True, 'supports_vision': False},
            'MiniMax-M2.7-highspeed':     {'supports_prompt_caching': True, 'supports_vision': False},
            # OpenRouter 模型
            'anthropic/claude-sonnet-4.6':        {'supports_prompt_caching': True, 'supports_vision': True},
            'anthropic/claude-opus-4.6':          {'supports_prompt_caching': True, 'supports_vision': True},
            'anthropic/claude-sonnet-4.5':        {'supports_prompt_caching': True, 'supports_vision': True},
            'anthropic/claude-haiku-4.5':         {'supports_prompt_caching': True, 'supports_vision': True},
            'openai/gpt-5.2':                     {'supports_prompt_caching': True, 'supports_vision': True},
            'openai/gpt-5.3-codex':               {'supports_prompt_caching': True, 'supports_vision': True},
            'openai/o4-mini':                     {'supports_prompt_caching': True, 'supports_vision': True},
            'google/gemini-3-flash-preview':      {'supports_prompt_caching': True, 'supports_vision': True},
            'google/gemini-2.5-pro':              {'supports_prompt_caching': True, 'supports_vision': True},
            'google/gemini-2.5-flash':            {'supports_prompt_caching': True, 'supports_vision': True},
            'deepseek/deepseek-v3.2':             {'supports_prompt_caching': True, 'supports_vision': False},
            'deepseek/deepseek-r1':               {'supports_prompt_caching': True, 'supports_vision': False},
            'x-ai/grok-4.1-fast':                 {'supports_prompt_caching': True, 'supports_vision': True},
            'meta-llama/llama-4-maverick':        {'supports_prompt_caching': True, 'supports_vision': True},
            'qwen/qwen3-235b-a22b':               {'supports_prompt_caching': True, 'supports_vision': False},
            'mistralai/mistral-large-2512':       {'supports_prompt_caching': True, 'supports_vision': True},
        }
        self._refresh_models('ollama')
        self.model_combo.setMinimumWidth(100)
        self.model_combo.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.model_combo.setEditable(False)  # 默认不可编辑，Custom 时切换为可编辑
        row.addWidget(self.model_combo, 1)
        
        # API Key 状态 — 紧凑指示（行内，限宽 + 省略号）
        self.key_status = QtWidgets.QLabel()
        self.key_status.setObjectName("keyStatus")
        self.key_status.setMaximumWidth(90)
        self.key_status.setMinimumWidth(0)
        from houdini_agent.qt_compat import QtCore as _qc
        self.key_status.setTextInteractionFlags(_qc.Qt.NoTextInteraction)
        row.addWidget(self.key_status)
        
        # Web / Think 开关
        self.web_check = QtWidgets.QCheckBox(tr("header.web"))
        self.web_check.setObjectName("chkWeb")
        self.web_check.setChecked(True)
        row.addWidget(self.web_check)
        
        self.think_check = QtWidgets.QCheckBox(tr("header.think"))
        self.think_check.setObjectName("chkThink")
        self.think_check.setChecked(True)
        self.think_check.setToolTip(tr('header.think.tooltip'))
        row.addWidget(self.think_check)
        
        # ⋯ 溢出菜单按钮
        self.btn_overflow = QtWidgets.QPushButton("···")
        self.btn_overflow.setObjectName("btnOverflow")
        self.btn_overflow.setFixedSize(24, 22)
        self.btn_overflow.setCursor(QtCore.Qt.PointingHandCursor)
        self.btn_overflow.clicked.connect(self._show_overflow_menu)
        row.addWidget(self.btn_overflow)
        
        outer.addLayout(row)
        
        # -------- 隐藏按钮（保持 self.btn_xxx 引用兼容 _wire_events）--------
        # 这些按钮不加入布局，仅用于信号连接
        self.btn_key = QtWidgets.QPushButton(tr("menu.api_key"))
        self.btn_key.setObjectName("btnSmall")
        self.btn_key.setVisible(False)
        
        self.btn_clear = QtWidgets.QPushButton(tr("btn.clear"))
        self.btn_clear.setObjectName("btnSmall")
        self.btn_clear.setVisible(False)
        
        self.btn_cache = QtWidgets.QPushButton(tr("menu.cache"))
        self.btn_cache.setObjectName("btnSmall")
        self.btn_cache.setVisible(False)
        
        self.btn_optimize = QtWidgets.QPushButton(tr("menu.optimize"))
        self.btn_optimize.setObjectName("btnOptimize")
        self.btn_optimize.setVisible(False)
        
        self.btn_update = QtWidgets.QPushButton(tr("menu.update"))
        self.btn_update.setObjectName("btnUpdate")
        self.btn_update.setVisible(False)
        
        self.btn_font_scale = QtWidgets.QPushButton("Aa")
        self.btn_font_scale.setObjectName("btnFontScale")
        self.btn_font_scale.setVisible(False)
        
        # 语言下拉框（隐藏，仅用于引用 + 信号）
        self.lang_combo = QtWidgets.QComboBox()
        self.lang_combo.setObjectName("langCombo")
        self.lang_combo.addItem("中文", "zh")
        self.lang_combo.addItem("EN", "en")
        self.lang_combo.setCurrentIndex(0 if get_language() == 'zh' else 1)
        self.lang_combo.currentIndexChanged.connect(self._on_language_changed)
        self.lang_combo.setVisible(False)
        
        return header

    def _show_overflow_menu(self):
        """显示溢出菜单：低频功能集中在此"""
        menu = QtWidgets.QMenu(self)
        
        menu.addAction(tr("menu.api_key"), self.btn_key.click)
        menu.addAction(tr("menu.clear_chat"), self.btn_clear.click)
        menu.addAction(tr("menu.cache"), self.btn_cache.click)
        menu.addAction(tr("menu.optimize"), self.btn_optimize.click)
        menu.addSeparator()
        menu.addAction(tr("menu.update"), self.btn_update.click)
        menu.addAction(tr("menu.font"), self.btn_font_scale.click)
        menu.addSeparator()
        menu.addAction(tr('rules.menu_label'), self._open_rules_editor)
        menu.addAction(tr('plugin.menu_label'), self._open_plugin_manager)
        menu.addAction(tr('experience.menu_label'), self._open_experience_review)

        # 长期记忆系统全局开关（默认关闭）—— checkable action
        act_memory = menu.addAction(tr('memory.menu_label'))
        act_memory.setCheckable(True)
        act_memory.setChecked(True)
        act_memory.setEnabled(False)
        act_memory.setToolTip(tr('memory.menu_tooltip'))
        act_memory.toggled.connect(self._on_memory_toggle_from_menu)

        menu.addSeparator()
        
        # 语言子菜单
        lang_menu = menu.addMenu(tr("menu.language"))
        act_zh = lang_menu.addAction("中文")
        act_en = lang_menu.addAction("EN")
        current_lang = get_language()
        act_zh.setCheckable(True)
        act_en.setCheckable(True)
        act_zh.setChecked(current_lang == 'zh')
        act_en.setChecked(current_lang == 'en')
        act_zh.triggered.connect(lambda: self._set_lang_from_menu('zh'))
        act_en.triggered.connect(lambda: self._set_lang_from_menu('en'))
        
        # 弹出位置：溢出按钮下方
        menu.exec_(self._overflow_anchor_pos())

    def _overflow_anchor_pos(self):
        """Return a stable global popup position near the visible overflow button."""
        anchor = getattr(self, "btn_overflow", None)
        try:
            if anchor is not None and anchor.isVisible():
                return anchor.mapToGlobal(QtCore.QPoint(0, anchor.height()))
        except RuntimeError:
            pass
        return self.mapToGlobal(QtCore.QPoint(max(0, self.width() - 24), 24))

    def _open_rules_editor(self):
        """打开用户自定义规则编辑器"""
        try:
            from .cursor_widgets import RulesEditorDialog
            dlg = RulesEditorDialog(parent=self)
            dlg.exec_()
        except Exception as e:
            print(f"[Header] Failed to open rules editor: {e}")

    def _open_plugin_manager(self):
        """打开插件管理面板"""
        try:
            from .cursor_widgets import PluginManagerDialog
            dlg = PluginManagerDialog(parent=self)
            dlg.pluginStateChanged.connect(self._on_plugin_state_changed)
            dlg.exec_()
        except Exception as e:
            print(f"[Header] Failed to open plugin manager: {e}")

    def _open_experience_review(self):
        """打开工作流经验沉淀审阅中心"""
        try:
            from .experience_review_dialog import ExperienceReviewDialog
            dlg = getattr(self, "_experience_review_dialog", None)
            try:
                if dlg is not None and dlg.isVisible():
                    dlg.raise_()
                    dlg.activateWindow()
                    return
            except RuntimeError:
                dlg = None

            dlg = ExperienceReviewDialog(self, parent=self)
            dlg.setModal(False)
            dlg.setWindowModality(QtCore.Qt.NonModal)
            dlg.destroyed.connect(lambda *_: setattr(self, "_experience_review_dialog", None))
            self._experience_review_dialog = dlg
            dlg.show()
            dlg.raise_()
            dlg.activateWindow()
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self,
                tr('experience.title'),
                tr('experience.open_failed', e),
            )

    def _on_plugin_state_changed(self):
        """插件状态变化后的回调（重新挂载按钮等）"""
        try:
            from ..utils.hooks import get_hook_manager
            bridge = get_hook_manager().get_ui_bridge()
            if bridge:
                bridge.mount_buttons()
        except Exception:
            pass

    def _on_memory_toggle_from_menu(self, checked: bool):
        """溢出菜单切换长期记忆系统开关"""
        try:
            self.set_memory_enabled(bool(checked))
        except Exception as e:
            print(f"[Header] Memory toggle failed: {e}")

    def _set_lang_from_menu(self, lang: str):
        """从溢出菜单切换语言"""
        if lang != get_language():
            set_language(lang)
            # 同步隐藏的 lang_combo（保持状态一致）
            expected_idx = 0 if lang == 'zh' else 1
            if self.lang_combo.currentIndex() != expected_idx:
                self.lang_combo.blockSignals(True)
                self.lang_combo.setCurrentIndex(expected_idx)
                self.lang_combo.blockSignals(False)

    def _on_language_changed(self, index: int):
        """语言下拉框切换"""
        lang = self.lang_combo.itemData(index)
        if lang and lang != get_language():
            set_language(lang)

    def _retranslate_header(self):
        """语言切换后更新 Header 区域所有翻译文本"""
        self.think_check.setToolTip(tr('header.think.tooltip'))
        self.web_check.setText(tr("header.web"))
        self.think_check.setText(tr("header.think"))
        self.btn_cache.setToolTip(tr('header.cache.tooltip'))
        self.btn_optimize.setToolTip(tr('header.optimize.tooltip'))
        self.btn_update.setToolTip(tr('header.update.tooltip'))
        self.btn_font_scale.setToolTip(tr('header.font.tooltip'))
        self.btn_key.setText(tr('menu.api_key'))
        self.btn_clear.setText(tr('btn.clear'))
        self.btn_cache.setText(tr('menu.cache'))
        self.btn_optimize.setText(tr('menu.optimize'))
        self.btn_update.setText(tr('menu.update'))
        # 同步下拉框选中项（防止外部调用 set_language 后不同步）
        lang = get_language()
        expected_idx = 0 if lang == 'zh' else 1
        if self.lang_combo.currentIndex() != expected_idx:
            self.lang_combo.blockSignals(True)
            self.lang_combo.setCurrentIndex(expected_idx)
            self.lang_combo.blockSignals(False)

    # ============================================================
    # Custom Provider 配置
    # ============================================================

    def _load_custom_provider_config(self):
        """从持久化配置文件加载 Custom Provider 设置"""
        try:
            from shared.common_utils import load_config
            cfg, _ = load_config('ai', dcc_type='houdini')
            if cfg:
                self._custom_provider_config['api_url'] = cfg.get('custom_api_url', '')
                self._custom_provider_config['api_key'] = cfg.get('custom_api_key', '')
                models_str = cfg.get('custom_models', '')
                if models_str:
                    model_chunks = models_str.replace('\n', ',').replace(';', ',').split(',')
                    self._custom_provider_config['models'] = [m.strip() for m in model_chunks if m.strip()]
                try:
                    self._custom_provider_config['context_limit'] = int(cfg.get('custom_context_limit', '128000'))
                except (ValueError, TypeError):
                    pass
                self._custom_provider_config['supports_vision'] = cfg.get('custom_supports_vision', 'false').lower() == 'true'
                self._custom_provider_config['supports_fc'] = cfg.get('custom_supports_fc', 'true').lower() != 'false'
                # 更新模型列表
                self._model_map['custom'] = self._custom_provider_config['models']
                # 同步到 AIClient（如果已初始化）
                self._sync_custom_to_client()
        except Exception as e:
            print(f"[Header] 加载 Custom 配置失败: {e}")

    def _save_custom_provider_config(self):
        """将 Custom Provider 设置持久化到配置文件"""
        try:
            from shared.common_utils import load_config, save_config
            cfg, _ = load_config('ai', dcc_type='houdini')
            cfg = cfg or {}
            cc = self._custom_provider_config
            cfg['custom_api_url'] = cc['api_url']
            cfg['custom_api_key'] = cc['api_key']
            cfg['custom_models'] = ','.join(cc['models'])
            cfg['custom_context_limit'] = str(cc['context_limit'])
            cfg['custom_supports_vision'] = 'true' if cc['supports_vision'] else 'false'
            cfg['custom_supports_fc'] = 'true' if cc['supports_fc'] else 'false'
            save_config('ai', cfg, dcc_type='houdini')
        except Exception as e:
            print(f"[Header] 保存 Custom 配置失败: {e}")

    def _sync_custom_to_client(self):
        """将 Custom 配置同步到 AIClient"""
        try:
            client = getattr(self, 'client', None)
            if client is None:
                return
            cc = self._custom_provider_config
            if cc['api_url']:
                client.set_custom_provider(
                    api_url=cc['api_url'],
                    api_key=cc['api_key'],
                    supports_fc=cc['supports_fc'],
                )
            if cc['api_key']:
                client._api_keys['custom'] = cc['api_key']
        except Exception as e:
            print(f"[Header] 同步 Custom 配置到 Client 失败: {e}")

    def _on_provider_changed_custom_visibility(self):
        """Provider 切换时更新 Custom 配置按钮可见性和模型下拉框可编辑状态"""
        provider = self._current_provider()
        is_custom = (provider == 'custom')
        self.btn_custom_config.setVisible(is_custom)
        # Custom 模式下允许用户直接在 model_combo 中输入模型名
        self.model_combo.setEditable(is_custom)
        if is_custom and not self._custom_provider_config.get('api_url'):
            # 首次选择 Custom 且未配置，自动弹出配置对话框
            QtCore.QTimer.singleShot(100, self._open_custom_provider_dialog)

    def _open_custom_provider_dialog(self):
        """打开 Custom Provider 配置对话框"""
        dlg = _CustomProviderDialog(self._custom_provider_config, parent=self)
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            new_cfg = dlg.get_config()
            self._custom_provider_config.update(new_cfg)
            # 更新模型列表
            self._model_map['custom'] = new_cfg['models']
            # 动态注册模型特性和上下文限制
            for m in new_cfg['models']:
                self._model_context_limits[m] = new_cfg['context_limit']
                self._model_features[m] = {
                    'supports_prompt_caching': True,
                    'supports_vision': new_cfg['supports_vision'],
                }
            # 同步到 AIClient
            self._sync_custom_to_client()
            # 持久化
            self._save_custom_provider_config()
            # 刷新 UI
            if self._current_provider() == 'custom':
                current_model = self.model_combo.currentText()
                self._refresh_models('custom')
                if current_model in new_cfg['models']:
                    self.model_combo.setCurrentText(current_model)
                self._update_key_status()


class _CustomProviderDialog(QtWidgets.QDialog):
    """Custom Provider 配置对话框 — 配置 API URL、Key、模型名等"""

    def __init__(self, current_config: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("custom.title"))
        self.setMinimumWidth(460)
        self.setObjectName("customProviderDialog")
        self._build_ui(current_config)

    def _build_ui(self, cfg: dict):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(16, 16, 16, 16)

        # 说明
        info = QtWidgets.QLabel(
            tr("custom.info")
        )
        info.setWordWrap(True)
        info.setStyleSheet(f"color: #aaa; font-size: {ThemeEngine.scaled_px(12)}px; margin-bottom: 4px;")
        layout.addWidget(info)

        form = QtWidgets.QFormLayout()
        form.setSpacing(8)
        form.setLabelAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        # API URL
        self._url_edit = QtWidgets.QLineEdit()
        self._url_edit.setPlaceholderText(tr("custom.url_placeholder"))
        self._url_edit.setText(cfg.get('api_url', ''))
        self._url_edit.setMinimumHeight(28)
        form.addRow("API URL:", self._url_edit)

        # API Key
        self._key_edit = QtWidgets.QLineEdit()
        self._key_edit.setPlaceholderText(tr("custom.key_placeholder"))
        self._key_edit.setText(cfg.get('api_key', ''))
        self._key_edit.setEchoMode(QtWidgets.QLineEdit.Password)
        self._key_edit.setMinimumHeight(28)
        # 显示/隐藏按钮
        key_row = QtWidgets.QHBoxLayout()
        key_row.setSpacing(4)
        key_row.addWidget(self._key_edit)
        self._btn_show_key = QtWidgets.QPushButton("👁")
        self._btn_show_key.setFixedSize(28, 28)
        self._btn_show_key.setCheckable(True)
        self._btn_show_key.toggled.connect(
            lambda checked: self._key_edit.setEchoMode(
                QtWidgets.QLineEdit.Normal if checked else QtWidgets.QLineEdit.Password
            )
        )
        key_row.addWidget(self._btn_show_key)
        form.addRow("API Key:", key_row)

        # 模型名列表：一行一个；粘贴逗号或分号分隔的列表也可以。
        self._models_edit = QtWidgets.QPlainTextEdit()
        self._models_edit.setMinimumHeight(96)
        self._models_edit.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed
        )
        self._models_edit.setPlaceholderText("glm-4.5\nglm-4.7\nglm-5.1")
        self._models_edit.setPlainText('\n'.join(cfg.get('models', [])))

        models_row = QtWidgets.QHBoxLayout()
        models_row.setSpacing(4)
        models_row.addWidget(self._models_edit, 1)

        self._btn_fetch_models = QtWidgets.QPushButton("⟳")
        self._btn_fetch_models.setFixedSize(28, 28)
        self._btn_fetch_models.setToolTip(tr("custom.fetch_models"))
        self._btn_fetch_models.clicked.connect(self._fetch_models)
        models_row.addWidget(self._btn_fetch_models)

        form.addRow(tr("custom.models"), models_row)

        # 上下文长度
        self._ctx_spin = QtWidgets.QSpinBox()
        self._ctx_spin.setRange(1024, 10000000)
        self._ctx_spin.setSingleStep(1024)
        self._ctx_spin.setValue(cfg.get('context_limit', 128000))
        self._ctx_spin.setSuffix(" tokens")
        self._ctx_spin.setMinimumHeight(28)
        form.addRow(tr("custom.context_length"), self._ctx_spin)

        # 特性开关
        features_row = QtWidgets.QHBoxLayout()
        features_row.setSpacing(12)
        self._chk_vision = QtWidgets.QCheckBox(tr("custom.supports_vision"))
        self._chk_vision.setChecked(cfg.get('supports_vision', False))
        features_row.addWidget(self._chk_vision)
        self._chk_fc = QtWidgets.QCheckBox(tr("custom.supports_fc"))
        self._chk_fc.setChecked(cfg.get('supports_fc', True))
        features_row.addWidget(self._chk_fc)
        features_row.addStretch()
        form.addRow(tr("custom.features"), features_row)

        layout.addLayout(form)

        # 测试连接按钮
        test_row = QtWidgets.QHBoxLayout()
        test_row.addStretch()
        self._btn_test = QtWidgets.QPushButton(tr("custom.test"))
        self._btn_test.setMinimumWidth(100)
        self._btn_test.setMinimumHeight(28)
        self._btn_test.clicked.connect(self._test_connection)
        test_row.addWidget(self._btn_test)
        self._test_status = QtWidgets.QLabel("")
        self._test_status.setStyleSheet(f"font-size: {ThemeEngine.scaled_px(12)}px;")
        test_row.addWidget(self._test_status)
        test_row.addStretch()
        layout.addLayout(test_row)

        # 按钮
        btn_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        btn_box.button(QtWidgets.QDialogButtonBox.Ok).setText(tr("btn.ok"))
        btn_box.button(QtWidgets.QDialogButtonBox.Cancel).setText(tr("btn.cancel"))
        btn_box.accepted.connect(self._on_accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

        # 样式
        self.setStyleSheet("""
            QDialog#customProviderDialog {
                background: #1e1e1e;
                color: #ddd;
            }
            QLabel { color: #ccc; }
            QLineEdit, QSpinBox, QComboBox, QPlainTextEdit {
                background: #2a2a2a;
                color: #eee;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 4px 8px;
            }
            QLineEdit:focus, QSpinBox:focus, QComboBox:focus, QPlainTextEdit:focus {
                border-color: #6a9eff;
            }
            QComboBox::drop-down {
                border: none;
                width: 24px;
                subcontrol-position: center right;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #aaa;
                margin-right: 6px;
            }
            QComboBox QAbstractItemView {
                background: #2a2a2a;
                color: #eee;
                border: 1px solid #555;
                selection-background-color: #3a5a8a;
                outline: none;
            }
            QCheckBox { color: #ccc; }
            QPushButton {
                background: #333;
                color: #ddd;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 4px 12px;
            }
            QPushButton:hover { background: #444; border-color: #6a9eff; }
        """)

    def _model_names(self) -> list:
        """Return model names from the multiline model editor."""
        text = self._models_edit.toPlainText()
        names = []
        seen = set()
        for raw in text.replace(';', ',').replace('\n', ',').split(','):
            name = raw.strip()
            if name and name not in seen:
                names.append(name)
                seen.add(name)
        return names

    def _set_model_names(self, models: list):
        """Replace the multiline model editor content with one model per line."""
        unique = []
        seen = set()
        for model in models:
            name = str(model).strip()
            if name and name not in seen:
                unique.append(name)
                seen.add(name)
        self._models_edit.setPlainText('\n'.join(unique))

    def _fetch_models(self):
        """从 API 获取可用模型列表并填充到模型列表"""
        url = self._url_edit.text().strip()
        key = self._key_edit.text().strip()

        if not url:
            self._test_status.setText(tr("custom.need_url"))
            self._test_status.setStyleSheet(f"color: #f5a623; font-size: {ThemeEngine.scaled_px(12)}px;")
            return

        self._btn_fetch_models.setEnabled(False)
        self._test_status.setText(tr("custom.fetching_models"))
        self._test_status.setStyleSheet(f"color: #aaa; font-size: {ThemeEngine.scaled_px(12)}px;")

        try:
            import requests
            models_url = normalize_custom_models_url(url)

            headers = {'Content-Type': 'application/json'}
            if key:
                headers['Authorization'] = f'Bearer {key}'

            resp = requests.get(models_url, headers=headers, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                model_ids = [m.get('id', '') for m in data.get('data', []) if m.get('id')]
                if model_ids:
                    self._set_model_names(sorted(model_ids))
                    self._test_status.setText(tr("custom.models_found", len(model_ids)))
                    self._test_status.setStyleSheet(f"color: #4caf50; font-size: {ThemeEngine.scaled_px(12)}px;")
                else:
                    self._test_status.setText(tr("custom.no_models"))
                    self._test_status.setStyleSheet(f"color: #f5a623; font-size: {ThemeEngine.scaled_px(12)}px;")
            else:
                err = resp.text[:120]
                self._test_status.setText(f"❌ HTTP {resp.status_code}: {err}")
                self._test_status.setStyleSheet(f"color: #f44336; font-size: {ThemeEngine.scaled_px(12)}px;")
        except Exception as e:
            self._test_status.setText(f"❌ {str(e)[:100]}")
            self._test_status.setStyleSheet(f"color: #f44336; font-size: {ThemeEngine.scaled_px(12)}px;")
        finally:
            self._btn_fetch_models.setEnabled(True)

    def _test_connection(self):
        """测试 Custom API 连接"""
        url = self._url_edit.text().strip()
        key = self._key_edit.text().strip()
        models = self._model_names()
        model = models[0] if models else 'test'

        if not url:
            self._test_status.setText(tr("custom.need_url"))
            self._test_status.setStyleSheet(f"color: #f5a623; font-size: {ThemeEngine.scaled_px(12)}px;")
            return

        test_url = normalize_custom_chat_url(url)

        self._btn_test.setEnabled(False)
        self._test_status.setText(tr("custom.connecting"))
        self._test_status.setStyleSheet(f"color: #aaa; font-size: {ThemeEngine.scaled_px(12)}px;")

        try:
            import requests
            headers = {'Content-Type': 'application/json'}
            if key:
                headers['Authorization'] = f'Bearer {key}'
            payload = {
                'model': model,
                'messages': [{'role': 'user', 'content': 'Hi'}],
                'max_tokens': 5,
                'stream': False,
            }
            resp = requests.post(test_url, json=payload, headers=headers, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                recv_model = data.get('model', model)
                self._test_status.setText(tr("custom.connect_ok", recv_model))
                self._test_status.setStyleSheet(f"color: #4caf50; font-size: {ThemeEngine.scaled_px(12)}px;")
            else:
                err = resp.text[:120]
                self._test_status.setText(f"❌ HTTP {resp.status_code}: {err}")
                self._test_status.setStyleSheet(f"color: #f44336; font-size: {ThemeEngine.scaled_px(12)}px;")
        except Exception as e:
            self._test_status.setText(f"❌ {str(e)[:100]}")
            self._test_status.setStyleSheet(f"color: #f44336; font-size: {ThemeEngine.scaled_px(12)}px;")
        finally:
            self._btn_test.setEnabled(True)

    def _on_accept(self):
        """确认前校验必填项"""
        url = self._url_edit.text().strip()
        models = self._model_names()
        if not url:
            QtWidgets.QMessageBox.warning(self, tr("dialog.notice"), tr("custom.need_url_plain"))
            return
        if not models:
            QtWidgets.QMessageBox.warning(self, tr("dialog.notice"), tr("custom.need_model"))
            return
        self.accept()

    def get_config(self) -> dict:
        """返回用户配置的字典"""
        models = self._model_names()
        return {
            'api_url': self._url_edit.text().strip(),
            'api_key': self._key_edit.text().strip(),
            'models': models,
            'context_limit': self._ctx_spin.value(),
            'supports_vision': self._chk_vision.isChecked(),
            'supports_fc': self._chk_fc.isChecked(),
        }
