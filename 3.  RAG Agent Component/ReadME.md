# RAG Agent Component

A concise module that combines retrieval (ChromaDB + inverted search) with generation (Hugging Face Inference API) for end-to-end RAG-powered restaurant Q&A.

---

## 1. Overview
The `rag_agent.py` script defines three core classes:
- **Retriever**: hybrid vector + inverted-index search over `restaurants` and `menu_items` collections in ChromaDB
- **Generator**: calls HF Inference API (`Llama-3.3-70B-Instruct`) to produce conversational answers from context
- **NuggetsBot**: orchestrates retrieval + generation and manages chat history

This agent powers the chatbot interface by:
1. Retrieving relevant restaurant/menu data for a user query
2. Building a structured context prompt
3. Generating a natural response via LLM

---

## 2. Key Features
- **Multi Inference**: uses Hugging face inference as its primary inference and in case of any error it fallbacks to groq(14000 free tokens/minute).
- **Hybrid Retrieval**: combines FAISS-like vector search with term-based inverted indices for recall and precision
- **Context Builder**: extracts restaurant names, categories, and menu items to assemble bullet-point context
- **LLM Integration**: leverages Hugging Face’s InferenceClient for on-demand chat completions
- **History Management**: retains last 3 turns to support coherent multi-turn dialogue
- **OOS & Clarification**: built-in logic to handle out-of-scope questions and ask clarifiers

---

## 3. Usage
Run from project root:
```bash
python rag_agent.py
```
- Initializes or reuses the vector DB at `../public/restaurant_vector_db`
- Prompts “Nuggets Restaurant Bot is ready!”
- Enter queries interactively; type `exit` to quit

Example:
```
You: best vegetarian starters
Nuggets: RESTAURANTS:
- Barbeque Nation in Gomti Nagar (Rating: 4.4)
MENU ITEMS:
- Tandoori Paneer Tikka at Barbeque Nation, ₹310 (veg)
```

---

## 4. Project Structure
```
rag_agent.py           # Retriever, Generator, and NuggetsBot definitions
```
Dependencies:
- `chromadb` (PersistentClient)
- `huggingface_hub` (InferenceClient)
- `re`, `warnings` (built-in)

---

## 5. Design Choices
- **Three core classes**:
  - `Retriever`: hybrid vector + inverted-index lookup over restaurants and menu items
  - `Generator`: formats prompts and invokes HF Inference API for response generation
  - `NuggetsBot`: orchestrates retrieval, context building, generation, and history
- **Hybrid Retrieval**: semantic vector search combined with token-based inverted indices
- **Role-based Prompts**: system vs. user framing to guide LLM behavior
- **Lightweight Context**: bullet-point layouts to maximize relevance and brevity in prompts

## 6. Assumptions & Limitations
- **Vector DB Path**: expects `../public/restaurant_vector_db` with preloaded collections
- **API Latency**: HF Inference may introduce delay; no retry/backoff logic
- **Static Index**: in-memory inverted indices built at startup; no dynamic updates
- **Simplified Parser**: regex-based extraction of restaurant/category; may miss complex queries

---

## 7. Challenges
- **Model benchmarking time**: spent significant effort comparing response quality across Gemma 9B, Meta 7B, and BitNet-B1, ultimately settling on Llama 3.3 70B for its balanced latency–quality ratio
- **Optimal context length**: struggled to determine how much retrieved context to include without overloading prompts or diluting relevance
- **Vector vs. keyword trade-off**: tuning hybrid retrieval for both semantic recall and exact-match precision
- **Prompt design**: crafting system vs. user messages that reliably steer the LLM toward concise, accurate restaurant answers
- **Multi-turn coherence**: managing limited chat-history window while preserving conversational context

## 8. Future Improvements
- **Dynamic Updates**: allow refreshing vector DB without restart
- **Error Handling**: add robust retry/backoff for API calls
- **Advanced Parsing**: NLP-based intent and entity extraction
- **Customizable Models**: support alternative LLM providers or open-source weights

---
