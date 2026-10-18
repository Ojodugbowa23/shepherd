from pathlib import Path
import requests

GRAPH = "https://graph.facebook.com/v25.0"


def fetch_page_photos(page_id, token, limit=8, folder="page_photos"):
    Path(folder).mkdir(exist_ok=True)
    url = f"{GRAPH}/{page_id}/photos"
    params = {"type": "uploaded", "fields": "images", "limit": min(limit, 25), "access_token": token}
    saved = []
    while url and len(saved) < limit:
        data = requests.get(url, params=params, timeout=30).json()
        if "error" in data:
            raise RuntimeError(data["error"].get("message", "Facebook returned an error"))
        for photo in data.get("data", []):
            if len(saved) >= limit:
                break
            best = max(photo["images"], key=lambda i: i.get("width", 0))["source"]
            path = Path(folder) / f"{photo['id']}.jpg"
            if not path.exists():
                path.write_bytes(requests.get(best, timeout=60).content)
            saved.append(str(path))
        url = data.get("paging", {}).get("next")
        params = None
    return saved