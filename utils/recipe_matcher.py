# utils/recipe_matcher.py
from rapidfuzz import fuzz
import math

def recipe_score(available, recipe):
    """
    score based on ingredient coverage. Returns percentage (0-100).
    """
    avail_set = set([a.lower() for a in available])
    req = [ing.lower() for ing in recipe.get("ingredients", [])]
    matched = sum(1 for r in req if any(fuzz.partial_ratio(r, a) > 80 for a in avail_set))
    if not req:
        return 0
    return int(100 * matched / len(req))

def find_matching_recipes(available_ings, recipes, diet="Any", max_time=9999, difficulties=None, min_score=30):
    available_ings = [i.lower() for i in available_ings]
    difficulties = difficulties or ["Easy", "Medium", "Hard"]
    scored = []
    for r in recipes:
        if diet != "Any" and diet.lower() not in [d.lower() for d in r.get("diet", [])]:
            continue
        if r.get("time_min", 9999) > max_time:
            continue
        if r.get("difficulty") not in difficulties:
            continue
        score = recipe_score(available_ings, r)
        if score >= min_score:
            r = r.copy()
            r["match_score"] = score
            scored.append(r)
    # sort by score desc then time asc
    scored.sort(key=lambda x: (-x["match_score"], x.get("time_min", 0)))
    return scored

def adjust_servings(recipe, desired_servings):
    """Scale ingredient quantities if 'quantity' present in ingredient items like '1 cup' strings.
       This function only multiplies numeric prefixes (best effort)."""
    scaled = []
    factor = desired_servings / recipe.get("servings", 1)
    for ing in recipe.get("ingredients", []):
        # Attempt to scale numeric prefix
        parts = ing.split(" ", 1)
        try:
            num = float(parts[0])
            new_num = num * factor
            scaled_ing = f"{round(new_num,2)} {parts[1]}" if len(parts) > 1 else str(round(new_num,2))
        except Exception:
            # no numeric prefix -> leave as-is
            scaled_ing = ing
        scaled.append(scaled_ing)
    return scaled
