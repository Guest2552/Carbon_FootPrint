
import streamlit as st
import pandas as pd
import plotly.express as px
import streamlit as st
from utils.db import get_leaderboard

MEDALS  = ["🥇", "🥈", "🥉"]
ROW_CSS = ["lb-gold", "lb-silver", "lb-bronze"]

@st.cache_data(ttl=60)
def _cached_leaderboard():
    return get_leaderboard(limit=20)

def render(user):
    st.markdown("## 🏆 Community Leaderboard")
    st.caption("Rankings by lowest average monthly footprint. Lower footprint = higher rank. Refresh every 60 seconds.")

    rows = _cached_leaderboard()
    if not rows:
        st.info("No community data yet. Be the first to log your footprint on the Dashboard!")
        return

    for i, row in enumerate(rows):
        medal = MEDALS[i] if i < 3 else f"#{i+1}"
        css   = ROW_CSS[i] if i < 3 else "lb-row"
        you   = " ← you" if row["username"] == user["username"] else ""
        st.markdown(
            f"<div class='{css}'>{medal} &nbsp; <b>{row['username']}</b>{you} "
            f"<span style='opacity:.65'>· {row['persona']}</span> &nbsp;·&nbsp; "
            f"Avg footprint: <b>{row['avg_em']} kg CO₂e/mo</b> &nbsp;·&nbsp; "
            f"Score: <b>{int(row['avg_score'])}</b> &nbsp;·&nbsp; "
            f"Streak: {row['streak']}🔥</div>",
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.markdown("### Average footprint by persona")
    st.caption("Bar chart comparing average monthly CO₂e across different user personas on the platform.")
    df = pd.DataFrame(rows)
    persona_avg = df.groupby("persona")["avg_em"].mean().reset_index()
    fig = px.bar(
        persona_avg, x="persona", y="avg_em", color="persona",
        labels={"avg_em": "Avg kg CO₂e/month", "persona": "Persona"},
        template="plotly_dark",
        color_discrete_sequence=px.colors.qualitative.Pastel,
    )
    fig.update_layout(height=320, showlegend=False,
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      margin=dict(l=8,r=8,t=24,b=8))
    st.plotly_chart(fig, use_container_width=True)
