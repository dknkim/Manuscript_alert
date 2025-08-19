## Progress summary

### What’s done
- RAG-only scoring in the app (scores from KB similarity only)
  - Sidebar: RAG toggle, top‑k slider, and collection selector (default `kb_alz`)
  - RAG mode fetch scope limited to keywords: `MRI`, `PET`, `brain` (fetch only; scoring is KB‑only)
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
