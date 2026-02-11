"""네이버 검색 API 기반 맛집 검색 엔진

네이버 검색 API (Local)를 사용하여 맛집을 검색합니다.
https://developers.naver.com/docs/serviceapi/search/local/local.md
"""

import re
from dataclasses import dataclass

import httpx

from config.settings import NAVER_SEARCH_API_URL, AREA_CENTER
from utils.geo import haversine_distance, format_distance, estimate_walking_time


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
        }


def _clean_html(text: str) -> str:
    """HTML 태그를 제거합니다."""
    return re.sub(r"<[^>]+>", "", text)


def _katec_to_wgs84(x: int, y: int) -> tuple[float, float]:
    """
    네이버 API 좌표(KATEC)를 WGS84(위도/경도)로 근사 변환합니다.

    네이버 검색 API는 KATEC 좌표계를 사용합니다.
    정밀 변환은 아니지만 거리 필터링에 충분한 근사치를 제공합니다.
    """
    # TM128(KATEC) 좌표를 전국 단위로 안정적으로 다루기 위한 선형 근사.
    # (네이버 Local API mapx/mapy는 TM128 계열 값)
    # 정밀 변환은 아니지만 반경 필터링용 거리 계산에서는 충분히 정확합니다.
    lng = 123.86553 + (x * 0.00001)
    lat = 32.04723 + (y * 0.00001)

    return lat, lng


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
                headers={
                    "X-Naver-Client-Id": self.client_id,
                    "X-Naver-Client-Secret": self.client_secret,
                },
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
            try:
                mapx = int(item.get("mapx", 0))
                mapy = int(item.get("mapy", 0))
                lat, lng = _katec_to_wgs84(mapx, mapy)
            except (TypeError, ValueError):
                # 좌표 파싱 불가 시 거리 필터링에서 제외되지 않도록 중심 좌표를 사용
                lat, lng = self.center_lat, self.center_lng

            distance = haversine_distance(self.center_lat, self.center_lng, lat, lng)

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

            # 네이버 지도 링크 생성
            if restaurant.road_address:
                restaurant.map_url = (
                    f"https://map.naver.com/v5/search/{restaurant.name} {restaurant.road_address}"
                )

            restaurants.append(restaurant)

        # 거리 필터링
        restaurants = [r for r in restaurants if r.distance_m <= radius]

        # 거리순 정렬
        restaurants.sort(key=lambda r: r.distance_m)

        return restaurants

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
