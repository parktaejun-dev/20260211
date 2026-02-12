"""거리 계산 유틸리티"""

from math import radians, cos, sin, asin, sqrt


def haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    두 좌표 사이의 거리를 미터 단위로 계산 (Haversine 공식).

    Args:
        lat1, lng1: 첫 번째 지점 위도/경도
        lat2, lng2: 두 번째 지점 위도/경도

    Returns:
        거리 (미터)
    """
    R = 6371000  # 지구 반경 (미터)

    lat1, lng1, lat2, lng2 = map(radians, [lat1, lng1, lat2, lng2])

    dlat = lat2 - lat1
    dlng = lng2 - lng1

    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlng / 2) ** 2
    c = 2 * asin(sqrt(a))

    return R * c


def is_within_radius(
    lat: float, lng: float, center_lat: float, center_lng: float, radius_m: float
) -> bool:
    """지정된 좌표가 중심점으로부터 반경 이내인지 확인."""
    distance = haversine_distance(lat, lng, center_lat, center_lng)
    return distance <= radius_m


def format_distance(distance_m: float) -> str:
    """거리를 사람이 읽기 쉬운 형태로 포맷."""
    if distance_m < 1000:
        return f"{int(distance_m)}m"
    return f"{distance_m / 1000:.1f}km"


def estimate_walking_time(distance_m: float) -> str:
    """도보 시간 추정 (평균 보행 속도 4.5km/h 기준)."""
    minutes = distance_m / (4500 / 60)  # 4.5km/h = 75m/min
    if minutes < 1:
        return "1분 미만"
    return f"도보 {int(minutes)}분"
