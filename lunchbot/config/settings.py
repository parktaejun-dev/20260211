"""전역 설정"""

# 지역 설정 - 광화문/시청/무교동 중심 좌표
AREA_CENTER = {
    "lat": 37.5682,
    "lng": 126.9783,
    "name": "광화문/시청/무교동",
}

# 지역 선택 옵션
AREA_OPTIONS = {
    "광화문/시청/무교동": {"lat": 37.5682, "lng": 126.9783},
    "광화문역": {"lat": 37.5710, "lng": 126.9769},
    "시청역": {"lat": 37.5657, "lng": 126.9769},
    "무교동": {"lat": 37.5680, "lng": 126.9810},
    "종각역": {"lat": 37.5700, "lng": 126.9828},
    "을지로입구역": {"lat": 37.5660, "lng": 126.9822},
}

RADIUS_OPTIONS = [300, 500, 1000]  # meters

# 음식 종류 (표시명 → 검색 키워드)
CUISINE_TYPES = {
    "한식": "한식",
    "중식": "중식 중국집",
    "일식": "일식 초밥",
    "양식": "양식 파스타 스테이크",
    "분식": "분식",
    "동남아": "베트남 태국 동남아",
    "뷔페": "뷔페",
}

# 예산 옵션 (1인당)
BUDGET_OPTIONS = {
    "상관없음": (0, 999999),
    "~1만원": (0, 10000),
    "1~1.5만원": (10000, 15000),
    "1.5~2만원": (15000, 20000),
    "2~3만원": (20000, 30000),
    "3만원 이상": (30000, 999999),
}

# 시간 옵션
TIME_SLOTS = [
    "11:00",
    "11:30",
    "12:00",
    "12:30",
    "13:00",
    "13:30",
]

# 인원 범위
MIN_PARTY_SIZE = 2
MAX_PARTY_SIZE = 30
DEFAULT_PARTY_SIZE = 12

# 네이버 API
NAVER_SEARCH_API_URL = "https://openapi.naver.com/v1/search/local.json"
NAVER_PLACE_URL = "https://map.naver.com/v5/entry/place"
NAVER_BOOKING_BASE_URL = "https://booking.naver.com"

# 예약 이력 DB
HISTORY_DB_PATH = "data/history.db"

# 즐겨찾기 파일
FAVORITES_PATH = "data/favorites.json"
