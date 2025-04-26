# Web Scraper Component

A concise, self-contained module for extracting restaurant data from Justdial pages, producing structured JSON ready for the RAG pipeline.

---

## 1. Overview
This component fetches and parses HTML from Justdial restaurant URLs to collect:
- **Metadata:** name, rating, review count, address, contact, hours, special notes
- **Menu:** categorized items with name, price, and veg/non‑veg status
- **Output:** timestamped JSON files in `scraped_data/`

## 2. Key Features
- **Robust Requests:** custom headers, error handling, retries
- **Clean Parsing:** BeautifulSoup with `lxml` for reliable element selection
- **Modular Design:** separate methods for menu extraction and JSON assembly
- **Dual Modes:** CLI-driven interactive (single URL) and batch (list of targets)
- **Automated Storage:** creates `scraped_data/` and writes `<RestaurantName>.json`

## 3. Usage
Run from project root:
```bash
python scraper.py
```
Select:
- **Interactive Mode:** enter one Justdial URL, see live output, save JSON
- **Update Mode:** iterate over the hardcoded `target_restaurants` list and save each JSON

## 4. Project Structure
```
scraper.py          # Core scraper and CLI modes
scraped_data/       # Generated JSON files
Scraping.ipynb      # Exploratory notebook (optional)
```

## 5. Design Choices
- **Requests + BeautifulSoup:** no JS rendering needed
- **Extract then Assemble:** `extract_menu()` → `create_restaurant_json()`
- **JSON-centric:** easy downstream ingestion into vector store or DB
- **CLI Wrapper:** flexible for one-off tests or bulk runs

## 6. Data Schema
```json
{
  "scrape_metadata": { "scrape_url": "...", "scrape_timestamp": "..." },
  "basic_info": { "name": "...", "rating": 4.2, "rating_count": "123", "address": "...", "contact": "...", "operating_hours": "...", "special_info": "..." },
  "menu": { "Starters": [{ "name": "Aloo Tikki", "price": 120, "veg_status": "veg" }, … ], … }
}
```

## 7. Assumptions & Limitations
- **Justdial-specific:** tailored CSS selectors; may break on layout changes
- **Static Content:** no handling for JS-loaded menus
- **No Proxy/CAPTCHA:** not suited for high‑volume or blocked requests

## 8. Challenges
- Identifying stable selectors for nested menu sections
- Handling absent or malformed fields without stopping the run
- Balancing speed (batch mode) vs. politeness (rate‑limiting)

## 9. Future Improvements
- Adapter pattern for multiple domains (Zomato, Yelp, etc.)
- Async or Scrapy integration for faster batch runs
- Headless browser support for dynamic content
- Configurable retry/backoff and proxy rotation

