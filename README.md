# 📊 PMO Portfolio Management Dashboard

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.54.0-FF4B4B.svg)](https://streamlit.io/)
[![Plotly](https://img.shields.io/badge/Plotly-6.5.2-3F4F75.svg)](https://plotly.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An enterprise-grade, modular Project Management Office (PMO) analytics platform and interactive [Streamlit](https://streamlit.io/) dashboard designed to provide executive visibility into organizational project portfolios, Gantt execution schedules, financial budget utilization, and RAG health governance.

---

## 🌟 Key Features

- **Synthetic Data Engineering (`src/generate_pmo_data.py`)**:
  - Automated generation of realistic enterprise project portfolios using `Faker`, `NumPy`, and `Pandas`.
  - Realistic multi-factor modeling of project budgets, actual expenditures, completion percentages, lifecycle phases, and RAG health statuses (`Green`, `Amber`, `Red`).
  - Dynamic, secure directory and path resolution using Python's standard `pathlib`.
  - Deterministic reproducibility via configurable random seeds and CLI parameterization (`--num-projects`, `--seed`, `--output`).

- **High-Performance Data Processing (`src/data_processing.py`)**:
  - Robust type validation, datetime sanitization, and automated fallback data synthesis.
  - Derived business intelligence metrics: budget variance, budget utilization percentage, project duration, and health indices.
  - Standardized hex color mapping for RAG health governance (`#10b981`, `#f59e0b`, `#ef4444`).
  - Sub-second dashboard load times powered by Streamlit caching (`@st.cache_data`).

- **Interactive Executive Dashboard (`app.py`)**:
  - **Dynamic Sidebar Controls**: Filter by project status, RAG health, project manager, department, custom date range horizon, and real-time free-text keyword search.
  - **Executive KPI Cards**: Real-time totals for Planned Budget, Actual Spend, Net Budget Variance, Active vs. Total Projects, and Overall Portfolio Health (% Green).
  - **Tab 1: Portfolio Overview**:
    - Interactive Plotly Gantt timeline chart with dynamic sorting, RAG color coding, detailed hover cards, and a real-time calendar marker for today's date.
    - Strategic priority and lifecycle completion breakdown charts.
  - **Tab 2: Budget & Health**:
    - Project health distribution donut chart (RAG breakdown).
    - Planned Budget vs. Actual Spend comparison grouped by organizational department.
    - Project risk matrix scatter plot (Budget Utilization vs. Completion Progress) highlighting early warning anomalies and projects exceeding 100% budget.
    - Escalated initiatives alert panel for red projects needing PMO intervention.
  - **Tab 3: Raw PMO Data Explorer**:
    - Embedded within a collapsible `st.expander("🔍 Explore Raw PMO Data")`.
    - Interactive `st.dataframe()` with custom column formatting (currency formatting, progress indicators, date formatters).
    - One-click CSV export of the active filtered portfolio.

---

## 🏗️ Project Architecture

```text
PMO-Portfolio-Management-Dashboard/
│
├── .gitignore                   # Version control exclusions for cache & virtual envs
├── LICENSE                      # Project open source license
├── README.md                    # Comprehensive documentation and quickstart
├── requirements.txt             # Python project dependencies
├── pytest.ini                   # Pytest test suite configuration
├── app.py                       # Main Streamlit dashboard application entry point
│
├── data/                        # Dynamic dataset storage directory
│   ├── .gitkeep                 # Folder persistence placeholder
│   └── pmo_projects.csv         # Generated synthetic PMO portfolio dataset
│
├── src/                         # Modular business logic and data engineering package
│   ├── __init__.py              # Python package initializer
│   ├── generate_pmo_data.py     # Faker-based synthetic PMO data generation script
│   └── data_processing.py       # Caching, datetime sanitization, RAG coloring & KPIs
│
└── tests/                       # Automated unit and integration test suite
    └── test_pmo_dashboard.py    # Test specifications for generation, processing & filtering
```

---

## 🚀 Quickstart Guide

### 1. Prerequisites

Ensure Python 3.10 or higher is installed on your system.

### 2. Installation

Clone this repository and install the required dependencies:

```bash
git clone https://github.com/kiwisibk/PMO-Portfolio-Management-Dashboard.git
cd PMO-Portfolio-Management-Dashboard

# Optional: Create and activate a virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# Install required dependencies
pip install -r requirements.txt
```

### 3. Generate PMO Data (Optional)

The dashboard will automatically generate synthetic data on its initial run if no CSV is found. To pre-generate or customize the dataset manually:

```bash
python src/generate_pmo_data.py --num-projects 60 --seed 42
```

### 4. Launch the Dashboard

Start the interactive Streamlit dashboard:

```bash
streamlit run app.py
```

Once launched, navigate to `http://localhost:8501` in your web browser.

---

## 🧪 Running Automated Tests

Run the comprehensive test suite with `pytest`:

```bash
python -m pytest -v
```

---

## 📊 RAG Status Definition & Governance

| RAG Status | Hex Color | PMO Definition | Strategic Action Required |
|:---:|:---:|:---|:---|
| **Green** | `#10b981` | On track. Budget variance within ±5%, milestones met. | Routine PMO monitoring. |
| **Amber** | `#f59e0b` | Potential risk detected. Minor budget or schedule overrun. | Preventive review with Project Manager. |
| **Red** | `#ef4444` | Critical deviation. Significant overrun or blocker. | Executive steering committee escalation. |

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
