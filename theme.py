"""全局主题管理：深色 / 浅色色板统一在此定义，通过单一接口切换。

- 切换方式（任选其一，需在创建界面控件前生效）：
    1. ``conf/setup.ini`` 中 ``[ui] theme = dark|light``（启动时由 app.py 读取）；
    2. 代码调用 ``theme.set_theme("light")``。
- QSS：``render_qss()`` 读取 ``resource/qss/app.qss`` 模板并替换 ``@token@`` 占位符。
- 代码内颜色（pyqtgraph 图表、内联样式等）：用 ``color("token")`` 读取当前主题，
  禁止再硬编码十六进制颜色。

注意：主题在界面构建时生效；运行中切换只会更新 QSS，已创建的 pyqtgraph
图表颜色不会自动刷新，完整换肤需重启应用。
"""
import os
import re

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_QSS = os.path.join(_BASE_DIR, "resource", "qss", "app.qss")

DARK = {
    # 面板与表面
    "panel_bg": "#171a1b",
    "panel_bg_alt": "#1a1e20",
    "surface": "#1e2224",
    "surface_2": "#232729",
    "input_bg": "#121517",
    "disabled_bg": "#1a1e20",
    "table_bg": "#14171a",
    "table_alt_bg": "#181c1f",
    "header_view_bg": "#1e2224",
    # 边框
    "border": "#31383d",
    "border_subtle": "#272c30",
    "border_hover": "#41505c",
    # 文字
    "text": "#d8e2ed",
    "text_secondary": "#aeb8c2",
    "text_dim": "#8a97a3",
    "text_disabled": "#5a656e",
    "text_bright": "#eaf2f9",
    # 强调与选中
    "accent": "#3d9be9",
    "selection_bg": "#31577a",
    "selection_bg_soft": "#2a4a63",
    "selection_text": "#eaf2f9",
    # 滚动条
    "scrollbar_handle": "#31383d",
    "scrollbar_handle_hover": "#41505c",
    # 危险 / 关闭
    "danger_hover": "#7a3a3a",
    "danger_pressed": "#a13a3a",
    "close_hover": "#f08080",
    "close_pressed": "#ff0000",
    # 页签
    "tabbar_bg": "#121517",
    "tab_bg": "#121517",
    "tab_hover_bg": "#1e2224",
    "tab_checked_bg": "#232729",
    # Header（品牌蓝）
    "header_text": "#b9d7f0",
    "header_text_hover": "#ffffff",
    "header_bg_start": "#1d86d8",
    "header_bg_end": "#1668ab",
    "header_hover": "#1f8adb",
    "header_underline": "#9fd6ff",
    "header_splitter": "#4a9bd8",
    "header_progress_track": "#0f4c81",
    "header_progress_chunk": "#7fd0ff",
    "header_progress_text": "#eaf2f9",
    "startstop_bg": "#cde7fa",
    "startstop_text_started": "#1a9e50",
    "startstop_text_stopped": "#1668ab",
    # 音频控制窗口按钮（统一蓝色样式）
    "device_btn_bg": "#197ccc",
    "device_btn_hover": "#1f8adb",
    "device_btn_pressed": "#1668ab",
    "device_btn_text": "#ffffff",
    "device_btn_disabled_bg": "#2a2f33",
    "device_btn_disabled_text": "#5a656e",
    # 通用按钮
    "button_bg": "#232729",
    "button_pressed_bg": "#1c2a36",
    # pyqtgraph 图表（曲线颜色不在此定义，保持业务约定）
    "plot_bg": "#121517",
    "plot_axis": "#3a4147",
    "plot_text": "#8a97a3",
    "plot_label": "#aeb8c2",
    # 图标
    "arrow_down": "resource/pic/arrow_down_light.png",
    "arrow_up": "resource/pic/arrow_up_light.png",
}

LIGHT = {
    # 面板与表面
    "panel_bg": "#ffffff",
    "panel_bg_alt": "#f0f0f0",
    "surface": "#e4e4e4",
    "surface_2": "#ffffff",
    "input_bg": "#ffffff",
    "disabled_bg": "#dcdcdc",
    "table_bg": "#ffffff",
    "table_alt_bg": "#eeeeee",
    "header_view_bg": "#eeeeee",
    # 边框
    "border": "#747474",
    "border_subtle": "#dcdcdc",
    "border_hover": "#9a9a9a",
    # 文字
    "text": "#141414",
    "text_secondary": "#666666",
    "text_dim": "#898989",
    "text_disabled": "#717171",
    "text_bright": "#000000",
    # 强调与选中
    "accent": "#197ccc",
    "selection_bg": "#def0fe",
    "selection_bg_soft": "#b3ddff",
    "selection_text": "#386487",
    # 滚动条
    "scrollbar_handle": "#c4c4c4",
    "scrollbar_handle_hover": "#a6a6a6",
    # 危险 / 关闭
    "danger_hover": "#f08080",
    "danger_pressed": "#ff0000",
    "close_hover": "#f08080",
    "close_pressed": "#ff0000",
    # 页签
    "tabbar_bg": "#c9c9c9",
    "tab_bg": "#e4e4e4",
    "tab_hover_bg": "#ffffff",
    "tab_checked_bg": "#ffffff",
    # Header（品牌蓝）
    "header_text": "#cde7f8",
    "header_text_hover": "#ffffff",
    "header_bg_start": "#197ccc",
    "header_bg_end": "#197ccc",
    "header_hover": "#3089d1",
    "header_underline": "#acd0ed",
    "header_splitter": "#4796d6",
    "header_progress_track": "#ffffff",
    "header_progress_chunk": "#88c8fc",
    "header_progress_text": "#000000",
    "startstop_bg": "#acd0ed",
    "startstop_text_started": "#eb6100",
    "startstop_text_stopped": "#197ccc",
    # 音频控制窗口按钮（统一蓝色样式）
    "device_btn_bg": "#197ccc",
    "device_btn_hover": "#3089d1",
    "device_btn_pressed": "#1668ab",
    "device_btn_text": "#ffffff",
    "device_btn_disabled_bg": "#e2ebf4",
    "device_btn_disabled_text": "#656a6e",
    # 通用按钮
    "button_bg": "#ffffff",
    "button_pressed_bg": "#e2ebf4",
    # pyqtgraph 图表（曲线颜色不在此定义，保持业务约定）
    "plot_bg": "#ffffff",
    "plot_axis": "#c9c9c9",
    "plot_text": "#717171",
    "plot_label": "#555555",
    # 图标
    "arrow_down": "resource/pic/arrow_down.png",
    "arrow_up": "resource/pic/arrow_up.png",
}

THEMES = {"dark": DARK, "light": LIGHT}

_current = "dark"


def available_themes():
    """返回可用主题名列表。"""
    return sorted(THEMES.keys())


def current_theme():
    """返回当前主题名。"""
    return _current


def set_theme(name):
    """切换全局主题。未知主题名抛出 ValueError。"""
    global _current
    key = str(name).strip().lower()
    if key not in THEMES:
        raise ValueError(
            "未知主题 %r，可用主题：%s" % (name, ", ".join(available_themes()))
        )
    _current = key


def tokens():
    """返回当前主题的完整 token 字典（含字体等常量）。"""
    merged = {"font": "Microsoft YaHei"}
    merged.update(THEMES[_current])
    return merged


def color(key):
    """读取当前主题的颜色 token，未定义抛出 KeyError。"""
    return tokens()[key]


_TOKEN_RE = re.compile(r"@[a-z_]+@")


def render_qss(qss_path=None):
    """渲染 QSS 模板：将 ``@token@`` 占位符替换为当前主题色。

    模板中残留的未知占位符会抛出 ValueError，防止静默输出未替换的样式。
    """
    path = qss_path or DEFAULT_QSS
    with open(path, "r", encoding="utf-8") as handle:
        template = handle.read()
    values = tokens()
    rendered = template
    for name, value in values.items():
        rendered = rendered.replace("@%s@" % name, value)
    leftovers = sorted(set(_TOKEN_RE.findall(rendered)))
    if leftovers:
        raise ValueError("QSS 模板存在未定义的主题占位符: %s" % ", ".join(leftovers))
    return rendered
