"""
부서점심 자동예약 (LunchBot)
============================

음식 종류, 지역, 예산, 인원만 선택하면
광화문/시청/무교동 인근 맛집을 찾아주는 Streamlit 앱

실행: streamlit run app.py
"""

import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st

from app_config.constants import SESSION_KEY_SEARCH_RESULTS, SESSION_KEY_INPUT_DATA
from core.search import RestaurantSearcher
from core.notification import SlackNotifier
from ui.styles import CUSTOM_CSS
from ui.components import render_header
from ui.pages.home import render_input_form, render_auto_select_button
from ui.pages.search_results import render_search_results
from ui.pages.history import render_history_page
from utils.date_helper import format_date_korean


# ── 페이지 설정 ──────────────────────────────────────────
st.set_page_config(
    page_title="KOBACO 부서점심 자동예약",
    page_icon="🍽️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# 커스텀 CSS 적용
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ── Secrets에서 API 키 로드 ───────────────────────────────
def _get_secret(key: str, default: str = "") -> str:
    """st.secrets에서 값을 안전하게 읽습니다."""
    try:
        return st.secrets[key]
    except (KeyError, FileNotFoundError):
        return default


NAVER_CLIENT_ID = _get_secret("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = _get_secret("NAVER_CLIENT_SECRET")
SLACK_WEBHOOK_URL = _get_secret("SLACK_WEBHOOK_URL")

if not NAVER_CLIENT_ID or not NAVER_CLIENT_SECRET:
    st.error(
        "⚠️ 네이버 API 키가 설정되지 않았습니다.\n\n"
        "**Streamlit Cloud**: Settings → Secrets 에 아래 내용을 추가하세요.\n\n"
        "```toml\n"
        'NAVER_CLIENT_ID = "your_client_id"\n'
        'NAVER_CLIENT_SECRET = "your_client_secret"\n'
        "```\n\n"
        "**로컬 실행**: `.streamlit/secrets.toml` 파일을 생성하세요."
    )
    st.stop()


# ── 세션 상태 초기화 ──────────────────────────────────────
if SESSION_KEY_SEARCH_RESULTS not in st.session_state:
    st.session_state[SESSION_KEY_SEARCH_RESULTS] = None
if SESSION_KEY_INPUT_DATA not in st.session_state:
    st.session_state[SESSION_KEY_INPUT_DATA] = None


# ── 메인 영역 ────────────────────────────────────────────
render_header()

# 탭 구성
tab_search, tab_history = st.tabs(["🔍 맛집 검색", "📜 검색 이력"])


def _run_search(form_data: dict) -> None:
    """검색을 실행하고 결과를 세션에 저장합니다."""
    import random

    with st.spinner("🔍 맛집을 검색하고 있습니다..."):
        try:
            coords = form_data["area_coords"]
            searcher = RestaurantSearcher(
                client_id=NAVER_CLIENT_ID,
                client_secret=NAVER_CLIENT_SECRET,
                center_lat=coords["lat"],
                center_lng=coords["lng"],
            )

            results = searcher.search(
                area_name=form_data["area"],
                cuisine_keyword=form_data["cuisine_keyword"],
                radius=form_data["radius"],
            )

            # 결과가 없으면 자동 반경 확대
            if not results:
                results, _ = searcher.search_with_expanded_radius(
                    area_name=form_data["area"],
                    cuisine_keyword=form_data["cuisine_keyword"],
                    initial_radius=form_data["radius"],
                )
                if results:
                    st.info("검색 반경을 자동으로 넓혔습니다.")

            # 자동선택 모드: 3개만 랜덤 선정
            if form_data.get("auto_select") and results and len(results) > 3:
                results = random.sample(results, 3)

            st.session_state[SESSION_KEY_SEARCH_RESULTS] = results
            st.session_state[SESSION_KEY_INPUT_DATA] = form_data
            st.rerun()

        except Exception as e:
            st.error(f"검색 중 오류가 발생했습니다: {str(e)}")


# ── 검색 탭 ───────────────────────────────────────────────
with tab_search:

    # 검색 결과가 없을 때: 입력 폼 표시
    if st.session_state[SESSION_KEY_SEARCH_RESULTS] is None:

        # 자동 선택 버튼
        auto_data = render_auto_select_button()
        if auto_data:
            _run_search(auto_data)

        st.markdown("---")

        # 수동 검색 폼
        form_data = render_input_form()
        if form_data:
            _run_search(form_data)

    # 검색 결과가 있을 때: 결과 표시
    else:
        results = st.session_state[SESSION_KEY_SEARCH_RESULTS]
        input_data = st.session_state[SESSION_KEY_INPUT_DATA]

        selected = render_search_results(results, input_data)

        if selected:
            # 이력 저장
            from core.db import db

            db.save_search_result(
                restaurant_name=selected.name,
                address=selected.road_address or selected.address,
                phone=selected.phone,
                cuisine_type=input_data["cuisine"],
                area=input_data["area"],
                reservation_date=format_date_korean(input_data["date"]),
                reservation_time=input_data["time"],
                party_size=input_data["party_size"],
                link=selected.link,
            )

            # Slack 알림
            if SLACK_WEBHOOK_URL:
                notifier = SlackNotifier(SLACK_WEBHOOK_URL)
                notifier.send_search_result(
                    restaurant_name=selected.name,
                    address=selected.road_address or selected.address,
                    date_str=format_date_korean(input_data["date"]),
                    time_str=input_data["time"],
                    party_size=input_data["party_size"],
                    phone=selected.phone,
                )

        # 다시 검색 버튼
        st.markdown("---")
        if st.button("🔄 새로 검색하기", use_container_width=True):
            st.session_state[SESSION_KEY_SEARCH_RESULTS] = None
            st.session_state[SESSION_KEY_INPUT_DATA] = None
            if "random_picks" in st.session_state:
                del st.session_state["random_picks"]
            st.rerun()


# ── 이력 탭 ───────────────────────────────────────────────
with tab_history:
    render_history_page()

