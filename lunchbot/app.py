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

from config.constants import SESSION_KEY_SEARCH_RESULTS, SESSION_KEY_INPUT_DATA
from core.search import RestaurantSearcher
from core.notification import SlackNotifier
from ui.styles import CUSTOM_CSS
from ui.components import render_header
from ui.pages.home import render_input_form, render_sidebar
from ui.pages.search_results import render_search_results
from ui.pages.history import render_history_page, save_search_result
from utils.date_helper import format_date_korean


# ── 페이지 설정 ──────────────────────────────────────────
st.set_page_config(
    page_title="KOBACO 부서점심 자동예약",
    page_icon="🍽️",
    layout="centered",
    initial_sidebar_state="expanded",
)

# 커스텀 CSS 적용
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ── 세션 상태 초기화 ──────────────────────────────────────
if SESSION_KEY_SEARCH_RESULTS not in st.session_state:
    st.session_state[SESSION_KEY_SEARCH_RESULTS] = None
if SESSION_KEY_INPUT_DATA not in st.session_state:
    st.session_state[SESSION_KEY_INPUT_DATA] = None


# ── 사이드바: API 설정 ────────────────────────────────────
sidebar_info = render_sidebar()


# ── 메인 영역 ────────────────────────────────────────────
render_header()

# 탭 구성
tab_search, tab_history = st.tabs(["🔍 맛집 검색", "📜 검색 이력"])


# ── 검색 탭 ───────────────────────────────────────────────
with tab_search:

    # 검색 결과가 없을 때: 입력 폼 표시
    if st.session_state[SESSION_KEY_SEARCH_RESULTS] is None:
        form_data = render_input_form()

        if form_data:
            # API 키 검증
            if not sidebar_info["client_id"] or not sidebar_info["client_secret"]:
                st.error("⚠️ 사이드바에서 네이버 API 키를 입력해주세요.")
                st.stop()

            # 검색 실행
            with st.spinner("🔍 맛집을 검색하고 있습니다..."):
                try:
                    coords = form_data["area_coords"]
                    searcher = RestaurantSearcher(
                        client_id=sidebar_info["client_id"],
                        client_secret=sidebar_info["client_secret"],
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

                    st.session_state[SESSION_KEY_SEARCH_RESULTS] = results
                    st.session_state[SESSION_KEY_INPUT_DATA] = form_data
                    st.rerun()

                except Exception as e:
                    st.error(f"검색 중 오류가 발생했습니다: {str(e)}")

    # 검색 결과가 있을 때: 결과 표시
    else:
        results = st.session_state[SESSION_KEY_SEARCH_RESULTS]
        input_data = st.session_state[SESSION_KEY_INPUT_DATA]

        selected = render_search_results(results, input_data)

        if selected:
            # 이력 저장
            save_search_result(
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
            slack_url = sidebar_info.get("slack_webhook")
            if slack_url:
                notifier = SlackNotifier(slack_url)
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
            st.rerun()


# ── 이력 탭 ───────────────────────────────────────────────
with tab_history:
    render_history_page()
