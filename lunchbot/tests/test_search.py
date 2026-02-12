"""맛집 검색 모듈 테스트"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from bot_core.search import (
    BlogReview,
    Restaurant,
    RestaurantSearcher,
    _clean_html,
    _is_reasonable_korea_coordinate,
    _katec_to_wgs84,
)
from bot_config.settings import AREA_CENTER, NAVER_BLOG_SEARCH_API_URL, NAVER_SEARCH_API_URL


def test_restaurant_dataclass():
    """Restaurant 데이터클래스 생성 테스트."""
    r = Restaurant(
        name="테스트식당",
        address="서울 종로구",
        lat=37.570,
        lng=126.977,
        category="한식",
        phone="02-1234-5678",
    )
    assert r.name == "테스트식당"
    assert r.category == "한식"


def test_restaurant_to_dict():
    """Restaurant to_dict 변환 테스트."""
    r = Restaurant(
        name="테스트",
        address="서울",
        blog_reviews=[BlogReview(title="리뷰", link="https://example.com")],
    )
    d = r.to_dict()
    assert isinstance(d, dict)
    assert d["name"] == "테스트"
    assert "category" in d
    assert d["blog_reviews"][0]["title"] == "리뷰"


def test_clean_html():
    """HTML 태그 제거 테스트."""
    assert _clean_html("<b>맛집</b>") == "맛집"
    assert _clean_html("일반텍스트") == "일반텍스트"
    assert _clean_html("<a href='x'>링크</a>") == "링크"


def test_katec_to_wgs84():
    """KATEC 좌표 변환 테스트."""
    lat, lng = _katec_to_wgs84(310000, 552000)
    # 광화문 인근 좌표가 나와야 함
    assert 37.0 < lat < 38.0
    assert 126.0 < lng < 128.0


def test_search_with_invalid_map_coordinates(monkeypatch):
    """mapx/mapy 파싱 불가 데이터가 있어도 검색이 실패하지 않아야 한다."""

    class MockResponse:
        def __init__(self, payload):
            self._payload = payload

        def raise_for_status(self):
            return None

        def json(self):
            return self._payload

    def mock_get(url, *args, **kwargs):
        if url == NAVER_SEARCH_API_URL:
            return MockResponse(
                {
                    "items": [
                        {
                            "title": "<b>테스트 식당</b>",
                            "address": "서울 종로구",
                            "roadAddress": "서울 종로구 세종대로",
                            "mapx": "",
                            "mapy": None,
                            "category": "한식",
                            "description": "<b>맛집</b>",
                            "telephone": "02-0000-0000",
                            "link": "https://example.com",
                        }
                    ]
                }
            )

        return MockResponse({"items": []})

    monkeypatch.setattr("bot_core.search.httpx.get", mock_get)

    searcher = RestaurantSearcher(
        client_id="id",
        client_secret="secret",
        center_lat=37.5682,
        center_lng=126.9783,
    )
    results = searcher.search("광화문", "한식")

    assert len(results) == 1
    assert results[0].name == "테스트 식당"


def test_reasonable_korea_coordinate():
    """좌표 유효성 판별 테스트."""
    assert _is_reasonable_korea_coordinate(37.56, 126.97) is True
    assert _is_reasonable_korea_coordinate(10.0, 126.97) is False


def test_search_fallback_when_all_filtered_out(monkeypatch):
    """거리 필터에서 전부 탈락해도 원본 결과를 반환해야 한다."""

    class MockResponse:
        def __init__(self, payload):
            self._payload = payload

        def raise_for_status(self):
            return None

        def json(self):
            return self._payload

    def mock_get(url, *args, **kwargs):
        if url == NAVER_SEARCH_API_URL:
            return MockResponse(
                {
                    "items": [
                        {
                            "title": "<b>테스트 식당A</b>",
                            "address": "서울 종로구",
                            "roadAddress": "서울 종로구 세종대로",
                            "mapx": "800000",
                            "mapy": "900000",
                            "category": "한식",
                            "description": "<b>맛집</b>",
                        },
                        {
                            "title": "<b>테스트 식당B</b>",
                            "address": "서울 종로구",
                            "roadAddress": "서울 종로구 세종대로",
                            "mapx": "810000",
                            "mapy": "910000",
                            "category": "한식",
                            "description": "<b>맛집</b>",
                        },
                    ]
                }
            )

        return MockResponse({"items": []})

    monkeypatch.setattr("bot_core.search.httpx.get", mock_get)

    searcher = RestaurantSearcher(
        client_id="id",
        client_secret="secret",
        center_lat=37.5682,
        center_lng=126.9783,
    )

    # 아주 작은 반경으로 필터링을 강제해도 결과 자체는 반환되어야 함
    results = searcher.search("광화문", "한식", radius=10)

    assert len(results) == 2


def test_map_uses_restaurant_name_only_and_blog_reviews(monkeypatch):
    """지도 검색 링크는 상호명만 사용하고 블로그 리뷰를 포함해야 한다."""

    class MockResponse:
        def __init__(self, payload):
            self._payload = payload

        def raise_for_status(self):
            return None

        def json(self):
            return self._payload

    def mock_get(url, *args, **kwargs):
        if url == NAVER_SEARCH_API_URL:
            return MockResponse(
                {
                    "items": [
                        {
                            "title": "<b>테스트 식당</b>",
                            "address": "서울 종로구",
                            "roadAddress": "서울 종로구 세종대로",
                            "mapx": "310000",
                            "mapy": "552000",
                            "category": "한식",
                            "description": "<b>맛집</b>",
                        }
                    ]
                }
            )

        if url == NAVER_BLOG_SEARCH_API_URL:
            return MockResponse(
                {
                    "items": [
                        {
                            "title": "<b>리뷰1</b>",
                            "link": "https://blog.example/1",
                            "description": "<b>좋았음</b>",
                        },
                        {
                            "title": "<b>리뷰2</b>",
                            "link": "https://blog.example/2",
                            "description": "<b>괜찮음</b>",
                        },
                    ]
                }
            )

        raise AssertionError("unexpected url")

    monkeypatch.setattr("bot_core.search.httpx.get", mock_get)

    searcher = RestaurantSearcher(
        client_id="id",
        client_secret="secret",
        center_lat=37.5682,
        center_lng=126.9783,
    )
    results = searcher.search("광화문", "한식")

    assert len(results) == 1
    assert "/%ED%85%8C%EC%8A%A4%ED%8A%B8%20%EC%8B%9D%EB%8B%B9" in results[0].map_url
    assert "%EC%84%B8%EC%A2%85%EB%8C%80%EB%A1%9C" not in results[0].map_url
    assert len(results[0].blog_reviews) == 2


def test_searcher_init():
    """RestaurantSearcher 초기화 테스트."""
    searcher = RestaurantSearcher(
        client_id="test_id",
        client_secret="test_secret",
    )
    assert searcher.client_id == "test_id"
    assert searcher.center_lat == AREA_CENTER["lat"]


def test_searcher_custom_center():
    """RestaurantSearcher 커스텀 중심점 테스트."""
    searcher = RestaurantSearcher(
        client_id="id",
        client_secret="secret",
        center_lat=37.0,
        center_lng=127.0,
    )
    assert searcher.center_lat == 37.0
    assert searcher.center_lng == 127.0


def test_map_url_and_phone_extraction(monkeypatch):
    """지도가 주소 없이 상호명만 사용하는지, 전화번호가 추출되는지 확인."""

    class MockResponse:
        def __init__(self, payload):
            self._payload = payload

        def raise_for_status(self):
            return None

        def json(self):
            return self._payload

    def mock_get(url, *args, **kwargs):
        if url == NAVER_SEARCH_API_URL:
            return MockResponse(
                {
                    "items": [
                        {
                            "title": "<b>맛있는 식당</b>",
                            "address": "서울 종로구",
                            "roadAddress": "서울 종로구 세종대로 123",
                            "mapx": "310000",
                            "mapy": "552000",
                            "category": "한식",
                            "description": "맛집입니다",
                            "telephone": "02-1234-5678",
                            "link": "https://restaurant.com",
                        }
                    ]
                }
            )
        return MockResponse({"items": []})

    monkeypatch.setattr("bot_core.search.httpx.get", mock_get)

    searcher = RestaurantSearcher(
        client_id="id",
        client_secret="secret",
    )
    results = searcher.search("광화문", "한식")

    assert len(results) == 1
    r = results[0]

    # 1. 지도 링크 확인: 상호명만 포함되어야 함
    # 주소(세종대로, 123 등)가 포함되면 안 됨
    assert "https://map.naver.com/v5/search/" in r.map_url
    assert "%EB%A7%9B%EC%9E%88%EB%8A%94%20%EC%8B%9D%EB%8B%B9" in r.map_url  # '맛있는 식당' URL 인코딩
    assert "123" not in r.map_url
    assert "세종대로" not in r.map_url

    # 2. 전화번호 확인
    assert r.phone == "02-1234-5678"
