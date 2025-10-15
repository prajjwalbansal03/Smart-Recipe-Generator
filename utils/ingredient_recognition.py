# utils/ingredient_recognition.py
from PIL import Image
import io

# Optional: Hugging Face Inference API
def recognize_ingredients_from_image(uploaded_file, hf_token=None):
    """
    Two modes:
     - If hf_token is provided, call Hugging Face inference (image-classification)
       endpoint for better labels (user must provide token).
     - Otherwise, fallback to a simple heuristic: filename keywords or basic color-based hints.
    Returns list of ingredient names (lowercase).
    """
    # If HF token provided, try using Hugging Face Inference API
    if hf_token:
        import base64
        import requests
        headers = {"Authorization": f"Bearer {hf_token}"}
        # Use a general image-classification model endpoint name (user must have access)
        hf_api = "https://api-inference.huggingface.co/models/google/vit-base-patch16-224"
        img_bytes = uploaded_file.getvalue()
        resp = requests.post(hf_api, headers=headers, data=img_bytes, timeout=30)
        if resp.status_code != 200:
            raise Exception(f"HuggingFace inference failed: {resp.status_code} {resp.text}")
        out = resp.json()
        # out is list of dicts with 'label' and 'score'
        labels = [d["label"].lower().replace("_", " ") for d in out[:8]]
        # Map to ingredient-like labels (best effort)
        possible = []
        for lbl in labels:
            # simple heuristics:
            for token in ["tomato","onion","egg","banana","apple","carrot","potato","lemon","garlic","chicken","cheese","milk","bread","cucumber","pepper","spinach","mushroom","rice"]:
                if token in lbl:
                    possible.append(token)
        if possible:
            return list(dict.fromkeys(possible))
        return [l.split(",")[0] for l in labels[:5]]

    # Fallback heuristic: try reading filename or simple color heuristics
    try:
        filename = getattr(uploaded_file, "name", "") or ""
        fname = filename.lower()
        keywords = []
        for k in ["tomato","onion","egg","milk","bread","apple","banana","carrot","potato","chicken","cheese","lemon","garlic","mushroom","rice","spinach","pepper","cucumber"]:
            if k in fname:
                keywords.append(k)
        if keywords:
            return keywords
    except Exception:
        pass

    # Last fallback: return empty to ask user to switch to text mode.
    return []
