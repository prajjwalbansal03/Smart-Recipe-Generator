# utils/persistence.py
import pandas as pd
from pathlib import Path

def ensure_csv(path, cols):
    p = Path(path)
    if not p.parent.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
    if not p.exists():
        df = pd.DataFrame(columns=cols)
        df.to_csv(p, index=False)

def save_rating(csv_path, recipe_id, rating):
    ensure_csv(csv_path, ["recipe_id", "rating"])
    df = pd.read_csv(csv_path)
    df = df[df.recipe_id != int(recipe_id)]
    df = df.append({"recipe_id": int(recipe_id), "rating": int(rating)}, ignore_index=True)
    df.to_csv(csv_path, index=False)

def load_ratings(csv_path):
    p = Path(csv_path)
    if not p.exists():
        return {}
    df = pd.read_csv(p)
    return {str(int(r.recipe_id)): int(r.rating) for _, r in df.iterrows()}

def save_favorite(csv_path, recipe_id):
    ensure_csv(csv_path, ["recipe_id"])
    df = pd.read_csv(csv_path)
    if int(recipe_id) in df.recipe_id.values:
        return
    df = df.append({"recipe_id": int(recipe_id)}, ignore_index=True)
    df.to_csv(csv_path, index=False)

def load_favorites(csv_path):
    p = Path(csv_path)
    if not p.exists():
        return []
    df = pd.read_csv(p)
    return [str(int(x)) for x in df.recipe_id.values]
