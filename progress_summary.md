## Progress summary

### What’s done
- RAG-only scoring in the app (scores from KB similarity only)
  - Sidebar: RAG toggle, top‑k slider, and collection selector (default `kb_alz`)
- Dynamic Chroma collection binding via cached factory
- PubMed KB tooling
  - `scripts/generate_kb_seed.py`: generate `kb_seed.json` (title+abstract) from a PMIDs file
  - `scripts/build_kb_from_pubmed_ids.py`: build chunks/embeddings and ingest to Chroma (`--one-chunk-per-pmid` supported)
- Vector DB: Chroma persisted under `data/vector_db/chroma`

### Generate seed (KB_alz)
```bash
./scripts/generate_kb_seed.py --pmids-file KB_alz/pmids.json
```
- Output: `KB_alz/kb_seed.json` with full title+abstract per PMID

### Run the app
```bash
streamlit run app.py
```
- In sidebar: enable RAG, set collection to `kb_alz`, adjust top‑k.

### Recent updates
- Added visible “RAG Options” in the sidebar (toggle, top‑k, collection, model, DB path)
- RAG mode now ignores keyword filtering (no “min 2 keywords” gate)
- Similarity mapping fixed for L2 distances: `cos = 1 − (d^2)/2` → score = `10·cos` (clamped)
- Added fallback cosine over stored KB embeddings if the distance path returns ~0

### Troubleshooting
- If scores are all 0 or the collection is empty:
  - Regenerate and ingest the seed
  ```bash
  ./scripts/generate_kb_seed.py --pmids-file KB_alz/pmids.json
  ./scripts/ingest_seed_to_chroma.py --seed KB_alz/kb_seed.json --collection kb_alz --recreate
  ```
  - In the app, set “RAG collection name” to `kb_alz` and refresh
- To verify collections
  ```bash
  python - <<'PY'
  import chromadb; c=chromadb.PersistentClient(path='data/vector_db/chroma')
  print([col.name for col in c.list_collections()])
  for col in c.list_collections(): print(col.name, '=>', col.count())
  PY
  ```
- If the sidebar lacks RAG controls, ensure you’re running the updated `app.py` (via `streamlit run app.py`).

### Notes
- If you see “collection is empty”, re‑ingest or switch to an existing collection in the sidebar.
- UUID folders in `data/vector_db/chroma` are Chroma internals; prefer dropping via API or re‑ingest.
