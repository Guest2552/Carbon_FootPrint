
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.carbon_engine import (
    calc_transport, calc_flights, calc_food,
    calc_electricity, calc_digital, calc_shopping,
    MODE_MAP, DIET_PROFILES, SHOPPING_FACTORS, WASTE_FACTORS,
    PERSONA_BENCHMARKS,
)

def render(user):
    persona   = user["persona"]
    benchmark = PERSONA_BENCHMARKS.get(persona, 180)

    st.markdown("## ⚙️ Scenario Lab")
    st.caption("Simulate what-if lifestyle changes and instantly see how your projected monthly footprint changes.")

    if "last_result" not in st.session_state:
        st.warning("Run a calculation from the Dashboard first to load your baseline data.")
        return

    res            = st.session_state["last_result"]
    base_breakdown = res["breakdown"]
    base_total     = res["total"]
    inp            = res["inputs"]

    st.markdown(f"**Your current baseline:** `{base_total} kg CO₂e/month` &nbsp;|&nbsp; Persona benchmark: `{benchmark} kg`")
    st.markdown("---")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### 🚗 Transport scenario")
        new_mode = st.selectbox("Switch commute to",
                                list(MODE_MAP.keys()),
                                index=list(MODE_MAP.keys()).index(inp["mode"]))
        new_km   = st.slider("New daily km", 0, 80, inp["daily_km"])
        new_days = st.slider("New commute days/week", 0, 7, inp["days_per_week"])
        new_occ  = st.slider("New car occupancy", 1, 6, inp["occupancy"])
        st.markdown("#### ✈️ Flight reduction")
        new_sfl = st.slider("Short flights/yr (scenario)", 0, 20, inp["short_flights"])
        new_lfl = st.slider("Long flights/yr (scenario)",  0, 12, inp["long_flights"])
        new_dfl = st.slider("Domestic flights/yr (scenario)", 0, 20, inp["domestic_flights"])

    with c2:
        st.markdown("#### 🥗 Diet scenario")
        new_diet = st.selectbox("Switch diet to",
                                list(DIET_PROFILES.keys()),
                                index=list(DIET_PROFILES.keys()).index(inp["diet_profile"]))
        new_mult = st.slider("Food quantity intensity (scenario)", 0.7, 1.5, inp["diet_multiplier"], 0.05)
        st.markdown("#### ⚡ Home energy scenario")
        new_kwh   = st.slider("Monthly electricity kWh (scenario)", 30, 1200, inp["kwh"])
        new_green = st.slider("Green power share (scenario)", 0.0, 0.5, inp["green_share"], 0.05)
        st.markdown("#### 📦 Digital and shopping")
        new_stream = st.slider("Streaming hrs/wk (scenario)", 0, 60, inp["streaming"])
        new_game   = st.slider("Gaming hrs/wk (scenario)",    0, 50, inp["gaming"])
        new_shop   = st.select_slider("Shopping intensity (scenario)", options=list(SHOPPING_FACTORS.keys()), value=inp["shopping"])
        new_waste  = st.select_slider("Waste level (scenario)",        options=list(WASTE_FACTORS.keys()),    value=inp["waste"])

    new_transport = calc_transport(new_mode, new_km, new_days, new_occ)
    new_flights   = calc_flights(new_sfl, new_lfl, new_dfl)
    new_food, _   = calc_food(new_diet, new_mult)
    new_elec      = calc_electricity(new_kwh, inp["household_size"], new_green)
    new_digital   = calc_digital(new_stream, new_game, inp["cloud_gb"])
    new_shopping  = calc_shopping(new_shop, new_waste)

    new_breakdown = {
        "Transport":        round(new_transport + new_flights, 2),
        "Food":             round(new_food, 2),
        "Electricity":      round(new_elec, 2),
        "Digital":          round(new_digital, 2),
        "Shopping & Waste": round(new_shopping, 2),
    }
    new_total = round(sum(new_breakdown.values()), 2)
    saving    = round(base_total - new_total, 2)
    pct_save  = round(100 * saving / base_total, 1) if base_total else 0

    st.markdown("---")
    st.markdown("### 📊 Projected result")
    s1, s2, s3 = st.columns(3)
    s1.metric("Projected footprint",  f"{new_total} kg CO₂e",
              help="Monthly footprint if you adopt all scenario changes.")
    s2.metric("Reduction",            f"{saving:+} kg",
              delta=f"{pct_save}% potential savings")
    s3.metric("vs Benchmark",         f"{round(new_total - benchmark, 1):+} kg",
              delta=f"{persona} baseline: {benchmark} kg")

    st.markdown("### Current vs Projected comparison")
    st.caption("Grouped bar chart comparing your current category emissions with projected emissions under the scenario settings above.")
    categories = list(base_breakdown.keys())
    fig = go.Figure(data=[
        go.Bar(name="Current",   x=categories,
               y=[base_breakdown[c] for c in categories],
               marker_color="#38bdf8"),
        go.Bar(name="Projected", x=categories,
               y=[new_breakdown[c]  for c in categories],
               marker_color="#10b981"),
    ])
    fig.update_layout(
        barmode="group", height=380, template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=8,r=8,t=24,b=8),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Projected footprint gauge")
    st.caption("Gauge showing projected CO₂e against your baseline. Blue line marks your persona benchmark.")
    gauge = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=new_total,
        delta={"reference": base_total, "valueformat": ".1f"},
        title={"text": "Projected monthly CO₂e (kg)", "font": {"color": "#e2e8f0"}},
        gauge={
            "axis":  {"range": [0, max(500, base_total * 1.2)], "tickcolor": "#64748b"},
            "bar":   {"color": "#10b981"},
            "steps": [
                {"range": [0, 140],  "color": "#052e16"},
                {"range": [140, 260],"color": "#1c1917"},
                {"range": [260, 500],"color": "#7f1d1d"},
            ],
            "threshold": {"line": {"color": "#38bdf8", "width": 3}, "value": benchmark},
        },
    ))
    gauge.update_layout(
        height=320, paper_bgcolor="rgba(0,0,0,0)",
        font={"color": "#e2e8f0"}, margin=dict(l=16,r=16,t=32,b=16),
    )
    st.plotly_chart(gauge, use_container_width=True)
