"""메인 입력 페이지"""

import streamlit as st
from datetime import date

from app_config.settings import (
    AREA_OPTIONS,
    CUISINE_TYPES,
    BUDGET_OPTIONS,
    TIME_SLOTS,
    RADIUS_OPTIONS,
    MIN_PARTY_SIZE,
    MAX_PARTY_SIZE,
    DEFAULT_PARTY_SIZE,
)
from utils.date_helper import get_next_monday


def render_input_form() -> dict | None:
    """
    사용자 입력 폼을 렌더링합니다.
    제출 시 입력값 딕셔너리를 반환, 미제출 시 None 반환.
    """
    with st.form("search_form"):
        st.subheader("📌 검색 조건 입력")

        # 음식 종류
        cuisine = st.selectbox(
            "🍽️ 음식 종류",
            options=list(CUISINE_TYPES.keys()),
            index=0,
        )

        col1, col2 = st.columns(2)

        with col1:
            # 지역 선택
            area = st.selectbox(
                "📍 지역",
                options=list(AREA_OPTIONS.keys()),
                index=list(AREA_OPTIONS.keys()).index("무교동"),
            )

        with col2:
            # 반경
            radius_labels = {300: "300m", 500: "500m", 1000: "1km"}
            radius = st.select_slider(
                "🔍 검색 반경",
                options=RADIUS_OPTIONS,
                value=500,
                format_func=lambda x: radius_labels[x],
            )

        col3, col4 = st.columns(2)

        with col3:
            # 예산
            budget = st.selectbox(
                "💰 1인 예산",
                options=list(BUDGET_OPTIONS.keys()),
                index=list(BUDGET_OPTIONS.keys()).index("1.5~2만원"),
            )

        with col4:
            # 인원수
            party_size = st.number_input(
                "👥 인원수",
                min_value=MIN_PARTY_SIZE,
                max_value=MAX_PARTY_SIZE,
                value=DEFAULT_PARTY_SIZE,
                step=1,
            )

        col5, col6 = st.columns(2)

        with col5:
            # 날짜 선택 (기본: 다음 월요일)
            default_date = get_next_monday()
            reservation_date = st.date_input(
                "📅 날짜",
                value=default_date,
                min_value=date.today(),
                help="기본: 다음 월요일",
            )

        with col6:
            # 시간 선택
            time_slot = st.selectbox(
                "🕐 시간",
                options=TIME_SLOTS,
                index=TIME_SLOTS.index("12:00"),
            )

        # 제출 버튼
        submitted = st.form_submit_button(
            "🔍 맛집 검색하기", type="primary", use_container_width=True
        )

        if submitted:
            return {
                "cuisine": cuisine,
                "cuisine_keyword": CUISINE_TYPES[cuisine],
                "area": area,
                "area_coords": AREA_OPTIONS[area],
                "radius": radius,
                "budget": budget,
                "budget_range": BUDGET_OPTIONS[budget],
                "party_size": party_size,
                "date": reservation_date,
                "time": time_slot,
            }

    return None
