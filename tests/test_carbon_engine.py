
# tests/test_carbon_engine.py
# Run with: pytest -q
# These unit tests validate the core calculation logic independent of the Streamlit UI.

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Patch st.cache_data to be a no-op decorator so tests run without Streamlit context
import unittest.mock as mock
import streamlit as st
st.cache_data = lambda func=None, **kwargs: func if func else lambda f: f

from utils.carbon_engine import (
    calc_transport,
    calc_food,
    calc_electricity,
    calc_digital,
    calc_shopping,
    score_band,
    full_breakdown,
    generate_actions,
    PERSONA_BENCHMARKS,
    MODE_MAP,
    DIET_PROFILES,
    SHOPPING_FACTORS,
    WASTE_FACTORS,
)


# ── Transport ─────────────────────────────────────────────────────────

def test_transport_non_negative():
    assert calc_transport("Bus", 0, 0, 1) >= 0

def test_transport_increases_with_distance():
    short = calc_transport("Bus", daily_km=5,  days_per_week=5, occupancy=1)
    long  = calc_transport("Bus", daily_km=30, days_per_week=5, occupancy=1)
    assert long > short

def test_transport_walk_cycle_is_zero():
    result = calc_transport("Walk / Cycle", 10, 5, 1)
    assert result == 0.0

def test_transport_car_occupancy_reduces_emissions():
    single = calc_transport("Petrol Car", 10, 5, occupancy=1)
    shared = calc_transport("Petrol Car", 10, 5, occupancy=4)
    assert shared < single

def test_transport_all_modes_return_float():
    for mode in MODE_MAP.keys():
        result = calc_transport(mode, 10, 5, 1)
        assert isinstance(result, float)
        assert result >= 0


# ── Food ─────────────────────────────────────────────────────────────

def test_food_profile_ordering():
    vegan, _  = calc_food("Vegan", 1.0)
    veg, _    = calc_food("Vegetarian", 1.0)
    heavy, _  = calc_food("Heavy Red Meat", 1.0)
    assert vegan < veg < heavy

def test_food_all_profiles_non_negative():
    for profile in DIET_PROFILES.keys():
        val, detail = calc_food(profile, 1.0)
        assert val >= 0
        for k, v in detail.items():
            assert v >= 0

def test_food_multiplier_scales_linearly():
    base, _   = calc_food("Vegetarian", 1.0)
    doubled, _ = calc_food("Vegetarian", 2.0)
    assert abs(doubled - 2 * base) < 0.01


# ── Electricity ───────────────────────────────────────────────────────

def test_electricity_non_negative():
    assert calc_electricity(0, 1, 0.0) >= 0

def test_electricity_scales_with_kwh():
    low  = calc_electricity(50,  2, 0.0)
    high = calc_electricity(300, 2, 0.0)
    assert high > low

def test_electricity_green_share_reduces_emissions():
    no_green   = calc_electricity(200, 2, 0.0)
    half_green = calc_electricity(200, 2, 0.5)
    assert half_green < no_green

def test_electricity_household_size_divides_correctly():
    single   = calc_electricity(200, 1, 0.0)
    four_hh  = calc_electricity(200, 4, 0.0)
    assert abs(single - 4 * four_hh) < 0.01


# ── Digital ───────────────────────────────────────────────────────────

def test_digital_zero_inputs():
    assert calc_digital(0, 0, 0) == 0.0

def test_digital_increases_with_usage():
    low  = calc_digital(2, 2, 10)
    high = calc_digital(40, 30, 400)
    assert high > low


# ── Shopping ─────────────────────────────────────────────────────────

def test_shopping_all_combinations_non_negative():
    for shop in SHOPPING_FACTORS.keys():
        for waste in WASTE_FACTORS.keys():
            assert calc_shopping(shop, waste) >= 0

def test_shopping_very_high_greater_than_low():
    low  = calc_shopping("Low",      "Low")
    high = calc_shopping("Very High", "High")
    assert high > low


# ── Score band ────────────────────────────────────────────────────────

def test_score_band_monotonic():
    s1, _ = score_band(100)
    s2, _ = score_band(200)
    s3, _ = score_band(350)
    s4, _ = score_band(500)
    assert s1 > s2 > s3 > s4

def test_score_band_valid_range():
    for total in [50, 150, 250, 400, 600]:
        score, band = score_band(total)
        assert 0 <= score <= 100
        assert isinstance(band, str)


# ── Persona benchmarks ────────────────────────────────────────────────

def test_persona_benchmarks_exist_and_positive():
    for p in ["Student", "Working Professional", "Remote Worker", "Freelancer"]:
        assert p in PERSONA_BENCHMARKS
        assert PERSONA_BENCHMARKS[p] > 0


# ── Full breakdown ────────────────────────────────────────────────────

def test_full_breakdown_returns_correct_keys():
    inputs = dict(
        mode="Bus", daily_km=10, days_per_week=5, occupancy=1,
        short_flights=1, long_flights=0, domestic_flights=2,
        diet_profile="Vegetarian", diet_multiplier=1.0,
        kwh=150, household_size=3, green_share=0.0,
        streaming=10, gaming=5, cloud_gb=50,
        shopping="Moderate", waste="Moderate",
    )
    breakdown, total, score, band, food_detail = full_breakdown(inputs)
    assert set(breakdown.keys()) == {"Transport", "Food", "Electricity", "Digital", "Shopping & Waste"}
    assert total == round(sum(breakdown.values()), 2)
    assert 0 <= score <= 100
    assert isinstance(food_detail, dict)

def test_full_breakdown_total_non_negative():
    inputs = dict(
        mode="Walk / Cycle", daily_km=0, days_per_week=0, occupancy=1,
        short_flights=0, long_flights=0, domestic_flights=0,
        diet_profile="Vegan", diet_multiplier=0.7,
        kwh=30, household_size=8, green_share=0.5,
        streaming=0, gaming=0, cloud_gb=0,
        shopping="Low", waste="Low",
    )
    _, total, _, _, _ = full_breakdown(inputs)
    assert total >= 0


# ── Generate actions ─────────────────────────────────────────────────

def test_generate_actions_returns_list():
    breakdown = {"Transport": 100, "Food": 80, "Electricity": 40, "Digital": 10, "Shopping & Waste": 20}
    actions = generate_actions(breakdown, 250)
    assert isinstance(actions, list)
    assert len(actions) > 0

def test_generate_actions_saving_non_negative():
    breakdown = {"Transport": 120, "Food": 90, "Electricity": 50, "Digital": 15, "Shopping & Waste": 25}
    for a in generate_actions(breakdown, 300):
        assert a["saving_kg"] >= 0
