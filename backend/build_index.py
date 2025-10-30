# backend/build_index.py
import json
from pathlib import Path
from sentence_transformers import SentenceTransformer
import numpy as np

DATA = Path("models/recipes_clean.jsonl")
OUT_INDEX = Path("models/recipes.index")
META_OUT = Path("models/recipes_meta.json")
MODEL_NAME = "all-MiniLM-L6-v2"   # compact and fast

embedder = SentenceTransformer(MODEL_NAME)

docs = []
meta = []
with DATA.open('r', encoding='utf-8') as f:
    for line in f:
        d = json.loads(line)
        docs.append(" ".join(d['ingredients']) or d['name'])
        meta.append(d)

emb = embedder.encode(docs, show_progress_bar=True, convert_to_numpy=True)

# --- try faiss first ---
try:
    import faiss
    dim = emb.shape[1]
    index = faiss.IndexFlatIP(dim)
    # normalize for cosine-style similarity
    faiss.normalize_L2(emb)
    index.add(emb) # type: ignore
    faiss.write_index(index, str(OUT_INDEX))
    print("Saved FAISS index to", OUT_INDEX)
except Exception as e:
    print("FAISS unavailable:", e)
    # fallback: save numpy arrays to disk so Annoy or simple search can use them
    import numpy as np
    np.save("models/embeddings.npy", emb)
    print("Saved raw embeddings to models/embeddings.npy")

with META_OUT.open('w', encoding='utf-8') as m:
    json.dump(meta, m, ensure_ascii=False, indent=2)

print("Saved meta to", META_OUT)
