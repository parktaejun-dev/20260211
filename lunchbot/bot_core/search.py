"""네이버 검색 API 기반 맛집 검색 엔진

네이버 검색 API (Local)를 사용하여 맛집을 검색합니다.
https://developers.naver.com/docs/serviceapi/search/local/local.md
"""

import re
from dataclasses import dataclass, field
from urllib.parse import quote

import httpx

from bot_config.settings import NAVER_SEARCH_API_URL, NAVER_BLOG_SEARCH_API_URL, AREA_CENTER, SEARCH_AREAS
from bot_utils.geo import haversine_distance, format_distance, estimate_walking_time


@dataclass
class BlogReview:
    """블로그 리뷰 요약 데이터 클래스."""

    title: str
    link: str
    snippet: str = ""


@dataclass
class Restaurant:
    """식당 정보 데이터 클래스."""

    name: str
    address: str
    road_address: str = ""
    lat: float = 0.0
    lng: float = 0.0
    category: str = ""
    description: str = ""
    phone: str = ""
    link: str = ""
    map_url: str = ""
    distance_m: float = 0.0
    price: str = "" # 평균 가격대 (블로그 검색 등으로 추정)
    distance_text: str = ""
    walking_time: str = ""
    blog_reviews: list[BlogReview] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "address": self.address,
            "road_address": self.road_address,
            "lat": self.lat,
            "lng": self.lng,
            "category": self.category,
            "phone": self.phone,
            "link": self.link,
            "map_url": self.map_url,
            "distance_m": self.distance_m,
            "distance_text": self.distance_text,
            "walking_time": self.walking_time,
            "blog_reviews": [
                {"title": r.title, "link": r.link, "snippet": r.snippet}
                for r in self.blog_reviews
            ],
        }


def _clean_html(text: str) -> str:
    """HTML 태그를 제거합니다."""
    return re.sub(r"<[^>]+>", "", text)


def _katec_to_wgs84(x: int, y: int) -> tuple[float, float]:
    """
    네이버 API 좌표(KATEC/TM128)를 WGS84(위도/경도)로 근사 변환합니다.

    NOTE:
        TM128 정밀 변환 라이브러리(pyproj 등)가 없는 환경을 고려해
        서비스에 필요한 범위(서울권)에서 충분한 정확도의 근사식을 사용합니다.
    """
    # 서울/수도권에서 실사용 가능한 경험식 근사
    lng = 123.76 + (x * 1.0e-5)
    lat = 32.85 + (y * 8.8e-6)

    return lat, lng


def _is_reasonable_korea_coordinate(lat: float, lng: float) -> bool:
    """대한민국 권역의 합리적 위경도인지 확인합니다."""
    return 33.0 <= lat <= 39.5 and 124.0 <= lng <= 132.0


class RestaurantSearcher:
    """네이버 검색 API로 맛집을 검색하는 클래스."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        center_lat: float | None = None,
        center_lng: float | None = None,
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.center_lat = center_lat or AREA_CENTER["lat"]
        self.center_lng = center_lng or AREA_CENTER["lng"]

    @property
    def _api_headers(self) -> dict[str, str]:
        return {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret,
        }

    def _fetch_blog_reviews(
        self,
        restaurant_name: str,
        review_count: int = 3,
    ) -> list[BlogReview]:
        """식당 블로그 리뷰를 가져옵니다."""
        try:
            response = httpx.get(
                NAVER_BLOG_SEARCH_API_URL,
                params={
                    "query": f"{restaurant_name} 후기",
                    "display": review_count,
                    "start": 1,
                    "sort": "sim",
                },
                headers=self._api_headers,
                timeout=10,
            )
            response.raise_for_status()
            items = response.json().get("items", [])
        except (httpx.HTTPError, ValueError):
            return []

        reviews: list[BlogReview] = []
        for item in items:
            reviews.append(
                BlogReview(
                    title=_clean_html(item.get("title", "")),
                    link=item.get("link", ""),
                    snippet=_clean_html(item.get("description", "")),
                )
            )

        return reviews

    def search_blog_for_price(self, restaurant_name: str) -> str:
        """
        블로그 검색 API를 이용하여 식당의 메뉴 가격 정보를 추정합니다.
        
        Args:
           restaurant_name: 식당 이름 (예: "명동교자")
           
        Returns:
            str: 추정된 가격 정보 (예: "11,000원") 또는 빈 문자열
        """
        query = f"{restaurant_name} 메뉴판 가격"
        params = {
            "query": query,
            "display": 5,
            "sort": "sim"
        }
        
        try:
            res = httpx.get(
                NAVER_BLOG_SEARCH_API_URL,
                headers=self.headers,
                params=params,
                timeout=2.0 # 빠른 응답 요구
            )
            
            if res.status_code == 200:
                data = res.json()
                items = data.get("items", [])
                
                prices = []
                for item in items:
                    description = item.get("description", "")
                    # HTML 태그 제거 및 텍스트 정제
                    text = re.sub(r"<[^>]+>", "", description)
                    
                    # 가격 패턴 찾기 (숫자 + 원) - 예: 10,000원, 11000원
                    # 너무 작은 숫자나 배달비 제외, 4자리 이상 숫자
                    matches = re.findall(r'([0-9,]{3,})원', text)
                    for m in matches:
                        price = int(m.replace(",", ""))
                        if 3000 <= price <= 300000: # 합리적인 범위
                            prices.append(price)
                            
                if prices:
                    # 가장 빈번하게 등장한 가격 또는 평균값? 
                    # 보통 대표 메뉴 가격이 많이 언급됨.
                    # 최빈값 찾기
                    from collections import Counter
                    most_common = Counter(prices).most_common(1)
                    if most_common:
                        return f"{most_common[0][0]:,}원"
            
        except Exception as e:
            print(f"[ERROR] Blog search failed: {e}")
            
        return ""

    def _search_single_area(
        self,
        area_name: str,
        cuisine_keyword: str,
        budget_keyword: str = "",
        display: int = 5,
    ) -> list[dict]:
        """단일 지역으로 네이버 API를 호출, raw items을 반환합니다."""
        parts = [area_name, cuisine_keyword]
        if budget_keyword:
            parts.append(budget_keyword)
        query = " ".join(parts)

        try:
            response = httpx.get(
                NAVER_SEARCH_API_URL,
                params={
                    "query": query,
                    "display": min(display, 10),
                    "start": 1,
                    "sort": "comment",
                },
                headers=self._api_headers,
                timeout=10,
            )
            response.raise_for_status()
            return response.json().get("items", [])
        except (httpx.HTTPError, ValueError):
            return []

    def search(
        self,
        area_name: str,
        cuisine_keyword: str,
        radius: int = 1000,
        display: int = 10,
        budget_keyword: str = "",
    ) -> list[Restaurant]:
        """
        여러 지역명으로 네이버 검색 API를 호출하고 결과를 병합합니다.

        Args:
            area_name: 미사용 (호환성 유지)
            cuisine_keyword: 검색 키워드 (예: "한식", "맛집")
            radius: 검색 반경 (미터)
            display: 결과 표시 개수
            budget_keyword: 예산 관련 키워드 (예: "저렴한 가성비")

        Returns:
            Restaurant 리스트 (중복 제거, 거리순 정렬)
        """
        # 여러 지역으로 검색하여 raw items 수집
        all_items: list[dict] = []
        seen_names: set[str] = set()

        # "양식 파스타 스테이크" 처럼 공백으로 구분된 키워드를 분리하여 각각 검색
        keywords = cuisine_keyword.split()

        for area in SEARCH_AREAS:
            for kw in keywords:
                items = self._search_single_area(area, kw, budget_keyword)
                for item in items:
                    name = _clean_html(item.get("title", ""))
                    if name and name not in seen_names:
                        seen_names.add(name)
                        all_items.append(item)

        from bot_core.db import db

        restaurants = []
        for item in all_items:
            title = _clean_html(item.get("title", ""))
            address = item.get("address", "")

            # 제외된 식당 필터링
            # 제외된 식당 필터링 (사용자 설정)
            if db.is_excluded(title, address):
                continue
            
            # 업종 필터링 (카페, 술집 등 제외)
            from bot_config.settings import EXCLUDED_CATEGORIES
            category = _clean_html(item.get("category", ""))
            # 카테고리 문자열에 제외 키워드가 포함되어 있으면 건너뜀
            if any(exc in category for exc in EXCLUDED_CATEGORIES):
                continue

            lat, lng = self.center_lat, self.center_lng
            distance = 0.0
            try:
                raw_x = item.get("mapx", 0)
                raw_y = item.get("mapy", 0)
                mapx = int(raw_x) if raw_x else 0
                mapy = int(raw_y) if raw_y else 0

                if mapx > 0 and mapy > 0:
                    # 2023.08 이후: WGS84 좌표 (정수형, 10^7 배율)
                    # 예: mapx=1269873882 → lng=126.9873882
                    if mapx > 1000000:
                        converted_lng = mapx / 1e7
                        converted_lat = mapy / 1e7
                    else:
                        # 혹시 구형 KATEC 좌표가 오면 근사 변환
                        converted_lng = 123.76 + (mapx * 1.0e-5)
                        converted_lat = 32.85 + (mapy * 8.8e-6)

                    if _is_reasonable_korea_coordinate(converted_lat, converted_lng):
                        lat, lng = converted_lat, converted_lng
                        distance = haversine_distance(self.center_lat, self.center_lng, lat, lng)
            except (TypeError, ValueError):
                pass

            restaurant = Restaurant(
                name=title,
                address=address,
                road_address=item.get("roadAddress", ""),
                lat=lat,
                lng=lng,
                category=item.get("category", ""),
                description=_clean_html(item.get("description", "")),
                phone=item.get("telephone", ""),
                link=item.get("link", ""),
                distance_m=distance,
                distance_text=format_distance(distance),
                walking_time=estimate_walking_time(distance),
            )

            if restaurant.name:
                restaurant.map_url = f"https://map.naver.com/v5/search/{quote(restaurant.name)}"

            # 블로그 리뷰
            restaurant.blog_reviews = self._fetch_blog_reviews(restaurant.name)

            restaurants.append(restaurant)

        # 거리 필터링
        # 거리 필터링
        filtered = [r for r in restaurants if r.distance_m <= radius]

        final_results = []
        if filtered:
            filtered.sort(key=lambda r: r.distance_m)
            final_results = filtered[:display]
        elif restaurants:
            # 폴백: 전부 탈락 시 거리순 전체 반환
            restaurants.sort(key=lambda r: r.distance_m)
            final_results = restaurants[:display]

        # 최종 결과에 대해 가격 정보 채우기 (API 호출 최소화)
        for r in final_results:
             if not r.price:
                 r.price = self.search_blog_for_price(r.name)

        return final_results

    def search_with_expanded_radius(
        self,
        area_name: str,
        cuisine_keyword: str,
        initial_radius: int = 1000,
        max_radius: int = 2000,
    ) -> tuple[list[Restaurant], int]:
        """
        검색 결과가 부족하면 반경을 자동 확대합니다 (최대 2km).

        Returns:
            (식당 리스트, 최종 사용된 반경)
        """
        for radius in [initial_radius, min(initial_radius * 2, max_radius)]:
            results = self.search(area_name, cuisine_keyword, radius)
            if results:
                return results, radius

        # 최대 반경으로 마지막 시도
        results = self.search(area_name, cuisine_keyword, radius=max_radius)
        return results, max_radius
