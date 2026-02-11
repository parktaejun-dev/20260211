"""맛집 검색 모듈 테스트"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.search import Restaurant, RestaurantSearcher
from config.settings import AREA_CENTER


def test_restaurant_dataclass():
    """Restaurant 데이터클래스 생성 테스트."""
    r = Restaurant(
        name="테스트식당",
        address="서울 종로구",
        lat=37.570,
        lng=126.977,
        rating=4.5,
        review_count=100,
        is_bookable=True,
    )
    assert r.name == "테스트식당"
    assert r.rating == 4.5
    assert r.is_bookable is True


def test_restaurant_to_dict():
    """Restaurant to_dict 변환 테스트."""
    r = Restaurant(name="테스트", address="서울")
    d = r.to_dict()
    assert isinstance(d, dict)
    assert d["name"] == "테스트"
    assert "is_bookable" in d


def test_searcher_init_default_center():
    """RestaurantSearcher 기본 중심점 설정 테스트."""
    searcher = RestaurantSearcher()
    assert searcher.center_lat == AREA_CENTER["lat"]
    assert searcher.center_lng == AREA_CENTER["lng"]


def test_searcher_init_custom_center():
    """RestaurantSearcher 커스텀 중심점 설정 테스트."""
    searcher = RestaurantSearcher(center_lat=37.0, center_lng=127.0)
    assert searcher.center_lat == 37.0
    assert searcher.center_lng == 127.0


def test_filter_by_distance():
    """거리 기반 필터링 테스트."""
    searcher = RestaurantSearcher()
    restaurants = [
        Restaurant(name="가까운곳", address="", lat=37.5682, lng=126.9783, distance_m=100),
        Restaurant(name="먼곳", address="", lat=37.6, lng=127.0, distance_m=5000),
        Restaurant(name="좌표없음", address="", lat=0, lng=0, distance_m=0),
    ]

    filtered = searcher._filter_by_distance(restaurants, 500)
    names = [r.name for r in filtered]
    assert "가까운곳" in names
    assert "좌표없음" in names  # 좌표 없는 식당은 통과
    assert "먼곳" not in names
