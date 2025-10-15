# utils/ui_helpers.py
import streamlit as st
from utils.recipe_matcher import adjust_servings

def show_recipe_card(recipe, servings=2, rating=None, is_fav=False):
    st.header(f"{recipe['name']}  {'⭐'*int(rating) if rating else ''}")
    st.write(f"**Match:** {recipe.get('match_score', '—')}%  •  **Time:** {recipe.get('time_min', '—')} min  •  **Difficulty:** {recipe.get('difficulty','—')}")
    st.write(f"**Diet:** {', '.join(recipe.get('diet',[])) or 'Any'}")
    st.write(f"**Calories:** {recipe.get('calories', 'N/A')} kcal • **Protein:** {recipe.get('protein', 'N/A')} g")
    st.subheader("Ingredients")
    scaled = adjust_servings(recipe, servings)
    for ing in scaled:
        st.write(f"- {ing}")
    st.subheader("Steps")
    for i, s in enumerate(recipe.get("steps", []), start=1):
        st.write(f"{i}. {s}")
    if is_fav:
        st.info("★ Favorited")
