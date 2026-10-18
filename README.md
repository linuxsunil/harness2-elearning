# 🧠 Harness² eLearning

> Domain-adaptive branching scenario generator — inspired by [Google Research Harness²](https://github.com/google-research/harness2) · powered by Claude API · deployable to Streamlit Cloud

[![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.38+-red?style=flat-square&logo=streamlit)](https://streamlit.io)
[![Claude](https://img.shields.io/badge/Claude-claude--sonnet--4--5-purple?style=flat-square)](https://anthropic.com)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

---

## What is this?

Generic AI produces compliance scenarios where wrong answers are obviously wrong. Real professionals make mistakes under pressure because the wrong choice *looks reasonable*. This tool applies the **Harness² Propose → Probe → Compose → Reflect** pattern to fix that.

**Every run makes 3 live Claude API calls:**

```
🔵 PROPOSE   Generic agent — no domain knowledge → baseline scenario
🟣 PROBE     Domain agent — regulatory vocab, real consequences → adapted scenario  
⚖️ COMPOSE   Evaluator agent — scores both on 3 ID dimensions → picks winner
🧠 REFLECT   Lesson extracted → saved to memory.json → next run starts stronger
```

**Live harness trace (real output):**
```
08:41:02.134  GENERIC  call_start | prompt=312c | model=claude-sonnet-4-5
08:41:05.442  GENERIC  ✓ elapsed=3.31s | output_tokens=612
08:41:05.447  DOMAIN   call_start | domain=Pharma Compliance | refined=false
08:41:09.218  DOMAIN   ✓ elapsed=3.77s | output_tokens=748
08:41:09.221  EVAL     scoring: regulatory_accuracy · consequence_realism · decision_pressure
08:41:10.884  EVAL     generic=187/300  domain=261/300  Δ=+74  winner=domain
08:41:10.886  EVAL     lesson saved → memory.json
```

---

## Domains

| Domain | Regulations & Standards | Vocabulary |
|---|---|---|
| **Pharma Compliance** | 21 CFR Part 11, 21 CFR Part 211, GDP, GMP | CAPA, deviation, SOP, batch record, OOS, quarantine |
| **Financial Services** | MiFID II Art. 25, FCA COBS, KYC/AML, GDPR | suitability assessment, KYC, AML, SAR, PEP, TCER |
| **Cybersecurity** | NIST CSF 2.0, MITRE ATT&CK, ISO 27001 | BEC, spear-phishing, lateral movement, IOC, SIEM |

---

## Quickstart

```bash
git clone https://github.com/linuxsunil/harness2-elearning
cd harness2-elearning
pip install -r requirements.txt

# Add your Anthropic API key
cp .env.example .env
# Edit .env → ANTHROPIC_API_KEY=sk-ant-...

streamlit run app.py
```

### Deploy to Streamlit Cloud

1. Fork this repo
2. Go to [share.streamlit.io](https://share.streamlit.io) → New app → point to `app.py`
3. **Settings → Secrets** → paste:
   ```toml
   ANTHROPIC_API_KEY = "sk-ant-..."
   ```
4. Deploy — live in ~60 seconds

---

## Project structure

```
harness2-elearning/
├── app.py                    ← Streamlit UI (4 screens)
├── requirements.txt
│
├── agents/
│   ├── generic_agent.py      ← baseline, no domain knowledge
│   ├── domain_agent.py       ← reads memory + domain prompt
│   └── evaluator_agent.py    ← scores both + extracts lesson
│
├── exporters/
│   ├── rise_exporter.py      ← self-contained Rise 360 HTML
│   └── storyline_exporter.py ← Storyline 360 XML (File → Import → XML)
│
└── harness/
    ├── memory.json           ← refined prompts persist here
    └── prompts/
        ├── generic.txt
        ├── pharma.txt        ← 21 CFR Part 11/211, CAPA, GMP
        ├── finserv.txt       ← MiFID II, KYC/AML, FCA COBS
        └── cyber.txt         ← NIST CSF 2.0, MITRE ATT&CK
```

---

## App screens

| Screen | What happens |
|---|---|
| **1 · Configure** | Pick domain, enter learning objective + audience |
| **2 · Generate** | Live side-by-side streaming — generic left, domain-adapted right. Real harness trace with timestamps and token counts updates as Claude writes. |
| **3 · Results** | Evaluator scores on 3 ID dimensions. Play both scenarios in tabs. Export buttons. |
| **4 · Memory** | Save the winning domain prompt to `memory.json` — next run uses it automatically. |

---

## Exports

- **Rise HTML** — self-contained, embeddable as a Web Object block in Articulate Rise 360
- **Storyline XML** — import via File → Import → XML in Articulate Storyline 360; includes slides, feedback layers, triggers, and score variable

---

## How it differs from the Google Research repo

The original [google-research/harness²](https://github.com/google-research/harness2) is a research CLI for LLM benchmark evaluation on Vertex AI. This is a standalone instructional design tool built on the same **recursive harnessing** pattern (agent outputs refine the next agent's prompts) but applied to compliance eLearning authoring, using the Anthropic API directly.

---

## Built by

**Sunil Iyer** — Senior Instructional Designer,  · Tenkasi

10+ years in eLearning 

· Articulate Rise 360 / Storyline 360 · SCORM/xAPI · AI-assisted course design

---

*Inspired by [Google Research Harness²](https://arxiv.org/abs/2311.04507) · Built with [Claude](https://anthropic.com) + [Streamlit](https://streamlit.io)*
