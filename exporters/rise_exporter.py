"""
Rise HTML Exporter
Converts a scenario JSON dict to a self-contained embeddable HTML file
compatible with Articulate Rise 360 as an embed/web-object block.
"""

import html as html_lib
from datetime import datetime


def _esc(s: str) -> str:
    return html_lib.escape(str(s), quote=True)


def export(scenario: dict, domain: str = "", agent_label: str = "Domain-Adapted") -> str:
    """
    Returns a self-contained HTML string.
    """
    title = _esc(scenario.get("title", "Branching Scenario"))
    context = _esc(scenario.get("context", ""))
    scenes = scenario.get("scenes", [])
    tags = scenario.get("tags", [])

    tags_html = "".join(
        f'<span class="tag">{_esc(t)}</span>' for t in tags
    )

    scenes_js = []
    for i, scene in enumerate(scenes):
        situation = _esc(scene.get("situation", ""))
        choices_js = []
        for c in scene.get("choices", []):
            choices_js.append({
                "key": _esc(c.get("key", "")),
                "text": _esc(c.get("text", "")),
                "correct": bool(c.get("correct", False)),
                "feedback": _esc(c.get("feedback", "")),
            })
        scenes_js.append({
            "index": i,
            "situation": situation,
            "choices": choices_js,
        })

    import json
    scenes_json = json.dumps(scenes_js)

    generated = datetime.now().strftime("%Y-%m-%d %H:%M")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
  /*
    Palette — Mocha Mousse (Pantone 17-1230, CoY 2025)
    --mocha:   #A47864  accent / buttons / labels
    --mocha-d: #7A5548  hover / borders
    --mocha-l: #C4A494  secondary accents
    --cream:   #FAF7F4  page background
    --parchment: #F0EAE4 card surfaces
    --linen:   #E4D9D0  borders
    --espresso:#2C1A14  primary text
    --warm-mid:#7A6258  secondary text
    --warm-dim:#B8A89E  muted / meta
    --sage:    #6B8F71  correct
    --terracotta: #C0533A wrong
  */
  *, *::before, *::after {{ box-sizing: border-box; }}
  body {{
    margin: 0; padding: 0;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: #FAF7F4;
    color: #2C1A14;
    min-height: 100vh;
  }}
  .shell {{
    max-width: 780px;
    margin: 0 auto;
    padding: 32px 24px 64px;
  }}
  .badge {{
    display: inline-flex; align-items: center; gap: 6px;
    background: #F0EAE4; border: 1px solid #E4D9D0;
    border-radius: 6px; padding: 4px 10px;
    font-size: 11px; color: #7A6258; margin-bottom: 20px;
    font-family: 'SF Mono', 'Fira Code', monospace;
  }}
  .badge-dot {{ width: 7px; height: 7px; border-radius: 50%; background: #A47864; }}
  h1 {{
    font-size: 1.5rem; font-weight: 700; margin: 0 0 10px;
    color: #2C1A14; line-height: 1.3;
  }}
  .context {{
    font-size: 0.95rem; color: #7A6258; line-height: 1.7;
    margin-bottom: 16px;
    padding: 16px; background: #F0EAE4; border-radius: 10px;
    border-left: 3px solid #A47864;
  }}
  .tags {{ display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 28px; }}
  .tag {{
    background: #F0EAE4; border: 1px solid #E4D9D0;
    border-radius: 99px; padding: 3px 12px;
    font-size: 11px; color: #A47864; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.05em;
  }}
  .progress-bar {{
    height: 4px; background: #E4D9D0; border-radius: 2px;
    margin-bottom: 28px; overflow: hidden;
  }}
  .progress-fill {{
    height: 100%; background: linear-gradient(90deg, #A47864, #C4A494);
    border-radius: 2px; transition: width 0.5s ease;
  }}
  .scene-label {{
    font-size: 11px; font-weight: 700; letter-spacing: 0.1em;
    color: #A47864; text-transform: uppercase; margin-bottom: 10px;
    font-family: 'SF Mono', 'Fira Code', monospace;
  }}
  .situation {{
    font-size: 1.05rem; line-height: 1.75; color: #2C1A14;
    margin-bottom: 24px;
  }}
  .choices {{ display: flex; flex-direction: column; gap: 10px; }}
  .choice {{
    display: flex; align-items: flex-start; gap: 14px;
    background: #F0EAE4; border: 1.5px solid #E4D9D0;
    border-radius: 12px; padding: 16px;
    cursor: pointer; transition: all 0.18s ease;
    text-align: left; width: 100%; color: #2C1A14;
    font-size: 0.95rem; line-height: 1.55;
  }}
  .choice:hover:not(:disabled) {{
    border-color: #A47864; background: #EDE0D4;
  }}
  .choice:disabled {{ cursor: default; }}
  .choice.correct {{ border-color: #6B8F71; background: #EBF3EC; }}
  .choice.wrong {{ border-color: #C0533A; background: #FAEAE6; }}
  .choice-key {{
    width: 28px; height: 28px; min-width: 28px; border-radius: 8px;
    background: #E4D9D0; display: flex; align-items: center; justify-content: center;
    font-size: 12px; font-weight: 700; color: #7A6258;
    font-family: 'SF Mono', 'Fira Code', monospace;
    transition: background 0.18s;
  }}
  .choice.correct .choice-key {{ background: #6B8F71; color: #fff; }}
  .choice.wrong .choice-key {{ background: #C0533A; color: #fff; }}
  .feedback-box {{
    margin-top: 16px; padding: 14px 16px;
    border-radius: 10px; font-size: 0.9rem; line-height: 1.65;
    display: none;
  }}
  .feedback-box.show {{ display: block; }}
  .feedback-box.correct {{ background: #EBF3EC; border: 1px solid #6B8F71; color: #2D5A35; }}
  .feedback-box.wrong {{ background: #FAEAE6; border: 1px solid #C0533A; color: #7A2A14; }}
  .next-btn {{
    margin-top: 24px; padding: 12px 28px;
    background: #A47864;
    color: #fff; border: none; border-radius: 10px;
    font-size: 0.95rem; font-weight: 600; cursor: pointer;
    display: none; transition: background 0.18s;
  }}
  .next-btn:hover {{ background: #7A5548; }}
  .next-btn.show {{ display: inline-flex; align-items: center; gap: 8px; }}
  .summary {{
    text-align: center; padding: 40px 0;
  }}
  .summary h2 {{ font-size: 1.8rem; margin-bottom: 8px; color: #2C1A14; }}
  .score-ring {{
    width: 120px; height: 120px; border-radius: 50%;
    border: 6px solid #A47864;
    display: flex; align-items: center; justify-content: center;
    margin: 20px auto;
    font-size: 2rem; font-weight: 800; color: #2C1A14;
  }}
  .score-label {{ color: #7A6258; font-size: 0.9rem; margin-top: 4px; }}
  .restart-btn {{
    margin-top: 24px; padding: 12px 32px;
    background: #F0EAE4; border: 1.5px solid #E4D9D0;
    color: #2C1A14; border-radius: 10px;
    font-size: 0.95rem; font-weight: 600; cursor: pointer;
  }}
  .restart-btn:hover {{ border-color: #A47864; }}
  .meta {{
    font-size: 10px; color: #B8A89E; text-align: center;
    margin-top: 40px; font-family: 'SF Mono', 'Fira Code', monospace;
  }}
</style>
</head>
<body>
<div class="shell">
  <div class="badge"><span class="badge-dot"></span>{_esc(agent_label)} · {_esc(domain)}</div>
  <h1>{title}</h1>
  <div class="context">{context}</div>
  <div class="tags">{tags_html}</div>
  <div class="progress-bar"><div class="progress-fill" id="prog" style="width:0%"></div></div>

  <div id="player"></div>
  <div class="meta">Generated {generated} · Harness² eLearning · harness2-elearning</div>
</div>

<script>
const SCENES = {scenes_json};
let current = 0;
let score = 0;
let answered = false;

function updateProgress() {{
  const pct = (current / SCENES.length) * 100;
  document.getElementById('prog').style.width = pct + '%';
}}

function renderScene() {{
  answered = false;
  const scene = SCENES[current];
  const n = SCENES.length;
  let choicesHtml = scene.choices.map(c => `
    <button class="choice" onclick="pick(this, ${{c.correct}}, '${{c.feedback}}')" data-correct="${{c.correct}}">
      <span class="choice-key">${{c.key}}</span>
      <span>${{c.text}}</span>
    </button>
  `).join('');
  document.getElementById('player').innerHTML = `
    <div class="scene-label">Scene ${{current + 1}} of ${{n}}</div>
    <div class="situation">${{scene.situation}}</div>
    <div class="choices" id="choices">${{choicesHtml}}</div>
    <div class="feedback-box" id="fb"></div>
    <button class="next-btn" id="nxt" onclick="nextScene()">
      ${{current < n - 1 ? 'Next Scene →' : 'See Results →'}}
    </button>
  `;
  updateProgress();
}}

function pick(btn, correct, feedback) {{
  if (answered) return;
  answered = true;
  if (correct) score++;

  document.querySelectorAll('.choice').forEach(b => {{
    b.disabled = true;
    if (b.dataset.correct === 'true') b.classList.add('correct');
  }});
  btn.classList.add(correct ? 'correct' : 'wrong');

  const fb = document.getElementById('fb');
  fb.textContent = feedback;
  fb.className = 'feedback-box show ' + (correct ? 'correct' : 'wrong');
  document.getElementById('nxt').classList.add('show');
}}

function nextScene() {{
  current++;
  if (current >= SCENES.length) {{
    renderSummary();
  }} else {{
    renderScene();
  }}
}}

function renderSummary() {{
  document.getElementById('prog').style.width = '100%';
  const pct = Math.round((score / SCENES.length) * 100);
  document.getElementById('player').innerHTML = `
    <div class="summary">
      <h2>Scenario Complete</h2>
      <div class="score-ring">${{pct}}%</div>
      <div class="score-label">${{score}} of ${{SCENES.length}} correct</div>
      <br>
      <button class="restart-btn" onclick="restart()">↩ Try Again</button>
    </div>
  `;
}}

function restart() {{
  current = 0; score = 0;
  renderScene();
}}

renderScene();
</script>
</body>
</html>"""
    return html


def export_to_file(scenario: dict, path: str, domain: str = "", agent_label: str = "Domain-Adapted"):
    with open(path, "w", encoding="utf-8") as f:
        f.write(export(scenario, domain=domain, agent_label=agent_label))
