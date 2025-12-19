# EDUC-5913-Final-Project-Beibei
This file contain the code and streamlit link of the final artifact, which is a dog calories tracker app can be used repeatedly. 

PawPal Tracker is a Streamlit app to help dog owners log meals, estimate calories from typed input, detect potentially toxic foods, and ask an AI assistant (via OpenRouter/DeepSeek) for guidance. The app stores logs in st.session_state and uses a local FOOD_DATABASE to estimate calories.

**Table of Contents**
1. Imports & Configuration
2. Data constants
3. Parsing helpers
4. Estimation core: estimate_from_text
5. State management
6. Vet assistant integration: get_vet_advice
7. Streamlit UI: Sidebar, Tabs (Dashboard, Add Food, Ask the Vet)

**1. Imports & Configuration**
  1. streamlit as st: Main UI framework.
  2. pandas as pd: Used to show tables (today's logs).
  3. from openai import OpenAI: Minimal client to call DeepSeek via OpenRouter.
  4. json: Present for potential usage.
  5. plotly.graph_objects as go: For the dashboard gauge.
  6. re, difflib, datetime, os: Utilities for parsing, fuzzy matching, date/time, and environment variables.
   
		 *Configuration:*
  1. st.set_page_config(...) sets title, icon, and layout for the Streamlit app.
  2. Custom CSS via st.markdown(..., unsafe_allow_html=True) styles progress bars and warning/safe boxes.


**2. Data constants**
  1. FOOD_DATABASE: maps food item names → metadata (calories, unit, is_toxic, optional warning). Units are human-readable (e.g., "cup", "slice", "tbsp"). Toxic items include is_toxic: True and a warning.
  2. FOOD_CATEGORY_MAP: groups DB keys into categories for the UI.
  3. DANGEROUS_KEYWORDS: substring → warning used to flag typed inputs not in DB.
Edge cases:
  1. Units vary (not normalized). Helper conversion logic uses heuristics and is partial.


**3. Parsing helpers**
These parse free-text entries to extract quantity, unit, and item name.
  1. _QTY_RE — regex for integers, decimals, fractions, mixed numbers, optional unit token.
  2. detect_dangerous_keywords(text: str) -> list[str] — finds dangerous substrings and returns deduped warnings.
  3. _parse_mixed_number(s: str) -> float — handles 1 1/2, 3/4, .5, etc.
  4. _canonicalize_unit(u: str | None) -> str | None — normalizes common unit words (tablespoon → tbsp).
  5. _best_food_match(name: str, food_names: list[str]) -> str | None — matching strategy: exact lowercase → substring → difflib fuzzy match. Returns DB key or None.
  6. _parse_item_fragment(fragment: str) -> tuple[float, str | None, str] — returns (qty, unit, guessed_name). Defaults to 1.0 if no qty found.
  7. [_convert_quantity_if_needed(qty: float, typed_unit: str | None, db_unit: str) -> tuple[float, list[str]]](http://vscodecontentref/23) — attempts simple conversions (kg↔g↔oz; tbsp/tsp↔cup) and otherwise returns qty with a conversion note.

*Limitations:*
  1. Conversion is heuristic and incomplete. Nonstandard units or ingredient-specific density conversions are not handled.


**4. Core: estimate_from_text(input_text: str, FOOD_DATABASE: dict) -> dict**
*Purpose:*
  1. Parse a free-text meal string (comma/plus-separated) and estimate calories.

     Inputs:
        input_text example: "1 cup boiled chicken breast + 1 tbsp peanut butter, 120 g white rice".
        FOOD_DATABASE: local mapping.
     
      Outputs (dict):
        items: parsed items with fields {name_input, qty_typed, unit_typed, name_matched, qty_db_units, unit_db, kcal_each}
        total_kcal: total calories (float)
        toxicity: toxicity warnings for matched toxic items
        messages: conversion/uncertainty notes
        unmatched: list of unrecognized fragments

*Algorithm summary:*
  1. Split on + or ,, parse fragments, match to DB, handle toxicity, convert units where possible, compute kcal.

*Edge cases:*
  1. No matches → items empty and unmatched populated.
  2. Toxic matches are returned in toxicity; UI prevents logging toxic items.

 
**5. Session State & Simple Helpers**
  1. Initializes st.session_state for food_logs, chat_history, and dog_profile.
  2. calculate_mer(weight, factor) computes Maintenance Energy Requirement (MER) using RER (70 * weight^0.75) scaled by factor.

 
**6. External API: get_vet_advice(api_key: str, question: str, dog_profile: dict) -> str**
  1. Wraps OpenAI client to call a DeepSeek model via OpenRouter.
  2. Builds a cautious system prompt including selected dog profile details.
  3. Returns assistant response or an error string.

     Notes:
        1. Requires an OpenRouter API key (sidebar or OPENROUTER_API_KEY env).
        2. Errors return a descriptive string displayed in UI.
        
**7. Streamlit UI**
  
	Structure:
    
		Sidebar: settings + dog profile inputs + API key field + Clear Data button.
    
		Main: Title + three tabs:
        1. Daily Dashboard (tab1): today's logs, progress bar, gauge, metrics.
        2. Add Food (tab2): left = select from DB categories; right = free-text entry parsed by estimate_from_text. Toxic detection blocks logging.
        3. Ask the Vet (tab3): chat interface using get_vet_advice, stores chat in session.
  
	Key behaviors:
    1. Category logging: toxic items show styled warning and are not logged.
    2. Free-text logging: danger keywords block logging; parsed items are shown with breakdown and logged into st.session_state.food_logs.
    3. Chat messages preserved in st.session_state.chat_history.

