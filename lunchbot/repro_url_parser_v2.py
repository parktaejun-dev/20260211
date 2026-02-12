import requests
import re
from bs4 import BeautifulSoup
import json

def parse_naver_map_url(url: str):
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"
    }
    
    try:
        # 1. Expand Short URL
        print(f"Expanding {url}...")
        session = requests.Session()
        res = session.get(url, headers=headers, allow_redirects=True)
        final_url = res.url
        print(f"Final URL: {final_url}")
        
        # 2. Extract Place ID
        place_id = None
        patterns = [r'place/(\d+)', r'restaurant/(\d+)', r'id=(\d+)', r'pinId=(\d+)']
        for pattern in patterns:
            match = re.search(pattern, final_url)
            if match:
                place_id = match.group(1)
                break
        
        if place_id:
            print(f"Place ID: {place_id}")
            
            # 3. Fetch Mobile Place Page
            mobile_url = f"https://m.place.naver.com/restaurant/{place_id}/home"
            print(f"Mobile URL: {mobile_url}")
            
            m_res = session.get(mobile_url, headers=headers)
            # UTF-8 Encoding enforcement
            m_res.encoding = "utf-8"
            
            soup = BeautifulSoup(m_res.text, "html.parser")
            
            # Extract Meta Tags
            og_title = soup.find("meta", property="og:title")
            title = og_title["content"] if og_title else ""
            print(f"OG Title: {title}")
            
            name = title.split(":")[0].strip()
            print(f"Name: {name}")

            # Try JSON-LD
            scripts = soup.find_all("script", type="application/ld+json")
            for s in scripts:
                try:
                    js = json.loads(s.string)
                    # print(json.dumps(js, indent=2, ensure_ascii=False))
                    if "@type" in js:
                         print(f"LD-JSON Type: {js.get('@type')}")
                         print(f"LD-JSON Name: {js.get('name')}")
                         print(f"LD-JSON Category: {js.get('servesCuisine')}") # Sometimes works
                         print(f"LD-JSON Address: {js.get('address', {}).get('streetAddress')}")
                except:
                    pass
            
            # Category from Title or meta? Usually not there.
            # Try searching specific span containing category keywords
            # <span class="DJJvD">한식</span>  <- class name is obfuscated.
            # But usually it's near the Title.
            
            # Fallback: if category missing, return just name/address.
            # DB logic can be updated to accept empty category.
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    parse_naver_map_url("https://naver.me/Gj6XOmzg")
