
import streamlit as st
from utils.db import get_badges, get_streak

BADGE_DESC = {
    "🌱 Green Pioneer":   "Achieved a monthly footprint below 120 kg CO₂e.",
    "⭐ Carbon Champion":  "Scored 80 or above on the carbon score index.",
    "🔥 7-Day Logger":    "Logged activity for at least 7 different days.",
    "🏆 30-Day Veteran":  "Logged activity for at least 30 different days.",
    "⚡ 3-Day Streak":    "Logged activity on 3 consecutive days.",
}
ALL_BADGES = list(BADGE_DESC.keys())

def render(user):
    uid = user["id"]
    st.markdown("## 🏅 Badges and Achievements")
    st.caption("Earn badges by logging consistently and improving your footprint over time.")

    streak = get_streak(uid)
    col1, col2 = st.columns(2)
    col1.metric("Current streak", f"{streak.get('current_streak',0)} days 🔥",
                help="Number of consecutive days you have logged activity.")
    col2.metric("Best streak ever", f"{streak.get('longest_streak',0)} days",
                help="Your longest consecutive logging streak.")

    earned = get_badges(uid)
    earned_names = {b["badge_name"] for b in earned}

    st.markdown("### Earned badges")
    if not earned:
        st.info("No badges earned yet. Log your first activity on the Dashboard to get started!")
    else:
        cols = st.columns(min(len(earned), 4))
        for i, b in enumerate(earned):
            with cols[i % 4]:
                st.markdown(
                    f"<div class='card-dark' style='text-align:center'>"
                    f"<div style='font-size:2rem'>{b['badge_name'].split()[0]}</div>"
                    f"<b>{b['badge_name']}</b><br>"
                    f"<small style='color:#64748b'>{BADGE_DESC.get(b['badge_name'],'')}</small><br>"
                    f"<small style='color:#475569'>Earned: {b['awarded_at'][:10]}</small></div>",
                    unsafe_allow_html=True,
                )

    st.markdown("### All achievements")
    st.caption("Complete list of available badges and their unlock conditions.")
    for badge in ALL_BADGES:
        status = "✅ Earned" if badge in earned_names else "🔒 Locked"
        color  = "#10b981" if badge in earned_names else "#475569"
        st.markdown(
            f"<div class='lb-row'>"
            f"<b style='color:{color}'>{status}</b> &nbsp; {badge} — "
            f"<small>{BADGE_DESC[badge]}</small></div>",
            unsafe_allow_html=True,
        )
