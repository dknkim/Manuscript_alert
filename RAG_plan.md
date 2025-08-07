
# ✅ Our Goal

🔍 We have a knowledge base (KB) of curated articles (e.g., on Alzheimer's disease, MRI/PET), and we want to:

- Search PubMed (already implemented in our GitHub)
- For each new PubMed article, check similarity to our KB
- Select the top-k most similar new articles (e.g., top 20)
- Use an LLM to generate a summary of those top-k new articles
- The summary should include their titles, journals, and key findings

This is not querying the KB for a new article. It is:

> **Finding new content that is similar to what’s already in our KB**

---

## ✅ What We're Building

A **“Reverse RAG” monitor** — instead of retrieving from our KB for a new question, we're monitoring new documents (PubMed articles) and asking:

> “Which of these are similar to the knowledge base I already have?”

Then we **summarize the similar new articles**.

---

## 🧭 Implementation Plan (Step-by-Step)

### 🔹 Step 1: Prepare Our Knowledge Base

- Manually collect 20–30 PDFs on Alzheimer’s disease, MRI, PET
- Extract text from each PDF (title, abstract, full text)
- Embed them using `sentence-transformers`
- Store embeddings in a vector store (e.g., ChromaDB)

✅ Tools:
```bash
pip install sentence-transformers chromadb pymupdf
```

---

### 🔹 Step 2: Fetch Recent PubMed Articles

This is already in our GitHub codebase:

- Pull recent PubMed papers on relevant keywords
- Extract: title, abstract, journal name
- Treat each article as a document for embedding

✅ Output format example:
```json
{
  "title": "Amyloid PET Imaging in Mild Cognitive Impairment",
  "abstract": "...",
  "journal": "Neurobiology of Aging",
  "pub_date": "2025-08-05"
}
```

---

### 🔹 Step 3: Compare New PubMed Articles to KB

For each PubMed article:

- Embed the article (title + abstract)
- Run similarity search in our KB vector store
- If any similarity > threshold, keep the article
- Rank by similarity score to KB

✅ Result:
```json
[
  {"title": ..., "journal": ..., "abstract": ..., "similarity": 0.82},
  {"title": ..., "journal": ..., "abstract": ..., "similarity": 0.79}
]
```

---

### 🔹 Step 4: Summarize Top-k PubMed Articles

Take top 20 new articles (similar to KB) and generate a summary with an LLM.

✅ Prompt Template:
```text
You are a research assistant monitoring new literature.

Below are 20 recent PubMed articles similar to a known body of Alzheimer’s disease imaging literature.

List the articles (title + journal), and then summarize the key findings and trends.

Articles:
1. "Amyloid PET Imaging in MCI" — Neurobiology of Aging
2. "MRI Subtypes of Alzheimer's Disease" — Brain Imaging and Behavior
...

Summary:
...
```

✅ Tools: OpenAI, Anthropic, or any LLM we prefer

---

## 📦 Folder/Module Structure Example

```
manuscript_alert/
├── knowledge_base/
│   └── project_alzheimers/
│       ├── papers/
│       ├── embeddings/
│       └── metadata.json
├── pubmed_monitor/
│   ├── fetch_pubmed.py
│   ├── embed_articles.py
│   ├── find_similar_to_kb.py
│   └── summarize_new_articles.py
```

---

## ✅ Summary of the Corrected Flow

| Step     | Action                                                              |
|----------|----------------------------------------------------------------------|
| 1. KB Setup | Embed 20–30 curated Alzheimer’s articles and store in vector DB  |
| 2. Fetch    | Pull recent PubMed articles (already in our system)             |
| 3. Embed    | Convert new articles to embeddings                                |
| 4. Compare  | For each new article, compute similarity to our KB               |
| 5. Select   | Keep top 20 most similar new articles                             |
| 6. Summarize| Use LLM to generate a bullet list of titles/journals + summary    |

---

## 🚀 Want Help with Next Steps?

- `find_similar_to_kb.py`: Compares new PubMed articles to our knowledge base
- `summarize_new_articles.py`: Generates LLM-based summary of the top-k
