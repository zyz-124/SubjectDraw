# -*- coding: utf-8 -*-
import glob
import json
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser

from config import (SUBJECTS_DIR, DEFAULT_FORMAT, DEFAULT_THEME,
                    DEFAULT_STYLE, GUI_SETTINGS_PATH, DEFAULT_GUI_THEME)
from core.gui_themes import THEMES, list_gui_themes
from core.renderer import render_html
from core.format_manager import discover_formats, load_prompt
from core.theme import list_themes
from core.decorations import list_styles
from core.prompts import PROMPT_STYLES
import colorsys


def _hex_to_rgb(h):
    h = h.lstrip("#")
    if len(h) == 3:
        h = h[0]*2 + h[1]*2 + h[2]*2
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _rgb_to_hex(r, g, b):
    return f"#{max(0,min(255,r)):02x}{max(0,min(255,g)):02x}{max(0,min(255,b)):02x}"


def _hex_to_hsl(h):
    r, g, b = _hex_to_rgb(h)
    r, g, b = r/255, g/255, b/255
    mx, mn = max(r, g, b), min(r, g, b)
    l = (mx + mn) / 2
    if mx == mn:
        h2 = s = 0
    else:
        d = mx - mn
        s = d / (2 - mx - mn) if l > 0.5 else d / (mx + mn)
        if mx == r:
            h2 = (g - b) / d + (6 if g < b else 0)
        elif mx == g:
            h2 = (b - r) / d + 2
        else:
            h2 = (r - g) / d + 4
        h2 /= 6
    return h2, s, l


def _hsl_to_hex(h, s, l):
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    return _rgb_to_hex(int(r*255), int(g*255), int(b*255))


def _shift_hsl(hex_color, h_off=0, s_off=0, l_off=0):
    h, s, l = _hex_to_hsl(hex_color)
    return _hsl_to_hex((h + h_off) % 1.0, max(0, min(1, s + s_off)), max(0, min(1, l + l_off)))


def colors_rgba(hex_color, alpha):
    r, g, b = _hex_to_rgb(hex_color)
    return f"#{r:02x}{g:02x}{b:02x}"


def generate_scheme(primary_hex):
    p = primary_hex
    return {
        "primary":          p,
        "primary_h":        _shift_hsl(p, h_off=0.02, s_off=0, l_off=-0.08),
        "accent":           _shift_hsl(p, h_off=0.08, s_off=0.05, l_off=0.05),
        "bg":               _shift_hsl(p, s_off=-0.85, l_off=0.42),
        "card":             _shift_hsl(p, s_off=-0.88, l_off=0.46),
        "border":           _shift_hsl(p, s_off=-0.7, l_off=0.25),
        "input_bg":         _shift_hsl(p, s_off=-0.9, l_off=0.48),
        "text":             _shift_hsl(p, s_off=-0.6, l_off=-0.35),
        "text2":            _shift_hsl(p, s_off=-0.5, l_off=-0.2),
        "muted":            _shift_hsl(p, s_off=-0.3, l_off=0.1),
        "sidebar_bg":       _shift_hsl(p, s_off=-0.55, l_off=-0.32),
        "sidebar_fg":       _shift_hsl(p, s_off=-0.6, l_off=0.38),
        "sidebar_active":   _shift_hsl(p, s_off=-0.4, l_off=-0.15),
        "sidebar_accent":   _shift_hsl(p, h_off=-0.05, s_off=0.1, l_off=0.1),
        "btn_primary_bg":   p,
        "btn_primary_fg":   "#ffffff" if _hex_to_hsl(p)[2] < 0.55 else "#222222",
        "btn_secondary_bg": _shift_hsl(p, s_off=-0.7, l_off=0.35),
        "btn_secondary_fg": _shift_hsl(p, s_off=-0.5, l_off=-0.2),
        "scrollbar_bg":     _shift_hsl(p, s_off=-0.8, l_off=0.38),
        "scrollbar_fg":     _shift_hsl(p, s_off=-0.4, l_off=0.15),
        "link":             _shift_hsl(p, h_off=0.05, s_off=0.1, l_off=0.05),
        "hover_bg":         _shift_hsl(p, s_off=-0.8, l_off=0.35),
        "success":          "#4caf50",
        "error":            "#e53935",
    }

PRESET_SUBJECTS = ["历史", "地理", "生物", "语文", "政治"]


COLOR_GROUPS = [
    ("侧边栏", [("背景", "sidebar_bg"), ("文字", "sidebar_fg"),
                ("悬停", "sidebar_active"), ("强调", "sidebar_accent")]),
    ("内容区", [("背景", "bg"), ("卡片", "card"), ("边框", "border")]),
    ("文字",   [("主文字", "text"), ("次文字", "text2"), ("辅助", "muted")]),
    ("强调色", [("主色", "primary"), ("悬停", "primary_h"), ("强调", "accent")]),
    ("输入框", [("背景", "input_bg")]),
    ("按钮",   [("主按钮背景", "btn_primary_bg"), ("主按钮文字", "btn_primary_fg"),
                ("次按钮背景", "btn_secondary_bg"), ("次按钮文字", "btn_secondary_fg")]),
    ("滚动条", [("背景", "scrollbar_bg"), ("滑块", "scrollbar_fg")]),
    ("其他",   [("链接", "link"), ("悬停背景", "hover_bg"),
                ("成功", "success"), ("错误", "error")]),
]


def load_gui_settings():
    if os.path.isfile(GUI_SETTINGS_PATH):
        try:
            with open(GUI_SETTINGS_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"gui_theme": DEFAULT_GUI_THEME}


def save_gui_settings(settings):
    with open(GUI_SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)


def _load_theme_colors(theme_name):
    base = dict(THEMES.get(theme_name, THEMES[DEFAULT_GUI_THEME]))
    settings = load_gui_settings()
    custom = settings.get("custom_colors", {})
    if custom:
        base.update(custom)
    for key in ("font_family", "font_size", "sidebar_width", "card_radius"):
        if key in settings:
            base[key] = settings[key]
    base["_name"] = theme_name
    return base


def scan_json_files():
    result = {}
    pattern = os.path.join(SUBJECTS_DIR, "*", "*.json")
    for path in sorted(glob.glob(pattern)):
        subject = os.path.basename(os.path.dirname(path))
        topic = os.path.splitext(os.path.basename(path))[0]
        result[f"{subject}/{topic}"] = path
    return result


class SidebarItem(tk.Frame):
    def __init__(self, parent, icon, text, command, colors):
        super().__init__(parent, bg=colors["sidebar_bg"], cursor="hand2")
        self.colors = colors
        self.command = command
        self.is_active = False
        ff = colors.get("font_family", "Microsoft YaHei UI")
        fs = colors.get("font_size", 10)
        self.indicator = tk.Frame(self, bg=colors["sidebar_bg"], width=3)
        self.indicator.pack(side="left", fill="y")
        self.icon_label = tk.Label(
            self, text=icon,
            bg=colors["sidebar_bg"], fg=colors["sidebar_fg"],
            font=(ff, 13),
            anchor="w", padx=12, pady=10, width=2,
        )
        self.icon_label.pack(side="left")
        self.label = tk.Label(
            self, text=text,
            bg=colors["sidebar_bg"], fg=colors["sidebar_fg"],
            font=(ff, fs + 1),
            anchor="w", padx=4, pady=10,
        )
        self.label.pack(side="left", fill="both", expand=True)
        for w_ in (self, self.label, self.icon_label):
            w_.bind("<Enter>", self._on_enter)
            w_.bind("<Leave>", self._on_leave)
            w_.bind("<Button-1>", self._on_click)

    def _on_enter(self, _):
        if not self.is_active:
            bg = self.colors["sidebar_active"]
            for w_ in (self, self.indicator, self.label, self.icon_label):
                try:
                    w_.configure(bg=bg)
                except Exception:
                    pass

    def _on_leave(self, _):
        if not self.is_active:
            bg = self.colors["sidebar_bg"]
            for w_ in (self, self.indicator, self.label, self.icon_label):
                try:
                    w_.configure(bg=bg)
                except Exception:
                    pass

    def _on_click(self, _):
        self.command()

    def set_active(self, active):
        self.is_active = active
        if active:
            bg = self.colors["sidebar_active"]
            accent = self.colors["sidebar_accent"]
            for w_ in (self, self.label, self.icon_label):
                try:
                    w_.configure(bg=bg, fg=accent)
                except Exception:
                    pass
            self.indicator.configure(bg=accent)
        else:
            bg = self.colors["sidebar_bg"]
            fg = self.colors["sidebar_fg"]
            for w_ in (self, self.label, self.icon_label):
                try:
                    w_.configure(bg=bg, fg=fg)
                except Exception:
                    pass
            self.indicator.configure(bg=bg)

    def set_text_visible(self, visible):
        if visible:
            self.label.pack(side="left", fill="both", expand=True)
        else:
            self.label.pack_forget()


class SubjectDrawGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("SubjectDraw")
        self.root.geometry("850x650")
        self.root.resizable(True, True)
        self.root.minsize(700, 500)

        gui_settings = load_gui_settings()
        theme_name = gui_settings.get("gui_theme", DEFAULT_GUI_THEME)
        if theme_name not in THEMES:
            theme_name = DEFAULT_GUI_THEME
        self.C = _load_theme_colors(theme_name)
        self.root.configure(bg=self.C["bg"])

        self.status_var = tk.StringVar(value="就绪")
        self.current_page = "prompt"
        self._prompt_text_content = ""
        self._json_text_content = ""

        avail = discover_formats() or [DEFAULT_FORMAT]
        default_fmt = DEFAULT_FORMAT if DEFAULT_FORMAT in avail else avail[0]

        self.format_a_var = tk.StringVar(value=default_fmt)
        self.subject_var = tk.StringVar(value=PRESET_SUBJECTS[0])
        self.topic_var = tk.StringVar()
        self.prompt_style_var = tk.StringVar(value="简约")
        self.format_b_var = tk.StringVar(value=default_fmt)
        self.json_choice_var = tk.StringVar()
        self.theme_var = tk.StringVar(value=DEFAULT_THEME)
        self.style_var = tk.StringVar(value=DEFAULT_STYLE)
        self.center_pos_var = tk.StringVar(value="center")
        self.mm_primary_var = tk.StringVar(value="")


        self._apply_styles()
        self._build_status_bar()
        self._build_sidebar()
        self._build_content_area()
        self._switch_page("prompt")

    def _rebuild_gui(self):
        for w in self.root.winfo_children():
            w.destroy()
        gui_settings = load_gui_settings()
        theme_name = gui_settings.get("gui_theme", DEFAULT_GUI_THEME)
        if theme_name not in THEMES:
            theme_name = DEFAULT_GUI_THEME
        self.C = _load_theme_colors(theme_name)
        self.root.configure(bg=self.C["bg"])
        self._apply_styles()
        self._build_status_bar()
        self._build_sidebar()
        self._build_content_area()
        self._switch_page(self.current_page)

    def _apply_styles(self):
        s = ttk.Style()
        s.theme_use("clam")
        C = self.C
        ff = C.get("font_family", "Microsoft YaHei UI")
        fs = C.get("font_size", 10)
        s.configure(".", background=C["bg"], foreground=C["text"],
                     font=(ff, fs))
        s.configure("TFrame", background=C["bg"])
        s.configure("Card.TFrame", background=C["card"])
        s.configure("TLabel", background=C["bg"], foreground=C["text"],
                     font=(ff, fs))
        s.configure("Card.TLabel", background=C["card"], foreground=C["text"])
        s.configure("TEntry", fieldbackground=C["input_bg"], foreground=C["text"],
                     borderwidth=1, relief="solid", padding=[8, 6])
        s.map("TEntry", bordercolor=[("focus", C["primary"])],
              relief=[("focus", "solid")])
        s.configure("TCombobox", fieldbackground=C["input_bg"], foreground=C["text"],
                     borderwidth=1, relief="solid", padding=[8, 6])
        s.map("TCombobox", bordercolor=[("focus", C["primary"])])
        s.configure("Primary.TButton", background=C.get("btn_primary_bg", C["primary"]),
                     foreground=C.get("btn_primary_fg", "#FFFFFF"),
                     borderwidth=0, padding=[20, 9],
                     font=(ff, fs, "bold"))
        s.map("Primary.TButton",
              background=[("active", C["primary_h"]), ("pressed", C["primary_h"])])
        s.configure("Secondary.TButton", background=C.get("btn_secondary_bg", C["card"]),
                     foreground=C.get("btn_secondary_fg", C["primary"]),
                     borderwidth=1, relief="solid", padding=[14, 7],
                     font=(ff, fs - 1))
        s.map("Secondary.TButton", background=[("active", C["hover_bg"])])
        s.configure("Link.TButton", background=C["card"], foreground=C["muted"],
                     borderwidth=0, padding=[8, 4],
                     font=(ff, fs - 1))
        s.map("Link.TButton", foreground=[("active", C["primary"])])
        s.configure("Horizontal.TScrollbar",
                     background=C.get("scrollbar_bg", C["border"]),
                     troughcolor=C["bg"],
                     borderwidth=0, arrowsize=0)

    def _build_status_bar(self):
        C = self.C
        ff = C.get("font_family", "Microsoft YaHei UI")
        fs = C.get("font_size", 10)
        bar = tk.Frame(self.root, bg=C["card"], height=32)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)
        dot = tk.Frame(bar, bg=C["success"], width=8, height=8)
        dot.pack(side="left", padx=(12, 6), pady=12)
        tk.Label(
            bar, textvariable=self.status_var,
            anchor="w", bg=C["card"], fg=C["muted"],
            font=(ff, fs - 1),
        ).pack(side="left", fill="x", expand=True)
        tk.Frame(bar, bg=C["border"], height=1).pack(fill="x", side="top")

    def _build_sidebar(self):
        C = self.C
        ff = C.get("font_family", "Microsoft YaHei UI")
        fs = C.get("font_size", 10)
        sidebar_w = C.get("sidebar_width", 220)
        self._sidebar_full_w = sidebar_w
        self._sidebar_collapsed = False
        self.sidebar = tk.Frame(self.root, bg=C["sidebar_bg"], width=sidebar_w)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        tf = tk.Frame(self.sidebar, bg=C["sidebar_bg"])
        tf.pack(fill="x", pady=(28, 0), padx=0)
        self._toggle_btn = tk.Label(
            tf, text="\u25C0", bg=C["sidebar_bg"], fg=C["sidebar_fg"],
            font=(ff, 11), cursor="hand2", padx=8, pady=4,
        )
        self._toggle_btn.pack(side="right", padx=(0, 8), pady=(4, 0))
        self._toggle_btn.bind("<Button-1>", lambda _: self._toggle_sidebar())
        logo_f = tk.Frame(tf, bg=C["sidebar_bg"])
        logo_f.pack(fill="x", padx=20)
        self._sb_title = tk.Label(logo_f, text="SubjectDraw",
                 bg=C["sidebar_bg"], fg=C["sidebar_fg"],
                 font=(ff, 17, "bold"),
                 anchor="w")
        self._sb_title.pack(fill="x")
        self._sb_subtitle = tk.Label(logo_f, text="知识卡片排版工具",
                 bg=C["sidebar_bg"],
                 fg=colors_rgba(C["sidebar_fg"], 0.7),
                 font=(ff, fs - 1),
                 anchor="w")
        self._sb_subtitle.pack(fill="x", pady=(2, 0))
        self._sb_spacer = tk.Frame(self.sidebar, bg=C["sidebar_bg"], height=28)
        self._sb_spacer.pack()
        self._sb_sep = tk.Frame(self.sidebar, bg=colors_rgba(C["sidebar_fg"], 0.15), height=1)
        self._sb_sep.pack(fill="x", padx=20)
        nf = tk.Frame(self.sidebar, bg=C["sidebar_bg"])
        nf.pack(fill="x", pady=(12, 0))
        self.prompt_item = SidebarItem(nf, "\u270D", "生成提示词",
                                       lambda: self._switch_page("prompt"), C)
        self.prompt_item.pack(fill="x")
        self.preview_item = SidebarItem(nf, "\u25A3", "生成预览",
                                         lambda: self._switch_page("preview"), C)
        self.preview_item.pack(fill="x")
        self.tutorial_item = SidebarItem(nf, "\u2753", "使用教程",
                                          lambda: self._show_tutorial(), C)
        self.tutorial_item.pack(fill="x")
        tk.Frame(self.sidebar, bg=C["sidebar_bg"]).pack(fill="both", expand=True)
        self._sb_sep2 = tk.Frame(self.sidebar, bg=colors_rgba(C["sidebar_fg"], 0.15), height=1)
        self._sb_sep2.pack(fill="x", padx=20)
        sf = tk.Frame(self.sidebar, bg=C["sidebar_bg"], cursor="hand2")
        sf.pack(fill="x", pady=(10, 28))
        self._sb_settings_text = tk.Label(sf, text="  \u2699  设置",
                      bg=C["sidebar_bg"], fg=C["sidebar_fg"],
                      font=(ff, fs),
                      anchor="w", padx=20, pady=10)
        self._sb_settings_text.pack(fill="x")
        def se(_):
            for w_ in (sf, self._sb_settings_text):
                try:
                    w_.configure(bg=C["sidebar_active"])
                except Exception:
                    pass
        def slv(_):
            for w_ in (sf, self._sb_settings_text):
                try:
                    w_.configure(bg=C["sidebar_bg"])
                except Exception:
                    pass
        for w_ in (sf, self._sb_settings_text):
            w_.bind("<Enter>", se)
            w_.bind("<Leave>", slv)
            w_.bind("<Button-1>", lambda _: self.open_settings())

    def _toggle_sidebar(self):
        self._sidebar_collapsed = not self._sidebar_collapsed
        collapsed = self._sidebar_collapsed
        C = self.C
        if collapsed:
            self.sidebar.configure(width=64)
            self._toggle_btn.configure(text="\u25B6")
            self.prompt_item.set_text_visible(False)
            self.preview_item.set_text_visible(False)
            self.tutorial_item.set_text_visible(False)
            self._sb_settings_text.configure(text="\u2699", fg=C["sidebar_bg"])
        else:
            self.sidebar.configure(width=self._sidebar_full_w)
            self._toggle_btn.configure(text="\u25C0")
            self.prompt_item.set_text_visible(True)
            self.preview_item.set_text_visible(True)
            self.tutorial_item.set_text_visible(True)
            self.prompt_item.set_active(self.current_page == "prompt")
            self.preview_item.set_active(self.current_page == "preview")
            self._sb_settings_text.configure(text="  \u2699  设置", fg=C["sidebar_fg"])

    def _show_tutorial(self):
        C = self.C
        ff = C.get("font_family", "Microsoft YaHei UI")
        fs = C.get("font_size", 10)
        dlg = tk.Toplevel(self.root)
        dlg.title("使用教程")
        dlg.geometry("580x520")
        dlg.resizable(False, True)
        dlg.configure(bg=C["bg"])
        dlg.transient(self.root)
        dlg.grab_set()
        dlg.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - 580) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - 520) // 2
        dlg.geometry(f"+{x}+{y}")

        tk.Label(dlg, text="SubjectDraw 使用教程",
                 bg=C["bg"], fg=C["primary"],
                 font=(ff, 15, "bold")).pack(pady=(20, 10))

        text = tk.Text(dlg, wrap="word", bg=C["card"], fg=C["text"],
                       font=(ff, fs), relief="flat", padx=20, pady=16,
                       highlightthickness=1, highlightbackground=C["border"])
        text.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        text.configure(state="normal")

        tutorial = """【Step 1】生成提示词
1. 在左侧选择学科和主题
2. 选择格式（思维导图/表格/时间轴/大纲）
3. 选择写作风格
4. 点击"生成提示词"
5. 点击"复制"按钮，将提示词粘贴到 AI 对话中

【Step 2】获取 AI 返回的 JSON
1. 将提示词发送给 AI（如 ChatGPT、Claude、Kimi 等）
2. AI 会返回一段 JSON 格式的知识卡片数据
3. 复制 AI 返回的 JSON 内容

【Step 3】生成预览
1. 切换到"生成预览"页面
2. 将 JSON 粘贴到文本框中
3. 选择格式、色彩主题、装饰风格
4. 可选：调整中心卡片位置（center/left/right/top/bottom）
5. 可选：自定义思维导图颜色（主题色、强调色、背景色、文字色）
6. 点击"生成预览"查看效果

【思维导图交互操作】
• 拖拽：按住鼠标左键拖动任意卡片
• 缩放：鼠标滚轮 或 右上角 +/- 按钮
• 平移：拖拽空白区域
• 右键菜单：右键点击分支/要点/中心卡片
  - 编辑文字、高光、反转方向、添加要点
  - 更改背景色/边框色/文字色
  - 删除要点/删除分支
  - 中心卡片：展开/折叠所有分支
• 撤销/重做：Ctrl+Z / Ctrl+Y（或右下角按钮）
• 反转方向：只移动要点到另一侧，分支标题不动
• 拖拽越过中心：连接线自动换边

【设置】
• 点击侧边栏底部"设置"
• 可切换 GUI 主题、字体、侧边栏宽度
• 可自定义 GUI 各区域颜色"""
        text.insert("1.0", tutorial)
        text.configure(state="disabled")

        tk.Button(dlg, text="关闭", bg=C["primary"], fg=C["bg"],
                  font=(ff, fs + 1, "bold"), relief="flat",
                  padx=30, pady=6, command=dlg.destroy).pack(pady=(0, 16))

    def _build_content_area(self):
        self.content = tk.Frame(self.root, bg=self.C["bg"])
        self.content.pack(side="left", fill="both", expand=True)

    def _switch_page(self, page):
        if hasattr(self, "prompt_text") and self.prompt_text.winfo_exists():
            self._prompt_text_content = self.prompt_text.get("1.0", "end").strip()
        if hasattr(self, "json_text") and self.json_text.winfo_exists():
            self._json_text_content = self.json_text.get("1.0", "end").strip()
        for w_ in self.content.winfo_children():
            w_.destroy()
        self.current_page = page
        self.prompt_item.set_active(page == "prompt")
        self.preview_item.set_active(page == "preview")
        if page == "prompt":
            self._build_page_prompt()
        else:
            self._build_page_preview()

    def _card(self, parent, **kw):
        cr = self.C.get("card_radius", 12)
        f = tk.Frame(parent, bg=self.C["card"], **kw)
        if cr > 0:
            f.configure(
                highlightthickness=1,
                highlightbackground=self.C["border"],
                highlightcolor=self.C["primary"],
            )
        return f

    def _lbl(self, parent, text):
        ff = self.C.get("font_family", "Microsoft YaHei UI")
        return tk.Label(parent, text=text,
                        bg=self.C["card"], fg=self.C["text2"],
                        font=(ff, 9))

    def _input(self, parent, variable, width=20, **kw):
        return ttk.Entry(parent, textvariable=variable, width=width, **kw)

    def _combo(self, parent, variable, values, width=18):
        return ttk.Combobox(parent, textvariable=variable,
                            values=values, width=width, state="readonly")

    def _build_page_prompt(self):
        C = self.C
        ff = C.get("font_family", "Microsoft YaHei UI")
        fs = C.get("font_size", 10)
        outer = tk.Frame(self.content, bg=C["bg"])
        outer.pack(fill="both", expand=True, padx=24, pady=20)
        c1 = self._card(outer)
        c1.pack(fill="x")
        i1 = tk.Frame(c1, bg=C["card"])
        i1.pack(fill="x", padx=20, pady=18)
        tk.Label(i1, text="基本信息", bg=C["card"], fg=C["primary"],
                 font=(ff, fs + 2, "bold")).pack(anchor="w", pady=(0, 12))
        g = tk.Frame(i1, bg=C["card"])
        g.pack(fill="x")
        g.columnconfigure(1, weight=1)
        g.columnconfigure(3, weight=1)
        avail = discover_formats() or [DEFAULT_FORMAT]
        self._lbl(g, "格式").grid(row=0, column=0, sticky="w", padx=(0, 6), pady=(0, 3))
        self._combo(g, self.format_a_var, avail, 16).grid(
            row=1, column=0, columnspan=2, sticky="ew", padx=(0, 16), pady=(0, 10))
        self._lbl(g, "学科").grid(row=0, column=2, sticky="w", padx=(0, 6), pady=(0, 3))
        self._combo(g, self.subject_var, PRESET_SUBJECTS, 16).grid(
            row=1, column=2, columnspan=2, sticky="ew", pady=(0, 10))
        self._lbl(g, "主题").grid(row=2, column=0, sticky="w", padx=(0, 6), pady=(0, 3))
        self._input(g, self.topic_var, 16).grid(row=3, column=0, columnspan=2, sticky="ew", padx=(0, 16), pady=(0, 6))
        self._lbl(g, "提示词风格").grid(row=2, column=2, sticky="w", padx=(0, 6), pady=(0, 3))
        self._combo(g, self.prompt_style_var, PROMPT_STYLES, 16).grid(
            row=3, column=2, columnspan=2, sticky="ew", pady=(0, 6))

        c2 = self._card(outer)
        c2.pack(fill="x", pady=(14, 0))
        i2 = tk.Frame(c2, bg=C["card"])
        i2.pack(fill="x", padx=20, pady=14)
        bf = tk.Frame(i2, bg=C["card"])
        bf.pack(fill="x")
        ttk.Button(bf, text="生成提示词", style="Primary.TButton",
                   command=self.on_generate_prompt).pack(side="left", padx=(0, 8))
        ttk.Button(bf, text="设置", style="Link.TButton",
                   command=self.open_settings).pack(side="right")

        c3 = self._card(outer)
        c3.pack(fill="both", expand=True, pady=(14, 0))
        i3 = tk.Frame(c3, bg=C["card"])
        i3.pack(fill="both", expand=True, padx=16, pady=(10, 16))
        self.prompt_text = tk.Text(
            i3, wrap="word", state="disabled",
            bg=C["input_bg"], fg=C["text"],
            font=("Consolas", 10), relief="flat",
            borderwidth=0, highlightthickness=1,
            highlightbackground=C["border"], highlightcolor=C["primary"],
            padx=10, pady=10)
        sb = ttk.Scrollbar(i3, command=self.prompt_text.yview)
        self.prompt_text.configure(yscrollcommand=sb.set)
        self.prompt_text.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        if self._prompt_text_content:
            self.prompt_text.configure(state="normal")
            self.prompt_text.insert("1.0", self._prompt_text_content)
            self.prompt_text.configure(state="disabled")

    def _build_page_preview(self):
        C = self.C
        ff = C.get("font_family", "Microsoft YaHei UI")
        fs = C.get("font_size", 10)
        outer = tk.Frame(self.content, bg=C["bg"])
        outer.pack(fill="both", expand=True, padx=24, pady=20)
        c1 = self._card(outer)
        c1.pack(fill="x")
        i1 = tk.Frame(c1, bg=C["card"])
        i1.pack(fill="x", padx=20, pady=14)
        self._lbl(i1, "JSON 文件").pack(anchor="w", pady=(0, 6))
        ff2 = tk.Frame(i1, bg=C["card"])
        ff2.pack(fill="x")
        self.json_map = scan_json_files()
        self.json_combo = ttk.Combobox(
            ff2, textvariable=self.json_choice_var,
            values=list(self.json_map.keys()), width=30, state="readonly")
        self.json_combo.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.json_combo.bind("<<ComboboxSelected>>", self.on_select_json)
        ttk.Button(ff2, text="浏览", style="Secondary.TButton",
                   command=self.on_browse_json).pack(side="left")

        c2 = self._card(outer)
        c2.pack(fill="x", pady=(14, 0))
        i2 = tk.Frame(c2, bg=C["card"])
        i2.pack(fill="x", padx=20, pady=14)
        tk.Label(i2, text="样式设置", bg=C["card"], fg=C["primary"],
                 font=(ff, fs + 2, "bold")).pack(anchor="w", pady=(0, 12))
        g2 = tk.Frame(i2, bg=C["card"])
        g2.pack(fill="x")
        g2.columnconfigure(1, weight=1)
        g2.columnconfigure(3, weight=1)
        avail = discover_formats() or [DEFAULT_FORMAT]
        self._lbl(g2, "格式").grid(row=0, column=0, sticky="w", padx=(0, 6), pady=(0, 3))
        self._combo(g2, self.format_b_var, avail, 14).grid(
            row=1, column=0, columnspan=2, sticky="ew", padx=(0, 16), pady=(0, 10))
        self._lbl(g2, "装饰风格").grid(row=0, column=2, sticky="w", padx=(0, 6), pady=(0, 3))
        self._combo(g2, self.style_var, list_styles(), 14).grid(
            row=1, column=2, columnspan=2, sticky="ew", pady=(0, 10))
        self._lbl(g2, "中心位置").grid(row=2, column=0, sticky="w", padx=(0, 6), pady=(0, 3))
        POSITIONS = ["center", "left", "right", "top", "bottom"]
        self._combo(g2, self.center_pos_var, POSITIONS, 14).grid(
            row=3, column=0, columnspan=2, sticky="ew", padx=(0, 16), pady=(0, 6))
        self._lbl(g2, "自定义主题色").grid(row=2, column=2, sticky="w", padx=(0, 6), pady=(8, 3))
        cf = tk.Frame(g2, bg=C["card"])
        cf.grid(row=3, column=2, columnspan=2, sticky="ew", pady=(0, 6))
        color_entry = tk.Entry(cf, textvariable=self.mm_primary_var, width=9,
                               bg=C["input_bg"], fg=C["text"],
                               font=(ff, fs), relief="flat",
                               highlightthickness=1,
                               highlightbackground=C["border"],
                               highlightcolor=C["primary"])
        color_entry.pack(side="left")
        swatch = tk.Canvas(cf, width=24, height=24,
                           bg=self.mm_primary_var.get() or "#ffffff",
                           highlightthickness=1,
                           highlightbackground=C["border"],
                           cursor="hand2")
        swatch.pack(side="left", padx=(6, 0))
        def _pick_color(_e=None):
            from tkinter import colorchooser
            c = colorchooser.askcolor(initialcolor=self.mm_primary_var.get() or "#4a90d9")
            if c and c[1]:
                self.mm_primary_var.set(c[1])
                swatch.configure(bg=c[1])
        swatch.bind("<Button-1>", _pick_color)
        def _sync_swatch(*_a):
            v = self.mm_primary_var.get().strip()
            if v:
                swatch.configure(bg=v)
        self.mm_primary_var.trace_add("write", _sync_swatch)

        c4 = self._card(outer)
        c4.pack(fill="both", expand=True, pady=(14, 0))
        i4 = tk.Frame(c4, bg=C["card"])
        i4.pack(fill="both", expand=True, padx=16, pady=(10, 16))
        bf = tk.Frame(i4, bg=C["card"])
        bf.pack(fill="x", pady=(0, 10))
        tk.Label(i4, text="在此粘贴 AI 生成的 JSON", bg=C["card"], fg=C["text2"],
                 font=(ff, fs - 1)).pack(anchor="w", pady=(0, 6))
        self.json_text = tk.Text(
            i4, wrap="none",
            bg=C["input_bg"], fg=C["text"],
            font=("Consolas", 10), relief="flat",
            borderwidth=0, highlightthickness=1,
            highlightbackground=C["border"], highlightcolor=C["primary"],
            padx=10, pady=10)
        js = ttk.Scrollbar(i4, command=self.json_text.yview)
        self.json_text.configure(yscrollcommand=js.set)
        self.json_text.pack(side="left", fill="both", expand=True)
        js.pack(side="right", fill="y")
        ttk.Button(bf, text="生成预览", style="Primary.TButton",
                   command=self.on_generate_preview).pack(side="right")
        if self._json_text_content:
            self.json_text.insert("1.0", self._json_text_content)

    def open_settings(self):
        gui_settings = load_gui_settings()
        C = self.C
        theme_name = C.get("_name", DEFAULT_GUI_THEME)

        dlg = tk.Toplevel(self.root)
        dlg.title("设置")
        dlg.geometry("500x520")
        dlg.resizable(False, False)
        dlg.configure(bg=C["bg"])
        dlg.transient(self.root)
        dlg.grab_set()
        dlg.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - 500) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - 520) // 2
        dlg.geometry(f"+{x}+{y}")

        canvas = tk.Canvas(dlg, bg=C["bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(dlg, orient="vertical", command=canvas.yview)
        scrollable = tk.Frame(canvas, bg=C["bg"])
        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind("<MouseWheel>", _on_mousewheel)
        scrollable.bind("<MouseWheel>", _on_mousewheel)

        def _bind_wheel(widget):
            widget.bind("<MouseWheel>", _on_mousewheel)
            for child in widget.winfo_children():
                _bind_wheel(child)

        def _on_canvas_configure(event):
            canvas.itemconfig(canvas.find_all()[-1], width=event.width)
        canvas.bind("<Configure>", _on_canvas_configure)

        tc = self._card(scrollable)
        tc.pack(fill="x", padx=12, pady=(12, 0))
        ti = tk.Frame(tc, bg=C["card"])
        ti.pack(fill="x", padx=16, pady=14)
        tk.Label(ti, text="界面设置", bg=C["card"], fg=C["primary"],
                 font=("Microsoft YaHei UI", 11, "bold")).pack(anchor="w", pady=(0, 10))
        tf = tk.Frame(ti, bg=C["card"])
        tf.pack(fill="x")
        self._lbl(tf, "界面主题").pack(anchor="w", pady=(0, 2))
        gui_theme_var = tk.StringVar(value=gui_settings.get("gui_theme", DEFAULT_GUI_THEME))
        ttk.Combobox(tf, textvariable=gui_theme_var,
                     values=list_gui_themes(), width=20, state="readonly").pack(fill="x", pady=(0, 6))
        tk.Label(ti, text="切换后立即生效",
                 bg=C["card"], fg=C["muted"],
                 font=("Microsoft YaHei UI", 8)).pack(anchor="w")

        lf = tk.Frame(ti, bg=C["card"])
        lf.pack(fill="x", pady=(8, 0))
        lf.columnconfigure(1, weight=1)
        self._lbl(lf, "字体").grid(row=0, column=0, sticky="w", padx=(0, 6))
        theme_def = THEMES.get(gui_settings.get("gui_theme", DEFAULT_GUI_THEME), {})
        font_family_var = tk.StringVar(value=gui_settings.get("font_family", theme_def.get("font_family", "Microsoft YaHei UI")))
        ttk.Combobox(lf, textvariable=font_family_var, width=18, state="readonly",
                     values=["Microsoft YaHei UI", "SimHei", "SimSun", "KaiTi",
                             "Arial", "Consolas", "Segoe UI", "PingFang SC"]).grid(
            row=1, column=0, columnspan=2, sticky="ew", padx=(0, 16))
        self._lbl(lf, "字号").grid(row=0, column=2, sticky="w", padx=(0, 6))
        font_size_var = tk.StringVar(value=str(gui_settings.get("font_size", theme_def.get("font_size", 10))))
        ttk.Combobox(lf, textvariable=font_size_var, width=6, state="readonly",
                     values=["8", "9", "10", "11", "12", "14", "16"]).grid(
            row=1, column=2, sticky="ew")

        sf = tk.Frame(ti, bg=C["card"])
        sf.pack(fill="x", pady=(8, 0))
        sf.columnconfigure(1, weight=1)
        self._lbl(sf, "侧边栏宽度").grid(row=0, column=0, sticky="w", padx=(0, 6))
        sidebar_width_var = tk.StringVar(value=str(gui_settings.get("sidebar_width", theme_def.get("sidebar_width", 180))))
        ttk.Combobox(sf, textvariable=sidebar_width_var, width=6, state="readonly",
                     values=["140", "160", "180", "200", "220", "240"]).grid(
            row=1, column=0, sticky="ew", padx=(0, 16))
        self._lbl(sf, "卡片圆角").grid(row=0, column=2, sticky="w", padx=(0, 6))
        card_radius_var = tk.StringVar(value=str(gui_settings.get("card_radius", theme_def.get("card_radius", 8))))
        ttk.Combobox(sf, textvariable=card_radius_var, width=6, state="readonly",
                     values=["0", "4", "6", "8", "10", "12", "16"]).grid(
            row=1, column=2, sticky="ew")

        custom_colors = gui_settings.get("custom_colors", {})
        color_vars = {}
        color_previews = {}

        cc_card = self._card(scrollable)
        cc_card.pack(fill="x", padx=12, pady=(10, 0))
        cc_inner = tk.Frame(cc_card, bg=C["card"])
        cc_inner.pack(fill="x", padx=16, pady=14)
        tk.Label(cc_inner, text="自定义颜色", bg=C["card"], fg=C["primary"],
                 font=("Microsoft YaHei UI", 11, "bold")).pack(anchor="w", pady=(0, 2))
        tk.Label(cc_inner, text="点击色块选择颜色，留空使用主题默认色",
                 bg=C["card"], fg=C["muted"],
                 font=("Microsoft YaHei UI", 8)).pack(anchor="w", pady=(0, 10))

        PALETTE = [
            "#222222", "#333333", "#555555", "#888888", "#aaaaaa", "#cccccc", "#eeeeee", "#ffffff",
            "#d32f2f", "#e64a19", "#f57c00", "#fbc02d", "#689f38", "#388e3c", "#0097a7", "#0288d1",
            "#303f9f", "#512da8", "#7b1fa2", "#c2185b", "#ff5252", "#ff9800", "#ffeb3b", "#69f0ae",
            "#40c4ff", "#536dfe", "#e040fb", "#ff6e40", "#8d6e63", "#78909c", "#90a4ae", "#b0bec5",
        ]

        def open_palette(key, var, preview):
            pal_dlg = tk.Toplevel(dlg)
            pal_dlg.title("选择颜色")
            pal_dlg.configure(bg=C["bg"])
            pal_dlg.transient(dlg)
            pal_dlg.grab_set()
            pal_dlg.resizable(False, False)

            tk.Label(pal_dlg, text="点击选择颜色", bg=C["bg"], fg=C["text"],
                     font=("Microsoft YaHei UI", 10, "bold")).pack(padx=12, pady=(10, 6), anchor="w")

            grid_f = tk.Frame(pal_dlg, bg=C["bg"])
            grid_f.pack(padx=12, pady=4)

            selected = {"val": var.get()}
            sel_preview = tk.Frame(grid_f, bg=selected["val"] or "#cccccc",
                                   width=36, height=36, relief="solid", bd=2)
            sel_preview.grid(row=0, column=0, columnspan=8, pady=(0, 8), sticky="w")
            sel_lbl = tk.Label(grid_f, text=selected["val"] or "(默认)", bg=C["bg"], fg=C["text"],
                               font=("Consolas", 9))
            sel_lbl.grid(row=1, column=0, columnspan=8, pady=(0, 6), sticky="w")

            def pick(color):
                selected["val"] = color
                sel_preview.configure(bg=color)
                sel_lbl.configure(text=color)
                var.set(color)
                default_val = THEMES.get(theme_name, {}).get(key, "#FFFFFF")
                try:
                    preview.configure(bg=color or default_val)
                except Exception:
                    pass

            for idx, color in enumerate(PALETTE):
                row = 2 + idx // 8
                col = idx % 8
                swatch = tk.Frame(grid_f, bg=color, width=30, height=30,
                                  relief="raised", bd=1, cursor="hand2")
                swatch.grid(row=row, column=col, padx=2, pady=2)
                swatch.bind("<Button-1>", lambda e, c=color: pick(c))

            btn_f = tk.Frame(pal_dlg, bg=C["bg"])
            btn_f.pack(fill="x", padx=12, pady=(8, 4))

            def open_system():
                init = selected["val"] or "#333333"
                result = colorchooser.askcolor(initialcolor=init, parent=pal_dlg, title="自定义颜色")
                if result and result[1]:
                    pick(result[1])

            ttk.Button(btn_f, text="更多颜色...", command=open_system).pack(side="left", padx=(0, 6))

            def clear_color():
                selected["val"] = ""
                var.set("")
                sel_preview.configure(bg=THEMES.get(theme_name, {}).get(key, "#cccccc"))
                sel_lbl.configure(text="(默认)")
                default_val = THEMES.get(theme_name, {}).get(key, "#FFFFFF")
                try:
                    preview.configure(bg=default_val)
                except Exception:
                    pass

            ttk.Button(btn_f, text="恢复默认", command=clear_color).pack(side="left", padx=(0, 6))
            ttk.Button(btn_f, text="确定", command=pal_dlg.destroy).pack(side="right")

            pal_dlg.update_idletasks()
            dx = dlg.winfo_x() + (dlg.winfo_width() - pal_dlg.winfo_reqwidth()) // 2
            dy = dlg.winfo_y() + (dlg.winfo_height() - pal_dlg.winfo_reqheight()) // 2
            pal_dlg.geometry(f"+{dx}+{dy}")

        quick_f = tk.Frame(cc_inner, bg=C["card"])
        quick_f.pack(fill="x", pady=(0, 8))
        tk.Label(quick_f, text="一键配色", bg=C["card"], fg=C["primary"],
                 font=("Microsoft YaHei UI", 10, "bold")).pack(anchor="w", pady=(0, 4))
        tk.Label(quick_f, text="选择一个主色，自动生成完整配色方案",
                 bg=C["card"], fg=C["muted"],
                 font=("Microsoft YaHei UI", 8)).pack(anchor="w", pady=(0, 6))

        QUICK_PRESETS = [
            ("#333333", "经典黑"), ("#1a73e8", "谷歌蓝"), ("#e53935", "中国红"),
            ("#00897b", "青竹绿"), ("#7b1fa2", "皇家紫"), ("#f57c00", "暖阳橙"),
            ("#5d4037", "复古棕"), ("#37474f", "石墨灰"),
        ]

        qp_row = tk.Frame(quick_f, bg=C["card"])
        qp_row.pack(fill="x", pady=(0, 6))
        for qi, (qc, qn) in enumerate(QUICK_PRESETS):
            sf = tk.Frame(qp_row, bg=C["card"])
            sf.pack(side="left", padx=(0, 6))
            sw = tk.Frame(sf, bg=qc, width=28, height=28, relief="raised",
                          bd=1, cursor="hand2")
            sw.pack()
            tk.Label(sf, text=qn, bg=C["card"], fg=C["text2"],
                     font=("Microsoft YaHei UI", 7)).pack()

            def _apply_scheme(color=qc):
                scheme = generate_scheme(color)
                for k, v in scheme.items():
                    if k in color_vars:
                        color_vars[k].set(v)
                        if k in color_previews:
                            try:
                                color_previews[k].configure(bg=v)
                            except Exception:
                                pass
            sw.bind("<Button-1>", lambda e, fn=_apply_scheme: fn())

        def _apply_custom():
            result = colorchooser.askcolor(initialcolor="#1a73e8",
                                           parent=dlg, title="选择主色")
            if result and result[1]:
                scheme = generate_scheme(result[1])
                for k, v in scheme.items():
                    if k in color_vars:
                        color_vars[k].set(v)
                        if k in color_previews:
                            try:
                                color_previews[k].configure(bg=v)
                            except Exception:
                                pass

        ttk.Button(quick_f, text="自定义主色...", command=_apply_custom).pack(anchor="w")

        sep = tk.Frame(cc_inner, bg=C["border"], height=1)
        sep.pack(fill="x", pady=(6, 2))

        tk.Label(cc_inner, text="单独微调", bg=C["card"], fg=C["primary"],
                 font=("Microsoft YaHei UI", 10, "bold")).pack(anchor="w", pady=(4, 4))

        for group_name, fields in COLOR_GROUPS:
            tk.Label(cc_inner, text=group_name, bg=C["card"], fg=C["text2"],
                     font=("Microsoft YaHei UI", 9, "bold")).pack(anchor="w", pady=(8, 2))
            row_frame = tk.Frame(cc_inner, bg=C["card"])
            row_frame.pack(fill="x")
            for i, (label_text, key) in enumerate(fields):
                r = i // 2
                c = (i % 2) * 3
                current_val = custom_colors.get(key, "")
                default_val = THEMES.get(theme_name, {}).get(key, "#FFFFFF")
                var = tk.StringVar(value=current_val)
                color_vars[key] = var

                preview = tk.Frame(row_frame, bg=current_val or default_val,
                                   width=22, height=22,
                                   highlightthickness=1,
                                   highlightbackground=C["border"],
                                   cursor="hand2")
                preview.grid(row=r, column=c, padx=(0, 3), pady=2, sticky="w")
                color_previews[key] = preview

                color_btn = tk.Button(row_frame, text=label_text, bg=C["card"], fg=C["text2"],
                                      font=("Microsoft YaHei UI", 9), bd=0, cursor="hand2",
                                      anchor="w", padx=2,
                                      command=lambda k=key, v=var, p=preview: open_palette(k, v, p))
                color_btn.grid(row=r, column=c+1, columnspan=2, sticky="w", padx=(0, 12), pady=2)

        def reset_colors():
            for key, var in color_vars.items():
                var.set("")
                default_val = THEMES.get(theme_name, {}).get(key, "#FFFFFF")
                if key in color_previews:
                    try:
                        color_previews[key].configure(bg=default_val)
                    except Exception:
                        pass

        tk.Button(cc_inner, text="恢复默认颜色", bg=C["card"], fg=C["primary"],
                  font=("Microsoft YaHei UI", 9), bd=0, cursor="hand2",
                  command=reset_colors).pack(anchor="w", pady=(8, 0))

        def on_save():
            custom = {}
            for key, var in color_vars.items():
                val = var.get().strip()
                if val:
                    custom[key] = val
            settings = {"gui_theme": gui_theme_var.get()}
            if custom:
                settings["custom_colors"] = custom
            settings["font_family"] = font_family_var.get()
            settings["font_size"] = int(font_size_var.get())
            settings["sidebar_width"] = int(sidebar_width_var.get())
            settings["card_radius"] = int(card_radius_var.get())
            save_gui_settings(settings)
            dlg.destroy()
            self._rebuild_gui()

        bf2 = tk.Frame(scrollable, bg=C["bg"])
        bf2.pack(fill="x", padx=12, pady=(12, 16))
        ttk.Button(bf2, text="保存", style="Primary.TButton",
                   command=on_save).pack(side="left")

        _bind_wheel(scrollable)

    def on_generate_prompt(self):
        subject = self.subject_var.get().strip()
        topic = self.topic_var.get().strip()
        fmt = self.format_a_var.get().strip()
        style = self.prompt_style_var.get().strip()
        if not subject or not topic:
            self.status_var.set("请填写学科和主题")
            return
        try:
            text = load_prompt(fmt, subject, topic, style=style)
        except Exception as e:
            self.status_var.set(f"错误: {e}")
            return
        self.prompt_text.configure(state="normal")
        self.prompt_text.delete("1.0", "end")
        self.prompt_text.insert("1.0", text)
        self.prompt_text.configure(state="disabled")
        self._prompt_text_content = text
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.status_var.set("提示词已复制，粘贴到 AI 聊天中，再点「粘贴 JSON」")

    def on_select_json(self, event=None):
        label = self.json_choice_var.get()
        path = self.json_map.get(label)
        if path:
            self._load_json_into_editor(path)

    def on_browse_json(self):
        path = filedialog.askopenfilename(
            initialdir=SUBJECTS_DIR,
            title="选择知识库 JSON",
            filetypes=[("JSON 文件", "*.json"), ("所有文件", "*.*")],
        )
        if not path:
            return
        self.json_choice_var.set(os.path.basename(path))
        self._load_json_into_editor(path)

    def _load_json_into_editor(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            self.status_var.set(f"错误: 无法读取文件 ({e})")
            return
        self.json_text.delete("1.0", "end")
        self.json_text.insert("1.0", content)
        self._json_text_content = content
        self.status_var.set(f"已加载: {os.path.basename(path)}")

    def on_generate_preview(self):
        raw = self.json_text.get("1.0", "end").strip()
        if not raw:
            self.status_var.set("错误: JSON 内容为空")
            return
        try:
            decoder = json.JSONDecoder()
            data, _ = decoder.raw_decode(raw)
        except (json.JSONDecodeError, ValueError) as e:
            self.status_var.set(f"错误: JSON 格式无效 ({e})")
            messagebox.showerror("JSON 解析失败", str(e))
            return
        try:
            from config import OUTPUT_DIR
            import webbrowser
            fmt = self.format_b_var.get().strip() or DEFAULT_FORMAT
            center_pos = self.center_pos_var.get().strip() or "center"
            if center_pos != "center":
                data["centerPosition"] = center_pos
            elif "centerPosition" not in data:
                data["centerPosition"] = "center"
            fmt_opts = dict(
                style=self.style_var.get().strip() or DEFAULT_STYLE,
                mm_colors={
                    "primary": self.mm_primary_var.get().strip(),
                },
            )
            html = render_html(data, fmt=fmt, **fmt_opts)
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            center = data.get("center", "output")
            subject = data.get("subject", "")
            filename = f"{subject}_{center}.html" if subject else f"{center}.html"
            out_path = os.path.join(OUTPUT_DIR, filename)
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(html)
            webbrowser.open("file:///" + os.path.abspath(out_path).replace("\\", "/"))
            self.status_var.set(f"已生成: {filename}")
        except Exception as e:
            self.status_var.set(f"错误: {e}")


def run():
    root = tk.Tk()
    icon_path = os.path.join(os.path.dirname(__file__), "icon.png")
    if os.path.isfile(icon_path):
        icon_img = tk.PhotoImage(file=icon_path)
        root.iconphoto(True, icon_img)
    SubjectDrawGUI(root)
    root.mainloop()


if __name__ == "__main__":
    run()