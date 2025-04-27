# Nugget Bot

A friendly, RAG-powered chatbot assistant for restaurants, built as an assignment submission for the Zomato internship.

## Table of Contents
- [Project Overview](#project-overview)
- [Assignment Requirements](#assignment-requirements)
- [Key Features](#key-features)
- [Installation](#installation)
- [Usage](#usage)
- [Repository Structure](#repository-structure)
- [Dataset](#dataset)
- [Technical Documentation](#technical-documentation)
- [Demo Video](#demo-video)
- [Future Improvements](#future-improvements)
- [License](#license)

## Project Overview
Nugget Bot is an AI-driven restaurant guide that answers user queries about menus, pricing, dietary options, and comparisons. It integrates three main components:

1. **Web Scraper** – extracts restaurant metadata and menu items from Justdial into structured JSON.
2. **VectorDB Generator & Retriever** – ingests JSON into ChromaDB with separate collections for restaurants and menu items, enabling semantic and keyword search.
3. **RAG Agent** – combines a hybrid LLM pipeline (Hugging Face primary, Groq fallback) with retrieved context to generate warm, accurate responses.

## Assignment Requirements
- **Scraped Dataset**: View the collected JSON in `public/scraped_data/`.
- **Technical Documentation**: See the [Technical Documentation](#technical-documentation) section below.
- **Demo Video**:  [Demo Video](https://jmp.sh/fvmxcTmM)

## Key Features
- **Robust Scraping**: Custom headers, retries, and error handling with BeautifulSoup parsing.
- **Hybrid Search**: Combines semantic embeddings and inverted indexing for precise retrieval.
- **Dual Collections**: Separate ChromaDB stores for restaurant-level and menu-item embeddings.
- **Multi-Model Inference**: Primary Hugging Face LLM with Groq fallback for gated or exhausted APIs.
- **Interactive CLI**: User-friendly, colorized command-line interface.

## Installation
1. **Prerequisites**
   - Python 3.10+
   - `pip install -r requirements.txt`
2. **Environment Variables**
   - Create a `.env` file:
     ```dotenv
     HUGGING_FACE_TOKEN=<your_hf_token>
     ```
    - Step for testing the agent and not needed for interacting with the bot. [As it will ask for key]
## Usage
```
python3 main.py
```  
Interact via CLI until you type `exit`.

## Repository Structure
```
├── scraper.py                         # Justdial scraping module
├── vectordb_generator_retriever.py    # Ingest & query ChromaDB
├── rag_agent.py                       # RAG-based chatbot agent
├── public/
│   └── scraped_data/                  # Structured JSON output
├── restaurant_vector_db/              # Persistent ChromaDB store
├── docs/
│   ├── technical.md                   # System design & implementation details
│   └── schema.md                      # Data schema & scraping methodology
├── demo.mp4                           # 3‑minute demo video (link placeholder)
├── requirements.txt                   # Python dependencies
└── README.md                          # This file
```

## Dataset
All extracted JSON files reside in `public/scraped_data/`. Each file includes:
```json
{
  "scrape_metadata": {"url": "...", "timestamp": "..."},
  "basic_info": {"name": "...", "rating": 4.2, "address": "...", …},
  "menu": {"Starters": [{"name": "Aloo Tikki", "price": 120, "veg_status": "veg"}, …], …}
}
```
Refer to `docs/schema.md` for field definitions and parsing logic.

## Technical Documentation
An in-depth overview of system design, implementation, and decisions:

### 1. System Architecture
- **Scraper Module** (`scraper.py`): CLI-driven modes (interactive & batch) fetch HTML from Justdial, parse metadata and menu sections via BeautifulSoup, and output timestamped JSON.
- **VectorDB Generator** (`vectordb_generator_retriever.py`): Sanitizes data, generates text templates, and populates two ChromaDB collections (`restaurants`, `menu_items`) with metadata filters and embeddings.
- **RAG Agent** (`rag_agent.py`): Builds context by querying ChromaDB (semantic + inverted index), then submits prompts to LLM (Hugging Face → Groq fallback) for response generation.

### 2. Implementation Details & Design Decisions
- **Justdial-Specific Scraping**: Chose static HTML parsing for speed and reliability; may extend with headless rendering later.
- **Data Model**: JSON-centric structure to facilitate downstream ingestion and schema evolution.
- **Dual Collection Strategy**: Separates restaurant vs. menu-item embeddings, enabling targeted metadata filters (e.g., `veg_status`, `price_range`).
- **Hybrid Retrieval**: Merged vector similarity with inverted text-indexing to balance recall and precision.
- **Multi-Model Inference Pipeline**: Primary Llama-3 via Hugging Face; fallback to Groq model to handle API limits and gating.

### 3. Challenges & Solutions
1. **Stable Selector Identification**: Overcame layout inconsistencies with robust CSS/XPath patterns and fallback checks.
2. **Handling Missing Data**: Implemented default values and try/except blocks to prevent pipeline breaks.
3. **Indexing Strategy**: Tuned vector vs. keyword thresholds; developed an inverted index for high-recall terms.
4. **Context-Length Tuning**: Experimented with prompt window size to optimize relevance without truncation.
5. **Gated Model & Rate Limits**: Integrated Groq API fallback, ensuring uninterrupted service.

### 4. Future Improvement Opportunities
- Adapter pattern for multi-domain scraping (Zomato, Yelp).
- Async or Scrapy integration for faster, large-scale data collection.
- Headless browser support for dynamic content.
- Geo-radius and advanced dietary filters in retrieval.
- Integration tests, CI/CD pipeline, and monitoring alerts.

## Demo Video
Watch the demo here: [Demo Video](https://jmp.sh/fvmxcTmM)

## Future Improvements
- Graph DB for knowledge base construction
- Adapter pattern for additional domains (Zomato, Yelp)
- Async or Scrapy integration for high-volume scraping
- Headless browser support for dynamic content
- Geo‑radius and advanced dietary filtering
- Integration tests and CI/CD pipeline

## License
This project is licensed under the MIT License. See `LICENSE` for details.

