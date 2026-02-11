"""유틸리티 모듈 테스트"""

import sys
from pathlib import Path
from datetime import date

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.geo import haversine_distance, is_within_radius, format_distance, estimate_walking_time
from utils.date_helper import get_next_monday, format_date_korean, format_date_short


# ── geo 테스트 ────────────────────────────────────────────

def test_haversine_same_point():
    """같은 지점의 거리는 0."""
    d = haversine_distance(37.5682, 126.9783, 37.5682, 126.9783)
    assert d == 0.0


def test_haversine_known_distance():
    """광화문역~시청역 거리 (약 600m)."""
    d = haversine_distance(37.5710, 126.9769, 37.5657, 126.9769)
    assert 500 < d < 700


def test_is_within_radius_true():
    d = is_within_radius(37.5690, 126.978, 37.5682, 126.9783, 500)
    assert d is True


def test_is_within_radius_false():
    d = is_within_radius(37.6, 127.0, 37.5682, 126.9783, 500)
    assert d is False


def test_format_distance_meters():
    assert format_distance(350) == "350m"


def test_format_distance_km():
    assert format_distance(1500) == "1.5km"


def test_estimate_walking_time():
    result = estimate_walking_time(300)
    assert "분" in result


# ── date_helper 테스트 ────────────────────────────────────

def test_get_next_monday_from_monday():
    """월요일에서 다음 월요일은 자기 자신."""
    monday = date(2026, 2, 16)  # 월요일
    assert get_next_monday(monday) == monday


def test_get_next_monday_from_wednesday():
    """수요일에서 다음 월요일."""
    wednesday = date(2026, 2, 11)  # 수요일
    result = get_next_monday(wednesday)
    assert result == date(2026, 2, 16)
    assert result.weekday() == 0  # 월요일


def test_format_date_korean():
    d = date(2026, 2, 16)
    result = format_date_korean(d)
    assert "2026년" in result
    assert "2월" in result
    assert "16일" in result
    assert "월" in result


def test_format_date_short():
    d = date(2026, 2, 16)
    result = format_date_short(d)
    assert "02/16" in result
    assert "월" in result
