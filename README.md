<div align="center">

<img src="https://raw.githubusercontent.com/Shweta-Mishra-ai/excel-auto-analyst/main/assets/logo.png" alt="Excel Auto-Analyst" width="120" onerror="this.style.display='none'"/>

# 📊 Excel Auto-Analyst

### AI-Powered Data Analytics — From Raw Data to Insights in Seconds

<p>
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white" alt="Streamlit"/>
  <img src="https://img.shields.io/badge/Groq-LLaMA_3.3-F55036?style=for-the-badge" alt="Groq"/>
  <img src="https://img.shields.io/badge/License-MIT-00C853?style=for-the-badge" alt="License"/>
</p>

<p>
  <img src="https://img.shields.io/github/stars/Shweta-Mishra-ai/excel-auto-analyst?style=for-the-badge&color=FFD700&label=Stars" alt="Stars"/>
  <img src="https://img.shields.io/github/forks/Shweta-Mishra-ai/excel-auto-analyst?style=for-the-badge&color=00BFFF&label=Forks" alt="Forks"/>
  <img src="https://img.shields.io/github/last-commit/Shweta-Mishra-ai/excel-auto-analyst?style=for-the-badge&color=8A2BE2" alt="Last Commit"/>
</p>

<br/>

**Upload any CSV/Excel → AI cleans it → Instant dashboards → Chat in plain English → Export PPT report**

<br/>

<a href="https://excel-auto-analyst-ne9ocshgvqtvqlitbapbjs.streamlit.app">
  <img src="https://img.shields.io/badge/🚀_LIVE_DEMO-Click_Here-0D9488?style=for-the-badge&labelColor=0F172A" alt="Live Demo"/>
</a>
&nbsp;
<a href="https://github.com/Shweta-Mishra-ai/excel-auto-analyst/stargazers">
  <img src="https://img.shields.io/badge/⭐_STAR_THIS_REPO-Support_the_Project-FFD700?style=for-the-badge&labelColor=0F172A" alt="Star"/>
</a>

</div>

<br/>

---

## ✨ Why Excel Auto-Analyst?

<table>
<tr>
<td width="50%" valign="top">

### 🔴 The Problem
- Hours wasted cleaning messy spreadsheets
- Manual chart-making for every report
- No technical skills → no insights
- Reports take days, not seconds
- "Fill missing values with 0" corrupts your data

</td>
<td width="50%" valign="top">

### ✅ The Solution
- **Smart cleaning** — median imputation, audit trail
- **Instant dashboards** — KPIs, trends, correlations
- **AI chat** — ask questions in plain English
- **One-click PPT** — 9-slide executive report
- **Zero setup** — works in your browser

</td>
</tr>
</table>

---

## 🎬 See It In Action

<div align="center">

| Upload & Clean | Instant Dashboard | Chat with AI | PPT Report |
|:---:|:---:|:---:|:---:|
| Drag & drop your file | KPIs auto-generated | Ask anything | 9-slide export |

</div>

---

## 🚀 Core Features

<table>
<tr>
<td valign="top" width="33%">

### 🏠 Smart Cleaning
- Median/Mean/Mode imputation
- **Never** fills with 0 (data integrity!)
- Duplicate detection & removal
- Full audit trail of every change
- Data Quality Score (0-100)

</td>
<td valign="top" width="33%">

### 📈 Auto Dashboard
- KPI cards (Sum, Avg, Max, Min, MoM)
- Distribution histograms
- Correlation heatmaps
- Outlier detection (IQR + Z-Score)
- Categorical breakdowns

</td>
<td valign="top" width="33%">

### 🎨 Custom Analysis
- Bar, Line, Scatter, Box, Area charts
- **Sort** ascending/descending
- **Top N** filtering
- Aggregation (Sum/Avg/Count/Median)
- Multi-category filters
- Export chart data as CSV

</td>
</tr>
<tr>
<td valign="top" width="33%">

### 🗣️ Chat with Data
- Plain English Q&A
- AI-generated charts on demand
- Powered by Groq LLaMA 3.3-70B
- Sandboxed code execution (secure)
- Conversation history

</td>
<td valign="top" width="33%">

### 📋 PPT Report
- 9 professional slides
- Real embedded charts (matplotlib)
- KPI summary + AI insights
- Outlier & correlation analysis
- One-click download

</td>
<td valign="top" width="33%">

### 🔐 Security First
- AST-sandboxed AI execution
- No raw `exec()` vulnerability
- 39+ unit tests passing
- Ruff lint-clean codebase
- CI/CD with GitHub Actions

</td>
</tr>
</table>

---

## 🏗️ Architecture

```
excel-auto-analyst/
├── app.py                       # Thin router — zero business logic
├── config/
│   └── settings.py              # Centralized configuration
├── core/
│   ├── data_loader.py           # CSV/Excel ingestion + validation
│   ├── validator.py             # Schema detection, data profiling
│   └── cleaner.py               # Smart imputation + audit trail
├── analytics/
│   └── stats_engine.py          # KPIs, correlation, outliers, stats
├── ai/
│   ├── safe_executor.py         # AST-sandboxed code execution
│   └── prompt_builder.py        # Structured LLM prompts
├── reports/
│   └── ppt_generator.py         # 9-slide PPT with real charts
├── ui/pages/
│   ├── upload_page.py           # Home & Data Cleaning
│   ├── stats_page.py            # Auto Dashboard
│   ├── custom_analysis_page.py  # Custom Report Builder
│   ├── chat_page.py             # Chat with Data
│   └── report_page.py           # PPT Report Generator
└── tests/                        # 39+ unit tests
```

---

## ⚡ Quick Start

### Option 1 — Try it Live (No Setup)

<div align="center">

**[👉 Open Live App](https://excel-auto-analyst-ne9ocshgvqtvqlitbapbjs.streamlit.app)**

</div>

### Option 2 — Run Locally

```bash
# Clone the repo
git clone https://github.com/Shweta-Mishra-ai/excel-auto-analyst.git
cd excel-auto-analyst

# Install dependencies
pip install -r requirements.txt

# Add your free Groq API key
echo 'GROQ_API_KEY = "gsk_your_key_here"' > .streamlit/secrets.toml

# Run
streamlit run app.py
```

Open **http://localhost:8501** 🎉

> 🔑 Get a **free** Groq API key at [console.groq.com](https://console.groq.com)

### Option 3 — Docker

```bash
docker compose up
```

---

## 🧪 Testing & Quality

```bash
pip install -r requirements-dev.txt
pytest tests/ -v --cov=. --cov-report=term-missing
ruff check .
ruff format .
```

<div align="center">

| Metric | Status |
|--------|--------|
| Unit Tests | ✅ 39 passing |
| Lint | ✅ Ruff clean |
| Security | ✅ AST sandbox |
| CI/CD | ✅ GitHub Actions |

</div>

---

## 🔄 Contributing — Branch Workflow

```bash
# 1. Create feature branch
git checkout -b feature/your-feature

# 2. Make changes, then verify
ruff format .
ruff check . --fix
pytest tests/ -v

# 3. Commit & push
git add .
git commit -m "feat: description of your feature"
git push origin feature/your-feature

# 4. Open a Pull Request → CI runs automatically
```

---

## 📊 PPT Report — What's Inside

<div align="center">

| # | Slide | Content |
|---|-------|---------|
| 1 | 🎯 Cover | Dataset name + quality score |
| 2 | 📋 Data Overview | Rows, columns, missing %, memory |
| 3 | 📈 KPI Summary | Total, mean, median, MoM change |
| 4 | 📊 Distribution | Histogram + mean/median lines |
| 5 | 🏆 Category Breakdown | Top categories bar chart |
| 6 | 🔍 Outlier Analysis | IQR detection per column |
| 7 | 🔗 Correlation | Heatmap + strong pairs |
| 8 | 🤖 AI Insights | Narrative + recommendations |
| 9 | 🎬 Closing | Branding & summary |

</div>

---

## 🛣️ Roadmap

- [x] Smart data cleaning with audit trail
- [x] AI-powered chat with sandboxed execution
- [x] 9-slide PPT auto-generation
- [x] Sort, filter & aggregation in Custom Analysis
- [ ] Multi-file upload & join
- [ ] Time-series forecasting (Prophet/ARIMA)
- [ ] PDF export
- [ ] User authentication & saved dashboards
- [ ] Compare-two-periods analysis

---

## 🤝 Feedback & Contributions

Found a bug? Have a feature idea? 

- 🐛 [Open an Issue](https://github.com/Shweta-Mishra-ai/excel-auto-analyst/issues)
- 💡 [Start a Discussion](https://github.com/Shweta-Mishra-ai/excel-auto-analyst/discussions)
- ⭐ **Star this repo** if it helped you!

---

<div align="center">

### Built with 💙 by [Shweta Mishra](https://github.com/Shweta-Mishra-ai)

*Shweta*

<p>
  <a href="https://github.com/Shweta-Mishra-ai">
    <img src="https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white" alt="GitHub"/>
  </a>
  <a href="https://www.linkedin.com/">
    <img src="https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white" alt="LinkedIn"/>
  </a>
</p>

<sub>If this project saved you time, consider giving it a ⭐ — it helps a lot!</sub>

</div>
