"""데이터 파싱 및 유틸리티"""
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import json
import streamlit as st

def parse_naver_map_url(url: str) -> dict | None:
    """
    네이버 지도 URL에서 식당 이름, 주소, 카테고리를 추출합니다.
    redirect URL을 추적하여 Place ID를 얻고, 모바일 페이지를 스크래핑하거나
    실패 시 네이버 검색 API를 통해 보정합니다.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"
    }
    
    try:
        # 1. Expand Short URL & Extract Place ID
        session = requests.Session()
        res = session.get(url, headers=headers, timeout=10, allow_redirects=True)
        # UTF-8 강제
        res.encoding = "utf-8"
        final_url = res.url
        
        place_id = None
        patterns = [r'place/(\d+)', r'restaurant/(\d+)', r'id=(\d+)', r'pinId=(\d+)']
        for pattern in patterns:
            match = re.search(pattern, final_url)
            if match:
                place_id = match.group(1)
                break
        
        name = ""
        category = ""
        address = ""
        
        if place_id:
            # 2. Scrape Mobile Page
            mobile_url = f"https://m.place.naver.com/restaurant/{place_id}/home"
            m_res = session.get(mobile_url, headers=headers, timeout=5)
            m_res.encoding = "utf-8"
            soup = BeautifulSoup(m_res.text, "html.parser")
            
            # Name from OG Title
            og_title = soup.find("meta", property="og:title")
            raw_title = og_title["content"] if og_title else ""
            # "부민옥 : 네이버" -> "부민옥"
            name = raw_title.split(":")[0].strip()
            
            # JSON-LD for Address & Category
            scripts = soup.find_all("script", type="application/ld+json")
            for s in scripts:
                try:
                    js = json.loads(s.string)
                    if "@type" in js and js["@type"] in ["Restaurant", "CafeOrCoffeeShop", "Place"]:
                         if not name: name = js.get("name", "")
                         if not category: category = js.get("servesCuisine", "")
                         if not address: address = js.get("address", {}).get("streetAddress", "")
                except:
                    pass
            
            # Fallback Address from OG Description if needed
            if not address:
                og_desc = soup.find("meta", property="og:description")
                desc = og_desc["content"] if og_desc else ""
                if "|" in desc:
                    address = desc.split("|")[0].strip()

        # 3. Fallback: If scraping failed to get Name, use basic extraction
        if not name and "naver.com" in url:
             # Basic fallback (old logic)
             pass

        # 4. Search API Fallback for Category/Address if Name exists but details missing
        if name and (not category or not address):
            api_info = _search_naver_api(name)
            if api_info:
                if not category: category = api_info.get("category", "")
                if not address: address = api_info.get("address", "")
        
        if name:
            return {
                "name": name,
                "address": address,
                "category": category, # New field
                "url": url
            }
            
    except Exception as e:
        print(f"[Parser Error] {e}")
        
    return None

def _search_naver_api(query: str) -> dict | None:
    """네이버 검색 API를 통해 카테고리와 주소를 보완합니다."""
    try:
        client_id = st.secrets["NAVER_CLIENT_ID"]
        client_secret = st.secrets["NAVER_CLIENT_SECRET"]
        
        url = "https://openapi.naver.com/v1/search/local.json"
        headers = {
            "X-Naver-Client-Id": client_id,
            "X-Naver-Client-Secret": client_secret
        }
        params = {"query": query, "display": 1, "sort": "random"}
        
        res = requests.get(url, headers=headers, params=params, timeout=3)
        if res.status_code == 200:
            items = res.json().get("items", [])
            if items:
                item = items[0]
                # category example: "음식점>한식"
                cat = item.get("category", "")
                # Clean html tags
                title = re.sub(r"<[^>]+>", "", item.get("title", ""))
                
                # Verify name match roughly
                if query.replace(" ", "") in title.replace(" ", ""):
                    return {
                        "category": cat,
                        "address": item.get("address", "")
                    }
    except Exception:
        pass
    return None

def parse_uploaded_file(uploaded_file) -> list[dict]:
    """
    업로드된 파일(CSV/Excel)을 파싱하여 딕셔너리 리스트로 반환합니다.
    기대 컬럼: name(필수), address, memo, category
    """
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(uploaded_file)
        else:
            return []
            
        # 컬럼 이름 정규화 (소문자, 공백 제거)
        df.columns = [str(c).lower().strip() for c in df.columns]
        
        # 필수 컬럼 확인
        if 'name' not in df.columns and '식당명' not in df.columns:
            return []
            
        # 이름 컬럼 매핑
        name_col = 'name' if 'name' in df.columns else '식당명'
        addr_col = 'address' if 'address' in df.columns else '주소'
        memo_col = 'memo' if 'memo' in df.columns else '메모'
        cat_col = 'category' if 'category' in df.columns else '카테고리'
        if cat_col not in df.columns: cat_col = '업종' # Alias
        
        results = []
        for _, row in df.iterrows():
            name = str(row[name_col]).strip()
            if not name or name.lower() == 'nan':
                continue
                
            address = str(row[addr_col]).strip() if addr_col in df.columns and str(row[addr_col]).lower() != 'nan' else ""
            memo = str(row[memo_col]).strip() if memo_col in df.columns and str(row[memo_col]).lower() != 'nan' else ""
            category = str(row[cat_col]).strip() if cat_col in df.columns and str(row[cat_col]).lower() != 'nan' else ""

            results.append({
                "name": name,
                "address": address,
                "memo": memo,
                "category": category
            })
            
        return results
        
    except Exception as e:
        print(f"[File Parse Error] {e}")
        return []
