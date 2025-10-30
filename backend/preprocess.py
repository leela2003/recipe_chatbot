# backend/preprocess.py
import json, re
from pathlib import Path

DATA_IN = Path("../data/recipe.json")   # adjust if path different
OUT = Path("models/recipes_clean.jsonl")
OUT.parent.mkdir(parents=True, exist_ok=True)

def normalize_ingredients(ings):
    if isinstance(ings, list):
        items = ings
    else:
        items = re.split(r',|\n|;|\|', str(ings))
    return [i.strip().lower() for i in items if i and i.strip()]

with open(DATA_IN, 'r', encoding='utf-8') as f:
    recipes = json.load(f)

with OUT.open('w', encoding='utf-8') as fw:
    for idx, r in enumerate(recipes):
        name = r.get('recipe_name') or r.get('name') or f'recipe_{idx}'
        ingredients_field = r.get('ingredients') or r.get('ingredient') or ''
        steps = r.get('step_by_step') or r.get('instructions') or r.get('steps') or ''
        doc = {
            "id": name,
            "name": name,
            "ingredients": normalize_ingredients(ingredients_field),
            "text": steps
        }
        fw.write(json.dumps(doc, ensure_ascii=False) + "\n")

print("Preprocessing completed. Wrote:", OUT)
