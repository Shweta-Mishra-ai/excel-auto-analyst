<div align="center">

<h1>📊 Excel Auto-Analyst</h1>

<p><strong>Upload any CSV or Excel file → Auto-clean → Dashboard → Chat with AI → Export PPT</strong></p>

[![Python](https://img.shields.io/badge/Python-3.9%2B-0d6efd?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.37%2B-ff4b4b?style=flat-square&logo=streamlit&logoColor=white)](https://streamlit.io)
[![Groq · LLaMA 3.3](https://img.shields.io/badge/Groq-LLaMA%203.3-f97316?style=flat-square)](https://groq.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-22c55e?style=flat-square)](LICENSE)
[![Stars](https://img.shields.io/github/stars/Shweta-Mishra-ai/excel-auto-analyst?style=flat-square&color=facc15&cacheSeconds=3600)](https://github.com/Shweta-Mishra-ai/excel-auto-analyst/stargazers)

<br/>

[🚀 **Live Demo**](https://excel-auto-analyst-ne9ocshgvqtvqtitbapbjs.streamlit.app/) &nbsp;·&nbsp; [🐛 Report Bug](https://github.com/Shweta-Mishra-ai/excel-auto-analyst/issues) &nbsp;·&nbsp; [⭐ Star the Repo](https://github.com/Shweta-Mishra-ai/excel-auto-analyst)

<br/>

> **No code. No setup. Drop your file — get a full analysis in seconds.**

</div>

---

## 🎬 Demo

https://github.com/Shweta-Mishra-ai/excel-auto-analyst/releases/download/v2.0.0/Excel.demo.mp4

---

## ✨ Features

| | Feature | What it does |
|---|---------|-------------|
| 🧹 | **Smart Data Cleaning** | Median imputation, duplicate removal, full audit trail — never fills with zero |
| 📊 | **Auto Dashboard** | KPIs, distributions, pie charts, correlation heatmap — instant |
| 🎨 | **Custom Charts** | Bar, line, scatter, box, area — with AI-written insights per chart |
| 💬 | **Chat with Your Data** | Ask questions in plain English — AI writes and runs the code for you |
| 📋 | **One-Click PPT Export** | 9-slide executive PowerPoint with real embedded charts |
| 🔐 | **Secure AI Execution** | AST-sandboxed code runner — no raw `exec()`, ever |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                        app.py                           │
│              (thin router — no business logic)          │
└───────────┬──────────────────────────────────┬──────────┘
            │                                  │
     ┌──────▼──────┐                   ┌───────▼───────┐
     │    core/    │                   │      ui/      │
     │─────────────│                   │───────────────│
     │ data_loader │                   │  upload_page  │
     │  validator  │                   │   stats_page  │
     │   cleaner   │                   │  custom_page  │
     └──────┬──────┘                   │   chat_page   │
            │                          │  report_page  │
     ┌──────▼──────┐                   └───────────────┘
     │ analytics/  │
     │─────────────│         ┌──────────────────────┐
     │ stats_engine│         │         ai/          │
     └─────────────┘         │──────────────────────│
                             │   safe_executor      │
     ┌─────────────┐         │  (AST sandbox)       │
     │  reports/   │         │   prompt_builder     │
     │─────────────│         └──────────────────────┘
     │ ppt_generator         
     └─────────────┘
```

---

## 📁 Project Structure

```
excel-auto-analyst/
│
├── app.py                       # Main router
├── config/
│   └── settings.py              # All constants
├── core/
│   ├── data_loader.py           # CSV + XLSX ingestion
│   ├── validator.py             # Schema detection, profiling
│   └── cleaner.py               # Smart cleaning + audit trail
├── analytics/
│   └── stats_engine.py          # KPIs, outliers, correlation
├── ai/
│   ├── safe_executor.py         # AST-sandboxed code runner
│   └── prompt_builder.py        # LLM prompt templates
├── reports/
│   └── ppt_generator.py         # 9-slide PPT with real charts
├── ui/pages/
│   ├── upload_page.py           # Upload & Data Cleaning
│   ├── stats_page.py            # Auto Dashboard
│   ├── custom_analysis_page.py  # Custom Report Builder
│   ├── chat_page.py             # Chat with Data
│   └── report_page.py           # PPT Export
└── tests/                       # 60+ unit tests
```

---

## 🚀 Quick Start

### Option 1 — Streamlit Cloud (Free, Recommended)

```
1. Fork this repo
2. Go to → share.streamlit.io
3. Connect your fork → Main file: app.py
4. Add secret:  GROQ_API_KEY = "gsk_..."
5. Deploy ✅
```

### Option 2 — Run Locally

```bash
# Clone
git clone https://github.com/Shweta-Mishra-ai/excel-auto-analyst.git
cd excel-auto-analyst

# Install
pip install -r requirements.txt

# Add API key
echo 'GROQ_API_KEY = "gsk_your_key_here"' > .streamlit/secrets.toml

# Run
streamlit run app.py
# → http://localhost:8501
```

**Free Groq API key:** [console.groq.com](https://console.groq.com) → Sign up → Create API key

### Option 3 — Docker

```bash
docker compose up
# → http://localhost:8501
```

---

## 📊 PPT Report — 9 Slides

| # | Slide | Content |
|---|-------|---------|
| 1 | Cover | Dataset name, quality score, column summary |
| 2 | Data Overview | Row/column count, missing %, memory |
| 3 | KPI Summary | Total, mean, median, std dev, MoM change |
| 4 | Distribution | Histogram with mean/median markers |
| 5 | Category Breakdown | Top categories bar chart |
| 6 | Outlier Analysis | IQR detection table per column |
| 7 | Correlation | Heatmap + strong pairs list |
| 8 | AI Insights | Headline + 3 insights + recommendation |
| 9 | Closing | Branding slide |

---

## 🧪 Testing

```bash
pip install pytest pytest-cov
pytest tests/ -v --cov=. --cov-report=term-missing
```

60+ unit tests covering cleaning, stats, AI execution, and report generation.

---

## 🔄 Dev Workflow

```bash
# Branch
git checkout -b feature/your-feature

# Format + lint
pip install ruff
ruff format .
ruff check . --fix

# Test
pytest tests/ -v

# Push + PR
git add .
git commit -m "feat: describe your change"
git push origin feature/your-feature
# Open PR → merge to main
```

---

## 🛠️ Tech Stack

| Layer | Tools |
|-------|-------|
| **Frontend** | Streamlit |
| **AI / LLM** | Groq API · LLaMA 3.3 70B |
| **Data** | pandas · NumPy · openpyxl |
| **Charts** | Matplotlib · Seaborn · Plotly |
| **Reports** | python-pptx |
| **Security** | AST sandbox (no raw exec) |
| **Testing** | pytest · pytest-cov |
| **Linting** | Ruff |
| **Deploy** | Streamlit Cloud · Render · Docker |

---

## 💡 Design Decisions

**Why median imputation?**  
Zero-filling missing values corrupts means, KPIs, and correlations. Median preserves the distribution without introducing fake zeros.

**Why AST sandboxing?**  
Chat generates live Python via LLM. Running that with raw `exec()` is a security risk. The sandbox validates the AST before execution — only data manipulation and plotting allowed.

**Why Groq + LLaMA 3.3?**  
Inference is fast enough that AI-generated charts in the chat tab feel interactive, not queued.

---

<div align="center">

Made with ❤️ by [Shweta Mishra](https://github.com/Shweta-Mishra-ai) &nbsp;·&nbsp; MIT License

*If this saved you time — a ⭐ means a lot.*

</div>
