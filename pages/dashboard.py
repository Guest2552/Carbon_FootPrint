
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.carbon_engine import (
    full_breakdown, generate_actions,
    PERSONA_BENCHMARKS, MODE_MAP, DIET_PROFILES,
    SHOPPING_FACTORS, WASTE_FACTORS,
)
from utils.db import save_log, get_streak, get_badges
from utils.groq_coach import get_coach_summary


def render(user):
    uid       = user["id"]
    persona   = user["persona"]
    benchmark = PERSONA_BENCHMARKS.get(persona, 180)
    streak_data = get_streak(uid)
    current_streak = streak_data.get("current_streak", 0)

    st.markdown("## 📊 Carbon Dashboard")
    st.caption("Enter your weekly lifestyle activity below, then click Calculate to see your monthly carbon footprint breakdown.")

    with st.form("inputs_form"):
        # ── Commute & Travel ─────────────────────────────────────────
        st.markdown("### 🚗 Commute and travel inputs")
        col1, col2, col3 = st.columns(3)

        with col1:
            mode      = st.selectbox("Primary commute mode",
                                     list(MODE_MAP.keys()),
                                     help="Select the transport mode you use most days.")
            daily_km  = st.slider("One-way daily distance (km)", 0, 80, 12,
                                   help="Average one-way distance for your main commute.")
            days_pw   = st.slider("Commute days per week", 0, 7, 5)
            occupancy = st.slider("Car occupancy (number of people)", 1, 6, 1,
                                   help="Only used for car modes to split emissions per person.")

        with col2:
            st.markdown("### ✈️ Flights per year")
            sh_fl  = st.number_input("Short-haul flights per year",  0, 20, 1)
            lo_fl  = st.number_input("Long-haul flights per year",   0, 12, 0)
            dom_fl = st.number_input("Domestic flights per year",    0, 20, 2)

        with col3:
            st.markdown("### 🌐 Digital and shopping")
            streaming = st.slider("Streaming hours per week",   0, 60,  10)
            gaming    = st.slider("Gaming hours per week",      0, 50,   6)
            cloud_gb  = st.slider("Cloud storage sync (GB/mo)", 0, 500, 80)
            shopping  = st.select_slider("Shopping intensity",  options=list(SHOPPING_FACTORS.keys()), value="Moderate")
            waste     = st.select_slider("Waste level",         options=list(WASTE_FACTORS.keys()),    value="Moderate")

        # ── Food & Home ───────────────────────────────────────────────
        st.markdown("### 🥗 Food and home energy inputs")
        c1, c2, c3 = st.columns(3)
        with c1:
            diet    = st.selectbox("Diet profile", list(DIET_PROFILES.keys()), index=1)
            d_mult  = st.slider("Food quantity intensity", 0.7, 1.5, 1.0, 0.05,
                                 help="Scale representing how much food you eat relative to average.")
        with c2:
            kwh     = st.slider("Monthly household electricity (kWh)", 30, 1200, 180)
            hh_size = st.slider("Household size", 1, 8, user.get("household_size", 3),
                                 help="Used to calculate your personal share of household electricity.")
        with c3:
            green   = st.slider("Green power share (0 = none, 0.5 = 50%)", 0.0, 0.5, 0.05, 0.05)

        submitted = st.form_submit_button(
            "🔍 Calculate and Save My Footprint",
            use_container_width=True,
        )

    if submitted:
        inputs = dict(
            mode=mode, daily_km=daily_km, days_per_week=days_pw,
            occupancy=occupancy, short_flights=sh_fl, long_flights=lo_fl,
            domestic_flights=dom_fl, diet_profile=diet, diet_multiplier=d_mult,
            kwh=kwh, household_size=hh_size, green_share=green,
            streaming=streaming, gaming=gaming, cloud_gb=cloud_gb,
            shopping=shopping, waste=waste,
        )
        breakdown, total, score, band, food_detail = full_breakdown(inputs)
        save_log(uid, breakdown, total, score, "Current")
        st.session_state["last_result"] = dict(
            breakdown=breakdown, total=total, score=score,
            band=band, food_detail=food_detail, inputs=inputs, benchmark=benchmark,
        )
        streak_data = get_streak(uid)

    res = st.session_state.get("last_result")
    if not res:
        st.info("Fill in your activity data above and click **Calculate and Save My Footprint** to see results.")
        return

    breakdown   = res["breakdown"]
    total       = res["total"]
    score       = res["score"]
    band        = res["band"]
    food_detail = res["food_detail"]
    gap         = round(total - benchmark, 1)

    st.markdown("---")
    st.markdown("### 📈 Your monthly footprint results")
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Monthly CO₂e",   f"{total} kg",    help="Your estimated total monthly carbon footprint.")
    m2.metric("Carbon Score",   f"{score}/100",   delta=f"{band} footprint band")
    m3.metric("vs Benchmark",   f"{gap:+} kg",    delta=f"{persona} baseline: {benchmark} kg")
    m4.metric("Top driver",     max(breakdown, key=breakdown.get))
    m5.metric("Daily streak",   f"{current_streak} 🔥", delta=f"Best: {streak_data.get('longest_streak',0)}")

    # ── Charts ────────────────────────────────────────────────────────
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### Emissions by category")
        df = pd.DataFrame({
            "Category": list(breakdown.keys()),
            "kg CO₂e":  list(breakdown.values()),
        }).sort_values("kg CO₂e", ascending=False)
        fig = px.bar(
            df, x="Category", y="kg CO₂e", color="Category",
            text="kg CO₂e", template="plotly_dark",
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig.update_traces(textposition="outside", texttemplate="%{text:.1f}")
        fig.update_layout(height=380, showlegend=False,
                          paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          margin=dict(l=8,r=8,t=24,b=8))
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Bar chart: monthly CO₂e emissions grouped by lifestyle category. Taller bars indicate larger contributors to your footprint.")

    with c2:
        st.markdown("#### Carbon mix (percentage share)")
        fig2 = px.pie(
            df, names="Category", values="kg CO₂e", hole=0.55,
            template="plotly_dark",
            color_discrete_sequence=px.colors.qualitative.Pastel,
        )
        fig2.update_layout(height=380, paper_bgcolor="rgba(0,0,0,0)",
                           margin=dict(l=8,r=8,t=24,b=8))
        st.plotly_chart(fig2, use_container_width=True)
        st.caption("Donut chart: percentage contribution of each category to your total monthly footprint. Hover to see exact values.")

    # ── Actions ───────────────────────────────────────────────────────
    st.markdown("### ⚡ Personalized reduction actions")
    st.caption("Actions ranked by potential impact on your specific footprint. Difficulty label indicates lifestyle change required.")
    actions = generate_actions(breakdown, total)
    for a in actions:
        css = "action-easy" if a["difficulty"] == "Easy" else "action-medium"
        st.markdown(
            f"<div class='{css}'>💡 <b>{a['action']}</b><br>"
            f"<small>Saves <b>{a['saving_kg']} kg CO₂e/month</b> · "
            f"Category: {a['category']} ({a['pct']}% of total) · "
            f"Difficulty: <b>{a['difficulty']}</b></small></div>",
            unsafe_allow_html=True,
        )

    # ── AI Coach ──────────────────────────────────────────────────────
    st.markdown("### 🤖 AI Climate Coach (Groq LLaMA 3.3 70B)")
    st.caption("Generates a personalized coaching summary using your actual footprint numbers, benchmark gap, and current streak.")
    with st.spinner("Generating your personalized coaching summary..."):
        summary = get_coach_summary(
            breakdown, total, score, band, persona,
            actions, food_detail, benchmark, current_streak,
        )
    st.markdown(f"<div class='card-dark'>{summary}</div>", unsafe_allow_html=True)

    # ── Badges ────────────────────────────────────────────────────────
    badges = get_badges(uid)
    if badges:
        st.markdown("### 🏅 Badges earned")
        st.markdown(
            " ".join([f"<span class='badge-chip'>{b['badge_name']}</span>" for b in badges]),
            unsafe_allow_html=True,
        )

    # ── Export ────────────────────────────────────────────────────────
    st.markdown("### ⬇️ Download your report")
    report_df = pd.DataFrame([{**breakdown, "Total (kg CO₂e)": total, "Score": score, "Band": band, "Persona": persona}])
    st.download_button(
        label="Download report as CSV",
        data=report_df.to_csv(index=False).encode(),
        file_name="carbonlens_footprint_report.csv",
        mime="text/csv",
        help="Download your current footprint breakdown as a CSV file.",
    )
