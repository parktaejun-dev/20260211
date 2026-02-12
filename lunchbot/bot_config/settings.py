"""전역 설정"""

# 거리 기준점 - 한국프레스센터 (서울특별시 중구 세종대로 124)
AREA_CENTER = {
    "lat": 37.5700,
    "lng": 126.9768,
    "name": "한국프레스센터",
}

# 네이버 검색 API에 사용할 지역명 목록
SEARCH_AREAS = [
    "광화문", "시청역", "을지로", "을지로입구",
    "종각", "다동", "북창동", "남대문", "서소문", "종로",
    "명동", "남대문시장",
]

RADIUS_OPTIONS = [500, 1000, 1500, 2000]  # meters (기본 1km, 최대 2km)
DEFAULT_RADIUS = 1000  # 기본 반경 1km

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

# 예산별 검색 키워드 (쿼리에 추가하여 가격대 유도)
BUDGET_KEYWORDS = {
    "상관없음": "",
    "~1만원": "저렴한 가성비",
    "1~1.5만원": "가성비 점심",
    "1.5~2만원": "점심 직장인",
    "2~3만원": "회식",
    "3만원 이상": "고급",
}

# 검색 결과에서 제외할 업종 키워드
# 샌드위치/샐러드는 점심 메뉴일 수 있음. 일단 카페류만 강력 제외.
EXCLUDED_CATEGORIES = [
    "카페", "커피", "디저트", "베이커리", "빵", "케이크", "빙수", 
    "찻집", "다방", "술집", "주점", "호프", "바(Bar)", 
]

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
DEFAULT_PARTY_SIZE = 6

# 네이버 API
NAVER_SEARCH_API_URL = "https://openapi.naver.com/v1/search/local.json"
NAVER_BLOG_SEARCH_API_URL = "https://openapi.naver.com/v1/search/blog.json"
NAVER_PLACE_URL = "https://map.naver.com/v5/entry/place"
NAVER_BOOKING_BASE_URL = "https://booking.naver.com"

# 예약 이력 DB
HISTORY_DB_PATH = "data/history.db"

# 즐겨찾기 파일
FAVORITES_PATH = "data/favorites.json"
