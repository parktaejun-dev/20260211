"""데이터 파싱 및 유틸리티"""
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import io

def parse_naver_map_url(url: str) -> dict | None:
    """
    네이버 지도 URL에서 식당 이름과 주소를 추출합니다.
    크롤링 차단으로 인해 제한적일 수 있으며, 메타 태그(Title/Og:Title)를 활용합니다.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        # 1. URL 유효성 검사
        if "naver.com" not in url:
            return None
            
        # 2. Requests 호출
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code != 200:
            return None
            
        soup = BeautifulSoup(res.text, "html.parser")
        
        # 3. 메타 태그 추출
        # og:title -> "식당이름 : 네이버 방문자리뷰..."
        og_title = soup.find("meta", property="og:title")
        title = og_title["content"] if og_title else soup.title.string if soup.title else ""
        
        # 정제: "명동교자 본점 : 네이버 방문자리뷰 1234건..." -> "명동교자 본점"
        name = title.split(":")[0].strip()
        
        # og:description -> "서울 중구 명동 ... | 메뉴..."
        og_desc = soup.find("meta", property="og:description")
        desc = og_desc["content"] if og_desc else ""
        
        # 주소 추출 시도 (설명 앞부분이 보통 주소)
        # "서울 중구 명동길 29"
        address = desc.split("|")[0].strip() if "|" in desc else desc
        
        if name:
            return {"name": name, "address": address, "url": url}
            
    except Exception as e:
        print(f"[Parser Error] {e}")
        
    return None

def parse_uploaded_file(uploaded_file) -> list[dict]:
    """
    업로드된 파일(CSV/Excel)을 파싱하여 딕셔너리 리스트로 반환합니다.
    기대 컬럼: name(필수), address, memo
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
        
        results = []
        for _, row in df.iterrows():
            name = str(row[name_col]).strip()
            if not name or name.lower() == 'nan':
                continue
                
            address = str(row[addr_col]).strip() if addr_col in df.columns and str(row[addr_col]).lower() != 'nan' else ""
            memo = str(row[memo_col]).strip() if memo_col in df.columns and str(row[memo_col]).lower() != 'nan' else ""
            
            results.append({
                "name": name,
                "address": address,
                "memo": memo
            })
            
        return results
        
    except Exception as e:
        print(f"[File Parse Error] {e}")
        return []
