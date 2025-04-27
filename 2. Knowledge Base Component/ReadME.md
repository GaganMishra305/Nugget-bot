# VectorDB Generator & Retriever

A standalone module that ingests scraped restaurant JSON into a ChromaDB vector store and provides retrieval utilities for RAG.

---

## 1. Overview

This script (`vectordb_generator_retriever.py`) transforms structured restaurant data into two ChromaDB collections:

- **restaurants**: embeds high-level restaurant metadata
- **menu\_items**: embeds individual menu-item documents

It also exposes search and comparison methods for downstream chatbot query resolution.

---

## 2. Key Features

- **Data Sanitization**: fills missing fields (`None` → defaults) to ensure clean embeddings
- **Dual Collections**: separates restaurant-level vs. item-level vectors for precise filtering
- **Metadata-rich**: stores name, location, rating, price\_range, veg\_status, etc., as `metadatas`
- **Flexible Main**: rebuild or reuse persistent DB via CLI prompts
- **Query Utilities**: functions for restaurant search, dish lookup, dietary filters, comparisons

---

## 3. Usage

Run from project root:

```bash
python vectordb_generator_retriever.py
```

- **On first run**: creates `./restaurant_vector_db/`, ingests all JSON in `../public/scraped_data`.
- **Subsequent runs**: prompts to delete/reuse existing DB.
- After ingestion, automatically executes `test_queries()` to validate search functions.

---

## 4. Project Structure

```
vectordb_generator_retriever.py   # Core vector ingestion & retrieval logic
scraped_data/                     # Input JSON files (from scraper)
restaurant_vector_db/             # Persistent ChromaDB store
```

Key class:

- `Vectorizer`: methods to sanitize, ingest, and query the vector DB

---

## 5. Design Choices
- **ChromaDB**: lightweight, on-disk vector store with metadata filtering
- **Text Templates**: concise, human-readable documents for embedding
- **Where-Clauses**: efficient metadata filters (`veg_status`, `price_range`, `location`)
- **Structured Queries**: pre-built methods (`search_restaurants`, `search_dishes`, `compare_restaurants`, `find_restaurants_for_dietary_needs`)
- **Vector DB with inverted indexing** for fast similarity search and metadata filters
- **Inverted indices** on key fields (`veg_status`, `price_range`, `location`) for efficient querying

## 6. Data Model

- **Restaurant Documents**: e.g. "Taj Restaurant is located in Colaba..."; metadata keys: `name`, `location`, `rating`, `type: restaurant`, etc.
- **Menu Item Documents**: e.g. "Paneer Tikka is a veg item in Starters..."; metadata keys: `name`, `category`, `price`, `price_range`, `veg_status`, `type: menu_item`, etc.

---

## 7. Assumptions & Limitations

- **Schema Stability**: expects same JSON structure as produced by scraper
- **ChromaDB v1 API**: tied to current Chromadb Python API signature
- **No Parallelism**: ingestion is sequential; may be slow for large datasets
- **Local Disk Only**: no remote or multi-node support

---

## 8. Challenges
- **Handling `None` values** robustly across nested JSON structures
- **Designing text templates** that balance context vs. brevity
- **Choosing effective `price_range` buckets** for filtering
- **Deciding optimal retrieval mechanism**: balancing vector similarity search with metadata-based inverted filtering

## 9. Future Improvements

- **Graph DB support**: generating a knowledge graph to better catch data relations and provide more optimal context for generation.
- **Batching & Parallel Ingestion**: speed up large-scale indexing
- **Configurable Collections**: allow dynamic collection names or third-party vector stores
- **Advanced Filters**: geo-radius, sentiment tags, dietary tags beyond veg/non-veg
- **Integration Tests**: verify end-to-end RAG retrieval fidelity

