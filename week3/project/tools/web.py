import os
import requests
from bs4 import BeautifulSoup

def web_search(query: str) -> dict:
    serper_key = os.environ.get("SERPER_API_KEY")
    if not serper_key: 
        return {"error": "Missing SERPER_API_KEY environment variable"}
    try:
        res = requests.post(
            "https://google.serper.dev/search", 
            headers={"X-API-KEY": serper_key, "Content-Type": "application/json"}, 
            json={"q": query, "num": 5}, 
            timeout=10
        )
        return {"results": [{"title": i.get("title"), "url": i.get("link"), "snippet": i.get("snippet")} for i in res.json().get("organic", [])]}
    except Exception as e: 
        return {"error": str(e)}

def web_fetch(url: str) -> dict:
    try:
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        for s in soup(["script", "style", "header", "footer", "nav"]): 
            s.decompose()
        txt = soup.get_text(separator=" ", strip=True)
        return {"url": url, "content": txt[:3500] + "..." if len(txt) > 3500 else txt}
    except Exception as e: 
        return {"error": str(e)}