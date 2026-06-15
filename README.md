# 🌍 CarbonLens AI — Version 3 (Hackathon Final)

> Full-stack personal carbon intelligence platform built with Streamlit + SQLite + Groq LLaMA 3.3

Application Here:** [![Live Demo](https://img.shields.io/badge/View_Live_Project-FF9900?style=for-the-badge&logo=render&logoColor=white)]([https://carbonfp.streamlit.app/)]
---

## 🚀 Quick start

```bash
pip install -r requirements.txt
streamlit run app.py
```

## 🧪 Run unit tests

```bash
pytest -q
```

## 📁 Project structure

```
carbonlens_v3/
├── app.py                          ← Auth + routing + sidebar
├── requirements.txt
├── carbonlens.db                   ← Auto-created on first run
├── data/
│   ├── transport_factors.csv       ← Our World in Data (2022)
│   ├── food_factors.csv            ← Our World in Data / Poore & Nemecek (2018)
│   └── electricity_factors_india.csv  ← GOI / CEA via Climatiq
├── utils/
│   ├── carbon_engine.py            ← All calculations + @st.cache_data
│   ├── db.py                       ← SQLite ORM: users, logs, streaks, badges
│   └── groq_coach.py               ← Groq llama-3.3-70b-versatile AI coach
├── pages/
│   ├── dashboard.py                ← Inputs, results, AI coach, badges, export
│   ├── history.py                  ← Trend charts + log table
│   ├── leaderboard.py              ← Community ranking + cached DB call
│   ├── badges.py                   ← Achievements display
│   └── scenario_lab.py             ← What-if simulator + gauge
└── tests/
    └── test_carbon_engine.py       ← 22 pytest unit tests
```

---

## 🔑 Groq API key

1. Visit https://console.groq.com — free account
2. Create an API key
3. Paste it in the sidebar under **Groq AI Coach** when the app is running
4. Key is stored only in session memory — never written to database

---

## ✅ Score improvements in v3

| Area           | Change                                              |
|----------------|-----------------------------------------------------|
| Testing (0→60+)  | 22 pytest unit tests for carbon engine             |
| Efficiency (60→75+) | @st.cache_data on data loads, cached leaderboard |
| Security (60→75+)   | Password validation, safe error messages        |
| Accessibility (45→65+) | Captions, headings, help text, descriptive labels |
| Code Quality   | Cleaner separation, type-consistent returns         |

---

## 📊 Data sources

| Dataset | Source |
|---------|--------|
| transport_factors.csv | Our World in Data — Carbon footprint of travel per km (2022) |
| food_factors.csv | Our World in Data — GHG per kg food product (Poore & Nemecek 2018) |
| electricity_factors_india.csv | Climatiq / Government of India — Central Electricity Authority |
