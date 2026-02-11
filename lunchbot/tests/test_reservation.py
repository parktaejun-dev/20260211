"""예약 모듈 테스트"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.reservation import NaverReservation, ReservationResult
from config.constants import (
    RESERVATION_STATUS_SUCCESS,
    RESERVATION_STATUS_FAILED,
)


def test_reservation_result_dataclass():
    """ReservationResult 데이터클래스 생성 테스트."""
    result = ReservationResult(
        status=RESERVATION_STATUS_SUCCESS,
        message="예약 완료!",
        restaurant_name="테스트식당",
        reservation_date="2026년 2월 16일 (월)",
        reservation_time="12:00",
        party_size=12,
        reservation_number="NV-20260216-12345",
    )
    assert result.status == RESERVATION_STATUS_SUCCESS
    assert result.party_size == 12
    assert result.reservation_number == "NV-20260216-12345"


def test_reservation_result_to_dict():
    """ReservationResult to_dict 변환 테스트."""
    result = ReservationResult(
        status=RESERVATION_STATUS_FAILED,
        message="만석",
        restaurant_name="테스트",
        alternative_times=["11:30", "13:00"],
    )
    d = result.to_dict()
    assert isinstance(d, dict)
    assert d["status"] == RESERVATION_STATUS_FAILED
    assert d["alternative_times"] == ["11:30", "13:00"]


def test_naver_reservation_init():
    """NaverReservation 인스턴스 생성 테스트."""
    reserver = NaverReservation()
    assert reserver is not None
