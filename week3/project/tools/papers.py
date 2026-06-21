import requests
import re

BASE_URL = "https://huggingface.co"

def clean_arxiv_id(raw_id: str) -> str:
    match = re.search(r"(\d{4}\.\d{4,5})(v\d+)?", raw_id)
    return match.group(1) if match else raw_id.strip()

def paper_search(query: str) -> dict:
    try:
        url = f"{BASE_URL}/api/papers/search"
        response = requests.get(url, params={"q": query}, timeout=10)
        if response.status_code != 200:
            return {"error": f"HuggingFace Papers search failure: {response.status_code}"}
        
        data = response.json()
        items = data.get("papers", data) if isinstance(data, dict) else data
        
        results = []
        for item in items[:5]:
            results.append({
                "arxiv_id": item.get("id"),
                "title": item.get("title"),
                "abstract": item.get("summary", "")[:200] + "..."
            })
        return {"papers": results}
    except Exception as e:
        return {"error": str(e)}

def read_paper(arxiv_id: str) -> dict:
    try:
        clean_id = clean_arxiv_id(arxiv_id)
        # Try fetching markdown body
        md_url = f"{BASE_URL}/papers/{clean_id}.md"
        response = requests.get(md_url, timeout=12)
        
        if response.status_code == 200:
            content = response.text
            return {
                "arxiv_id": clean_id,
                "content": content[:4000] + "..." if len(content) > 4000 else content,
                "url": f"https://arxiv.org/abs/{clean_id}"
            }
            
        # Fallback to Hub details metadata summary
        api_url = f"{BASE_URL}/api/papers/{clean_id}"
        api_resp = requests.get(api_url, timeout=10)
        if api_resp.status_code == 200:
            meta_data = api_resp.json()
            return {
                "arxiv_id": clean_id,
                "title": meta_data.get("title"),
                "abstract": meta_data.get("summary", "No abstract available."),
                "content": meta_data.get("summary", ""),
                "url": f"https://arxiv.org/abs/{clean_id}"
            }
        return {"error": f"Paper {clean_id} not found on HuggingFace Papers index."}
    except Exception as e:
        return {"error": str(e)}