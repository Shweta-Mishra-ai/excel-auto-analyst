<div align="center">

# 📊 Excel Auto-Analyst

### AI-Powered Data Analytics Platform

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue?style=for-the-badge&logo=python)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.37%2B-red?style=for-the-badge&logo=streamlit)](https://streamlit.io)
[![Groq](https://img.shields.io/badge/Groq-LLaMA%203.3-orange?style=for-the-badge)](https://groq.com)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![Stars](https://img.shields.io/github/stars/Shweta-Mishra-ai/excel-auto-analyst?style=for-the-badge&color=yellow)](https://github.com/Shweta-Mishra-ai/excel-auto-analyst/stargazers)

**Upload any CSV or Excel file → Clean → Analyse → Chat with AI → Export PPT Report**

[🚀 Live Demo](https://excel-auto-analyst-ne9ocshgvqtvqtitbapbjs.streamlit.app/) · [⭐ Star this repo](https://github.com/Shweta-Mishra-ai/excel-auto-analyst) · [🐛 Report Bug](https://github.com/Shweta-Mishra-ai/excel-auto-analyst/issues)

---

</div>

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🏠 **Smart Data Cleaning** | Median imputation (never fills with 0), duplicate removal, audit trail |
| 📈 **Auto Dashboard** | KPIs, distributions, pie charts, correlation heatmap |
| 🎨 **Custom Analysis** | Bar, line, scatter, box, area charts with AI insights |
| 🗣️ **Chat with Data** | Ask questions in plain English — AI generates code & charts |
| 📋 **PPT Report** | One-click 9-slide executive PowerPoint with real charts |
| 🔐 **Secure AI** | AST-sandboxed code execution — no raw `exec()` |

---

## 🚀 Quick Start

### Option 1 — Streamlit Cloud (Free, Recommended)

```
1. Fork this repo on GitHub
2. Go to share.streamlit.io
3. Connect your forked repo
4. Set Main file: app.py
5. Add secret: GROQ_API_KEY = "gsk_..."
6. Deploy ✅
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
```

Open **http://localhost:8501** 🎉

### Get Free Groq API Key
👉 [console.groq.com](https://console.groq.com) → Sign up → Create API key (free)

---

## 📁 Project Structure

```
excel-auto-analyst/
├── app.py                      # Main router — thin, no business logic
├── config/
│   └── settings.py             # All constants in one place
├── core/
│   ├── data_loader.py          # File loading (CSV, XLSX)
│   ├── validator.py            # Schema detection, data profiling
│   └── cleaner.py              # Smart cleaning with audit trail
├── analytics/
│   └── stats_engine.py         # KPIs, stats, outliers, correlation
├── ai/
│   ├── safe_executor.py        # AST-sandboxed code runner
│   └── prompt_builder.py       # Structured LLM prompts
├── reports/
│   └── ppt_generator.py        # 9-slide PPT with real charts
├── ui/pages/
│   ├── upload_page.py          # Home & Data Cleaning
│   ├── stats_page.py           # Auto Dashboard
│   ├── custom_analysis_page.py # Custom Report Builder
│   ├── chat_page.py            # Chat with Data
│   └── report_page.py          # PPT Report Generator
└── tests/                      # 60+ unit tests
```

---

## 🧪 Testing

```bash
pip install pytest pytest-cov
pytest tests/ -v --cov=. --cov-report=term-missing
```

---

## 🔄 Dev Workflow (Branch → Test → Merge)

```bash
# Create feature branch
git checkout -b feature/your-feature

# Make changes, then:
pip install ruff
ruff format .          # auto format
ruff check . --fix     # auto lint fix
pytest tests/ -v       # run all tests

# Commit and push
git add .
git commit -m "feat: your feature description"
git push origin feature/your-feature

# Open PR on GitHub → merge to main
```

---

## 🐳 Docker

```bash
docker compose up
# App runs at http://localhost:8501
```

---

## 📊 PPT Report Slides

| # | Slide | Content |
|---|-------|---------|
| 1 | Cover | Dataset name, quality score, column summary |
| 2 | Data Overview | Rows, columns, missing %, memory |
| 3 | KPI Summary | Total, mean, median, std, MoM change |
| 4 | Distribution | Histogram with mean/median lines |
| 5 | Category Breakdown | Top categories bar chart |
| 6 | Outlier Analysis | IQR detection table per column |
| 7 | Correlation | Heatmap + strong pairs list |
| 8 | AI Insights | Headline + 3 insights + recommendation |
| 9 | Closing | Built by Shweta Mishra branding |

---

## ⭐ If this helped you, please star the repo!

[![GitHub stars](https://img.shields.io/github/stars/Shweta-Mishra-ai/excel-auto-analyst?style=social)](https://github.com/Shweta-Mishra-ai/excel-auto-analyst/stargazers)

---

<div align="center">

**Made with ❤️ by [Shweta Mishra](https://github.com/Shweta-Mishra-ai)**

*Excel Auto-Analyst — Turn raw data into insights in seconds*

</div>
