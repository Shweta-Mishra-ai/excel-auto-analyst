<div align="center">

<img src="assets/logo.png" alt="Excel Auto-Analyst" width="80" />

# Excel Auto-Analyst

**Raw data in. Boardroom-ready insights out.**

Upload any CSV or Excel file — the app cleans it, profiles it, charts it, answers questions about it in plain English, and exports a 9-slide PowerPoint report. No code required.

[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-0d6efd?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.37%2B-ff4b4b?style=flat-square&logo=streamlit&logoColor=white)](https://streamlit.io)
[![Groq · LLaMA 3.3](https://img.shields.io/badge/Groq-LLaMA%203.3-f97316?style=flat-square)](https://groq.com)
[![MIT License](https://img.shields.io/badge/License-MIT-22c55e?style=flat-square)](LICENSE)
[![Stars](https://img.shields.io/github/stars/Shweta-Mishra-ai/excel-auto-analyst?style=flat-square&color=facc15&label=Stars)](https://github.com/Shweta-Mishra-ai/excel-auto-analyst/stargazers)

[**Live Demo →**](https://excel-auto-analyst-ne9ocshgvqtvqtitbapbjs.streamlit.app/)&nbsp;&nbsp;·&nbsp;&nbsp;[Report a Bug](https://github.com/Shweta-Mishra-ai/excel-auto-analyst/issues)&nbsp;&nbsp;·&nbsp;&nbsp;[Star the Repo ⭐](https://github.com/Shweta-Mishra-ai/excel-auto-analyst)

</div>

---

## What it does

| Step | What happens |
|------|-------------|
| **Upload** | Drop any `.csv` or `.xlsx` file |
| **Clean** | Median imputation, duplicate removal, full audit trail — no zero-filling |
| **Dashboard** | KPIs, distributions, correlation heatmap, category breakdowns — auto-generated |
| **Custom Charts** | Bar, line, scatter, box, area charts with AI-written insights |
| **Chat** | Ask anything in plain English — the AI writes and runs the analysis for you |
| **Export** | One click → 9-slide executive PowerPoint with real embedded charts |

All AI code execution runs inside an AST sandbox — no raw `exec()`, no arbitrary code on your server.

---

## Quick start

### Streamlit Cloud (recommended — free, no install)

```
1. Fork this repo
2. Go to share.streamlit.io → New app → select your fork
3. Main file: app.py
4. Secrets: GROQ_API_KEY = "gsk_..."
5. Deploy
```

### Local

```bash
git clone https://github.com/Shweta-Mishra-ai/excel-auto-analyst.git
cd excel-auto-analyst

pip install -r requirements.txt

echo 'GROQ_API_KEY = "gsk_your_key_here"' > .streamlit/secrets.toml

streamlit run app.py
# → http://localhost:8501
```

**Get a free Groq API key:** [console.groq.com](https://console.groq.com) → Sign up → Create API key

### Docker

```bash
docker compose up
# → http://localhost:8501
```

---

## Project structure

```
excel-auto-analyst/
│
├── app.py                       # Thin router — no business logic here
│
├── config/settings.py           # All constants in one place
│
├── core/
│   ├── data_loader.py           # CSV + XLSX ingestion
│   ├── validator.py             # Schema detection, data profiling
│   └── cleaner.py               # Smart cleaning with audit trail
│
├── analytics/stats_engine.py    # KPIs, outliers, correlation
│
├── ai/
│   ├── safe_executor.py         # AST-sandboxed code runner
│   └── prompt_builder.py        # Structured LLM prompts
│
├── reports/ppt_generator.py     # 9-slide PPT with real charts
│
├── ui/pages/
│   ├── upload_page.py           # Upload & Data Cleaning
│   ├── stats_page.py            # Auto Dashboard
│   ├── custom_analysis_page.py  # Custom Report Builder
│   ├── chat_page.py             # Chat with Data
│   └── report_page.py           # PPT Export
│
└── tests/                       # 60+ unit tests
```

---

## PPT report — what's in each slide

| # | Slide | Content |
|---|-------|---------|
| 1 | Cover | Dataset name, quality score, column summary |
| 2 | Data Overview | Row/column count, missing %, memory usage |
| 3 | KPI Summary | Total, mean, median, std dev, MoM change |
| 4 | Distribution | Histogram with mean/median lines |
| 5 | Category Breakdown | Top categories bar chart |
| 6 | Outlier Analysis | IQR detection table per column |
| 7 | Correlation | Heatmap + strong pairs list |
| 8 | AI Insights | Headline + 3 insights + recommendation |
| 9 | Closing | Branding slide |

---

## Development workflow

```bash
# 1. Create a branch
git checkout -b feature/your-feature

# 2. Make changes, then format + lint
pip install ruff
ruff format .
ruff check . --fix

# 3. Run tests
pytest tests/ -v --cov=. --cov-report=term-missing

# 4. Commit and push
git add .
git commit -m "feat: your feature description"
git push origin feature/your-feature

# 5. Open a PR → merge to main
```

---

## Design decisions worth knowing

**Why median imputation?** Zero-filling missing numeric values silently corrupts means, KPIs, and correlations. Median preserves the distribution without introducing artificial zeros.

**Why AST sandboxing?** The chat feature lets an LLM generate Python. Running that with `exec()` is a server security risk. The sandbox parses the AST first and blocks anything that isn't data manipulation or plotting.

**Why Groq/LLaMA 3.3?** Inference is fast enough that chart generation in the chat tab feels interactive, not batched.

---

## Tech stack

- **Frontend** — Streamlit
- **AI** — Groq API · LLaMA 3.3 70B
- **Data** — pandas · NumPy · openpyxl
- **Charts** — Matplotlib · Seaborn · Plotly
- **Reports** — python-pptx
- **Testing** — pytest · pytest-cov
- **Linting** — Ruff
- **Deploy** — Streamlit Cloud · Render · Docker

---

<div align="center">

Built by [Shweta Mishra](https://github.com/Shweta-Mishra-ai) · [arXiv research](https://arxiv.org/abs/2605.14362) · MIT License

*If this saved you time, a ⭐ goes a long way.*

</div>
