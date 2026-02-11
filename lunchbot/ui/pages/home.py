"""메인 입력 페이지"""

import streamlit as st
from datetime import date

from app_config.settings import (
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
from utils.date_helper import get_next_monday


def render_auto_select_button() -> dict | None:
    """
    자동 선택 버튼을 렌더링합니다.
    클릭 시 기본 설정으로 즉시 검색을 실행합니다 (전체 음식 종류).
    """
    st.markdown("### 🎲 자동 선택")
    st.caption(f"📍 기준: {AREA_CENTER['name']} | 반경 {DEFAULT_RADIUS // 1000}km | 전체 음식")

    if st.button("🎲 자동으로 3곳 추천받기", type="primary", use_container_width=True):
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
            # 반경
            radius_labels = {500: "500m", 1000: "1km", 1500: "1.5km", 2000: "2km"}
            radius = st.select_slider(
                "🔍 검색 반경",
                options=RADIUS_OPTIONS,
                value=DEFAULT_RADIUS,
                format_func=lambda x: radius_labels[x],
            )

        with col2:
            # 예산
            budget = st.selectbox(
                "💰 1인 예산",
                options=list(BUDGET_OPTIONS.keys()),
                index=list(BUDGET_OPTIONS.keys()).index("1.5~2만원"),
            )

        col3, col4 = st.columns(2)

        with col3:
            # 인원수
            party_size = st.number_input(
                "👥 인원수",
                min_value=MIN_PARTY_SIZE,
                max_value=MAX_PARTY_SIZE,
                value=DEFAULT_PARTY_SIZE,
                step=1,
            )

        with col4:
            pass  # 균형 맞추기

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
                "area": AREA_CENTER["name"],
                "area_coords": {"lat": AREA_CENTER["lat"], "lng": AREA_CENTER["lng"]},
                "radius": radius,
                "budget": budget,
                "budget_range": BUDGET_OPTIONS[budget],
                "party_size": party_size,
                "date": reservation_date,
                "time": time_slot,
            }

    return None

