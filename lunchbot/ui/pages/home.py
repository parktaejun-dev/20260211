"""메인 입력 페이지"""

import streamlit as st
from datetime import date

from bot_config.settings import (
    AREA_CENTER,
    CUISINE_TYPES,
    BUDGET_OPTIONS,
    TIME_SLOTS,
    RADIUS_OPTIONS,
    DEFAULT_RADIUS,
    MIN_PARTY_SIZE,
    MAX_PARTY_SIZE,
    DEFAULT_PARTY_SIZE,
)
from bot_utils.date_helper import get_next_monday


def render_auto_select_button() -> dict | None:
    """
    자동 선택 버튼을 렌더링합니다.
    클릭 시 기본 설정으로 즉시 검색을 실행합니다 (전체 음식 종류).
    """
    st.markdown("### 🎲 자동 선택")
    st.caption(f"📍 기준: {AREA_CENTER['name']} | 반경 {DEFAULT_RADIUS // 1000}km | 전체 음식")

    if st.button("🎲 자동으로 10곳 추천받기", type="primary", use_container_width=True):
        default_date = get_next_monday()
        return {
            "cuisine": "전체",
            "cuisine_keyword": "맛집",  # 전체 음식 종류
            "area": AREA_CENTER["name"],
            "area_coords": {"lat": AREA_CENTER["lat"], "lng": AREA_CENTER["lng"]},
            "radius": DEFAULT_RADIUS,
            "budget": "상관없음",
            "budget_range": (0, 999999),
            "party_size": DEFAULT_PARTY_SIZE,
            "date": default_date,
            "time": "12:00",
            "auto_select": True,  # 자동선택 플래그
        }

    return None


def render_input_form() -> dict | None:
    """
    사용자 입력 폼을 렌더링합니다.
    """
    with st.form("search_form"):
        st.subheader("📌 검색 조건 입력")

        # 검색 대상 선택
        search_source = st.radio(
            "검색 대상", 
            ["네이버 검색 (실시간 추천)", "내 DB 검색 (즐겨찾기/이력)"], 
            horizontal=True,
            index=0
        )

        if "네이버" in search_source:
            # ── 기존 네이버 검색 폼 ──
            cuisine = st.selectbox(
                "🍽️ 음식 종류",
                options=list(CUISINE_TYPES.keys()),
                index=0,
            )

            col1, col2 = st.columns(2)
            with col1:
                radius_labels = {500: "500m", 1000: "1km", 1500: "1.5km", 2000: "2km"}
                radius = st.select_slider(
                    "🔍 검색 반경",
                    options=RADIUS_OPTIONS,
                    value=DEFAULT_RADIUS,
                    format_func=lambda x: radius_labels[x],
                )
            with col2:
                budget = st.selectbox(
                    "💰 1인 예산",
                    options=list(BUDGET_OPTIONS.keys()),
                    index=list(BUDGET_OPTIONS.keys()).index("1.5~2만원"),
                )

            col3, col4 = st.columns(2)
            with col3:
                party_size = st.number_input(
                    "👥 인원수",
                    min_value=MIN_PARTY_SIZE,
                    max_value=MAX_PARTY_SIZE,
                    value=DEFAULT_PARTY_SIZE,
                    step=1,
                )
            with col4:
                # 날짜 선택
                default_date = get_next_monday()
                reservation_date = st.date_input(
                    "📅 날짜",
                    value=default_date,
                    min_value=date.today(),
                )

            time_slot = st.selectbox(
                "⏰ 예약 시간",
                options=TIME_SLOTS,
                index=2
            )

            submitted = st.form_submit_button("🔍 맛집 찾기", type="primary", use_container_width=True)

            if submitted:
                return {
                    "source": "naver",
                    "cuisine": cuisine,
                    "cuisine_keyword": CUISINE_TYPES[cuisine],
                    "area": AREA_CENTER["name"],
                    "area_coords": {"lat": AREA_CENTER["lat"], "lng": AREA_CENTER["lng"]},
                    "radius": radius,
                    "budget": budget,
                    "budget_range": BUDGET_OPTIONS[budget],
                    "party_size": party_size,
                    "date": reservation_date,
                    "time": time_slot,
                    "auto_select": False,
                }
        
        else:
            # ── 내 DB 검색 폼 ──
            st.info("즐겨찾기에 저장된 나만의 맛집을 검색합니다.")
            query = st.text_input("검색어 (식당명, 메모, 주소)", placeholder="예: 국밥, 맛있는 집")
            
            submitted = st.form_submit_button("🔎 내 데이터에서 찾기", type="primary", use_container_width=True)
            
            if submitted:
                 import datetime
                 return {
                    "source": "db",
                    "query": query,
                    "cuisine": "내 DB 검색", # Display용
                    "radius": 0,
                    "budget": "전체",
                    "party_size": 0,
                    "date": date.today(),
                    "time": "",
                    "auto_select": False,
                }

    return None
