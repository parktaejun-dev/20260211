"""상수 정의"""

# 예약 상태
RESERVATION_STATUS_SUCCESS = "success"
RESERVATION_STATUS_FAILED = "failed"
RESERVATION_STATUS_FULL = "full"
RESERVATION_STATUS_UNAVAILABLE = "unavailable"

# 세션 상태 키
SESSION_KEY_STEP = "current_step"
SESSION_KEY_SEARCH_RESULTS = "search_results"
SESSION_KEY_SELECTED_RESTAURANT = "selected_restaurant"
SESSION_KEY_RESERVATION_RESULT = "reservation_result"
SESSION_KEY_LOGGED_IN = "naver_logged_in"
SESSION_KEY_BROWSER_CONTEXT = "browser_context"

# 앱 단계
STEP_INPUT = "input"
STEP_SEARCH = "search"
STEP_RESERVE = "reserve"
STEP_RESULT = "result"

# 지역 좌표 기준점
LANDMARKS = {
    "광화문역": {"lat": 37.5710, "lng": 126.9769},
    "시청역": {"lat": 37.5657, "lng": 126.9769},
    "무교동": {"lat": 37.5680, "lng": 126.9810},
}

# CSS Selectors (네이버 예약 페이지 - 변경 시 여기만 수정)
SELECTORS = {
    # 로그인 페이지
    "login_id_input": "#id",
    "login_pw_input": "#pw",
    "login_button": ".btn_login",
    "login_error": "#err_common",
    # 네이버 지도 검색
    "map_search_input": ".input_search",
    "map_search_button": ".btn_search",
    "map_search_results": ".search_listview .item_search",
    # 식당 정보
    "place_name": ".place_name",
    "place_rating": ".rating",
    "place_review_count": ".review_count",
    "place_address": ".address",
    "place_booking_btn": "a[href*='booking.naver.com']",
    # 예약 폼
    "booking_date_picker": ".calendar",
    "booking_time_select": ".time_select",
    "booking_party_size": ".party_size",
    "booking_confirm_btn": ".btn_confirm",
    "booking_result": ".booking_result",
}
