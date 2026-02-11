"""네이버 검색 API 기반 맛집 검색 엔진

네이버 검색 API (Local)를 사용하여 맛집을 검색합니다.
https://developers.naver.com/docs/serviceapi/search/local/local.md
"""

import re
from dataclasses import dataclass, field
from urllib.parse import quote

import httpx

from config.settings import NAVER_SEARCH_API_URL, NAVER_BLOG_SEARCH_API_URL, AREA_CENTER
from utils.geo import haversine_distance, format_distance, estimate_walking_time


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
        area_name: str,
        restaurant_name: str,
        review_count: int = 3,
    ) -> list[BlogReview]:
        """식당 블로그 리뷰를 가져옵니다."""
        try:
            response = httpx.get(
                NAVER_BLOG_SEARCH_API_URL,
                params={
                    "query": f"{area_name} {restaurant_name} 후기",
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

    def search(
        self,
        area_name: str,
        cuisine_keyword: str,
        radius: int = 500,
        display: int = 10,
    ) -> list[Restaurant]:
        """
        네이버 검색 API로 맛집을 검색합니다.

        Args:
            area_name: 지역명 (예: "광화문")
            cuisine_keyword: 검색 키워드 (예: "한식")
            radius: 검색 반경 (미터)
            display: 결과 표시 개수

        Returns:
            Restaurant 리스트
        """
        query = f"{area_name} {cuisine_keyword} 맛집"

        try:
            response = httpx.get(
                NAVER_SEARCH_API_URL,
                params={
                    "query": query,
                    "display": min(display, 5),
                    "start": 1,
                    "sort": "comment",  # 리뷰 많은 순
                },
                headers=self._api_headers,
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()

        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"네이버 API 오류 (HTTP {e.response.status_code}): {e.response.text}")
        except httpx.RequestError as e:
            raise RuntimeError(f"네이버 API 요청 실패: {str(e)}")

        restaurants = []
        for item in data.get("items", []):
            lat, lng = self.center_lat, self.center_lng
            distance = 0.0
            try:
                mapx = int(item.get("mapx", 0))
                mapy = int(item.get("mapy", 0))
                converted_lat, converted_lng = _katec_to_wgs84(mapx, mapy)

                if _is_reasonable_korea_coordinate(converted_lat, converted_lng):
                    lat, lng = converted_lat, converted_lng
                    distance = haversine_distance(self.center_lat, self.center_lng, lat, lng)
            except (TypeError, ValueError):
                # 좌표 파싱 불가 시 거리 정보는 중심 좌표 기준으로 대체
                pass

            restaurant = Restaurant(
                name=_clean_html(item.get("title", "")),
                address=item.get("address", ""),
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

            # 네이버 지도 링크는 상호명만 사용
            if restaurant.name:
                restaurant.map_url = f"https://map.naver.com/v5/search/{quote(restaurant.name)}"

            # 블로그 리뷰 일부를 함께 노출
            restaurant.blog_reviews = self._fetch_blog_reviews(area_name, restaurant.name)

            restaurants.append(restaurant)

        # 거리 필터링
        filtered_restaurants = [r for r in restaurants if r.distance_m <= radius]

        # TM128 좌표 오차로 전부 탈락하는 경우를 방지하기 위해 원본 결과로 폴백
        if filtered_restaurants:
            filtered_restaurants.sort(key=lambda r: r.distance_m)
            return filtered_restaurants

        if restaurants:
            restaurants.sort(key=lambda r: r.distance_m)
            return restaurants

        return []

    def search_with_expanded_radius(
        self,
        area_name: str,
        cuisine_keyword: str,
        initial_radius: int = 500,
    ) -> tuple[list[Restaurant], int]:
        """
        검색 결과가 부족하면 반경을 자동 확대합니다.

        Returns:
            (식당 리스트, 최종 사용된 반경)
        """
        for radius in [initial_radius, initial_radius * 2, initial_radius * 4]:
            results = self.search(area_name, cuisine_keyword, radius)
            if results:
                return results, radius

        # 필터링 없이 전체 반환
        results = self.search(area_name, cuisine_keyword, radius=999999)
        return results, 999999
