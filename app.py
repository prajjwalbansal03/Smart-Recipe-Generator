import streamlit as st
import json
import pandas as pd
from pathlib import Path
from utils.recipe_matcher import find_matching_recipes, adjust_servings
from utils.ui_helpers import show_recipe_card
from utils.ingredient_recognition import recognize_ingredients_from_image

# -------------------------------
# Paths and setup
# -------------------------------
BASE_DIR = Path(__file__).parent
DATA_PATH = BASE_DIR / "data" / "recipes.json"
RATINGS_CSV = BASE_DIR / "data" / "ratings.csv"
FAV_CSV = BASE_DIR / "data" / "favorites.csv"

st.set_page_config(page_title="Smart Recipe Generator", layout="centered")

# -------------------------------
# Helper functions for persistence
# -------------------------------
def ensure_csv(path, cols):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        df = pd.DataFrame(columns=cols)
        df.to_csv(path, index=False)

def load_csv(path):
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)

def save_rating(recipe_id, rating):
    ensure_csv(RATINGS_CSV, ["recipe_id", "rating"])
    df = load_csv(RATINGS_CSV)
    df = df[df["recipe_id"] != recipe_id]
    df = pd.concat([df, pd.DataFrame([[recipe_id, rating]], columns=["recipe_id", "rating"])], ignore_index=True)
    df.to_csv(RATINGS_CSV, index=False)

def save_favorite(recipe_id):
    ensure_csv(FAV_CSV, ["recipe_id"])
    df = load_csv(FAV_CSV)
    if recipe_id not in df["recipe_id"].astype(str).values:
        df = pd.concat([df, pd.DataFrame([[recipe_id]], columns=["recipe_id"])], ignore_index=True)
        df.to_csv(FAV_CSV, index=False)

def remove_favorite(recipe_id):
    ensure_csv(FAV_CSV, ["recipe_id"])
    df = load_csv(FAV_CSV)
    df = df[df["recipe_id"].astype(str) != recipe_id]
    df.to_csv(FAV_CSV, index=False)

# -------------------------------
# Load recipes
# -------------------------------
@st.cache_data
def load_recipes():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

recipes = load_recipes()

# -------------------------------
# Initialize session state
# -------------------------------
if "ratings" not in st.session_state:
    ensure_csv(RATINGS_CSV, ["recipe_id", "rating"])
    df_r = load_csv(RATINGS_CSV)
    st.session_state["ratings"] = {str(r): int(v) for r, v in zip(df_r.get("recipe_id", []), df_r.get("rating", []))}

if "favorites" not in st.session_state:
    ensure_csv(FAV_CSV, ["recipe_id"])
    df_f = load_csv(FAV_CSV)
    st.session_state["favorites"] = set(df_f.get("recipe_id", []).astype(str).tolist())

if "ingredients" not in st.session_state:
    st.session_state["ingredients"] = []

if "fav_toggle" not in st.session_state:
    st.session_state["fav_toggle"] = {}

# -------------------------------
# Sidebar filters
# -------------------------------
st.sidebar.header("Filters & Options")
diet = st.sidebar.selectbox("Dietary Preference", ["Any", "Vegetarian", "Vegan", "Gluten-Free"])
max_time = st.sidebar.slider("Max Cooking Time (minutes)", 5, 180, 60)
difficulty = st.sidebar.multiselect("Difficulty", ["Easy", "Medium", "Hard"], default=["Easy", "Medium", "Hard"])

# -------------------------------
# Ingredient Input Section
# -------------------------------
st.title("🍳 Smart Recipe Generator")
st.write("Enter ingredients manually or upload multiple images — the app remembers all of them!")

mode = st.radio("Ingredient Input Mode", ["Text", "Image"])

def add_unique_items(existing, new_items):
    for item in new_items:
        if item not in existing:
            existing.append(item)
    return existing

if mode == "Text":
    raw = st.text_input("Enter ingredients (comma-separated)", placeholder="e.g. tomato, onion, milk")
    if raw:
        added = [x.strip().lower() for x in raw.split(",") if x.strip()]
        st.session_state["ingredients"] = add_unique_items(st.session_state["ingredients"], added)
        st.success(f"Added: {', '.join(added)}")

else:
    uploaded = st.file_uploader(
        "Upload ingredient image(s)", type=["jpg", "jpeg", "png"], accept_multiple_files=True
    )
    if uploaded:
        for img in uploaded:
            st.image(img, use_column_width=True)
            with st.spinner(f"Recognizing ingredients from {img.name}..."):
                detected = recognize_ingredients_from_image(img)
                if detected:
                    st.session_state["ingredients"] = add_unique_items(st.session_state["ingredients"], detected)
                    st.success(f"Detected and added: {', '.join(detected)}")
                else:
                    st.warning(f"No recognizable ingredients found in {img.name}.")

# Show all stored ingredients
if st.session_state["ingredients"]:
    st.markdown("**🧺 Current ingredients:**")
    st.markdown(" | ".join(f"`{i}`" for i in st.session_state["ingredients"]))
    if st.button("🧹 Clear all ingredients"):
        st.session_state["ingredients"] = []
        st.success("Ingredient list cleared!")

servings = st.number_input("Desired Servings", 1, 10, 2)
st.divider()

# -------------------------------
# Recipe Matching and Display
# -------------------------------
if st.button("🔍 Find Recipes"):
    ingredients = st.session_state["ingredients"]
    if not ingredients:
        st.warning("Please add ingredients first.")
    else:
        with st.spinner("Finding best recipes..."):
            matched = find_matching_recipes(ingredients, recipes, diet=diet, max_time=max_time, difficulties=difficulty)

        if not matched:
            st.info("No matching recipes found. Try different filters or add more ingredients.")
        else:
            st.success(f"Found {len(matched)} matching recipe(s)!")

            for recipe in matched:
                st.divider()
                rid = str(recipe["id"])
                current_rating = st.session_state["ratings"].get(rid)

                # Initialize favorite toggle state if not exists
                if rid not in st.session_state["fav_toggle"]:
                    st.session_state["fav_toggle"][rid] = rid in st.session_state["favorites"]

                # Show recipe
                show_recipe_card(recipe, servings, current_rating, st.session_state["fav_toggle"][rid])

                # Rating and Favorites
                c1, c2, c3 = st.columns([1, 1, 1])
                with c1:
                    rating = st.selectbox(
                        "⭐ Rate (1–5)", [0, 1, 2, 3, 4, 5],
                        key=f"rate_{rid}", index=current_rating or 0
                    )
                with c2:
                    if st.button("💾 Save Rating", key=f"save_{rid}"):
                        if rating == 0:
                            st.warning("Select a rating first.")
                        else:
                            save_rating(rid, rating)
                            st.session_state["ratings"][rid] = rating
                            st.success("✅ Rating saved!")

                with c3:
                    fav_label = "💖 Remove Favorite" if st.session_state["fav_toggle"][rid] else "♡ Add to Favorites"
                    if st.button(fav_label, key=f"fav_{rid}"):
                        if st.session_state["fav_toggle"][rid]:
                            remove_favorite(rid)
                            st.session_state["favorites"].remove(rid)
                            st.session_state["fav_toggle"][rid] = False
                            st.success("❌ Removed from favorites")
                        else:
                            save_favorite(rid)
                            st.session_state["favorites"].add(rid)
                            st.session_state["fav_toggle"][rid] = True
                            st.success("💖 Added to favorites")

st.divider()

# -------------------------------
# Favorites Section
# -------------------------------
st.subheader("💾 My Favorite Recipes")
if st.button("Show Favorites"):
    favs = st.session_state["favorites"]
    if not favs:
        st.info("No favorites yet.")
    else:
        fav_recipes = [r for r in recipes if str(r["id"]) in favs]
        for r in fav_recipes:
            rid = str(r["id"])
            show_recipe_card(r, servings=2, rating=st.session_state["ratings"].get(rid), is_fav=True)

st.caption("Made By PRAJJWAL BANSAL")
