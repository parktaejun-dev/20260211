import requests
from bs4 import BeautifulSoup

def parse_naver_map_url(url: str):
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"
    }
    
    try:
        print(f"Fetching {url}...")
        res = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
        print(f"Status Code: {res.status_code}")
        print(f"Final URL: {res.url}")
        
        soup = BeautifulSoup(res.text, "html.parser")
        
        og_title = soup.find("meta", property="og:title")
        og_desc = soup.find("meta", property="og:description")
        
        print(f"OG Title raw: {og_title}")
        print(f"OG Desc raw: {og_desc}")
        
        title = og_title["content"] if og_title else soup.title.string if soup.title else ""
        print(f"Title extracted: {title}")
        
        # Original logic
        name = title.split(":")[0].strip()
        print(f"Name extracted: {name}")

        desc = og_desc["content"] if og_desc else ""
        address = desc.split("|")[0].strip() if "|" in desc else desc
        print(f"Address extracted: {address}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    parse_naver_map_url("https://naver.me/Gj6XOmzg")
