"""메인 입력 페이지"""

import streamlit as st
from datetime import date

from config.settings import (
    CUISINE_TYPES,
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
    with st.form("reservation_form"):
        st.subheader("📌 예약 정보 입력")

        # 음식 종류
        cuisine = st.selectbox(
            "음식 종류",
            options=list(CUISINE_TYPES.keys()),
            index=0,
            help="원하는 음식 종류를 선택하세요",
        )

        col1, col2 = st.columns(2)

        with col1:
            # 날짜 선택 (기본: 다음 월요일)
            default_date = get_next_monday()
            reservation_date = st.date_input(
                "📅 날짜",
                value=default_date,
                min_value=date.today(),
                help="예약할 날짜를 선택하세요 (기본: 다음 월요일)",
            )

        with col2:
            # 시간 선택
            time_slot = st.selectbox(
                "🕐 시간",
                options=TIME_SLOTS,
                index=TIME_SLOTS.index("12:00"),
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
            # 반경
            radius_labels = {300: "300m", 500: "500m", 1000: "1km"}
            radius = st.select_slider(
                "📍 검색 반경",
                options=RADIUS_OPTIONS,
                value=500,
                format_func=lambda x: radius_labels[x],
            )

        # 요청사항 (선택)
        request_note = st.text_input(
            "💬 요청사항 (선택)",
            placeholder="예: 단체석 준비 부탁드립니다",
        )

        # 제출 버튼
        col_search, col_reserve = st.columns(2)
        with col_search:
            search_submitted = st.form_submit_button(
                "🔍 맛집 검색하기", use_container_width=True
            )
        with col_reserve:
            direct_reserve = st.form_submit_button(
                "🚀 바로 예약하기", use_container_width=True
            )

        if search_submitted or direct_reserve:
            return {
                "cuisine": cuisine,
                "cuisine_keyword": CUISINE_TYPES[cuisine],
                "date": reservation_date,
                "time": time_slot,
                "party_size": party_size,
                "radius": radius,
                "request_note": request_note,
                "direct_reserve": direct_reserve,
            }

    return None


def render_login_sidebar():
    """사이드바에 네이버 로그인 정보 입력 폼을 렌더링합니다."""
    with st.sidebar:
        st.header("🔐 네이버 로그인")

        naver_id = st.text_input(
            "네이버 ID",
            type="default",
            placeholder="네이버 아이디 입력",
            key="naver_id",
        )
        naver_pw = st.text_input(
            "비밀번호",
            type="password",
            placeholder="비밀번호 입력",
            key="naver_pw",
        )

        st.caption("⚠️ 로그인 정보는 세션에만 유지되며 저장되지 않습니다.")

        # Slack 알림 설정 (선택)
        st.divider()
        st.subheader("📢 알림 설정 (선택)")
        slack_webhook = st.text_input(
            "Slack Webhook URL",
            type="password",
            placeholder="https://hooks.slack.com/...",
            key="slack_webhook",
        )

        return {
            "naver_id": naver_id,
            "naver_pw": naver_pw,
            "slack_webhook": slack_webhook,
        }
