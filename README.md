# 📊 Excel Auto-Analyst

**A No-Code Data Analytics Platform built with Python and Streamlit.**

Turn raw Excel/CSV files into interactive dashboards and AI-powered insights instantly—no formulas required.

---

## 📸 Project Demo

### 1. Home & Data Preview
Upload your file and instantly verify data integrity.
![Home View](assets/home_data.png)

### 2. Auto-Cleaning Options
One-click data sanitation (handle missing values, remove duplicates).
![Cleaning](assets/cleaning_view.png)

### 3. Instant Insights Dashboard
Automatic generation of KPIs, Distributions, and Split metrics.
![Dashboard](assets/auto_dashboard.png)

### 4. Custom Report Builder
Drag-and-drop analysis for specific deep-dives.
![Custom Report](assets/custom_report.png)

---

## 🚀 Features

* **📂 Smart Upload:** Supports `.csv` and `.xlsx` files.
* **🧹 Auto-Cleaning:** One-click removal of duplicates and handling of missing values.
* **📈 Instant Dashboards:** Automatically generates KPI cards, Bar Charts, and Pie Charts based on data types.
* **🎨 Custom Reports:** "Drag-and-drop" style interface to build your own comparison charts.
* **🤖 AI Insights:** Logic-based narrative engine that explains trends and volatility in plain English.
* **🗣️ Chat with Data:** Ask questions in plain English (e.g., "Show me sales by region") and get clear, non-technical answers. No code or complex jargon—just the insights you need. Powered by **Llama3** via **Groq**.

## 🛠️ Tech Stack

* **Python:** Core Logic
* **Streamlit:** UI/Web Framework
* **Pandas:** Data Processing Engine
* **Plotly:** Interactive Visualizations
* **PandasAI & Groq:** Generative AI Engine

## 📦 How to Run Locally

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/your-username/excel-auto-analyst.git](https://github.com/your-username/excel-auto-analyst.git)
    ```
2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Run the app:**
    ```bash
    streamlit run app.py
    ```

## 🔑 Configuration (Important!)
        
This app requires a **Groq API Key** to run the "Chat with Data" feature.

1.  **Get a Free Key:** [Groq Cloud Console](https://console.groq.com/keys)
2.  **Configure Locally:**
    *   Open `.streamlit/secrets.toml`
    *   Paste your key: `GROQ_API_KEY = "gsk_..."`
    *   *Note: This file is ignored by Git to keep your key safe.*

## ☁️ Deployment

This app is designed to be deployed instantly on **Streamlit Cloud**.
1. Fork this repo.
2. Login to [Streamlit Cloud](https://share.streamlit.io/).
3. Connect your GitHub and select this repository.
4. Click **Deploy**.

---
*Created by Shweta Mishra

