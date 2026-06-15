
from groq import Groq
import streamlit as st


def get_coach_summary(
    breakdown: dict,
    total: float,
    score: int,
    band: str,
    persona: str,
    top_actions: list,
    food_detail: dict,
    benchmark: float,
    streak: int,
) -> str:
    """
    Calls Groq LLaMA-3.3 70B to generate a personalized climate coaching summary.
    The API key is only read from Streamlit session state and is NEVER stored
    in the database or logged anywhere.
    """
    api_key = st.session_state.get("groq_api_key", "").strip()
    if not api_key:
        return (
            "_AI coaching disabled – paste your Groq API key in the sidebar to unlock. "
            "The key is stored only in your session memory and is never saved to the database._"
        )
    try:
        client = Groq(api_key=api_key)
        top_food = max(food_detail, key=food_detail.get) if food_detail else "N/A"
        actions_text = "\n".join(
            [f"- {a['action']} (saves {a['saving_kg']} kg CO₂e/month)" for a in top_actions]
        )
        gap_text = f"{round(total - benchmark, 1):+} kg vs {persona} baseline of {benchmark} kg"
        prompt = f"""You are CarbonLens AI, a friendly but data-driven personal climate coach.
The user is a {persona}. Here is their monthly carbon footprint data:

Category breakdown (kg CO₂e/month):
{chr(10).join([f"- {k}: {v}" for k, v in breakdown.items()])}
Total: {total} kg CO₂e/month
Carbon Score: {score}/100 ({band})
Benchmark gap: {gap_text}
Top food emission driver: {top_food}
Current daily logging streak: {streak} days

Recommended actions:
{actions_text}

Write a personalized 4-5 sentence coaching summary. Be specific, use their actual numbers,
motivate them with the streak, point out the single biggest win available to them, and give
one creative suggestion that is not obvious. Keep the tone warm, smart, and concise.
Do not use generic advice."""
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=350,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return (
            "_AI coach is temporarily unavailable. "
            "Check your API key or try again later._"
        )
