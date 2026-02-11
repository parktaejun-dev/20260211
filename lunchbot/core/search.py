"""네이버 플레이스 기반 맛집 검색 엔진

Playwright로 네이버 지도를 크롤링하여 맛집을 검색합니다.
검색 결과에서 네이버 예약 가능 식당을 필터링합니다.
"""

import re
import time
from dataclasses import dataclass, field

from playwright.sync_api import Page
from bs4 import BeautifulSoup

from config.settings import AREA_CENTER, NAVER_PLACE_SEARCH_URL
from utils.geo import haversine_distance, format_distance, estimate_walking_time


@dataclass
class Restaurant:
    """식당 정보를 담는 데이터 클래스."""

    name: str
    address: str
    lat: float = 0.0
    lng: float = 0.0
    rating: float = 0.0
    review_count: int = 0
    price_range: str = ""
    cuisine_type: str = ""
    is_bookable: bool = False
    booking_url: str = ""
    place_url: str = ""
    phone: str = ""
    distance_m: float = 0.0
    distance_text: str = ""
    walking_time: str = ""
    thumbnail_url: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "address": self.address,
            "lat": self.lat,
            "lng": self.lng,
            "rating": self.rating,
            "review_count": self.review_count,
            "price_range": self.price_range,
            "cuisine_type": self.cuisine_type,
            "is_bookable": self.is_bookable,
            "booking_url": self.booking_url,
            "place_url": self.place_url,
            "phone": self.phone,
            "distance_m": self.distance_m,
            "distance_text": self.distance_text,
            "walking_time": self.walking_time,
        }


class RestaurantSearcher:
    """네이버 플레이스에서 맛집을 검색하는 클래스."""

    def __init__(self, center_lat: float | None = None, center_lng: float | None = None):
        self.center_lat = center_lat or AREA_CENTER["lat"]
        self.center_lng = center_lng or AREA_CENTER["lng"]

    def search(
        self, page: Page, cuisine_type: str, cuisine_keyword: str, radius: int = 500
    ) -> list[Restaurant]:
        """
        네이버 지도에서 맛집을 검색합니다.

        Args:
            page: Playwright Page 객체
            cuisine_type: 음식 종류 (한식, 중식 등)
            cuisine_keyword: 검색에 사용할 키워드
            radius: 검색 반경 (미터)

        Returns:
            Restaurant 객체 리스트 (네이버 예약 가능한 것 우선)
        """
        query = f"{AREA_CENTER['name']} {cuisine_keyword} 맛집"

        try:
            # 네이버 지도 검색
            search_url = f"{NAVER_PLACE_SEARCH_URL}/{query}"
            page.goto(search_url, wait_until="networkidle", timeout=15000)
            time.sleep(2)

            # 검색 결과 파싱
            restaurants = self._parse_search_results(page, cuisine_type)

            # 거리 계산 및 필터링
            restaurants = self._calculate_distances(restaurants)
            restaurants = self._filter_by_distance(restaurants, radius)

            # 예약 가능 식당 우선 정렬
            restaurants.sort(key=lambda r: (not r.is_bookable, -r.rating))

            return restaurants[:10]  # 상위 10개

        except Exception as e:
            print(f"검색 중 오류 발생: {e}")
            return []

    def _parse_search_results(self, page: Page, cuisine_type: str) -> list[Restaurant]:
        """검색 결과 페이지에서 식당 정보를 파싱합니다."""
        restaurants = []

        try:
            # iframe 내부의 검색 결과 접근
            # 네이버 지도는 검색 결과를 iframe으로 렌더링
            frame = None
            for f in page.frames:
                if "search" in f.url:
                    frame = f
                    break

            if frame is None:
                frame = page

            # 검색 결과 아이템 대기
            frame.wait_for_selector("li.UEzoS", timeout=10000)
            time.sleep(1)

            items = frame.query_selector_all("li.UEzoS")

            for item in items[:15]:  # 최대 15개 파싱
                try:
                    restaurant = self._parse_restaurant_item(item, frame, cuisine_type)
                    if restaurant:
                        restaurants.append(restaurant)
                except Exception:
                    continue

        except Exception as e:
            print(f"검색 결과 파싱 오류: {e}")

        return restaurants

    def _parse_restaurant_item(
        self, item, frame, cuisine_type: str
    ) -> Restaurant | None:
        """개별 검색 결과 아이템에서 식당 정보를 추출합니다."""
        try:
            # 식당 이름
            name_el = item.query_selector(".place_bluelink, .TYaxT")
            name = name_el.inner_text().strip() if name_el else ""
            if not name:
                return None

            # 주소
            address = ""
            addr_el = item.query_selector(".LDgIH")
            if addr_el:
                address = addr_el.inner_text().strip()

            # 평점
            rating = 0.0
            rating_el = item.query_selector(".h69bs .place_blind + span, .orXYY")
            if rating_el:
                try:
                    rating = float(rating_el.inner_text().strip())
                except ValueError:
                    pass

            # 리뷰 수
            review_count = 0
            review_el = item.query_selector(".h69bs .place_blind ~ span:last-child, .YeGNA")
            if review_el:
                text = review_el.inner_text().strip()
                nums = re.findall(r"[\d,]+", text)
                if nums:
                    review_count = int(nums[0].replace(",", ""))

            # 네이버 예약 가능 여부
            is_bookable = False
            booking_url = ""
            booking_el = item.query_selector(
                "a[href*='booking'], .VYhTw, span.fKpVS"
            )
            if booking_el:
                is_bookable = True
                href = booking_el.get_attribute("href")
                if href and "booking" in href:
                    booking_url = href

            # 식당 링크
            place_url = ""
            link_el = item.query_selector("a.place_bluelink, a.TYaxT")
            if link_el:
                place_url = link_el.get_attribute("href") or ""

            # 가격대
            price_range = ""
            price_el = item.query_selector(".price_text")
            if price_el:
                price_range = price_el.inner_text().strip()

            return Restaurant(
                name=name,
                address=address,
                rating=rating,
                review_count=review_count,
                cuisine_type=cuisine_type,
                is_bookable=is_bookable,
                booking_url=booking_url,
                place_url=place_url,
                price_range=price_range,
            )
        except Exception:
            return None

    def _calculate_distances(self, restaurants: list[Restaurant]) -> list[Restaurant]:
        """각 식당의 중심점으로부터의 거리를 계산합니다."""
        for r in restaurants:
            if r.lat and r.lng:
                r.distance_m = haversine_distance(
                    self.center_lat, self.center_lng, r.lat, r.lng
                )
                r.distance_text = format_distance(r.distance_m)
                r.walking_time = estimate_walking_time(r.distance_m)
        return restaurants

    def _filter_by_distance(
        self, restaurants: list[Restaurant], max_radius: int
    ) -> list[Restaurant]:
        """반경 이내의 식당만 필터링합니다. 좌표가 없는 식당은 통과."""
        return [
            r for r in restaurants if r.distance_m <= max_radius or not (r.lat and r.lng)
        ]

    def search_with_expanded_radius(
        self,
        page: Page,
        cuisine_type: str,
        cuisine_keyword: str,
        initial_radius: int = 500,
    ) -> tuple[list[Restaurant], int]:
        """
        검색 결과가 부족하면 반경을 자동 확대하여 재검색합니다.

        Returns:
            (식당 리스트, 최종 사용된 반경)
        """
        for radius in [initial_radius, initial_radius * 2, initial_radius * 3]:
            results = self.search(page, cuisine_type, cuisine_keyword, radius)
            bookable = [r for r in results if r.is_bookable]
            if bookable:
                return results, radius

        return results, radius
