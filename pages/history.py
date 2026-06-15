
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.db import get_history

def render(user):
    uid = user["id"]
    st.markdown("## 📅 History and Trends")
    st.caption("Your full activity log and footprint trends over time.")

    logs = get_history(uid, limit=60)
    if not logs:
        st.info("No logs yet. Go to Dashboard, fill your inputs, and click Calculate!")
        return

    df = pd.DataFrame(logs)
    df["logged_at"] = pd.to_datetime(df["logged_at"])
    df = df.sort_values("logged_at")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total logs",             len(df))
    m2.metric("Avg monthly footprint",  f"{df['total_em'].mean():.1f} kg")
    m3.metric("Best carbon score",      int(df["score"].max()))
    if len(df) > 1:
        m4.metric("Latest vs previous",
                  f"{df['total_em'].iloc[-1]:.1f} kg",
                  delta=f"{df['total_em'].iloc[-1] - df['total_em'].iloc[-2]:.1f} kg")
    else:
        m4.metric("Latest footprint",   f"{df['total_em'].iloc[-1]:.1f} kg")

    st.markdown("### Total footprint over time")
    st.caption("Line chart showing how your monthly CO₂e estimate has changed across all logged sessions.")
    fig = px.line(df, x="logged_at", y="total_em", markers=True,
                  labels={"total_em": "kg CO₂e", "logged_at": "Date"},
                  template="plotly_dark",
                  color_discrete_sequence=["#38bdf8"])
    fig.update_layout(height=340, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      margin=dict(l=8,r=8,t=24,b=8))
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Category trends over time")
    st.caption("Multi-line chart showing how each emission category has changed across logged sessions.")
    cats   = ["transport_em","food_em","electricity_em","digital_em","shopping_em"]
    labels = ["Transport","Food","Electricity","Digital","Shopping & Waste"]
    colors = ["#38bdf8","#34d399","#f59e0b","#a78bfa","#f472b6"]
    fig2 = go.Figure()
    for cat, label, color in zip(cats, labels, colors):
        fig2.add_trace(go.Scatter(x=df["logged_at"], y=df[cat], name=label,
                                  mode="lines+markers",
                                  line=dict(color=color, width=2)))
    fig2.update_layout(height=360, template="plotly_dark",
                       paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                       margin=dict(l=8,r=8,t=24,b=8),
                       legend=dict(orientation="h", yanchor="bottom", y=1.02))
    st.plotly_chart(fig2, use_container_width=True)

    st.markdown("### Carbon score over time")
    st.caption("Area chart of your carbon score (0–100). Higher is better.")
    fig3 = px.area(df, x="logged_at", y="score",
                   labels={"score": "Carbon Score (0–100)", "logged_at": "Date"},
                   template="plotly_dark",
                   color_discrete_sequence=["#10b981"])
    fig3.update_layout(height=260, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                       margin=dict(l=8,r=8,t=24,b=8))
    st.plotly_chart(fig3, use_container_width=True)

    st.markdown("### Raw activity log")
    st.caption("Full history table sorted by most recent entry. Download or review your past submissions.")
    display = df[["logged_at","total_em","score","transport_em","food_em","electricity_em"]].rename(columns={
        "logged_at": "Date", "total_em": "Total (kg)",
        "score": "Score", "transport_em": "Transport",
        "food_em": "Food", "electricity_em": "Electricity",
    })
    st.dataframe(display.sort_values("Date", ascending=False).reset_index(drop=True), use_container_width=True)
    st.download_button(
        label="Download full history as CSV",
        data=display.to_csv(index=False).encode(),
        file_name="carbonlens_history.csv",
        mime="text/csv",
    )
