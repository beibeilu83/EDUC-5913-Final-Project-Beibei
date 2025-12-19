import streamlit as st
import pandas as pd
import json
import plotly.graph_objects as go
import re, difflib, datetime
import os


# --- CONFIGURATION ---
st.set_page_config(
    page_title="PawPal Tracker",
    page_icon="🐶",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- STYLING ---
st.markdown("""
    <style>
    .stProgress > div > div > div > div {
        background-color: #f5569B;
    }
    .warning-box {
        padding: 1rem;
        background-color: #ffcccc;
        border-radius: 0.5rem;
        border: 1px solid #ff0000;
        color: #990000;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    .safe-box {
        padding: 1rem;
        background-color: #e6fffa;
        border-radius: 0.5rem;
        border: 1px solid #00cccc;
        color: #006666;
        margin-bottom: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)

# --- LOCAL DATABASE ---
# Format: "Food Name": {"calories": int, "unit": str, "is_toxic": bool, "warning": str}
FOOD_DATABASE = {
    # Proteins (Cooked/Plain)
    "Boiled Chicken Breast": {"calories": 165, "unit": "cup", "is_toxic": False},
    "Lean Ground Beef (Cooked)": {"calories": 332, "unit": "cup", "is_toxic": False},
    "Turkey (Cooked, no skin)": {"calories": 238, "unit": "cup", "is_toxic": False},
    "Salmon (Cooked)": {"calories": 233, "unit": "fillet (3oz)", "is_toxic": False},
    "Tuna (Canned in water)": {"calories": 100, "unit": "can (3oz)", "is_toxic": False},
    "Pork Loin (Cooked)": {"calories": 180, "unit": "chop (3oz)", "is_toxic": False},
    "Hard Boiled Egg": {"calories": 70, "unit": "large egg", "is_toxic": False},
    "Scrambled Egg (Plain)": {"calories": 90, "unit": "large egg", "is_toxic": False},
    "Chicken Thigh (Cooked, no skin)": {"calories": 210, "unit": "cup", "is_toxic": False},
    "Turkey Mince (Cooked, lean)": {"calories": 220, "unit": "cup", "is_toxic": False},
    "White Fish (Cooked, plain)": {"calories": 140, "unit": "fillet (3oz)", "is_toxic": False},
    "Plain Tofu (Firm, cooked)": {"calories": 180, "unit": "cup", "is_toxic": False},


    # Grains & Carbs
    "White Rice (Cooked)": {"calories": 200, "unit": "cup", "is_toxic": False},
    "Brown Rice (Cooked)": {"calories": 216, "unit": "cup", "is_toxic": False},
    "Oatmeal (Plain, Cooked)": {"calories": 150, "unit": "cup", "is_toxic": False},
    "Sweet Potato (Boiled/Baked)": {"calories": 114, "unit": "cup", "is_toxic": False},
    "Potato (Boiled, no skin)": {"calories": 130, "unit": "medium potato", "is_toxic": False},
    "Pasta (Plain, Cooked)": {"calories": 200, "unit": "cup", "is_toxic": False},
    "Bread (White/Wheat)": {"calories": 70, "unit": "slice", "is_toxic": False},
    "Quinoa (Cooked)": {"calories": 222, "unit": "cup", "is_toxic": False},
    "Barley (Cooked)": {"calories": 193, "unit": "cup", "is_toxic": False},
    "Whole Wheat Pasta (Cooked)": {"calories": 174, "unit": "cup", "is_toxic": False},

    # Fruits
    "Apple (no seeds/core)": {"calories": 10, "unit": "slice", "is_toxic": False},
    "Banana": {"calories": 105, "unit": "medium banana", "is_toxic": False},
    "Blueberries": {"calories": 85, "unit": "cup", "is_toxic": False},
    "Strawberries": {"calories": 4, "unit": "medium berry", "is_toxic": False},
    "Watermelon (seedless)": {"calories": 45, "unit": "cup", "is_toxic": False},
    "Cantaloupe": {"calories": 50, "unit": "cup", "is_toxic": False},
    "Mango (no pit)": {"calories": 99, "unit": "cup", "is_toxic": False},
    "Pineapple (fresh)": {"calories": 80, "unit": "cup", "is_toxic": False},
    "Pear (no seeds/core)": {"calories": 96, "unit": "medium pear", "is_toxic": False},
    "Raspberries": {"calories": 64, "unit": "cup", "is_toxic": False},
    "Blackberries": {"calories": 62, "unit": "cup", "is_toxic": False},
    "Peach (no pit)": {"calories": 60, "unit": "medium peach", "is_toxic": False},

    # Vegetables
    "Carrot (Raw)": {"calories": 25, "unit": "medium carrot", "is_toxic": False},
    "Green Beans (Plain)": {"calories": 30, "unit": "cup", "is_toxic": False},
    "Broccoli (Steamed)": {"calories": 55, "unit": "cup", "is_toxic": False},
    "Cucumber": {"calories": 15, "unit": "cup", "is_toxic": False},
    "Zucchini": {"calories": 20, "unit": "cup", "is_toxic": False},
    "Spinach (Cooked)": {"calories": 40, "unit": "cup", "is_toxic": False},
    "Peas (Green)": {"calories": 117, "unit": "cup", "is_toxic": False},
    "Pumpkin (Pure canned)": {"calories": 50, "unit": "cup", "is_toxic": False},
    "Bell Pepper (Red/Yellow)": {"calories": 45, "unit": "cup", "is_toxic": False},
    "Celery": {"calories": 10, "unit": "stalk", "is_toxic": False},
    "Lettuce (Romaine/Iceberg)": {"calories": 8, "unit": "cup", "is_toxic": False},

    # Dairy & Others
    "Cheddar Cheese": {"calories": 110, "unit": "slice", "is_toxic": False},
    "Yogurt (Plain Greek)": {"calories": 120, "unit": "cup", "is_toxic": False},
    "Peanut Butter (Xylitol-free)": {"calories": 95, "unit": "tbsp", "is_toxic": False},
    "Salmon Oil": {"calories": 40, "unit": "tsp", "is_toxic": False},
    "Coconut Oil": {"calories": 120, "unit": "tbsp", "is_toxic": False},
    "Cottage Cheese (Low-Fat)": {"calories": 80, "unit": "1/2 cup", "is_toxic": False},
    "Mozzarella Cheese (Part-skim)": {"calories": 85, "unit": "1 oz", "is_toxic": False},
    "Bone Broth (No onion/garlic)": {"calories": 15, "unit": "1/2 cup", "is_toxic": False},

    # Commercial Food (Generic)
    "Dry Kibble (Standard)": {"calories": 350, "unit": "cup", "is_toxic": False},
    "Dry Kibble (High Protein)": {"calories": 450, "unit": "cup", "is_toxic": False},
    "Dry Kibble (Weight Mgmt)": {"calories": 250, "unit": "cup", "is_toxic": False},
    "Wet Canned Food (Standard)": {"calories": 95, "unit": "3 oz can", "is_toxic": False},
    "Dog Biscuit (Small)": {"calories": 20, "unit": "biscuit", "is_toxic": False},
    "Dog Biscuit (Large)": {"calories": 90, "unit": "biscuit", "is_toxic": False},
    "Dental Stick (Medium)": {"calories": 50, "unit": "stick", "is_toxic": False},
    "Bully Stick (6 inch)": {"calories": 88, "unit": "stick", "is_toxic": False},
    "Freeze-Dried Raw Bites": {"calories": 55, "unit": "1/4 cup", "is_toxic": False},
    "Training Treat (Small)": {"calories": 3, "unit": "treat", "is_toxic": False},

    # Toxic / Dangerous
    "Chocolate (Milk)": {"calories": 0, "unit": "any amount", "is_toxic": True, "warning": "Contains Theobromine. Highly toxic."},
    "Chocolate (Dark/Baking)": {"calories": 0, "unit": "any amount", "is_toxic": True, "warning": "EXTREMELY TOXIC even in small amounts."},
    "Grapes/Raisins": {"calories": 0, "unit": "any amount", "is_toxic": True, "warning": "Can cause rapid kidney failure."},
    "Onion": {"calories": 0, "unit": "any amount", "is_toxic": True, "warning": "Causes anemia (red blood cell damage)."},
    "Garlic": {"calories": 0, "unit": "any amount", "is_toxic": True, "warning": "More potent than onion. Toxic to blood cells."},
    "Xylitol (Gum/Candy)": {"calories": 0, "unit": "any amount", "is_toxic": True, "warning": "Causes liver failure and hypoglycemia."},
    "Macadamia Nuts": {"calories": 0, "unit": "any amount", "is_toxic": True, "warning": "Causes weakness, tremors, and paralysis."},
    "Avocado (Skin/Pit)": {"calories": 0, "unit": "any amount", "is_toxic": True, "warning": "Contains persin. Can cause vomiting/diarrhea."},
    "Alcohol": {"calories": 0, "unit": "any amount", "is_toxic": True, "warning": "Causes intoxication, coma, and death."},
    "Coffee/Caffeine": {"calories": 0, "unit": "any amount", "is_toxic": True, "warning": "Causes heart palpitations and seizures."},
    "Yeast Dough": {"calories": 0, "unit": "any amount", "is_toxic": True, "warning": "Expands in stomach; alcohol poisoning risk."},
    "Cooked Bones": {"calories": 0, "unit": "any amount", "is_toxic": True, "warning": "Splinter hazard. Can puncture gut."},
}

# --- CATEGORY MAP FOR DROPDOWN FILTERING ---
FOOD_CATEGORY_MAP = {
    "Proteins (Cooked/Plain)": [
        "Boiled Chicken Breast",
        "Lean Ground Beef (Cooked)",
        "Turkey (Cooked, no skin)",
        "Salmon (Cooked)",
        "Tuna (Canned in water)",
        "Pork Loin (Cooked)",
        "Hard Boiled Egg",
        "Scrambled Egg (Plain)",
        "Chicken Thigh (Cooked, no skin)",
        "Turkey Mince (Cooked, lean)",
        "White Fish (Cooked, plain)",
        "Plain Tofu (Firm, cooked)",
    ],
    "Grains & Carbs": [
        "White Rice (Cooked)",
        "Brown Rice (Cooked)",
        "Oatmeal (Plain, Cooked)",
        "Sweet Potato (Boiled/Baked)",
        "Potato (Boiled, no skin)",
        "Pasta (Plain, Cooked)",
        "Bread (White/Wheat)",
        "Quinoa (Cooked)",
        "Barley (Cooked)",
        "Whole Wheat Pasta (Cooked)",
    ],
    "Fruits": [
        "Apple (no seeds/core)",
        "Banana",
        "Blueberries",
        "Strawberries",
        "Watermelon (seedless)",
        "Cantaloupe",
        "Mango (no pit)",
        "Pineapple (fresh)",
        "Pear (no seeds/core)",
        "Raspberries",
        "Blackberries",
        "Peach (no pit)",
    ],
    "Vegetables": [
        "Carrot (Raw)",
        "Green Beans (Plain)",
        "Broccoli (Steamed)",
        "Cucumber",
        "Zucchini",
        "Spinach (Cooked)",
        "Peas (Green)",
        "Pumpkin (Pure canned)",
        "Bell Pepper (Red/Yellow)",
        "Celery",
        "Lettuce (Romaine/Iceberg)",
    ],
    "Dairy & Others": [
        "Cheddar Cheese",
        "Yogurt (Plain Greek)",
        "Peanut Butter (Xylitol-free)",
        "Salmon Oil",
        "Coconut Oil",
        "Cottage Cheese (Low-Fat)",
        "Mozzarella Cheese (Part-skim)",
        "Bone Broth (No onion/garlic)",
    ],
    "Commercial Food (Generic)": [
        "Dry Kibble (Standard)",
        "Dry Kibble (High Protein)",
        "Dry Kibble (Weight Mgmt)",
        "Wet Canned Food (Standard)",
        "Dog Biscuit (Small)",
        "Dog Biscuit (Large)",
        "Dental Stick (Medium)",
        "Bully Stick (6 inch)",
        "Freeze-Dried Raw Bites",
        "Training Treat (Small)",
    ],
}


# Simple dangerous keyword detection (for user-typed foods NOT in DB)
DANGEROUS_KEYWORDS = {
    "chocolate": "Chocolate (milk, dark, baking) is toxic to dogs.",
    "cocoa": "Cocoa/chocolate products are toxic to dogs.",
    "grape": "Grapes and raisins can cause kidney failure in dogs.",
    "grapes": "Grapes and raisins can cause kidney failure in dogs.",
    "raisin": "Grapes and raisins can cause kidney failure in dogs.",
    "raisins": "Grapes and raisins can cause kidney failure in dogs.",
    "onion": "Onions can damage red blood cells and cause anemia.",
    "garlic": "Garlic is more potent than onion and is toxic to dogs.",
    "xylitol": "Xylitol (sweetener) can cause hypoglycemia and liver failure.",
    "macadamia": "Macadamia nuts can cause weakness and tremors.",
    "avocado": "Avocado (especially skin/pit) can cause vomiting/diarrhea.",
    "alcohol": "Alcohol can cause intoxication, coma, and death in dogs.",
    "beer": "Alcohol (beer, wine, spirits) is dangerous for dogs.",
    "wine": "Alcohol (beer, wine, spirits) is dangerous for dogs.",
    "coffee": "Coffee/caffeine can cause heart problems and seizures.",
    "caffeine": "Caffeine can cause heart problems and seizures.",
    "espresso": "Caffeine can cause heart problems and seizures.",
    "yeast dough": "Yeast dough can expand and cause bloat and alcohol poisoning.",
    "cooked bones": "Cooked bones can splinter and puncture the gut.",
    "chicken bones": "Cooked bones can splinter and puncture the gut.",
}

_QTY_RE = re.compile(
    r"""(?P<num>\d+(\.\d+)?|\d+/\d+|\d+\s+\d+/\d+|\.\d+)\s*
        (?P<unit>kg|g|gram|grams|cup|cups|tbsp|tablespoon|tsp|teaspoon|oz|ounce|ounces|piece|pieces|slice|slices|egg|eggs|can|cans|biscuit|biscuits|stick|sticks|banana|bananas|potato|potatoes|carrot|carrots)?""",
    re.IGNORECASE | re.VERBOSE,
)

def detect_dangerous_keywords(text: str) -> list[str]:
    text_l = text.lower()
    hits = []
    for key, msg in DANGEROUS_KEYWORDS.items():
        if key in text_l:
            hits.append(msg)
    return list(dict.fromkeys(hits))  # dedupe while preserving order

def _parse_mixed_number(s: str) -> float:
    s = s.strip()
    if " " in s and "/" in s:
        a, b = s.split(" ", 1)
        n, d = b.split("/", 1)
        return float(a) + float(n) / float(d)
    if "/" in s:
        n, d = s.split("/", 1)
        return float(n) / float(d)
    return float(s)

def _canonicalize_unit(u: str | None) -> str | None:
    if not u:
        return None
    u = u.lower()
    # normalize some common words to more generic units
    mapping = {
        "gram": "g", "grams": "g",
        "ounce": "oz", "ounces": "oz",
        "tablespoon": "tbsp", "teaspoon": "tsp",
        "cup": "cup", "cups": "cup",
        "piece": "piece", "pieces": "piece",
        "slice": "slice", "slices": "slice",
        "egg": "egg", "eggs": "egg",
        "can": "can", "cans": "can",
        "biscuit": "biscuit", "biscuits": "biscuit",
        "stick": "stick", "sticks": "stick",
        "banana": "banana", "bananas": "banana",
        "potato": "potato", "potatoes": "potato",
        "carrot": "carrot", "carrots": "carrot",
    }
    return mapping.get(u, u)

def _best_food_match(name: str, food_names: list[str]) -> str | None:
    nm = name.strip().lower()
    if not nm:
        return None
    # exact lower match
    lower_map = {fn.lower(): fn for fn in food_names}
    if nm in lower_map:
        return lower_map[nm]
    # contains/contained
    for fn in food_names:
        if nm in fn.lower() or fn.lower() in nm:
            return fn
    # fuzzy match
    candidates = difflib.get_close_matches(name, food_names, n=1, cutoff=0.6)
    return candidates[0] if candidates else None

def _parse_item_fragment(fragment: str) -> tuple[float, str | None, str]:
    s = fragment.strip()
    m = _QTY_RE.search(s)
    if not m:
        return 1.0, None, s  # default to 1 unit
    num_str = m.group("num")
    unit = _canonicalize_unit(m.group("unit"))
    qty = _parse_mixed_number(num_str)

    name_guess = (s[:m.start()] + s[m.end():]).strip()
    name_guess = re.sub(r"\b(of|and|with|the|a)\b", " ", name_guess, flags=re.IGNORECASE)
    name_guess = re.sub(r"\s+", " ", name_guess).strip()
    return qty, unit, name_guess

def _convert_quantity_if_needed(qty: float, typed_unit: str | None, db_unit: str) -> tuple[float, list[str]]:
    notes = []
    tu = typed_unit or db_unit
    # If identical or very similar, just use qty as DB units
    if tu == db_unit or tu in db_unit.lower() or db_unit.lower() in tu:
        return qty, notes

    # Sample generic conversions (extend as needed)
    if db_unit == "g" and tu in {"kg", "oz"}:
        if tu == "kg":
            return qty * 1000.0, notes
        if tu == "oz":
            return qty * 28.3495, notes
    if db_unit == "cup" and tu in {"tbsp", "tsp"}:
        if tu == "tbsp":
            return qty / 16.0, notes
        if tu == "tsp":
            return qty / 48.0, notes

    # For slice/piece/egg/biscuit/stick, just treat them as a count
    if db_unit in {"slice", "biscuit", "stick", "large egg", "medium banana", "medium potato", "medium carrot", "medium peach", "medium pear"}:
        return qty, notes

    notes.append(f"Couldn’t reliably convert from '{tu}' to '{db_unit}'. Using quantity as {qty} {db_unit}(s).")
    return qty, notes

def estimate_from_text(input_text: str, FOOD_DATABASE: dict) -> dict:
    """
    Parse free text like:
        '1 cup boiled chicken breast + 1 tbsp peanut butter, 120 g white rice'
    and return items + total kcal.
    """
    results = {
        "items": [],
        "total_kcal": 0.0,
        "toxicity": [],
        "messages": [],
        "unmatched": [],
    }

    fragments = [p for p in re.split(r"[+,]", input_text) if p.strip()]
    food_names = list(FOOD_DATABASE.keys())

    for frag in fragments:
        qty_typed, unit_typed, name_guess = _parse_item_fragment(frag)
        matched = _best_food_match(name_guess, food_names)
        if not matched:
            results["unmatched"].append(name_guess or frag.strip())
            continue

        details = FOOD_DATABASE[matched]
        db_unit = details["unit"]
        per_unit_kcal = float(details["calories"])
        is_toxic = bool(details.get("is_toxic", False))
        if is_toxic:
            warn = details.get("warning", f"{matched} is marked as toxic to dogs.")
            results["toxicity"].append(f"⚠️ {warn}")

        tu = unit_typed or db_unit
        adj_qty, notes = _convert_quantity_if_needed(qty_typed, tu, db_unit)
        results["messages"].extend(notes)

        kcal = per_unit_kcal * adj_qty
        results["total_kcal"] += kcal

        results["items"].append({
            "name_input": frag.strip(),
            "qty_typed": qty_typed,
            "unit_typed": tu,
            "name_matched": matched,
            "qty_db_units": adj_qty,
            "unit_db": db_unit,
            "kcal_each": kcal,
        })

    return results

# --- STATE MANAGEMENT ---
if 'food_logs' not in st.session_state:
    st.session_state.food_logs = []
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'dog_profile' not in st.session_state:
    st.session_state.dog_profile = {
        "name": "Duoduo",
        "weight_kg": 25.0,
        "dog_breed": "Golden Retriver", 
        "activity_level": 1.6 # Default active
    }

# --- HELPER FUNCTIONS ---

def calculate_mer(weight, factor):
    """Calculates Maintenance Energy Requirement (MER)"""
    # RER = 70 * (weight_kg ^ 0.75)
    rer = 70 * (weight ** 0.75)
    return int(rer * factor)

def get_vet_advice(openrouter_api_key: str, question: str, dog_profile: dict) -> str:
    """
    Call DeepSeek via OpenRouter using HTTP requests.
    """

    if not openrouter_api_key:
        return "API key missing. Please add your OpenRouter API key."

    import requests

    # Build dog profile context
    name = dog_profile.get("name", "the dog")
    weight = dog_profile.get("weight", None)
    age = dog_profile.get("age", None)
    activity = dog_profile.get("activity_level", None)

    profile_bits = [f"Name: {name}"]
    if weight:
        profile_bits.append(f"Weight: {weight} kg")
    if age:
        profile_bits.append(f"Age: {age}")
    if activity:
        profile_bits.append(f"Activity level: {activity}")
    profile_str = "; ".join(profile_bits)

    system_prompt = (
        "You are a cautious canine nutrition assistant.\n"
        "You answer questions about safe/unsafe foods, calories, and general dog nutrition.\n"
        "You do NOT provide medical diagnoses. For emergencies or serious symptoms, "
        "always tell the user to contact a veterinarian immediately.\n"
        f"Dog profile: {profile_str}\n"
    )

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {openrouter_api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": "deepseek/deepseek-r1-0528:free",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=body, timeout=30)
        response.raise_for_status()

        data = response.json()
        return data["choices"][0]["message"]["content"].strip()

    except Exception as e:
        return f"Error contacting DeepSeek: {e}"



# --- SIDEBAR SETTINGS ---
with st.sidebar:
    st.header("⚙️ Settings")

    # Initialize once in session_state
    if "openrouter_api_key" not in st.session_state:
        st.session_state.openrouter_api_key = os.getenv("OPENROUTER_API_KEY", "")

    st.session_state.openrouter_api_key = st.text_input(
        "OpenRouter API Key (for DeepSeek via OpenRouter)",
        type="password",
        value=st.session_state.openrouter_api_key,
        help="Get your key at https://openrouter.ai/settings/keys",
    )
    #dog profile sidebar
    st.divider()
    st.subheader("🐕 Dog Profile")
    
    dog_name = st.text_input("Duoduo", value=st.session_state.dog_profile["name"])
    weight = st.number_input("Weight (kg)", value=st.session_state.dog_profile["weight_kg"], step=0.5)
    
    activity_options = {
        "Neutered/Spayed (Normal)": 1.6,
        "Intact (Normal)": 1.8,
        "Inactive/Obese prone": 1.2,
        "Weight Loss Goal": 1.0,
        "Highly Active/Working": 2.0,
        "Puppy (<4 months)": 3.0
    }
    
    activity_key = st.selectbox(
        "Life Stage / Activity", 
        options=list(activity_options.keys()),
        index=0
    )
    
    # Update Session State
    st.session_state.dog_profile["name"] = dog_name
    st.session_state.dog_profile["weight_kg"] = weight
    st.session_state.dog_profile["activity_level"] = activity_options[activity_key]
    
    # Calculate Goal
    daily_goal = calculate_mer(weight, activity_options[activity_key])
    st.metric(label="Daily Calorie Goal", value=f"{daily_goal} kcal")
    
    if st.button("Clear Data"):
        st.session_state.food_logs = []
        st.session_state.chat_history = []
        st.rerun()

# --- CALCULATE DAILY GOAL (MER) ---
weight = st.session_state.dog_profile.get("weight", 0)

if weight > 0:
    # RER formula
    rer = 70 * (weight ** 0.75)

    # Activity multiplier
    activity = st.session_state.dog_profile.get("activity_level", "normal")

    if activity == "low":
        multiplier = 1.2
    elif activity == "moderate":
        multiplier = 1.6
    elif activity == "high":
        multiplier = 2.0
    elif activity == "very_high":
        multiplier = 3.0
    else:
        multiplier = 1.6  # default

    daily_goal = int(rer * multiplier)

else:
    daily_goal = 0


# --- MAIN PAGE ---

st.title(f"🐶 PawPal: {st.session_state.dog_profile['name']}'s Tracker")

# Tabs for different functions
tab1, tab2, tab3 = st.tabs(["📊 Daily Dashboard", "🍖 Add Food (Local DB)", "🩺 Ask the Vet"])

# --- TAB 1: DASHBOARD ---
with tab1:
    # Filter logs for today
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    todays_logs = [log for log in st.session_state.food_logs if log['date'] == today_str]
    
    consumed_today = sum(log['calories'] for log in todays_logs)
    remaining = daily_goal - consumed_today
    
    # Progress Bar Logic
    col1, col2, col3 = st.columns(3)
    col1.metric("Consumed", f"{consumed_today} kcal")
    col2.metric("Goal", f"{daily_goal} kcal")
    col3.metric("Remaining", f"{remaining} kcal", delta_color="normal" if remaining > 0 else "inverse")
    
    progress = min(consumed_today / daily_goal, 1.0) if daily_goal > 0 else 0

    
    # Custom Progress Bar Color
    bar_color = "green"
    if progress > 1.0: bar_color = "red"
    elif progress > 0.9: bar_color = "orange"
    
    st.progress(progress)
    
    # Visual Chart
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = consumed_today,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Daily Intake"},
        gauge = {
            'axis': {'range': [None, daily_goal * 1.2]},
            'bar': {'color': bar_color},
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': daily_goal
            }
        }
    ))
    fig.update_layout(height=300)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("📝 Today's Logs")
    if todays_logs:
        df = pd.DataFrame(todays_logs)
        st.dataframe(df[['time', 'food', 'quantity', 'calories']], use_container_width=True)
    else:
        st.info("No food logged yet today.")


# --- TAB 2: ADD FOOD (CATEGORIES + FREE TEXT) ---
with tab2:
    st.header("Log a Meal")

    col_left, col_right = st.columns(2)

    # ---------- LEFT: SELECT FROM DATABASE BY CATEGORY ----------
    with col_left:
        st.subheader("Select from database")
        st.caption("Choose a category, then a specific food item from your local database.")

        big_category = st.selectbox(
            "Food Category",
            list(FOOD_CATEGORY_MAP.keys()),
            key="category_select_tab2",
        )

        # Filter foods that actually exist in the DB
        category_foods = [
            f for f in FOOD_CATEGORY_MAP.get(big_category, [])
            if f in FOOD_DATABASE
        ]
        if not category_foods:
            st.warning("No foods found for this category in the database.")
        else:
            selected_food_name = st.selectbox(
                "Food Item",
                category_foods,
                key="food_item_select_tab2",
            )

            food_details = FOOD_DATABASE[selected_food_name]
            unit = food_details["unit"]
            calories_per_unit = food_details["calories"]

            quantity = st.number_input(
                f"Quantity (in {unit}s)",
                min_value=0.1,
                value=1.0,
                step=0.25,
                key="quantity_category_tab2",
            )
            st.info(f"Basis: {calories_per_unit} kcal per {unit}")

            log_selected = st.button("Log Selected Food", use_container_width=True)

            if log_selected:
                if food_details.get("is_toxic"):
                    st.markdown(
                        f"""
                        <div class="warning-box">
                            ⚠️ WARNING: TOXIC FOOD SELECTED!<br>
                            Food: {selected_food_name}<br>
                            Reason: {food_details.get('warning', 'Toxic to dogs.')}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    st.error("This item cannot be logged because it is toxic.")
                else:
                    total_calories = int(calories_per_unit * quantity)
                    st.markdown(
                        f"""
                        <div class="safe-box">
                            ✅ <b>{selected_food_name}</b><br>
                            Quantity: {quantity} {unit}(s)<br>
                            Total Calories: <b>{total_calories} kcal</b>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    new_log = {
                        "date": datetime.date.today().strftime("%Y-%m-%d"),
                        "time": datetime.datetime.now().strftime("%H:%M"),
                        "food": selected_food_name,
                        "quantity": f"{quantity} {unit}",
                        "calories": total_calories,
                    }
                    st.session_state.food_logs.append(new_log)
                    st.success("Meal logged successfully!")
                    st.rerun()

    # ---------- RIGHT: FREE-TEXT ENTRY ----------
    with col_right:
        st.subheader("Or type a food + quantity")
        st.caption("Example: `1 cup boiled chicken breast + 1 tbsp peanut butter`")

        user_text = st.text_area(
            "Food + quantity",
            height=120,
            placeholder="1 cup boiled chicken breast + 1 tbsp peanut butter, 1/2 cup white rice",
            key="free_text_tab2",
        )

        log_text = st.button("Estimate & Log Typed Meal", use_container_width=True)

        if log_text:
            if not user_text.strip():
                st.warning("Please enter at least one item.")
            else:
                # 1) Check for dangerous keywords (even if not in DB)
                danger_hits = detect_dangerous_keywords(user_text)
                if danger_hits:
                    st.markdown(
                        "<div class='warning-box'>⚠️ Potential dangerous food detected:<br>"
                        + "<br>".join(danger_hits) +
                        "</div>",
                        unsafe_allow_html=True,
                    )
                    st.error("This meal was NOT logged. Remove dangerous items and try again.")
                else:
                    # 2) Parse and estimate using local DB
                    parsed = estimate_from_text(user_text, FOOD_DATABASE)

                    if parsed["toxicity"]:
                        st.markdown(
                            "<div class='warning-box'>⚠️ Toxic item(s) found in your input:<br>"
                            + "<br>".join(parsed["toxicity"]) +
                            "</div>",
                            unsafe_allow_html=True,
                        )
                        st.error("This meal was NOT logged due to toxic items.")
                    elif not parsed["items"]:
                        st.error("No items matched your local database, so calories cannot be estimated.")
                        if parsed["unmatched"]:
                            st.info("Unrecognized inputs: " + ", ".join(parsed["unmatched"]))
                    else:
                        # Show breakdown
                        st.markdown("<div class='safe-box'>✅ Parsed items:</div>", unsafe_allow_html=True)
                        for it in parsed["items"]:
                            st.write(
                                f"- **{it['name_input']}** → *{it['name_matched']}* "
                                f"(~{it['qty_db_units']:.2f} {it['unit_db']}(s)) "
                                f"→ **{int(round(it['kcal_each']))} kcal**"
                            )

                        if parsed["messages"]:
                            for msg in parsed["messages"]:
                                st.caption(f"ℹ️ {msg}")

                        total_calories = int(round(parsed["total_kcal"]))
                        st.markdown(
                            f"<div class='safe-box'>Total Estimated Calories: <b>{total_calories} kcal</b></div>",
                            unsafe_allow_html=True,
                        )

                        # Log each parsed item into session_state
                        now_date = datetime.date.today().strftime("%Y-%m-%d")
                        now_time = datetime.datetime.now().strftime("%H:%M")
                        for it in parsed["items"]:
                            qty_str = f"{it['qty_db_units']:.2f} {it['unit_db']}"
                            new_log = {
                                "date": now_date,
                                "time": now_time,
                                "food": it["name_matched"],
                                "quantity": qty_str,
                                "calories": int(round(it["kcal_each"])),
                            }
                            st.session_state.food_logs.append(new_log)

                        st.success("Typed meal logged successfully!")
                        st.rerun()


# --- TAB 3: ASK THE VET / AI ASSISTANT ---
with tab3:
    st.header("🩺 Ask the AI Vet Assistant")
    st.caption("This is not a real veterinarian. For emergencies or serious concerns, contact a vet immediately.")

    # Show previous chat messages
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    prompt = st.chat_input("Ask about dog nutrition, safe foods, calories, etc...")

    if prompt:
        api_key = st.session_state.get("openrouter_api_key", "").strip()

        if not api_key:
            st.error("Please add your OpenRouter API key in the sidebar before asking a question.")
        else:
            # Add and display user message
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.write(prompt)

            # Get AI response
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    response = get_vet_advice(api_key, prompt, st.session_state.dog_profile)
                    st.write(response)

            # Save AI response
            st.session_state.chat_history.append({"role": "assistant", "content": response})

