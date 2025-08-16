from app.config import Config
import httpx

def search_vendors(event_type, location):
    query = f"{event_type} vendors near {location}"

    # Try Tavily first
    try:
        response = httpx.post(
            "https://api.tavily.com/search",
            headers={"Authorization": f"Bearer {Config.TAVILY_API_KEY}"},
            json={"query": query, "search_depth": "basic"}
        )
        if response.status_code == 200:
            return [
                {"title": r["title"], "url": r["url"], "snippet": r.get("snippet", "")}
                for r in response.json().get("results", [])
            ]
    except:
        pass

    # Fallback: Bing Search
    try:
        response = httpx.get(
            "https://api.bing.microsoft.com/v7.0/search",
            headers={"Ocp-Apim-Subscription-Key": Config.BING_API_KEY},
            params={"q": query, "count": 5}
        )
        if response.status_code == 200:
            web_pages = response.json().get("webPages", {}).get("value", [])
            return [
                {"title": r["name"], "url": r["url"], "snippet": r.get("snippet", "")}
                for r in web_pages
            ]
    except:
        pass

    return []
