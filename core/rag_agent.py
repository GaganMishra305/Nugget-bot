from huggingface_hub import InferenceClient
from groq import Groq
import chromadb
from typing import Dict, List, Any, Optional
import warnings, re

warnings.filterwarnings("ignore")  # removes deprecation warnings

provider = 'cerebras'
default_model = 'meta-llama/Llama-3.3-70B-Instruct'

groq_fallback_key = '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'
groq_fallback_model = 'llama3-70b-8192'

class Retriever:
    def __init__(self, db_path: str = "./public/restaurant_vector_db"):
        self.client = chromadb.PersistentClient(path=db_path)
        self.res_col = self.client.get_collection("restaurants")
        self.menu_col = self.client.get_collection("menu_items")

        # preload everything
        self._all_restaurants = self.res_col.query(
            query_texts=[""], n_results=10_000, where={"type": "restaurant"}
        )["metadatas"][0]
        self._all_menu = self.menu_col.query(
            query_texts=[""], n_results=50_000, where={"type": "menu_item"}
        )["metadatas"][0]

        # inverted indexes
        self._res_index: Dict[str, List[Dict[str, Any]]] = {}
        for r in self._all_restaurants:
            for tok in set(re.findall(r"\w+", " ".join([r.get("name", ""), r.get("location", ""), r.get("cuisine", "")]).lower())):
                self._res_index.setdefault(tok, []).append(r)
        self._menu_index: Dict[str, List[Dict[str, Any]]] = {}
        for m in self._all_menu:
            for tok in set(re.findall(r"\w+", " ".join([m.get("name", ""), m.get("category", "")]).lower())):
                self._menu_index.setdefault(tok, []).append(m)

    def _inverted_search(self, index: Dict[str, List[Dict[str, Any]]], query: str) -> List[Dict[str, Any]]:
        scores: Dict[str, List[Any]] = {}
        for tok in set(re.findall(r"\w+", query.lower())):
            for item in index.get(tok, []):
                key = item.get("name", "") + "|" + item.get("restaurant_name", item.get("location", ""))
                scores.setdefault(key, [item, 0])[1] += 1
        return [entry[0] for entry in sorted(scores.values(), key=lambda x: x[1], reverse=True)]

    def search_restaurants(self, query: str) -> List[Dict[str, Any]]:
        vec = self.res_col.query(
            query_texts=[query], n_results=len(self._all_restaurants), where={"type": "restaurant"}
        )["metadatas"][0]
        inv = self._inverted_search(self._res_index, query)
        combined, seen = [], set()
        for r in vec + inv:
            name = r.get("name")
            if name and name not in seen:
                combined.append(r)
                seen.add(name)
        return combined

    def search_menu_items(
        self, query: str, restaurant: Optional[str] = None, category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        vec = self.menu_col.query(
            query_texts=[query], n_results=len(self._all_menu), where={"type": "menu_item"}
        )["metadatas"][0]
        cat_hits = []
        if category:
            cat_hits = self.menu_col.query(
                query_texts=[category], n_results=len(self._all_menu), where={"type": "menu_item"}
            )["metadatas"][0]
        inv = self._inverted_search(self._menu_index, query + (f" {category}" if category else ""))
        combined, seen = [], set()
        for bucket in (vec, cat_hits, inv):
            for m in bucket:
                key = f"{m.get('name','')}|{m.get('restaurant_name','')}"
                if key not in seen and (not restaurant or m.get("restaurant_name","\"").lower() == restaurant.lower()):
                    combined.append(m)
                    seen.add(key)
        return combined

    def list_all(self) -> List[Dict[str, Any]]:
        return self._all_restaurants


class Generator:
    def __init__(
        self,
        api_key: str,
        model_name: str = default_model,
        groq_api_key: str = groq_fallback_key,
        groq_model: str = groq_fallback_model,
    ):
        self.client = InferenceClient(provider=provider, api_key=api_key)
        self.model = model_name
        self.groq_client = Groq(api_key=groq_api_key)
        self.groq_model = groq_model

    def generate(self, query: str, context: str, history: str) -> str:
        system_prompt = (
            "You are Nuggets, a friendly, warm and knowledgeable local restaurant guide. "
            "Domain: restaurants, menus, pricing, comparisons, dietary options.\n\n"
            "1. Out-of-scope → Respond accordingly dont entertain questions beyond a restaurant guide.\n"
            "2. Ambiguous → ask a concise clarifier.\n"
            "3. No matches → “I couldn’t find a match—could you give me more details?”\n\n"
            "Otherwise, use CONTEXT to craft a warm, accurate answer."
        )
        user_prompt = f"""{history.strip()}

CONTEXT:
{context.strip()}

USER: {query.strip()}

NUGGETS:"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        try:
            resp = self.client.chat.completions.create(
                model=self.model, messages=messages, max_tokens=500
            )
            return resp.choices[0].message.content
        except Exception as e:
            print(f"Hugging Face inference failed, falling back to Groq: {e}")
            fallback = self.groq_client.chat.completions.create(
                model=self.groq_model, messages=messages, max_tokens=500
            )
            return fallback.choices[0].message.content


class NuggetsBot:
    def __init__(
        self,
        api_key: str,
        db_path: str = "./public/restaurant_vector_db",
        groq_api_key: str = groq_fallback_key,
        groq_model: str = groq_fallback_model,
    ):
        self.retriever = Retriever(db_path)
        self.generator = Generator(api_key=api_key, groq_api_key=groq_api_key, groq_model=groq_model)
        self.chat_history: List[Dict[str, str]] = []

    def _build_context(self, query: str) -> str:
        rm = re.search(r"(?:at|for)\s+([A-Z][\w\s]+)", query)
        cm = re.search(r"\b(desserts?|starters?|mains?|drinks?|beverages?)\b", query, re.IGNORECASE)
        restaurant = rm.group(1).strip() if rm else None
        category = cm.group(1).strip() if cm else None

        restos = self.retriever.search_restaurants(query)
        items = self.retriever.search_menu_items(query, restaurant, category)
        lines: List[str] = []

        if restos:
            lines.append("RESTAURANTS:")
            lines += [f"- {r['name']} in {r.get('location','Unknown')} (Rating: {r.get('rating','N/A')})" for r in restos]
        if items:
            lines.append("\nMENU ITEMS:")
            lines += [
                f"- {m['name']} at {m.get('restaurant_name','Unknown')}, ₹{m.get('price','N/A')} ({m.get('veg_status','Unknown')})"
                for m in items
            ]
        if not lines:
            allr = self.retriever.list_all()
            lines = ["AVAILABLE RESTAURANTS:"] + [
                f"- {r['name']} in {r.get('location','Unknown')}" for r in allr
            ]

        return "\n".join(lines)

    def process_query(self, query: str) -> str:
        self.chat_history.append({"input": query})
        history = "".join(
            f"{'User: ' + m['input'] if 'input' in m else 'Nuggets: ' + m['output']}\n"
            for m in self.chat_history[-3:]
        )
        ctx = self._build_context(query)
        ans = self.generator.generate(query, ctx, history)
        self.chat_history[-1]["output"] = ans
        return ans
