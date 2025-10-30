# backend/server.py
from fastapi import FastAPI
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
import json, numpy as np
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware  
from quantity_generator import generate_quantities

app = FastAPI(title="Local Recipe Bot API")

# ✅ Allow frontend (port 5500) to talk to backend (port 8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # you can later restrict e.g. ["http://127.0.0.1:5500"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MODEL = "all-MiniLM-L6-v2"
embedder = SentenceTransformer(MODEL)

INDEX_PATH = Path("models/recipes.index")
META_PATH = Path("models/recipes_meta.json")

# load metadata
with META_PATH.open('r', encoding='utf-8') as f:
    meta = json.load(f)

# Try to load FAISS index
USE_FAISS = False
try:
    import faiss
    idx = faiss.read_index(str(INDEX_PATH))
    USE_FAISS = True
    print("Using FAISS index")
except Exception as e:
    print("FAISS not available, using numpy embeddings fallback:", e)
    emb = np.load("models/embeddings.npy")


class Query(BaseModel):
    ingredients: list
    top_k: int = 3


@app.post("/api/recipe")
def get_recipe(q: Query):
    query_text = " ".join([x.lower().strip() for x in q.ingredients])
    vec = embedder.encode([query_text], convert_to_numpy=True)

    # normalize
    from numpy.linalg import norm
    vec = vec / (norm(vec, axis=1, keepdims=True) + 1e-10)

    results = []
    if USE_FAISS:
        import faiss
        faiss.normalize_L2(vec)
        distances, indices = idx.search(vec, q.top_k)
        for score, i in zip(distances[0], indices[0]):
            doc = meta[int(i)].copy()
            doc["score"] = float(score)
            results.append(doc)
    else:
        # fallback: cosine similarity
        emb_all = emb
        emb_norm = emb_all / (np.linalg.norm(emb_all, axis=1, keepdims=True) + 1e-10)
        qv = vec[0]
        sims = (emb_norm @ qv).tolist()
        top_idx = sorted(range(len(sims)), key=lambda i: sims[i], reverse=True)[:q.top_k]
        for i in top_idx:
            doc = meta[int(i)].copy()
            doc["score"] = float(sims[i])
            results.append(doc)

    # ✅ Add generated quantities for top recipe
    if results:
        best_recipe = results[0]
        best_recipe["quantity"] = generate_quantities(q.ingredients)
        # standardize keys for frontend
        best_recipe["recipe_name"] = best_recipe.get("recipe_name", best_recipe.get("name", "Recipe"))
        best_recipe["step_by_step"] = best_recipe.get("step_by_step", best_recipe.get("text", ""))
        best_recipe["ingredients"] = ", ".join(q.ingredients)

        return {"query": q.ingredients, "results": [best_recipe]}

    return {"query": q.ingredients, "results": []}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
