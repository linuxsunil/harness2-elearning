"""
Harness² eLearning — Streamlit App
Domain-adaptive branching scenario generator with live Claude API calls,
side-by-side generic vs. domain-adapted comparison, real harness trace,
and Rise HTML / Storyline XML export.
"""

import streamlit as st
import anthropic
import json
import time
import threading
from pathlib import Path
from datetime import datetime

# Agents
from agents import generic_agent, domain_agent, evaluator_agent

# Exporters
from exporters import rise_exporter, storyline_exporter

# ── Config ────────────────────────────────────────────────────────────────────
DOMAINS = ["Pharma Compliance", "Financial Services", "Cybersecurity"]
MEMORY_PATH = Path(__file__).parent / "harness" / "memory.json"

st.set_page_config(
    page_title="Harness² eLearning",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS — Mocha Mousse (Pantone 17-1230, Colour of Year 2025) ──────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;600&display=swap');

/*
  Palette — Mocha Mousse 2025
  --mocha:   #A47864  Pantone 17-1230 (primary accent)
  --mocha-d: #7A5548  darker mocha (hover, borders)
  --mocha-l: #C4A494  lighter mocha (secondary accents)
  --cream:   #FAF7F4  warm white background
  --parchment: #F0EAE4 card surfaces
  --linen:   #E4D9D0  borders / dividers
  --espresso:#2C1A14  primary text
  --warm-mid:#7A6258  secondary text
  --warm-dim:#B8A89E  muted text
  --sage:    #6B8F71  correct/success
  --terracotta: #C0533A wrong/error
*/

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.stApp { background: #FAF7F4; }
.main .block-container { padding: 2rem 2rem 4rem; max-width: 1400px; }

/* Hero header */
.hero {
  padding: 2.5rem 0 1.5rem;
  border-bottom: 1px solid #E4D9D0;
  margin-bottom: 2rem;
}
.hero h1 {
  font-size: 2.2rem; font-weight: 800; color: #2C1A14;
  margin: 0 0 8px;
}
.hero p { color: #7A6258; font-size: 1.05rem; margin: 0; }

/* Section labels */
.section-label {
  font-size: 11px; font-weight: 700; letter-spacing: 0.1em;
  text-transform: uppercase; color: #A47864;
  font-family: 'IBM Plex Mono', monospace;
  margin-bottom: 8px;
}

/* Trace log */
.trace-log {
  background: #FDF9F6; border: 2px solid #E4D9D0;
  border-radius: 12px; padding: 16px;
  font-family: 'IBM Plex Mono', monospace;
  font-size: 12px; color: #5A3E32;
  max-height: 380px; overflow-y: auto;
  line-height: 1.7;
}
.trace-entry { margin-bottom: 4px; }
.trace-generic { color: #B85C00; font-weight: 600; }
.trace-domain  { color: #7A4A2A; font-weight: 700; }
.trace-eval    { color: #2E7A4A; font-weight: 600; }
.trace-dim     { color: #B8A89E; }

/* Score cards */
.score-card {
  background: #F0EAE4; border: 1px solid #E4D9D0;
  border-radius: 12px; padding: 20px; text-align: center;
  margin-bottom: 12px;
}
.score-big { font-size: 3rem; font-weight: 800; color: #2C1A14; line-height: 1; }
.score-label { font-size: 11px; color: #7A6258; margin-top: 4px;
               text-transform: uppercase; letter-spacing: 0.05em; }
.score-dim  { font-size: 0.9rem; color: #B8A89E; }

/* Verdict badge */
.verdict-badge {
  display: inline-block; padding: 4px 12px;
  border-radius: 99px; font-size: 12px; font-weight: 700;
  letter-spacing: 0.04em; margin-bottom: 8px;
}
.verdict-winner { background: #A47864; color: #fff; }
.verdict-loser  { background: #F0EAE4; color: #7A6258; border: 1px solid #E4D9D0; }

/* Scenario player */
.scenario-frame {
  background: #F0EAE4; border: 1px solid #E4D9D0;
  border-radius: 14px; padding: 24px;
  margin-top: 12px;
}
.scene-situation { color: #2C1A14; line-height: 1.75; font-size: 0.97rem; }
.choice-btn-correct { border-left: 3px solid #6B8F71 !important; }
.choice-btn-wrong   { border-left: 3px solid #C0533A !important; }

/* Info boxes */
.info-box {
  background: #F0EAE4; border: 1px solid #E4D9D0;
  border-radius: 10px; padding: 14px 16px;
  font-size: 0.9rem; color: #7A6258; margin-bottom: 12px;
}
.info-box strong { color: #2C1A14; }

/* Highlight block */
.highlight-block {
  background: #F0EAE4; border-left: 3px solid #A47864;
  border-radius: 0 10px 10px 0; padding: 12px 16px;
  font-size: 0.9rem; color: #7A6258; margin-bottom: 12px;
}

/* Streamlit native widget overrides */
/* Primary action buttons (Generate etc) */
.stButton > button[kind="primary"],
.stButton > button:not([kind="secondary"]) {
  background: #A47864 !important; color: #fff !important;
  border: none !important; border-radius: 10px !important;
  font-weight: 600 !important;
}
.stButton > button[kind="primary"]:hover,
.stButton > button:not([kind="secondary"]):hover { background: #7A5548 !important; }

/* Download buttons — white bg, mocha border */
.stDownloadButton > button {
  background: #FFFFFF !important; color: #2C1A14 !important;
  border: 1.5px solid #E4D9D0 !important; border-radius: 10px !important;
  font-weight: 600 !important;
}
.stDownloadButton > button:hover {
  border-color: #A47864 !important; background: #F0EAE4 !important;
}
.stSelectbox > div > div { border-color: #E4D9D0 !important; background: #F0EAE4 !important; color: #2C1A14 !important; }
.stTextInput > div > div > input { border-color: #E4D9D0 !important; background: #F0EAE4 !important; color: #2C1A14 !important; }
.stTextArea > div > div > textarea { border-color: #E4D9D0 !important; background: #F0EAE4 !important; color: #2C1A14 !important; }
div[data-testid="stInfo"] { background: #F0EAE4 !important; border-color: #A47864 !important; color: #2C1A14 !important; }
div[data-testid="stSuccess"] { background: #EBF3EC !important; border-color: #6B8F71 !important; color: #2C1A14 !important; }
div[data-testid="stError"] { background: #FAEAE6 !important; border-color: #C0533A !important; color: #2C1A14 !important; }
.stTabs [data-baseweb="tab"] { color: #7A6258 !important; }
.stTabs [data-baseweb="tab"][aria-selected="true"] { color: #A47864 !important; border-bottom-color: #A47864 !important; }
.stProgress > div > div { background: #A47864 !important; }
h1, h2, h3 { color: #2C1A14 !important; }
p, li, label { color: #2C1A14 !important; }
</style>
""", unsafe_allow_html=True)


# ── Memory helpers ─────────────────────────────────────────────────────────────
def load_memory() -> dict:
    if MEMORY_PATH.exists():
        try:
            return json.loads(MEMORY_PATH.read_text())
        except Exception:
            pass
    return {"version": 1, "refined_prompts": {}, "lessons": [], "run_history": []}


def save_memory(memory: dict):
    MEMORY_PATH.write_text(json.dumps(memory, indent=2))


# ── Session state init ─────────────────────────────────────────────────────────
def init_state():
    defaults = {
        "screen": "input",          # input | generating | results | player
        "trace_log": [],
        "generic_result": None,
        "domain_result": None,
        "eval_result": None,
        "memory": load_memory(),
        "objective": "",
        "domain": DOMAINS[0],
        "audience": "",
        "active_player": None,     # "generic" | "domain"
        "scene_index": 0,
        "scene_answered": False,
        "score": 0,
        "generation_done": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()


# ── Anthropic client ──────────────────────────────────────────────────────────
def get_client():
    try:
        api_key = st.secrets["ANTHROPIC_API_KEY"]
    except Exception:
        import os
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        st.error("🔑 No API key found. Add ANTHROPIC_API_KEY to Streamlit secrets or environment.")
        st.stop()
    return anthropic.Anthropic(api_key=api_key)


# ── Trace log helper ──────────────────────────────────────────────────────────
def make_log_fn(placeholder):
    """Returns a log_fn callback + a flush function that updates the placeholder."""
    log = st.session_state.trace_log

    def log_fn(agent: str, event: str, data: dict):
        ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        css = {"generic": "trace-generic", "domain": "trace-domain", "evaluator": "trace-eval"}.get(agent, "")

        if event == "call_start":
            msg = f"[{ts}] <b>{agent.upper()}</b> → call_start"
            if "domain" in data:
                msg += f" | domain={data['domain']}"
            if "using_refined" in data:
                msg += f" | refined={data['using_refined']}"
            if "system_prompt_chars" in data:
                msg += f" | prompt={data['system_prompt_chars']}c"
        elif event == "tokens_in":
            msg = f"[{ts}] <span class='trace-dim'>{agent.upper()} input_tokens={data['count']}</span>"
        elif event == "streaming":
            chunk = data.get("chunk", "")[:60].replace("<", "&lt;").replace(">", "&gt;")
            msg = f"[{ts}] <span class='trace-dim'>{agent.upper()} ▸ {chunk}…</span>"
        elif event == "call_complete":
            msg = f"[{ts}] <b>{agent.upper()}</b> ✓ elapsed={data.get('elapsed')}s | out_tokens={data.get('output_tokens')}"
        elif event == "scores_ready":
            msg = (f"[{ts}] <b>EVAL</b> generic={data.get('generic_total')} "
                   f"domain={data.get('domain_total')} Δ={data.get('delta')} winner={data.get('winner')}")
        elif event == "parse_error":
            msg = f"[{ts}] ⚠ {agent.upper()} parse_error: {data.get('error','')}"
        else:
            msg = f"[{ts}] {agent.upper()} {event} {json.dumps(data)[:80]}"

        log.append(f'<div class="trace-entry {css}">{msg}</div>')

        html = "\n".join(log[-80:])  # keep last 80 entries
        placeholder.markdown(
            f'<div class="trace-log">{html}</div>',
            unsafe_allow_html=True
        )

    return log_fn


# ─────────────────────────────────────────────────────────────────────────────
# SCREEN 1: Input
# ─────────────────────────────────────────────────────────────────────────────
def screen_input():
    st.markdown("""
<div class="hero">
  <h1>🧠 Harness² eLearning</h1>
  <p>Domain-adaptive branching scenario generator &mdash; powered by Claude + Harness² pattern</p>
</div>
""", unsafe_allow_html=True)

    col1, col2 = st.columns([1.2, 1])

    with col1:
        st.markdown('<div class="section-label">01 · Configure</div>', unsafe_allow_html=True)

        domain = st.selectbox(
            "Domain",
            DOMAINS,
            index=DOMAINS.index(st.session_state.domain),
            help="Selects the domain-specific system prompt and regulatory vocabulary"
        )
        st.session_state.domain = domain

        objective = st.text_area(
            "Learning objective",
            value=st.session_state.objective or "",
            placeholder="e.g. Learners will correctly identify when to escalate an OOS result to QA vs proceeding with batch release.",
            height=110,
        )
        st.session_state.objective = objective

        audience = st.text_input(
            "Audience",
            value=st.session_state.audience or "",
            placeholder="e.g. QA analysts with 1–3 years experience",
        )
        st.session_state.audience = audience

        memory = st.session_state.memory
        refined_exists = domain in memory.get("refined_prompts", {})
        if refined_exists:
            st.info(f"✨ A refined prompt for **{domain}** exists in memory and will be used automatically.")

        if st.button("⚡ Generate Scenarios", type="primary", use_container_width=True,
                     disabled=not objective.strip()):
            if not objective.strip():
                st.warning("Please enter a learning objective.")
            else:
                st.session_state.screen = "generating"
                st.session_state.trace_log = []
                st.session_state.generic_result = None
                st.session_state.domain_result = None
                st.session_state.eval_result = None
                st.session_state.generation_done = False
                st.rerun()

    with col2:
        st.markdown('<div class="section-label">How it works</div>', unsafe_allow_html=True)
        st.markdown("""
<div class="info-box">
<strong>Harness² pattern</strong><br>
Inspired by Google's recursive agent harnessing research:
<br><br>
<b>1. Propose</b> — Generic agent generates a baseline scenario with no domain knowledge<br>
<b>2. Probe</b> — Domain agent uses a refined, domain-specific system prompt<br>
<b>3. Compose</b> — Evaluator agent scores both and extracts a lesson<br>
<b>4. Reflect</b> — Winning prompt persisted to memory for next run
</div>
<div class="highlight-block">
Live Claude API calls · Real streaming · Actual token counts · Memory persistence across runs
</div>
""", unsafe_allow_html=True)

        if st.session_state.memory.get("lessons"):
            st.markdown('<div class="section-label">Lessons from memory</div>', unsafe_allow_html=True)
            for lesson in st.session_state.memory["lessons"][-3:]:
                st.markdown(f'<div class="info-box">💡 {lesson}</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# SCREEN 2: Generating (live side-by-side)
# ─────────────────────────────────────────────────────────────────────────────
def screen_generating():
    st.markdown('<div class="section-label">⚡ Generating — Live Harness² Run</div>', unsafe_allow_html=True)

    objective = st.session_state.objective
    domain = st.session_state.domain
    audience = st.session_state.audience
    memory = st.session_state.memory

    col_g, col_d = st.columns(2)
    with col_g:
        st.markdown("**🔵 Generic Agent** — no domain knowledge")
        g_status = st.empty()
        g_output = st.empty()
    with col_d:
        st.markdown(f"**🟣 Domain Agent** — {domain} specialist")
        d_status = st.empty()
        d_output = st.empty()

    st.markdown("---")
    st.markdown('<div class="section-label">🔍 Live Harness Trace</div>', unsafe_allow_html=True)
    trace_placeholder = st.empty()

    log_fn = make_log_fn(trace_placeholder)
    client = get_client()

    # ── Run generic agent ──────────────────────────────────────────────────
    g_status.info("🔵 Running generic agent...")
    g_result = generic_agent.run(client, objective, domain, audience, log_fn=log_fn)
    st.session_state.generic_result = g_result

    if g_result["error"]:
        g_status.error(f"Parse error: {g_result['error']}")
        g_output.code(g_result["raw"][:600])
    else:
        g_status.success(f"✓ Generic done — {g_result['meta']['elapsed']}s · {g_result['meta']['output_tokens']} tokens")
        scenario = g_result["scenario"]
        g_output.markdown(f"""
**{scenario.get('title', 'Scenario')}**

{scenario.get('context', '')}

*{len(scenario.get('scenes', []))} scenes · Tags: {', '.join(scenario.get('tags', []))}*
""")

    # ── Run domain agent ───────────────────────────────────────────────────
    d_status.info(f"🟣 Running {domain} domain agent...")
    d_result = domain_agent.run(client, objective, domain, audience, memory, log_fn=log_fn)
    st.session_state.domain_result = d_result

    if d_result["error"]:
        d_status.error(f"Parse error: {d_result['error']}")
        d_output.code(d_result["raw"][:600])
    else:
        refined_tag = " ✨ (refined)" if d_result["meta"].get("using_refined") else ""
        d_status.success(f"✓ Domain done — {d_result['meta']['elapsed']}s · {d_result['meta']['output_tokens']} tokens{refined_tag}")
        scenario = d_result["scenario"]
        d_output.markdown(f"""
**{scenario.get('title', 'Scenario')}**

{scenario.get('context', '')}

*{len(scenario.get('scenes', []))} scenes · Tags: {', '.join(scenario.get('tags', []))}*
""")

    # ── Run evaluator ──────────────────────────────────────────────────────
    if not g_result["error"] and not d_result["error"]:
        st.markdown("---")
        st.markdown('<div class="section-label">⚖️ Evaluator Agent — scoring both outputs</div>',
                    unsafe_allow_html=True)
        eval_placeholder = st.empty()
        eval_placeholder.info("Evaluator running...")

        eval_result = evaluator_agent.run(client, g_result, d_result, log_fn=log_fn)
        st.session_state.eval_result = eval_result
        eval_placeholder.success("✓ Evaluation complete")

        # Persist lesson to memory
        if eval_result["scores"] and eval_result["scores"].get("lesson"):
            lesson = eval_result["scores"]["lesson"]
            memory["lessons"] = memory.get("lessons", [])
            memory["lessons"].append(lesson)
            memory["run_history"].append({
                "ts": datetime.now().isoformat(),
                "domain": domain,
                "objective": objective[:80],
                "delta": eval_result["scores"].get("delta"),
            })
            save_memory(memory)
            st.session_state.memory = memory

    st.session_state.generation_done = True

    # Proceed button
    st.markdown("---")
    if st.button("📊 View Results & Export →", type="primary", use_container_width=True):
        st.session_state.screen = "results"
        st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# SCREEN 3: Results — scores + side-by-side players + export
# ─────────────────────────────────────────────────────────────────────────────
def screen_results():
    st.markdown('<div class="section-label">📊 Results</div>', unsafe_allow_html=True)

    g_result = st.session_state.generic_result
    d_result = st.session_state.domain_result
    eval_result = st.session_state.eval_result
    domain = st.session_state.domain

    # ── Evaluator scores ───────────────────────────────────────────────────
    if eval_result and eval_result["scores"]:
        scores = eval_result["scores"]
        gs = scores.get("generic", {})
        ds = scores.get("domain", {})
        delta = scores.get("delta", 0)

        st.markdown("### Harness² Evaluation")

        col_gs, col_vs, col_ds = st.columns([1, 0.3, 1])
        with col_gs:
            st.markdown('<div class="verdict-badge verdict-loser">Generic (baseline)</div>', unsafe_allow_html=True)
            st.markdown(f"""
<div class="score-card">
  <div class="score-big">{gs.get('total', 0)}</div>
  <div class="score-label">/ 300 pts</div>
</div>
""", unsafe_allow_html=True)
            st.markdown(f"""
| Dimension | Score |
|---|---|
| Regulatory accuracy | {gs.get('regulatory_accuracy', 0)} |
| Consequence realism | {gs.get('consequence_realism', 0)} |
| Decision pressure | {gs.get('decision_pressure', 0)} |
""")
            verdict = scores.get("generic_verdict", "")
            if verdict:
                st.caption(f"⚠ {verdict}")

        with col_vs:
            st.markdown(f"""
<div style="text-align:center; padding-top: 60px; color: #6c6ff5;">
  <div style="font-size: 1.8rem; font-weight: 800;">+{delta:.0f}</div>
  <div style="font-size: 11px; color: #7c85b3; margin-top: 4px;">pts improvement</div>
</div>
""", unsafe_allow_html=True)

        with col_ds:
            st.markdown('<div class="verdict-badge verdict-winner">Domain-Adapted ✓ Winner</div>',
                        unsafe_allow_html=True)
            st.markdown(f"""
<div class="score-card">
  <div class="score-big" style="color: #10b981">{ds.get('total', 0)}</div>
  <div class="score-label">/ 300 pts</div>
</div>
""", unsafe_allow_html=True)
            st.markdown(f"""
| Dimension | Score |
|---|---|
| Regulatory accuracy | {ds.get('regulatory_accuracy', 0)} |
| Consequence realism | {ds.get('consequence_realism', 0)} |
| Decision pressure | {ds.get('decision_pressure', 0)} |
""")
            verdict = scores.get("domain_verdict", "")
            if verdict:
                st.caption(f"✅ {verdict}")

        lesson = scores.get("lesson", "")
        if lesson:
            st.markdown(f'<div class="highlight-block">💡 <strong>Lesson learned:</strong> {lesson}</div>',
                        unsafe_allow_html=True)

    st.markdown("---")

    # ── Side-by-side scenario players ─────────────────────────────────────
    st.markdown("### Play Both Scenarios")

    tab_g, tab_d = st.tabs(["🔵 Generic Scenario", "🟣 Domain-Adapted Scenario"])

    with tab_g:
        if g_result and g_result["scenario"]:
            render_player("generic", g_result["scenario"])
        else:
            st.error("Generic scenario unavailable.")

    with tab_d:
        if d_result and d_result["scenario"]:
            render_player("domain", d_result["scenario"])
        else:
            st.error("Domain scenario unavailable.")

    st.markdown("---")

    # ── Export section ─────────────────────────────────────────────────────
    st.markdown("### Export")
    col_r, col_s, col_m = st.columns(3)

    with col_r:
        st.markdown("**📦 Rise HTML** (domain-adapted)")
        st.caption("Self-contained HTML — embed in Articulate Rise 360 as a Web Object block")
        if d_result and d_result["scenario"]:
            rise_html = rise_exporter.export(
                d_result["scenario"],
                domain=domain,
                agent_label="Domain-Adapted"
            )
            st.download_button(
                "⬇ Download Rise HTML",
                data=rise_html,
                file_name=f"scenario_{domain.lower().replace(' ', '_')}_rise.html",
                mime="text/html",
                use_container_width=True,
            )
        else:
            st.button("⬇ Download Rise HTML", disabled=True, use_container_width=True)

    with col_s:
        st.markdown("**📋 Storyline XML** (domain-adapted)")
        st.caption("Import into Articulate Storyline 360 via File > Import > XML")
        if d_result and d_result["scenario"]:
            sl_xml = storyline_exporter.export(
                d_result["scenario"],
                domain=domain,
                agent_label="Domain-Adapted"
            )
            st.download_button(
                "⬇ Download Storyline XML",
                data=sl_xml,
                file_name=f"scenario_{domain.lower().replace(' ', '_')}_storyline.xml",
                mime="application/xml",
                use_container_width=True,
            )
        else:
            st.button("⬇ Download Storyline XML", disabled=True, use_container_width=True)

    with col_m:
        st.markdown("**🧠 Save refined prompt**")
        st.caption("Persist this domain prompt to memory so the next run starts stronger")
        if d_result and d_result["scenario"]:
            if st.button("💾 Save domain prompt to memory", use_container_width=True):
                memory = st.session_state.memory
                memory["refined_prompts"][domain] = d_result["meta"]["system_prompt"]
                save_memory(memory)
                st.session_state.memory = memory
                st.success(f"✓ Refined prompt for {domain} saved — next run will use it automatically!")
        else:
            st.button("💾 Save domain prompt to memory", disabled=True, use_container_width=True)

    st.markdown("---")
    if st.button("← Generate Another Scenario", use_container_width=True):
        st.session_state.screen = "input"
        st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# Scenario Player Component
# ─────────────────────────────────────────────────────────────────────────────
def render_player(key_prefix: str, scenario: dict):
    """Render scenario player as self-contained HTML component — no Streamlit button styling leakage."""
    import streamlit.components.v1 as components
    from exporters.rise_exporter import export as rise_export
    html = rise_export(scenario, domain=scenario.get("domain", ""), agent_label=key_prefix.capitalize())
    components.html(html, height=700, scrolling=True)


# ─────────────────────────────────────────────────────────────────────────────
# Router
# ─────────────────────────────────────────────────────────────────────────────
screen = st.session_state.screen

if screen == "input":
    screen_input()
elif screen == "generating":
    screen_generating()
elif screen == "results":
    screen_results()
else:
    st.session_state.screen = "input"
    st.rerun()
