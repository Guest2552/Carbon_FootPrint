
import pandas as pd
import numpy as np
from pathlib import Path
import streamlit as st

DATA_DIR = Path(__file__).parent.parent / "data"

@st.cache_data
def _load_data():
    t = pd.read_csv(DATA_DIR / "transport_factors.csv")
    t["kg_per_km"] = t["Transport emissions per kilometer travelled"] / 1000.0
    f = pd.read_csv(DATA_DIR / "food_factors.csv")
    f = f.rename(columns={"Greenhouse gas emissions per kilogram": "kg_per_kg"})
    e = pd.read_csv(DATA_DIR / "electricity_factors_india.csv")
    grid_factor = float(e.loc[0, "kgco2e_per_kwh"])
    t_dict = dict(zip(t["Entity"], t["kg_per_km"]))
    f_dict = dict(zip(f["Entity"], f["kg_per_kg"]))
    return t_dict, f_dict, grid_factor

MODE_MAP = {
    "Petrol Car":        "Petrol car",
    "Diesel Car":        "Diesel car",
    "Electric Car":      "Electric car",
    "Bus":               "Bus (average)",
    "Rail / Metro":      "National rail",
    "Motorbike":         "Motorbike",
    "Tram":              "Tram",
    "Walk / Cycle":      "Walk/Cycle",
    "Short-haul Flight": "Short-haul flight",
    "Long-haul Flight":  "Long-haul flight",
    "Domestic Flight":   "Domestic flight",
}

DIET_PROFILES = {
    "Vegan":         {"Tofu": 1.2,  "Other Pulses": 1.6, "Rice": 0.8,  "Other Vegetables": 3.0},
    "Vegetarian":    {"Milk": 1.5,  "Cheese": 0.25, "Rice": 1.0, "Other Vegetables": 3.0,  "Other Pulses": 1.0},
    "Eggetarian":    {"Eggs": 0.7,  "Milk": 1.2,   "Rice": 1.0, "Other Vegetables": 2.5,  "Other Pulses": 0.8},
    "Chicken-based": {"Poultry Meat": 1.0, "Eggs": 0.4, "Rice": 1.0, "Other Vegetables": 2.2, "Milk": 0.8},
    "Mixed Meat":    {"Poultry Meat": 0.8, "Pig Meat": 0.4, "Fish (farmed)": 0.4, "Rice": 1.0, "Other Vegetables": 2.0},
    "Heavy Red Meat":{"Beef (dairy herd)": 0.8, "Lamb & Mutton": 0.5, "Rice": 0.8, "Other Vegetables": 1.8, "Milk": 0.8},
}

SHOPPING_FACTORS = {"Low": 6, "Moderate": 18, "High": 35, "Very High": 60}
WASTE_FACTORS    = {"Low": 4, "Moderate": 10, "High": 18}

PERSONA_BENCHMARKS = {
    "Student": 140,
    "Working Professional": 220,
    "Remote Worker": 180,
    "Freelancer": 170,
}


def calc_transport(mode: str, daily_km: float, days_per_week: int, occupancy: int = 1) -> float:
    t_dict, _, _ = _load_data()
    base = MODE_MAP.get(mode, "Bus (average)")
    factor = t_dict.get(base, 0.0)
    monthly_km = daily_km * days_per_week * 4.33
    if mode in ("Petrol Car", "Diesel Car", "Electric Car"):
        factor = factor / max(occupancy, 1)
    return round(monthly_km * factor, 3)


def calc_flights(short: int, long_: int, domestic: int) -> float:
    t_dict, _, _ = _load_data()
    total = 0.0
    for label, count, dist in [
        ("Short-haul flight", short, 1500),
        ("Long-haul flight",  long_, 6000),
        ("Domestic flight",   domestic, 900),
    ]:
        factor = t_dict.get(label, 0.0)
        total += count * factor * dist
    return round(total / 12.0, 3)


def calc_food(profile: str, multiplier: float = 1.0):
    _, f_dict, _ = _load_data()
    total = 0.0
    detail = {}
    for item, qty in DIET_PROFILES[profile].items():
        factor = f_dict.get(item, 0.0)
        v = qty * multiplier * 4.33 * factor
        total += v
        detail[item] = round(v, 3)
    return round(total, 3), detail


def calc_electricity(kwh: float, household_size: int, green_share: float) -> float:
    _, _, grid_factor = _load_data()
    personal = kwh / max(household_size, 1)
    return round(personal * grid_factor * (1 - green_share), 3)


def calc_digital(streaming_h: float, gaming_h: float, cloud_gb: float) -> float:
    return round(streaming_h * 0.055 * 4.33 + gaming_h * 0.09 * 4.33 + cloud_gb * 0.02, 3)


def calc_shopping(level: str, waste: str) -> float:
    return float(SHOPPING_FACTORS[level] + WASTE_FACTORS[waste])


def score_band(total: float):
    if total < 120: return 90, "Excellent"
    if total < 180: return 75, "Good"
    if total < 260: return 55, "Moderate"
    if total < 360: return 35, "High"
    return 18, "Very High"


def full_breakdown(inputs: dict):
    transport   = calc_transport(inputs["mode"], inputs["daily_km"],
                                 inputs["days_per_week"], inputs["occupancy"])
    flights     = calc_flights(inputs["short_flights"], inputs["long_flights"],
                               inputs["domestic_flights"])
    food, food_detail = calc_food(inputs["diet_profile"], inputs["diet_multiplier"])
    electricity = calc_electricity(inputs["kwh"], inputs["household_size"],
                                   inputs["green_share"])
    digital     = calc_digital(inputs["streaming"], inputs["gaming"], inputs["cloud_gb"])
    shopping    = calc_shopping(inputs["shopping"], inputs["waste"])
    breakdown = {
        "Transport":        round(transport + flights, 2),
        "Food":             round(food, 2),
        "Electricity":      round(electricity, 2),
        "Digital":          round(digital, 2),
        "Shopping & Waste": round(shopping, 2),
    }
    total = round(sum(breakdown.values()), 2)
    score, band = score_band(total)
    return breakdown, total, score, band, food_detail


def generate_actions(breakdown: dict, total: float) -> list:
    actions = []
    for cat, val in sorted(breakdown.items(), key=lambda x: x[1], reverse=True)[:2]:
        pct = round(100 * val / total, 1) if total else 0
        if cat == "Transport":
            actions += [
                {"action": "Shift 2 commute days to bus/rail", "saving_kg": round(0.18*val,1), "difficulty": "Easy",   "category": cat, "pct": pct},
                {"action": "Carpool or use EV for remaining trips",     "saving_kg": round(0.12*val,1), "difficulty": "Medium", "category": cat, "pct": pct},
            ]
        elif cat == "Food":
            actions += [
                {"action": "Replace 2 meat meals/week with legumes",    "saving_kg": round(0.20*val,1), "difficulty": "Easy",   "category": cat, "pct": pct},
                {"action": "Cut dairy serving frequency by 30%",        "saving_kg": round(0.12*val,1), "difficulty": "Easy",   "category": cat, "pct": pct},
            ]
        elif cat == "Electricity":
            actions += [
                {"action": "Raise AC thermostat by 2°C",                "saving_kg": round(0.15*val,1), "difficulty": "Easy",   "category": cat, "pct": pct},
                {"action": "Switch to LED and eliminate standby loads",  "saving_kg": round(0.08*val,1), "difficulty": "Easy",   "category": cat, "pct": pct},
            ]
        elif cat == "Shopping & Waste":
            actions.append({"action": "Batch deliveries and delay non-essentials", "saving_kg": round(0.20*val,1), "difficulty": "Easy", "category": cat, "pct": pct})
        elif cat == "Digital":
            actions.append({"action": "Lower streaming resolution to 1080p",       "saving_kg": round(0.15*val,1), "difficulty": "Easy", "category": cat, "pct": pct})
    return actions[:5]
