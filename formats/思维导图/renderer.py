from core.theme import theme_css_vars
from core.decorations import (
    divider_html, title_ornament, bullet_svg,
    shared_css, decoration_css, student_info_html, footer_html,
    knowledge_panel_html, knowledge_panel_css, base_page_css,
)


LAYOUT_MAP = {
    "center": {"is_split": True, "direction": "row", "align": "center"},
    "left":   {"is_split": False, "direction": "row", "align": "start"},
    "right":  {"is_split": False, "direction": "row-reverse", "align": "start"},
    "top":    {"is_split": False, "direction": "column", "align": "center"},
    "bottom": {"is_split": False, "direction": "column-reverse", "align": "center"},
}


def _build_mm_color_overrides(colors):
    mapping = {
        "primary": "--primary",
        "accent": "--accent",
        "bg": "--bg",
        "text": "--text",
    }
    lines = []
    for key, var in mapping.items():
        val = colors.get(key, "")
        if val and val.strip():
            lines.append(f"  {var}: {val.strip()};")
    if lines:
        return ":root {\n" + "\n".join(lines) + "\n}"
    return ""


def render_html(data, **fmt_opts):
    theme = fmt_opts.get("theme", "素雅灰")
    style = fmt_opts.get("style", "简约几何")
    mm_colors = fmt_opts.get("mm_colors", {})

    center = data.get("center", "")
    subtitle = data.get("subtitle", "")
    subject = data.get("subject", "")
    branches = data.get("branches", [])
    timeline = data.get("timeline", [])

    position = data.get("centerPosition", "center")
    if position not in LAYOUT_MAP:
        position = "center"
    layout_cfg = LAYOUT_MAP[position]
    is_split = layout_cfg["is_split"]

    student_html = student_info_html(
        fmt_opts.get("student_name", ""),
        fmt_opts.get("cls", ""),
        fmt_opts.get("student_id", ""),
        fmt_opts.get("date", ""),
    )
    footer = footer_html("1", fmt_opts.get("date", ""))
    divider = divider_html(style)
    title_dec = title_ornament(style)

    if is_split and len(branches) >= 2:
        mid = (len(branches) + 1) // 2
        left_branches = branches[:mid]
        right_branches = branches[mid:]
    else:
        left_branches = branches
        right_branches = []

    def build_branch(bi, b, side_cls=""):
        title = b.get("title", "")
        points = b.get("points", [])
        pts = ""
        for pi, p in enumerate(points):
            pts += f'<div class="point-card" data-branch="{bi}" data-idx="{pi}"><span class="bullet">{bullet_svg(style)}</span><span class="card-text">{p}</span></div>'
        return f'<div class="branch-group{side_cls}" data-branch="{bi}"><div class="branch-title-card" data-branch="{bi}"><span class="card-text">{title}</span></div><div class="branch-points">{pts}</div></div>'

    if is_split:
        left_html = ""
        for bi, b in enumerate(left_branches):
            left_html += build_branch(bi, b, " side-left")
        right_html = ""
        for bi, b in enumerate(right_branches):
            right_html += build_branch(mid + bi, b, " side-right")
        mm_inner = (
            f'<div class="mm-side left" id="leftSide">{left_html}</div>'
            f'<div class="mm-center"><div class="mm-center-card" id="centerCard">{center}</div></div>'
            f'<div class="mm-side right" id="rightSide">{right_html}</div>'
        )
    else:
        all_branches = ""
        for bi, b in enumerate(branches):
            all_branches += build_branch(bi, b)
        mm_inner = (
            f'<div class="mm-center"><div class="mm-center-card" id="centerCard">{center}</div></div>'
            f'<div class="mm-branches" id="branchesWrap">{all_branches}</div>'
        )

    timeline_html = ""
    if timeline:
        tl_items = ""
        for t in timeline:
            tl_items += f'<div class="tl-item"><div class="tl-date">{t.get("date", "")}</div><div class="tl-event">{t.get("event", "")}</div></div>'
        timeline_html = f'<div class="timeline-section"><div class="section-title">{title_dec} 时间线 {title_dec}</div><div class="timeline-flow">{tl_items}</div></div>'

    kp_html = knowledge_panel_html(data, style)

    mm_direction = layout_cfg["direction"]
    mm_align = layout_cfg["align"]
    is_vertical = mm_direction in ("column", "column-reverse")

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>{center}</title>
<style>
{theme_css_vars(theme)}
{_build_mm_color_overrides(mm_colors)}
{shared_css()}
{decoration_css(style)}
{knowledge_panel_css()}
{base_page_css()}
* {{ box-sizing: border-box; }}
.divider-wrap {{ margin:12px auto; max-width:400px; }}

.mm-wrap {{ display:flex; flex-direction:{mm_direction}; align-items:{mm_align}; gap:0; margin-top:30px; width:100%; padding:0 10px; }}
.mm-center {{ flex:0 0 auto; display:flex; align-items:center; justify-content:center; position:relative; padding:0 30px; }}
.mm-center-card {{
    min-width:140px; max-width:200px; padding:18px 24px; display:flex; align-items:center; justify-content:center;
    background: linear-gradient(135deg, var(--primary, #222), var(--accent, #4a90d9));
    color:var(--bg, #fff); font-size:20px; font-weight:bold;
    letter-spacing:3px; border-radius:16px; text-align:center; cursor:grab; user-select:none;
    touch-action:none; position:relative; z-index:5;
    box-shadow:0 8px 32px rgba(0,0,0,0.18);
    animation: centerPulse 3s ease-in-out infinite;
}}
@keyframes centerPulse {{
    0%,100% {{ box-shadow:0 8px 32px rgba(0,0,0,0.18); transform:scale(1); }}
    50% {{ box-shadow:0 8px 48px rgba(0,0,0,0.28); transform:scale(1.03); }}
}}
.mm-branches {{ flex:1 1 auto; display:grid; gap:24px; align-content:start; padding:0 10px; }}
.mm-side {{ display:flex; flex-direction:column; gap:24px; padding:0 10px; flex:1; }}
.mm-side.left {{ align-items:flex-end; }}
.mm-side.right {{ align-items:flex-start; }}

.branch-group {{ display:flex; flex-direction:row; align-items:center; gap:10px; position:relative; transition:opacity 0.3s, transform 0.3s; }}
.side-left {{ flex-direction:row-reverse; align-items:center; }}
.side-left .branch-points {{ display:flex; flex-direction:column; align-items:flex-end; gap:5px; }}
.side-right {{ flex-direction:row; align-items:center; }}
.side-right .branch-points {{ display:flex; flex-direction:column; align-items:flex-start; gap:5px; }}

.mm-branches .branch-group.side-left {{ flex-direction:row-reverse; align-items:center; }}
.mm-branches .branch-group.side-left .branch-points {{ align-items:flex-end; }}
.mm-branches .branch-group.side-right {{ flex-direction:row; align-items:center; }}
.mm-branches .branch-group.side-right .branch-points {{ align-items:flex-start; }}

.branch-group.points-flipped .branch-points {{
    position:absolute; top:0; z-index:6;
}}
.branch-group.side-left.points-flipped .branch-points {{
    left:calc(100% + 20px);
}}
.branch-group.side-right.points-flipped .branch-points {{
    right:calc(100% + 20px);
}}
.branch-title-card {{
    display:inline-flex; max-width:180px; flex-shrink:0;
    font-size:13px; font-weight:bold; color:var(--primary, #222); letter-spacing:1px;
    padding:7px 14px; border:2px solid var(--primary, #222); border-radius:10px;
    background:var(--light-bg, #f5f5f5); cursor:grab; user-select:none; touch-action:none;
    position:relative; z-index:5; word-break:keep-all; overflow-wrap:normal;
    white-space:normal; line-height:1.4;
}}
.point-card {{
    display:block; max-width:200px;
    font-size:11px; color:var(--text, #333); line-height:1.4; padding:4px 9px;
    border:1.5px dashed var(--border, #888); border-radius:8px; background:var(--bg, #fff);
    cursor:grab; user-select:none; touch-action:none; position:relative; z-index:5;
    white-space:normal; word-break:keep-all;
}}
.dragging {{
    cursor:grabbing !important; box-shadow:0 16px 48px rgba(0,0,0,0.25);
    border-color:var(--accent, #4a90d9) !important; border-style:solid !important; z-index:100 !important;
}}

.conn-svg {{ position:absolute; top:0; left:0; width:100%; height:100%; pointer-events:none; z-index:3; overflow:visible; }}
.conn-path {{ fill:none; stroke-linecap:round; }}
.conn-main {{ stroke:var(--primary, #333); stroke-width:2.5; stroke-dasharray:8 5; opacity:0.6; }}
.conn-branch {{ stroke:var(--accent, #4a90d9); stroke-width:2; stroke-dasharray:8 4; opacity:0.65; }}
.conn-path {{ animation:flowDash 2s linear infinite; }}
@keyframes flowDash {{ to {{ stroke-dashoffset:-28; }} }}

.timeline-section {{ margin:16px 0 24px; }}
.section-title {{ text-align:center; font-size:14px; font-weight:bold; color:var(--primary, #333); letter-spacing:3px; margin-bottom:16px; }}
.timeline-flow {{ display:grid; grid-template-columns:1fr 1fr; gap:10px; }}
.tl-item {{ display:flex; align-items:baseline; gap:8px; padding:6px 10px; border-left:2px solid var(--accent, #888); }}
.tl-date {{ font-size:12px; font-weight:bold; color:var(--primary, #222); white-space:nowrap; }}
.tl-event {{ font-size:12px; color:var(--text, #444); line-height:1.4; }}

.zoom-viewport {{
    position:relative; overflow:hidden; width:100%; min-height:70vh;
    cursor:grab;
}}
.zoom-viewport.grabbing {{ cursor:grabbing; }}
.zoom-content {{
    position:relative; transform-origin:0 0; transition:transform 0.08s ease-out;
    will-change:transform;
}}
.zoom-controls {{
    position:fixed; top:16px; right:16px; z-index:200;
    display:flex; align-items:center; gap:4px;
    background:var(--card, #fff); border:1px solid var(--border, #ddd);
    border-radius:8px; padding:4px 8px;
    box-shadow:0 2px 12px rgba(0,0,0,0.1);
    font-family:"Microsoft YaHei UI",sans-serif;
}}
.zoom-controls button {{
    width:28px; height:28px; border:none; border-radius:6px;
    background:var(--light-bg, #f0f0f0); color:var(--text, #333);
    font-size:16px; font-weight:bold; cursor:pointer;
    display:flex; align-items:center; justify-content:center;
    transition:background 0.15s;
}}
.zoom-controls button:hover {{ background:var(--primary, #333); color:var(--bg, #fff); }}
.zoom-controls span {{
    font-size:12px; color:var(--muted, #888); min-width:40px; text-align:center;
    user-select:none;
}}

.ctx-menu {{
    display:none; position:fixed; z-index:999;
    background:var(--card, #fff); border:1px solid var(--border, #ddd);
    border-radius:10px; padding:6px 0; min-width:180px;
    box-shadow:0 8px 32px rgba(0,0,0,0.18);
    font-family:"Microsoft YaHei UI",sans-serif; font-size:13px;
}}
.ctx-menu.show {{ display:block; }}
.ctx-item {{
    display:flex; align-items:center; gap:8px;
    padding:8px 16px; cursor:pointer; color:var(--text, #333);
    transition:background 0.12s;
}}
.ctx-item:hover {{ background:var(--light-bg, #f0f0f0); }}
.ctx-item .icon {{ width:18px; text-align:center; font-size:14px; flex-shrink:0; }}
.ctx-sep {{ height:1px; background:var(--border, #e0e0e0); margin:4px 12px; }}
.ctx-sub {{ padding:4px 12px 4px 36px; display:flex; align-items:center; gap:6px; }}
.ctx-sub input[type="color"] {{
    width:22px; height:22px; border:1px solid var(--border, #ccc); border-radius:4px;
    padding:0; cursor:pointer; background:none;
}}
.ctx-item.danger {{ color:#d33; }}
.ctx-item.danger:hover {{ background:#fef0f0; }}

</style>
</head>
<body>
<div class="zoom-controls" id="zoomControls">
    <button id="zoomIn" title="放大">+</button>
    <span id="zoomLevel">100%</span>
    <button id="zoomOut" title="缩小">-</button>
    <button id="zoomReset" title="重置">&#x27F3;</button>
</div>
<div class="page" id="canvas">
    <div class="zoom-viewport" id="zoomViewport">
    <svg class="conn-svg" id="connSvg"></svg>
    <div class="top-bar">
        <div class="subject-label">{subject}</div>
        {student_html}
    </div>
    <div class="header">
        <h1>{title_dec} {center} {title_dec}</h1>
        <div class="subtitle">{subtitle}</div>
        <div class="divider-wrap">{divider}</div>
    </div>
    <div class="mm-wrap" id="mmWrap">
        {mm_inner}
    </div>
    {timeline_html}
    {kp_html}
    {footer}
    </div>
</div>
<div class="ctx-menu" id="ctxMenu">
    <div class="ctx-item" data-action="highlight"><span class="icon">&#9733;</span>高光</div>
    <div class="ctx-item" data-action="invert"><span class="icon">&#8644;</span>反转方向</div>
    <div class="ctx-sep"></div>
    <div class="ctx-item" data-action="edit"><span class="icon">&#9998;</span>编辑文字</div>
    <div class="ctx-item" data-action="addPoint"><span class="icon">+</span>添加要点</div>
    <div class="ctx-sep"></div>
    <div class="ctx-item" data-action="pickBg"><span class="icon">&#9632;</span>背景色
        <div class="ctx-sub"><input type="color" id="ctxBgColor" value="#ffffff"></div>
    </div>
    <div class="ctx-item" data-action="pickBorder"><span class="icon">&#9632;</span>边框色
        <div class="ctx-sub"><input type="color" id="ctxBorderColor" value="#222222"></div>
    </div>
    <div class="ctx-item" data-action="pickText"><span class="icon">&#9632;</span>文字色
        <div class="ctx-sub"><input type="color" id="ctxTextColor" value="#333333"></div>
    </div>
    <div class="ctx-sep"></div>
    <div class="ctx-item" data-action="reset"><span class="icon">&#8634;</span>恢复默认</div>
    <div class="ctx-item danger" data-action="deletePoint"><span class="icon">&#10005;</span>删除要点</div>
    <div class="ctx-item danger" data-action="delete"><span class="icon">&#10005;</span>删除分支</div>
</div>
<div class="ctx-menu" id="ctxCenter">
    <div class="ctx-item" data-action="edit"><span class="icon">&#9998;</span>编辑文字</div>
    <div class="ctx-item" data-action="highlight"><span class="icon">&#9733;</span>高光</div>
    <div class="ctx-sep"></div>
    <div class="ctx-item" data-action="expandAll"><span class="icon">&#9654;</span>展开所有分支</div>
    <div class="ctx-item" data-action="collapseAll"><span class="icon">&#9664;</span>折叠所有分支</div>
    <div class="ctx-sep"></div>
    <div class="ctx-item" data-action="pickBg"><span class="icon">&#9632;</span>背景色
        <div class="ctx-sub"><input type="color" id="ctxCenterBg" value="#ffffff"></div>
    </div>
    <div class="ctx-item" data-action="pickText"><span class="icon">&#9632;</span>文字色
        <div class="ctx-sub"><input type="color" id="ctxCenterText" value="#ffffff"></div>
    </div>
    <div class="ctx-sep"></div>
    <div class="ctx-item" data-action="resetAll"><span class="icon">&#8634;</span>恢复所有样式</div>
</div>
<script>
(function() {{
'use strict';

var canvas = document.getElementById('canvas');
var svg = document.getElementById('connSvg');
var centerCard = document.getElementById('centerCard');
var isSplit = { 'true' if is_split else 'false' };
var isVertical = { 'true' if is_vertical else 'false' };
var cards = Array.prototype.slice.call(document.querySelectorAll('.branch-title-card, .point-card, .mm-center-card'));
var mainConns = [];
var subConns = [];
var NS = 'http://www.w3.org/2000/svg';

// === ZOOM & PAN ===
var viewport = document.getElementById('zoomViewport');
var zoom = 1, panX = 0, panY = 0;
var isPanning = false, panSX = 0, panSY = 0, panOX = 0, panOY = 0;
var zoomLabel = document.getElementById('zoomLevel');
var MIN_ZOOM = 0.3, MAX_ZOOM = 3;

function wrapZoomContent() {{
    var wrapper = document.createElement('div');
    wrapper.className = 'zoom-content';
    wrapper.id = 'zoomContent';
    var children = Array.prototype.slice.call(viewport.childNodes);
    children.forEach(function(c) {{ wrapper.appendChild(c); }});
    viewport.appendChild(wrapper);
    return wrapper;
}}
var zc = document.getElementById('zoomContent') || wrapZoomContent();
function applyTransform() {{
    zc.style.transform = 'translate(' + panX + 'px,' + panY + 'px) scale(' + zoom + ')';
    zoomLabel.textContent = Math.round(zoom * 100) + '%';
}}

viewport.addEventListener('wheel', function(e) {{
    e.preventDefault();
    var rect = viewport.getBoundingClientRect();
    var mx = e.clientX - rect.left, my = e.clientY - rect.top;
    var delta = e.deltaY > 0 ? -0.08 : 0.08;
    var oldZoom = zoom;
    zoom = Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, zoom + delta * zoom));
    var ratio = zoom / oldZoom;
    panX = mx - ratio * (mx - panX);
    panY = my - ratio * (my - panY);
    applyTransform();
}}, {{ passive: false }});

viewport.addEventListener('mousedown', function(e) {{
    if (e.target.closest('.branch-title-card, .point-card, .mm-center-card')) return;
    isPanning = true; panSX = e.clientX; panSY = e.clientY; panOX = panX; panOY = panY;
    viewport.classList.add('grabbing');
}});
window.addEventListener('mousemove', function(e) {{
    if (!isPanning) return;
    panX = panOX + e.clientX - panSX;
    panY = panOY + e.clientY - panSY;
    applyTransform();
}});
window.addEventListener('mouseup', function() {{
    isPanning = false;
    viewport.classList.remove('grabbing');
}});

var lastTouchDist = 0, lastTouchMid = null;
viewport.addEventListener('touchstart', function(e) {{
    if (e.touches.length === 2) {{
        var dx = e.touches[0].clientX - e.touches[1].clientX;
        var dy = e.touches[0].clientY - e.touches[1].clientY;
        lastTouchDist = Math.sqrt(dx * dx + dy * dy);
        lastTouchMid = {{ x: (e.touches[0].clientX + e.touches[1].clientX) / 2, y: (e.touches[0].clientY + e.touches[1].clientY) / 2 }};
    }} else if (e.touches.length === 1 && !e.target.closest('.branch-title-card, .point-card, .mm-center-card')) {{
        isPanning = true; panSX = e.touches[0].clientX; panSY = e.touches[0].clientY;
        panOX = panX; panOY = panY;
    }}
}}, {{ passive: true }});
viewport.addEventListener('touchmove', function(e) {{
    if (e.touches.length === 2 && lastTouchDist) {{
        e.preventDefault();
        var dx = e.touches[0].clientX - e.touches[1].clientX;
        var dy = e.touches[0].clientY - e.touches[1].clientY;
        var dist = Math.sqrt(dx * dx + dy * dy);
        var rect = viewport.getBoundingClientRect();
        var mid = {{ x: (e.touches[0].clientX + e.touches[1].clientX) / 2 - rect.left, y: (e.touches[0].clientY + e.touches[1].clientY) / 2 - rect.top }};
        var ratio = dist / lastTouchDist;
        var oldZoom = zoom;
        zoom = Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, zoom * ratio));
        var r = zoom / oldZoom;
        panX = mid.x - r * (mid.x - panX);
        panY = mid.y - r * (mid.y - panY);
        panX += mid.x - lastTouchMid.x;
        panY += mid.y - lastTouchMid.y;
        lastTouchDist = dist;
        lastTouchMid = {{ x: mid.x + rect.left, y: mid.y + rect.top }};
        applyTransform();
    }} else if (e.touches.length === 1 && isPanning) {{
        e.preventDefault();
        panX = panOX + e.touches[0].clientX - panSX;
        panY = panOY + e.touches[0].clientY - panSY;
        applyTransform();
    }}
}}, {{ passive: false }});
viewport.addEventListener('touchend', function() {{ isPanning = false; lastTouchDist = 0; lastTouchMid = null; }});

document.getElementById('zoomIn').addEventListener('click', function() {{ zoom = Math.min(MAX_ZOOM, zoom + 0.15); applyTransform(); }});
document.getElementById('zoomOut').addEventListener('click', function() {{ zoom = Math.max(MIN_ZOOM, zoom - 0.15); applyTransform(); }});
document.getElementById('zoomReset').addEventListener('click', function() {{ zoom = 1; panX = 0; panY = 0; applyTransform(); }});

// Entrance animation
cards.forEach(function(c, i) {{
    c.style.opacity = '0';
    c.style.transform = 'translateY(18px) scale(0.95)';
    setTimeout(function() {{
        c.style.transition = 'opacity 0.5s cubic-bezier(.4,0,.2,1), transform 0.5s cubic-bezier(.4,0,.2,1)';
        c.style.opacity = '1';
        c.style.transform = 'translateY(0) scale(1)';
        setTimeout(function() {{ c.style.transition = ''; }}, 520);
    }}, 40 + i * 45);
}});

if (!isSplit) {{
    setTimeout(function() {{
        var cRect = centerCard.getBoundingClientRect();
        var cMidX = cRect.left + cRect.width / 2;
        document.querySelectorAll('.branch-group').forEach(function(g) {{
            var bt = g.querySelector('.branch-title-card');
            if (!bt) return;
            var bRect = bt.getBoundingClientRect();
            var bMidX = bRect.left + bRect.width / 2;
            g.classList.add(bMidX < cMidX ? 'side-left' : 'side-right');
        }});
    }}, 100);
}}

document.querySelectorAll('.branch-title-card').forEach(function(bt) {{
    var side = 'none';
    if (isSplit) {{ var p = bt.closest('.mm-side'); if (p) side = p.classList.contains('left') ? 'left' : 'right'; }}
    mainConns.push({{ from: centerCard, to: bt, side: side }});
}});
document.querySelectorAll('.branch-group').forEach(function(g) {{
    var title = g.querySelector('.branch-title-card');
    var side = 'none';
    if (isSplit) {{ var p = g.closest('.mm-side'); if (p) side = p.classList.contains('left') ? 'left' : 'right'; }}
    g.querySelectorAll('.point-card').forEach(function(pt) {{ subConns.push({{ from: title, to: pt, side: side }}); }});
}});

function makePath(cls) {{
    var p = document.createElementNS(NS, 'path');
    p.setAttribute('class', 'conn-path ' + cls);
    svg.appendChild(p);
    return p;
}}
var mainPaths = mainConns.map(function() {{ return makePath('conn-main'); }});
var subPaths = subConns.map(function() {{ return makePath('conn-branch'); }});

function relPos(el) {{
    var er = el.getBoundingClientRect();
    var cr = zc.getBoundingClientRect();
    return {{
        cx: (er.left - cr.left + er.width / 2) / zoom,
        top: (er.top - cr.top) / zoom,
        bottom: (er.bottom - cr.top) / zoom,
        cy: (er.top - cr.top + er.height / 2) / zoom,
        left: (er.left - cr.left) / zoom,
        right: (er.right - cr.left) / zoom,
        w: er.width / zoom, h: er.height / zoom
    }};
}}
function curve(x1, y1, x2, y2) {{
    var mx = (x1 + x2) / 2;
    return 'M' + x1 + ',' + y1 + ' C' + mx + ',' + y1 + ' ' + mx + ',' + y2 + ' ' + x2 + ',' + y2;
}}
function autoEdge(f, t) {{
    var dx = t.cx - f.cx, dy = t.cy - f.cy;
    if (Math.abs(dy) > Math.abs(dx) * 0.3)
        return [f.cx, dy > 0 ? f.bottom : f.top, t.cx, dy > 0 ? t.top : t.bottom];
    return [dx > 0 ? f.right : f.left, f.cy, dx > 0 ? t.left : t.right, t.cy];
}}

function drawAll() {{
    var i, c, f, t, e;
    for (i = 0; i < mainConns.length; i++) {{
        c = mainConns[i];
        if (!c.from || !c.from.parentNode || !c.to || !c.to.parentNode) continue;
        f = relPos(c.from); t = relPos(c.to);
        if (isSplit) {{
            mainPaths[i].setAttribute('d', f.cx < t.cx ? curve(f.right, f.cy, t.left, t.cy) : curve(f.left, f.cy, t.right, t.cy));
        }} else if (isVertical) {{
            e = autoEdge(f, t); mainPaths[i].setAttribute('d', curve(e[0], e[1], e[2], e[3]));
        }} else {{
            mainPaths[i].setAttribute('d', f.cx < t.cx ? curve(f.right, f.cy, t.left, t.cy) : curve(f.left, f.cy, t.right, t.cy));
        }}
    }}
    for (i = 0; i < subConns.length; i++) {{
        c = subConns[i];
        if (!c.from || !c.from.parentNode || !c.to || !c.to.parentNode) continue;
        f = relPos(c.from); t = relPos(c.to);
        if (isSplit) {{
            subPaths[i].setAttribute('d', f.cx < t.cx ? curve(f.right, f.cy, t.left, t.cy) : curve(f.left, f.cy, t.right, t.cy));
        }} else if (isVertical) {{
            e = autoEdge(f, t); subPaths[i].setAttribute('d', curve(e[0], e[1], e[2], e[3]));
        }} else {{
            subPaths[i].setAttribute('d', f.cx < t.cx ? curve(f.right, f.cy, t.left, t.cy) : curve(f.left, f.cy, t.right, t.cy));
        }}
    }}
}}
setTimeout(drawAll, 700);
window.addEventListener('resize', drawAll);

// === DRAG ===
var dragEl = null, dragChildren = [], dsx = 0, dsy = 0, dox = 0, doy = 0, raf = null;
function pt(el) {{
    var t = el.style.transform;
    if (!t) return {{ x:0, y:0 }};
    var m = t.match(/translate\\(\\s*([-\\d.]+)px[,\\s]+([-\\d.]+)px\\s*\\)/);
    return m ? {{ x:parseFloat(m[1]), y:parseFloat(m[2]) }} : {{ x:0, y:0 }};
}}
function onDown(e) {{
    var card = e.target.closest('.branch-title-card, .point-card, .mm-center-card');
    if (!card) return;
    e.preventDefault();
    var p = pt(card);
    dragEl = card; dsx = e.clientX; dsy = e.clientY; dox = p.x; doy = p.y;
    dragChildren = [];
    if (card.classList.contains('mm-center-card')) {{
        document.querySelectorAll('.branch-title-card').forEach(function(el) {{ dragChildren.push({{ el: el, off: pt(el) }}); }});
        document.querySelectorAll('.point-card').forEach(function(el) {{ dragChildren.push({{ el: el, off: pt(el) }}); }});
    }} else if (card.classList.contains('branch-title-card')) {{
        var bi = card.getAttribute('data-branch');
        document.querySelectorAll('.point-card[data-branch="' + bi + '"]').forEach(function(el) {{ dragChildren.push({{ el: el, off: pt(el) }}); }});
    }}
    card.classList.add('dragging');
    dragChildren.forEach(function(c) {{ c.el.classList.add('dragging'); }});
}}
function onMove(e) {{
    if (!dragEl) return;
    var dx = e.clientX - dsx, dy = e.clientY - dsy;
    dragEl.style.transform = 'translate(' + (dx + dox) + 'px, ' + (dy + doy) + 'px)';
    dragChildren.forEach(function(c) {{ c.el.style.transform = 'translate(' + (dx + c.off.x) + 'px, ' + (dy + c.off.y) + 'px)'; }});
    if (!raf) {{ raf = requestAnimationFrame(function() {{ drawAll(); raf = null; }}); }}
}}
function onUp() {{
    if (!dragEl) return;
    dragEl.classList.remove('dragging');
    dragChildren.forEach(function(c) {{ c.el.classList.remove('dragging'); }});
    dragEl = null; dragChildren = []; drawAll();
}}
canvas.addEventListener('mousedown', onDown);
window.addEventListener('mousemove', onMove);
window.addEventListener('mouseup', onUp);
canvas.addEventListener('touchstart', function(e) {{
    if (e.touches.length === 1) {{
        var t = e.touches[0], el = document.elementFromPoint(t.clientX, t.clientY);
        if (el) onDown({{ target:el, clientX:t.clientX, clientY:t.clientY, preventDefault:function(){{}} }});
    }}
}}, {{ passive:false }});
window.addEventListener('touchmove', function(e) {{
    if (dragEl && e.touches.length === 1) {{ e.preventDefault(); onMove({{ clientX:e.touches[0].clientX, clientY:e.touches[0].clientY }}); }}
}}, {{ passive:false }});
window.addEventListener('touchend', onUp);

// === CONTEXT MENU ===
var ctxMenu = document.getElementById('ctxMenu');
var ctxCenter = document.getElementById('ctxCenter');
var ctxTarget = null;
var highlightSet = {{}};

function hideAllCtx() {{ ctxMenu.classList.remove('show'); ctxCenter.classList.remove('show'); ctxTarget = null; }}
document.addEventListener('click', hideAllCtx);

document.addEventListener('contextmenu', function(e) {{
    var centerEl = e.target.closest('.mm-center-card');
    var branchEl = e.target.closest('.branch-title-card, .point-card');
    if (!centerEl && !branchEl) return;
    e.preventDefault();
    hideAllCtx();

    if (centerEl) {{
        ctxTarget = centerEl;
        ctxCenter.style.left = e.clientX + 'px';
        ctxCenter.style.top = e.clientY + 'px';
        ctxCenter.classList.add('show');
        var mr = ctxCenter.getBoundingClientRect();
        if (mr.right > window.innerWidth) ctxCenter.style.left = (e.clientX - mr.width) + 'px';
        if (mr.bottom > window.innerHeight) ctxCenter.style.top = (e.clientY - mr.height) + 'px';
    }} else {{
        ctxTarget = branchEl;
        ctxMenu.style.left = e.clientX + 'px';
        ctxMenu.style.top = e.clientY + 'px';
        ctxMenu.classList.add('show');
        var mr = ctxMenu.getBoundingClientRect();
        if (mr.right > window.innerWidth) ctxMenu.style.left = (e.clientX - mr.width) + 'px';
        if (mr.bottom > window.innerHeight) ctxMenu.style.top = (e.clientY - mr.height) + 'px';
    }}
}});

function rgbToHex(c) {{
    if (c.charAt(0) === '#') return c.length === 4 ? '#'+c[1]+c[1]+c[2]+c[2]+c[3]+c[3] : c;
    var m = c.match(/\\d+/g);
    if (!m || m.length < 3) return '#333333';
    return '#' + (+m[0]).toString(16).padStart(2,'0') + (+m[1]).toString(16).padStart(2,'0') + (+m[2]).toString(16).padStart(2,'0');
}}

// === BRANCH/POINT CONTEXT MENU ===
ctxMenu.addEventListener('click', function(e) {{
    e.stopPropagation();
    var item = e.target.closest('.ctx-item');
    if (!item || !ctxTarget) return;
    var action = item.getAttribute('data-action');
    var bi = ctxTarget.getAttribute('data-branch');
    var isTitle = ctxTarget.classList.contains('branch-title-card');
    var isPoint = ctxTarget.classList.contains('point-card');
    var group = ctxTarget.closest('.branch-group');

    if (action === 'highlight') {{
        var key = bi + (isTitle ? '_t' : '_p');
        if (highlightSet[key]) {{ ctxTarget.style.boxShadow = ''; ctxTarget.style.borderColor = ''; delete highlightSet[key]; }}
        else {{ ctxTarget.style.boxShadow = '0 0 18px 4px var(--accent, #4a90d9)'; ctxTarget.style.borderColor = 'var(--accent, #4a90d9)'; highlightSet[key] = true; }}
    }} else if (action === 'invert') {{
        if (!group) return;

        group.classList.toggle('points-flipped');
        setTimeout(drawAll, 50);
    }} else if (action === 'edit') {{
        var span = ctxTarget.querySelector('.card-text');
        if (span) {{
            span.contentEditable = 'true'; span.focus();
            window.getSelection().selectAllChildren(span);
            function finishEdit() {{ span.contentEditable = 'false'; span.removeEventListener('blur', finishEdit); span.removeEventListener('keydown', onKey); }}
            function onKey(ev) {{ if (ev.key === 'Enter') {{ ev.preventDefault(); span.blur(); }} if (ev.key === 'Escape') {{ span.blur(); }} }}
            span.addEventListener('blur', finishEdit);
            span.addEventListener('keydown', onKey);
        }}
    }} else if (action === 'addPoint') {{
        if (!group) return;

        var pts = group.querySelector('.branch-points');
        if (!pts) return;
        var newPt = document.createElement('div');
        newPt.className = 'point-card';
        newPt.setAttribute('data-branch', bi);
        newPt.setAttribute('data-idx', pts.children.length);
        var bSvg = pts.querySelector('.point-card .bullet');
        newPt.innerHTML = (bSvg ? bSvg.outerHTML : '') + '<span class="card-text">\\u65b0\\u8981\\u70b9</span>';
        pts.appendChild(newPt);
        cards.push(newPt);
        var span = newPt.querySelector('.card-text');
        if (span) {{
            span.contentEditable = 'true'; span.focus();
            window.getSelection().selectAllChildren(span);
            function finPt() {{ span.contentEditable = 'false'; span.removeEventListener('blur', finPt); }}
            span.addEventListener('blur', finPt);
        }}
        rebuildConns(); setTimeout(drawAll, 50);
    }} else if (action === 'pickBg') {{
        ctxTarget.style.background = document.getElementById('ctxBgColor').value;
    }} else if (action === 'pickBorder') {{
        ctxTarget.style.borderColor = document.getElementById('ctxBorderColor').value;
    }} else if (action === 'pickText') {{
        ctxTarget.style.color = document.getElementById('ctxTextColor').value;
    }} else if (action === 'reset') {{

        ctxTarget.style.cssText = '';
        delete highlightSet[bi + (isTitle ? '_t' : '_p')];
        if (group) group.querySelectorAll('.point-card').forEach(function(p) {{ p.style.cssText = ''; }});
    }} else if (action === 'deletePoint') {{
        if (!isPoint || !group) return;

        ctxTarget.remove();
        var ptCards = group.querySelectorAll('.point-card');
        for (var i = 0; i < ptCards.length; i++) ptCards[i].setAttribute('data-idx', i);
        rebuildConns(); setTimeout(drawAll, 50);
    }} else if (action === 'delete') {{
        if (!group) return;

        var delBi = group.getAttribute('data-branch');
        group.remove();
        mainConns = mainConns.filter(function(c) {{ return c.to && c.to.getAttribute('data-branch') !== delBi; }});
        subConns = subConns.filter(function(c) {{
            var fb = c.from ? c.from.closest('.branch-group') : null;
            var tb = c.to ? c.to.closest('.branch-group') : null;
            return (!fb || fb.getAttribute('data-branch') !== delBi) && (!tb || tb.getAttribute('data-branch') !== delBi);
        }});
        rebuildConns(); setTimeout(drawAll, 50);
    }}
    hideAllCtx();
}});

// === CENTER CARD CONTEXT MENU ===
ctxCenter.addEventListener('click', function(e) {{
    e.stopPropagation();
    var item = e.target.closest('.ctx-item');
    if (!item || !ctxTarget) return;
    var action = item.getAttribute('data-action');

    if (action === 'edit') {{
        var span = ctxTarget;
        span.contentEditable = 'true'; span.focus();
        window.getSelection().selectAllChildren(span);
        function finishEdit() {{ span.contentEditable = 'false'; span.removeEventListener('blur', finishEdit); span.removeEventListener('keydown', onKey); }}
        function onKey(ev) {{ if (ev.key === 'Enter') {{ ev.preventDefault(); span.blur(); }} if (ev.key === 'Escape') {{ span.blur(); }} }}
        span.addEventListener('blur', finishEdit);
        span.addEventListener('keydown', onKey);
    }} else if (action === 'highlight') {{
        if (highlightSet['_center']) {{ ctxTarget.style.boxShadow = ''; delete highlightSet['_center']; }}
        else {{ ctxTarget.style.boxShadow = '0 0 24px 6px var(--accent, #4a90d9)'; highlightSet['_center'] = true; }}
    }} else if (action === 'expandAll') {{

        document.querySelectorAll('.branch-group').forEach(function(g) {{ g.style.opacity = '1'; g.style.transform = ''; }});
        setTimeout(drawAll, 50);
    }} else if (action === 'collapseAll') {{

        document.querySelectorAll('.branch-group').forEach(function(g) {{ g.style.opacity = '0.3'; g.style.transform = 'scale(0.85)'; }});
        setTimeout(drawAll, 50);
    }} else if (action === 'pickBg') {{
        ctxTarget.style.background = document.getElementById('ctxCenterBg').value;
    }} else if (action === 'pickText') {{
        ctxTarget.style.color = document.getElementById('ctxCenterText').value;
    }} else if (action === 'resetAll') {{

        ctxTarget.style.cssText = '';
        delete highlightSet['_center'];
        document.querySelectorAll('.branch-title-card, .point-card').forEach(function(c) {{ c.style.cssText = ''; }});
    }}
    hideAllCtx();
}});

// === REBUILD CONNECTIONS ===
function rebuildConns() {{
    mainConns = []; subConns = [];
    centerCard = document.getElementById('centerCard');
    document.querySelectorAll('.branch-title-card').forEach(function(bt) {{
        var side = 'none';
        if (isSplit) {{ var g = bt.closest('.branch-group'); if (g) side = g.classList.contains('side-left') ? 'left' : 'right'; }}
        mainConns.push({{ from: centerCard, to: bt, side: side }});
    }});
    document.querySelectorAll('.branch-group').forEach(function(g) {{
        var title = g.querySelector('.branch-title-card');
        var side = 'none';
        if (isSplit) {{ side = g.classList.contains('side-left') ? 'left' : 'right'; }}
        g.querySelectorAll('.point-card').forEach(function(pt) {{ subConns.push({{ from: title, to: pt, side: side }}); }});
    }});
    while (svg.firstChild) svg.removeChild(svg.firstChild);
    mainPaths = mainConns.map(function() {{ return makePath('conn-main'); }});
    subPaths = subConns.map(function() {{ return makePath('conn-branch'); }});
    setTimeout(drawAll, 50);
}}

ctxMenu.querySelectorAll('input[type="color"]').forEach(function(inp) {{
    inp.addEventListener('click', function(e) {{ e.stopPropagation(); }});
    inp.addEventListener('input', function(e) {{
        e.stopPropagation();
        var action = inp.closest('.ctx-item').getAttribute('data-action');
        if (!ctxTarget) return;
        if (action === 'pickBg') ctxTarget.style.background = inp.value;
        else if (action === 'pickBorder') ctxTarget.style.borderColor = inp.value;
        else if (action === 'pickText') ctxTarget.style.color = inp.value;
    }});
}});
ctxCenter.querySelectorAll('input[type="color"]').forEach(function(inp) {{
    inp.addEventListener('click', function(e) {{ e.stopPropagation(); }});
    inp.addEventListener('input', function(e) {{
        e.stopPropagation();
        var action = inp.closest('.ctx-item').getAttribute('data-action');
        if (!ctxTarget) return;
        if (action === 'pickBg') ctxTarget.style.background = inp.value;
        else if (action === 'pickText') ctxTarget.style.color = inp.value;
    }});
}});

}})();
</script>
</body>
</html>"""
    return html
