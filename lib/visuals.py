"""Universal visualization renderer — takes structured vis data from LLM and renders ANY diagram."""
import json
import streamlit as st
from .schemas import Visualization


def render_interactive_visual(vis: Visualization | None, title: str = "", points: list[str] | None = None, visual_cue: str = ""):
    """Render any visualization. If vis is provided, use universal renderer. Otherwise fallback to points list."""

    if vis and vis.nodes:
        _render_universal(vis)
    elif points:
        _render_points_fallback(title, points, visual_cue)


def _render_universal(vis: Visualization):
    vis_data = {
        "vis_type": vis.vis_type,
        "title": vis.title,
        "layout": vis.layout,
        "nodes": [n.model_dump() for n in vis.nodes],
        "connections": [{"from_id": c.from_id, "to_id": c.to_id, "label": c.label, "animated": c.animated} for c in vis.connections],
    }

    html = f"""<!DOCTYPE html>
<html><head><style>
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{font-family:'Inter',system-ui,sans-serif;background:#0a0a1a;color:rgba(255,255,255,0.85);overflow-x:hidden;}}
.container{{padding:12px;}}
.title{{font-size:18px;font-weight:800;text-align:center;margin-bottom:4px;
  background:linear-gradient(135deg,#00d4aa,#7c3aed);-webkit-background-clip:text;-webkit-text-fill-color:transparent;}}
.vis-type{{text-align:center;font-size:10px;color:rgba(255,255,255,0.3);text-transform:uppercase;letter-spacing:2px;margin-bottom:12px;}}

/* Tabs */
.tabs{{display:flex;gap:6px;margin-bottom:16px;justify-content:center;}}
.tab{{padding:6px 18px;border-radius:20px;font-size:11px;font-weight:600;cursor:pointer;
  border:1px solid rgba(255,255,255,0.08);background:rgba(255,255,255,0.03);
  color:rgba(255,255,255,0.4);transition:all 0.3s;}}
.tab:hover{{border-color:rgba(255,255,255,0.2);color:rgba(255,255,255,0.7);}}
.tab.active{{background:rgba(0,212,170,0.15);border-color:rgba(0,212,170,0.4);color:#00d4aa;}}

/* Panels */
.panel{{display:none;}}.panel.active{{display:block;}}

/* Canvas area */
.canvas{{position:relative;width:100%;min-height:280px;background:rgba(255,255,255,0.02);
  border:1px solid rgba(255,255,255,0.06);border-radius:12px;overflow:hidden;}}

/* SVG connections */
.canvas svg{{position:absolute;top:0;left:0;width:100%;height:100%;pointer-events:none;}}

/* Nodes */
.node{{position:absolute;padding:10px 14px;border-radius:12px;cursor:pointer;
  transition:all 0.4s cubic-bezier(0.4,0,0.2,1);border:2px solid transparent;
  backdrop-filter:blur(8px);min-width:100px;text-align:center;z-index:2;}}
.node:hover{{transform:scale(1.08);z-index:10;box-shadow:0 8px 32px rgba(0,0,0,0.4);}}
.node.active{{transform:scale(1.1);z-index:10;box-shadow:0 8px 32px rgba(0,0,0,0.4);}}
.node-label{{font-size:12px;font-weight:700;margin-bottom:2px;}}
.node-icon{{font-size:16px;margin-bottom:4px;}}

/* Steps */
.steps{{display:flex;gap:6px;flex-wrap:wrap;justify-content:center;margin-top:12px;}}
.step{{padding:6px 14px;border-radius:20px;font-size:11px;font-weight:600;cursor:pointer;
  border:1px solid rgba(255,255,255,0.08);background:rgba(255,255,255,0.03);
  color:rgba(255,255,255,0.4);transition:all 0.3s;}}
.step:hover{{border-color:rgba(255,255,255,0.25);}}
.step.active{{color:white;transform:scale(1.05);box-shadow:0 4px 16px rgba(0,0,0,0.3);}}

/* Detail */
.detail{{margin-top:12px;padding:14px 18px;border-radius:12px;font-size:13px;
  line-height:1.7;color:rgba(255,255,255,0.75);transition:all 0.4s;
  border:1px solid rgba(255,255,255,0.06);background:rgba(255,255,255,0.02);min-height:60px;}}
.detail-dot{{width:8px;height:8px;border-radius:50%;display:inline-block;
  margin-right:10px;vertical-align:middle;animation:pulse 1.5s infinite;}}
@keyframes pulse{{0%,100%{{opacity:1;}}50%{{opacity:0.4;}}}}

/* Progress */
.progress-bar{{width:100%;height:3px;background:rgba(255,255,255,0.06);border-radius:2px;margin-top:8px;overflow:hidden;}}
.progress-fill{{height:100%;background:linear-gradient(90deg,#00d4aa,#7c3aed);border-radius:2px;transition:width 0.3s;}}

/* Controls */
.controls{{display:flex;gap:8px;justify-content:center;margin-top:12px;}}
.ctrl-btn{{padding:6px 16px;border-radius:10px;font-size:11px;font-weight:600;cursor:pointer;
  border:1px solid rgba(255,255,255,0.1);background:rgba(255,255,255,0.04);
  color:rgba(255,255,255,0.5);transition:all 0.2s;}}
.ctrl-btn:hover{{background:rgba(255,255,255,0.08);color:rgba(255,255,255,0.8);}}
.ctrl-btn.playing{{background:rgba(0,212,170,0.15);border-color:rgba(0,212,170,0.3);color:#00d4aa;}}

/* Points list */
.points-list{{display:flex;flex-direction:column;gap:6px;}}
.point-item{{background:rgba(255,255,255,0.03);border-radius:10px;padding:12px 16px;
  font-size:13px;color:rgba(255,255,255,0.6);line-height:1.5;cursor:pointer;
  transition:all 0.3s;border:1px solid rgba(255,255,255,0.06);}}
.point-item:hover{{background:rgba(255,255,255,0.06);}}
</style></head><body>
<div class="container">
  <div class="title">{json.dumps(vis.title)}</div>
  <div class="vis-type">{json.dumps(vis.vis_type)} diagram</div>

  <div class="tabs">
    <div class="tab active" onclick="showTab(0)">Interactive Diagram</div>
    <div class="tab" onclick="showTab(1)">All Details</div>
  </div>

  <div class="panel active" id="tab0">
    <div class="canvas" id="canvas"></div>
    <div class="steps" id="steps"></div>
    <div class="progress-bar"><div class="progress-fill" id="progress"></div></div>
    <div class="detail" id="detail">Click a node to learn more</div>
    <div class="controls">
      <div class="ctrl-btn" id="playBtn" onclick="autoPlay()">Auto Play</div>
      <div class="ctrl-btn" onclick="prevStep()">Prev</div>
      <div class="ctrl-btn" onclick="nextStep()">Next</div>
    </div>
  </div>

  <div class="panel" id="tab1">
    <div class="points-list" id="pointsList"></div>
  </div>
</div>

<script>
const vis = {json.dumps(vis_data)};
const nodes = vis.nodes;
const connections = vis.connections;
const layout = vis.layout;
let active = 0, autoInterval = null;

function setStep(i){{ active = i; render(); }}
function nextStep(){{ active = (active + 1) % nodes.length; render(); }}
function prevStep(){{ active = (active - 1 + nodes.length) % nodes.length; render(); }}

function autoPlay(){{
  const btn = document.getElementById('playBtn');
  if(autoInterval){{ clearInterval(autoInterval); autoInterval = null; btn.classList.remove('playing'); btn.textContent = 'Auto Play'; return; }}
  btn.classList.add('playing'); btn.textContent = 'Pause';
  autoInterval = setInterval(() => {{ active = (active + 1) % nodes.length; render(); }}, 3000);
}}

function showTab(i){{
  document.querySelectorAll('.tab').forEach((t,j) => t.classList.toggle('active', j===i));
  document.querySelectorAll('.panel').forEach((p,j) => p.classList.toggle('active', j===i));
}}

function positionNodes(){{
  const canvas = document.getElementById('canvas');
  const W = canvas.offsetWidth;
  const H = Math.max(280, 120);
  canvas.style.minHeight = H + 'px';
  canvas.innerHTML = '';

  const n = nodes.length;
  const positions = [];

  if(layout === 'horizontal') {{
    const gap = W / (n + 1);
    nodes.forEach((nd, i) => {{
      positions.push({{ x: gap * (i + 1) - 50, y: H / 2 - 30 }});
    }});
  }} else if(layout === 'vertical') {{
    const gap = H / (n + 1);
    nodes.forEach((nd, i) => {{
      positions.push({{ x: W / 2 - 50, y: gap * (i + 1) - 30 }});
    }});
  }} else if(layout === 'circular') {{
    const cx = W / 2, cy = H / 2, r = Math.min(W, H) / 2 - 50;
    nodes.forEach((nd, i) => {{
      const angle = (2 * Math.PI * i / n) - Math.PI / 2;
      positions.push({{ x: cx + r * Math.cos(angle) - 50, y: cy + r * Math.sin(angle) - 30 }});
    }});
  }} else if(layout === 'grid') {{
    const cols = Math.ceil(Math.sqrt(n));
    const cellW = W / cols;
    const cellH = H / Math.ceil(n / cols);
    nodes.forEach((nd, i) => {{
      const col = i % cols;
      const row = Math.floor(i / cols);
      positions.push({{ x: cellW * col + cellW / 2 - 50, y: cellH * row + cellH / 2 - 30 }});
    }});
  }} else {{
    const gap = W / (n + 1);
    nodes.forEach((nd, i) => {{
      positions.push({{ x: gap * (i + 1) - 50, y: H / 2 - 30 + (i % 2 === 0 ? -20 : 20) }});
    }});
  }}

  // Draw SVG connections
  let svg = '<svg viewBox="0 0 ' + W + ' ' + H + '" xmlns="http://www.w3.org/2000/svg">';
  svg += '<defs><marker id="arrow" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><polygon points="0 0, 8 3, 0 6" fill="rgba(255,255,255,0.3)"/></marker></defs>';

  connections.forEach(conn => {{
    const fromIdx = nodes.findIndex(n => n.id === conn.from_id);
    const toIdx = nodes.findIndex(n => n.id === conn.to_id);
    if(fromIdx === -1 || toIdx === -1) return;
    const from = positions[fromIdx];
    const to = positions[toIdx];
    const x1 = from.x + 50, y1 = from.y + 30;
    const x2 = to.x + 50, y2 = to.y + 30;
    const mx = (x1 + x2) / 2, my = (y1 + y2) / 2 - 20;

    const isActive = fromIdx === active || toIdx === active;
    const color = isActive ? 'rgba(0,212,170,0.5)' : 'rgba(255,255,255,0.12)';
    const width = isActive ? 2 : 1.5;

    svg += `<path d="M${{x1}} ${{y1}} Q${{mx}} ${{my}} ${{x2}} ${{y2}}" fill="none" stroke="${{color}}" stroke-width="${{width}}" marker-end="url(#arrow)" ${{conn.animated ? 'stroke-dasharray="6 4"' : ''}}>`;
    if(conn.animated && isActive) {{
      svg += `<animate attributeName="stroke-dashoffset" dur="1.5s" repeatCount="indefinite" values="0;20"/>`;
    }}
    svg += '</path>';

    if(conn.label) {{
      svg += `<text x="${{mx}}" y="${{my - 6}}" text-anchor="middle" fill="rgba(255,255,255,0.3)" font-size="9">${{conn.label}}</text>`;
    }}
  }});
  svg += '</svg>';
  canvas.innerHTML = svg;

  // Draw nodes
  nodes.forEach((nd, i) => {{
    const pos = positions[i];
    const isActive = i === active;
    const div = document.createElement('div');
    div.className = 'node' + (isActive ? ' active' : '');
    div.style.left = pos.x + 'px';
    div.style.top = pos.y + 'px';
    div.style.background = nd.color + (isActive ? '30' : '15');
    div.style.borderColor = isActive ? nd.color : nd.color + '40';
    div.onclick = () => setStep(i);

    let html = '';
    if(nd.icon) html += `<div class="node-icon">${{nd.icon}}</div>`;
    html += `<div class="node-label" style="color:${{nd.color}}">${{nd.label}}</div>`;
    div.innerHTML = html;
    canvas.appendChild(div);
  }});

  return positions;
}}

function render(){{
  const positions = positionNodes();
  const nd = nodes[active];

  // Steps
  document.getElementById('steps').innerHTML = nodes.map((n, i) =>
    `<div class="step ${{i===active?'active':''}}" onclick="setStep(${{i}})" style="${{i===active?'background:'+n.color+'25;border-color:'+n.color+'60;'+`color:${{n.color}}`:'color:rgba(255,255,255,0.4)'}}">${{n.label}}</div>`
  ).join('');

  // Detail
  document.getElementById('detail').innerHTML =
    `<span class="detail-dot" style="background:${{nd.color}}"></span>${{nd.detail}}`;
  document.getElementById('detail').style.background = nd.color + '08';
  document.getElementById('detail').style.borderColor = nd.color + '25';

  // Progress
  document.getElementById('progress').style.width = ((active + 1) / nodes.length * 100) + '%';

  // Points list
  document.getElementById('pointsList').innerHTML = nodes.map((n, i) =>
    `<div class="point-item" style="border-left:3px solid ${{n.color}};cursor:pointer;" onclick="showTab(0);setStep(${{i}})">
      <b style="color:${{n.color}}">${{n.icon || (i+1)}} ${{n.label}}</b><br>
      <span style="color:rgba(255,255,255,0.5);font-size:12px;">${{n.detail}}</span>
    </div>`
  ).join('');
}}

// Handle resize
window.addEventListener('resize', () => positionNodes());
render();
</script>
</body></html>"""

    st.components.v1.html(html, height=480, scrolling=False)


def _render_points_fallback(title: str, points: list[str], cue: str):
    """Fallback when no visualization data — render points as clickable cards."""
    colors = ["#00d4aa", "#7c3aed", "#FBBF24", "#60A5FA", "#F97316", "#EF4444"]
    steps_data = [{"label": f"Point {i+1}", "detail": pt, "color": colors[i % len(colors)]} for i, pt in enumerate(points[:6])]

    html = f"""<!DOCTYPE html>
<html><head><style>
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{font-family:'Inter',system-ui,sans-serif;background:#0a0a1a;color:rgba(255,255,255,0.85);overflow-x:hidden;}}
.container{{padding:12px;}}
.title{{font-size:18px;font-weight:800;text-align:center;margin-bottom:12px;
  background:linear-gradient(135deg,#00d4aa,#7c3aed);-webkit-background-clip:text;-webkit-text-fill-color:transparent;}}
.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:8px;margin-bottom:12px;}}
.card{{padding:12px;border-radius:12px;cursor:pointer;transition:all 0.3s;border:1px solid rgba(255,255,255,0.06);
  background:rgba(255,255,255,0.03);text-align:center;}}
.card:hover{{transform:translateY(-2px);box-shadow:0 8px 24px rgba(0,0,0,0.3);}}
.card.active{{transform:scale(1.05);box-shadow:0 8px 32px rgba(0,0,0,0.4);}}
.card-num{{width:32px;height:32px;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;
  font-size:14px;font-weight:700;margin-bottom:6px;}}
.card-label{{font-size:12px;font-weight:600;color:rgba(255,255,255,0.8);}}
.detail{{margin-top:12px;padding:14px 18px;border-radius:12px;font-size:13px;line-height:1.7;
  color:rgba(255,255,255,0.75);transition:all 0.4s;border:1px solid rgba(255,255,255,0.06);background:rgba(255,255,255,0.02);}}
.detail-dot{{width:8px;height:8px;border-radius:50%;display:inline-block;margin-right:10px;vertical-align:middle;animation:pulse 1.5s infinite;}}
@keyframes pulse{{0%,100%{{opacity:1;}}50%{{opacity:0.4;}}}}
.progress-bar{{width:100%;height:3px;background:rgba(255,255,255,0.06);border-radius:2px;margin-top:8px;overflow:hidden;}}
.progress-fill{{height:100%;background:linear-gradient(90deg,#00d4aa,#7c3aed);border-radius:2px;transition:width 0.3s;}}
.controls{{display:flex;gap:8px;justify-content:center;margin-top:12px;}}
.ctrl-btn{{padding:6px 16px;border-radius:10px;font-size:11px;font-weight:600;cursor:pointer;
  border:1px solid rgba(255,255,255,0.1);background:rgba(255,255,255,0.04);color:rgba(255,255,255,0.5);transition:all 0.2s;}}
.ctrl-btn:hover{{background:rgba(255,255,255,0.08);}}
.ctrl-btn.playing{{background:rgba(0,212,170,0.15);border-color:rgba(0,212,170,0.3);color:#00d4aa;}}
</style></head><body>
<div class="container">
  <div class="title">{title}</div>
  <div class="cards" id="cards"></div>
  <div class="progress-bar"><div class="progress-fill" id="progress"></div></div>
  <div class="detail" id="detail">Click a card to learn more</div>
  <div class="controls">
    <div class="ctrl-btn" id="playBtn" onclick="autoPlay()">Auto Play</div>
    <div class="ctrl-btn" onclick="prevStep()">Prev</div>
    <div class="ctrl-btn" onclick="nextStep()">Next</div>
  </div>
</div>
<script>
const steps = {json.dumps(steps_data)};
let active = 0, autoInterval = null;
function setStep(i){{ active = i; render(); }}
function nextStep(){{ active = (active + 1) % steps.length; render(); }}
function prevStep(){{ active = (active - 1 + steps.length) % steps.length; render(); }}
function autoPlay(){{
  const btn = document.getElementById('playBtn');
  if(autoInterval){{ clearInterval(autoInterval); autoInterval = null; btn.classList.remove('playing'); btn.textContent = 'Auto Play'; return; }}
  btn.classList.add('playing'); btn.textContent = 'Pause';
  autoInterval = setInterval(() => {{ active = (active + 1) % steps.length; render(); }}, 3000);
}}
function render(){{
  document.getElementById('cards').innerHTML = steps.map((s, i) =>
    `<div class="card ${{i===active?'active':''}}" onclick="setStep(${{i}})" style="${{i===active?'border-color:'+s.color:'border-color:rgba(255,255,255,0.06)'}}">
      <div class="card-num" style="background:${{s.color}}20;color:${{s.color}};">${{i+1}}</div>
      <div class="card-label">${{s.label}}</div>
    </div>`
  ).join('');
  const s = steps[active];
  document.getElementById('detail').innerHTML = `<span class="detail-dot" style="background:${{s.color}}"></span>${{s.detail}}`;
  document.getElementById('detail').style.background = s.color + '08';
  document.getElementById('detail').style.borderColor = s.color + '25';
  document.getElementById('progress').style.width = ((active + 1) / steps.length * 100) + '%';
}}
render();
</script>
</body></html>"""

    st.components.v1.html(html, height=380, scrolling=False)
